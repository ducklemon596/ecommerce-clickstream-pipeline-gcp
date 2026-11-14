"""Unit tests for the summary loader's pure parts: BSON stream, batching, watermark and writer."""
import io
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from bson import BSON
from pymongo.errors import BulkWriteError

from glamira_pipeline.load.bson_stream import iter_batches, iter_documents, open_member, pigz_available
from glamira_pipeline.load.checkpoint import Watermark
from glamira_pipeline.load.writer import insert_batch

MEMBER = "dump/countly/summary.bson"


def docs(n: int, pad: int = 0) -> list[bytes]:
    return [BSON.encode({"_id": i, "collection": "view", "pad": "x" * pad}) for i in range(n)]


def make_archive(path: Path, payload: bytes, member: str = MEMBER) -> None:
    with tarfile.open(path, "w:gz") as tar:
        info = tarfile.TarInfo(member)
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))


class StreamTests(unittest.TestCase):
    def test_documents_are_cut_by_length_prefix_across_read_blocks(self):
        source = docs(50, pad=300)
        with mock.patch("glamira_pipeline.load.bson_stream.READ_BLOCK", 1000):
            out = list(iter_documents(io.BytesIO(b"".join(source))))
        self.assertEqual(out, source)

    def test_invalid_length_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid BSON document length"):
            list(iter_documents(io.BytesIO((3).to_bytes(4, "little") + b"\x00" * 10)))

    def test_truncated_document_is_rejected(self):
        whole = docs(1)[0]
        with self.assertRaisesRegex(ValueError, "truncated"):
            list(iter_documents(io.BytesIO(whole + whole[:-2])))

    def test_batches_respect_document_and_byte_limits_with_contiguous_offsets(self):
        source = docs(25, pad=100)
        size = len(source[0])
        batches = list(iter_batches(io.BytesIO(b"".join(source)), max_docs=10, max_bytes=size * 4))
        self.assertEqual([len(b.docs) for b in batches], [4, 4, 4, 4, 4, 4, 1])
        self.assertEqual([b.index for b in batches], list(range(7)))
        self.assertEqual(batches[0].start_offset, 0)
        for previous, current in zip(batches, batches[1:]):
            self.assertEqual(previous.end_offset, current.start_offset)
        self.assertEqual(batches[-1].end_offset, size * 25)
        self.assertEqual([d for b in batches for d in b.docs], source)

    def test_oversized_document_forms_its_own_batch(self):
        source = docs(1) + docs(1, pad=500) + docs(1)
        batches = list(iter_batches(io.BytesIO(b"".join(source)), max_docs=10, max_bytes=100))
        self.assertEqual([len(b.docs) for b in batches], [1, 1, 1])

    def test_open_member_reads_archive_with_and_without_pigz(self):
        source = docs(30)
        modes = [False] + ([True] if pigz_available() else [])
        with TemporaryDirectory() as directory:
            archive = Path(directory) / "dump.tar.gz"
            make_archive(archive, b"".join(source))
            for pigz in modes:
                with self.subTest(pigz=pigz), open_member(archive, MEMBER, pigz=pigz) as reader:
                    self.assertEqual(list(iter_documents(reader)), source)
                    self.assertGreater(reader.bytes, 0)

    def test_missing_member_is_an_error(self):
        modes = [False] + ([True] if pigz_available() else [])
        with TemporaryDirectory() as directory:
            archive = Path(directory) / "dump.tar.gz"
            make_archive(archive, b"".join(docs(2)), member="dump/other.bson")
            for pigz in modes:
                with self.subTest(pigz=pigz), self.assertRaises((ValueError, RuntimeError)):
                    with open_member(archive, MEMBER, pigz=pigz) as reader:
                        list(iter_documents(reader))

    def test_stopping_early_does_not_raise(self):
        if not pigz_available():
            self.skipTest("pigz not installed")
        with TemporaryDirectory() as directory:
            archive = Path(directory) / "dump.tar.gz"
            make_archive(archive, b"".join(docs(20_000)))
            with open_member(archive, MEMBER, pigz=True) as reader:
                next(iter_documents(reader))


class WatermarkTests(unittest.TestCase):
    def test_out_of_order_completion_only_advances_over_contiguous_batches(self):
        mark = Watermark(next_index=5, offset=500)
        mark.complete(6, 700)
        self.assertEqual((mark.next_index, mark.offset), (5, 500))
        mark.complete(8, 900)
        mark.complete(5, 600)
        self.assertEqual((mark.next_index, mark.offset), (7, 700))
        mark.complete(7, 800)
        self.assertEqual((mark.next_index, mark.offset), (9, 900))


class WriterTests(unittest.TestCase):
    def test_success_counts_every_document(self):
        collection = mock.Mock()
        self.assertEqual(insert_batch(collection, docs(3)), (3, 0))
        _, kwargs = collection.insert_many.call_args
        self.assertFalse(kwargs["ordered"])

    def test_duplicate_keys_are_counted_not_raised(self):
        collection = mock.Mock()
        collection.insert_many.side_effect = BulkWriteError(
            {"nInserted": 1, "writeErrors": [{"code": 11000, "index": 0}, {"code": 11000, "index": 2}]})
        self.assertEqual(insert_batch(collection, docs(3)), (1, 2))

    def test_other_write_errors_are_raised(self):
        collection = mock.Mock()
        collection.insert_many.side_effect = BulkWriteError(
            {"nInserted": 0, "writeErrors": [{"code": 11000}, {"code": 121}]})
        with self.assertRaises(BulkWriteError):
            insert_batch(collection, docs(2))

    def test_write_concern_errors_are_raised(self):
        collection = mock.Mock()
        collection.insert_many.side_effect = BulkWriteError(
            {"nInserted": 2, "writeErrors": [], "writeConcernErrors": [{"code": 64}]})
        with self.assertRaises(BulkWriteError):
            insert_batch(collection, docs(2))


if __name__ == "__main__":
    unittest.main()
