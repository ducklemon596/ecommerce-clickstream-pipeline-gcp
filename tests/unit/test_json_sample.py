"""Streaming Extended JSON fidelity and malformed-file checks."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bson import Decimal128, Int64, ObjectId, json_util

from glamira_pipeline.sampling.json_reader import iter_json_documents


class JsonSampleTests(unittest.TestCase):
    def read_text(self, text, chunk_size=7):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.json'
            path.write_text(text, encoding='utf-8')
            return list(iter_json_documents(path, chunk_size))

    def test_canonical_types_survive_document_and_chunk_boundaries(self):
        docs = [{'_id': ObjectId(), 'large': Int64(1), 'decimal': Decimal128('1.25'), 'nested': [{'label': 'é, ] [ "'}]}, {'null': None, 'flag': False}]
        text = json_util.dumps(docs, json_options=json_util.CANONICAL_JSON_OPTIONS, ensure_ascii=False)
        result = self.read_text(text)
        self.assertEqual(result, docs)
        self.assertIsInstance(result[0]['large'], Int64)
        self.assertIsInstance(result[0]['decimal'], Decimal128)
        self.assertIsInstance(result[0]['_id'], ObjectId)

    def test_empty_array(self):
        self.assertEqual(self.read_text(' \n [ ] \n '), [])

    def test_malformed_and_non_document_inputs_are_rejected(self):
        for text in ('', '{}', '[1]', '[{},]', '[{}', '[{}] extra', '[{} {}]', '[{bad}]'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.read_text(text)
