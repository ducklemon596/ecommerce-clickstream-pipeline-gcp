"""Test bounded tar/BSON to Extended JSON sample extraction."""
from io import BytesIO
import json
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
import unittest

from bson import BSON, Int64, ObjectId, json_util

from glamira_pipeline.sampling.extract import MEMBER, extract_sample


def make_archive(path: Path, content: bytes) -> None:
    with tarfile.open(path, "w:gz") as archive:
        entry = tarfile.TarInfo(MEMBER)
        entry.size = len(content)
        archive.addfile(entry, BytesIO(content))


class ExtractTests(unittest.TestCase):
    def test_extract_creates_only_json_and_metadata_and_respects_limit(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "source.tar.gz"
            documents = [{"_id": ObjectId(), "n": Int64(5)}, {"_id": ObjectId(), "n": Int64(6)}]
            make_archive(archive, b"".join(BSON.encode(doc) for doc in documents))
            output = root / "sample.json"
            paths = extract_sample(archive, output, 1)
            self.assertEqual(paths, (output, root / "sample.metadata.json"))
            self.assertEqual(json_util.loads(output.read_text()), documents[:1])
            metadata = json.loads(paths[1].read_text())
            self.assertEqual(metadata["source_documents_read"], 1)
            self.assertEqual(metadata["json_documents_written"], 1)
            self.assertFalse((root / "sample.bson").exists())

    def test_corrupt_input_does_not_overwrite_existing_outputs(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "source.tar.gz"
            make_archive(archive, (20).to_bytes(4, "little") + b"short")
            output = root / "sample.json"
            metadata = root / "sample.metadata.json"
            output.write_text("old sample")
            metadata.write_text("old metadata")
            with self.assertRaises(ValueError):
                extract_sample(archive, output, 10)
            self.assertEqual(output.read_text(), "old sample")
            self.assertEqual(metadata.read_text(), "old metadata")

    def test_bson_output_extension_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "source.tar.gz"
            make_archive(archive, BSON.encode({"x": 1}))
            with self.assertRaisesRegex(ValueError, "end in .json"):
                extract_sample(archive, root / "sample.bson", 1)


if __name__ == "__main__":
    unittest.main()
