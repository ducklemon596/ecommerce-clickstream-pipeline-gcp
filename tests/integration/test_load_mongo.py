"""Optional local MongoDB tests for load-summary: full load, crash replay, resume and reconciliation.

Run with a disposable server, e.g.::

    docker run -d --rm -p 127.0.0.1:27099:27017 mongo:8.0
    GLAMIRA_TEST_MONGODB_URI=mongodb://127.0.0.1:27099/ uv run python -m unittest tests.integration.test_load_mongo
"""
import io
import os
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
import unittest
import uuid

from bson import BSON, ObjectId

from glamira_pipeline.load.checkpoint import RUNS_COLLECTION
from glamira_pipeline.load.loader import LoadError, LoadOptions, load_summary
from glamira_pipeline.load.reconcile import reconcile
from glamira_pipeline.mongo import connect

URI = os.environ.get("GLAMIRA_TEST_MONGODB_URI")
MEMBER = "dump/countly/summary.bson"
SOURCE = [BSON.encode({"_id": ObjectId(), "collection": ("view", "cart", "checkout")[i % 3],
                       "time_stamp": 1_570_000_000 + i}) for i in range(5_000)]


@unittest.skipUnless(URI, "set GLAMIRA_TEST_MONGODB_URI to a disposable local MongoDB")
class LoadMongoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = connect(URI)
        self.db = self.client["glamira_load_test_" + uuid.uuid4().hex[:8]]
        self.tmp = TemporaryDirectory()
        self.archive = Path(self.tmp.name) / "dump.tar.gz"
        payload = b"".join(SOURCE)
        with tarfile.open(self.archive, "w:gz") as tar:
            info = tarfile.TarInfo(MEMBER)
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
        self.options = LoadOptions(workers=3, batch_docs=100)

    def tearDown(self):
        self.client.drop_database(self.db.name)
        self.client.close()
        self.tmp.cleanup()

    def test_load_then_rerun_is_a_no_op(self):
        run = load_summary(self.archive, MEMBER, self.db, "summary", self.options)
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["progress"]["inserted"], len(SOURCE))
        again = load_summary(self.archive, MEMBER, self.db, "summary", self.options)
        self.assertEqual(again["_id"], run["_id"])
        self.assertEqual(self.db.summary.count_documents({}), len(SOURCE))

    def test_crash_replay_counts_duplicates_and_completes(self):
        # Simulate a crash: half the documents are in the target, but the checkpoint
        # (a failed run) only covers the first 10 batches.
        first = load_summary(self.archive, MEMBER, self.db, "summary", self.options)
        runs = self.db[RUNS_COLLECTION]
        self.db.summary.delete_many({"_id": {"$in": [BSON(d).decode()["_id"] for d in SOURCE[2_500:]]}})
        runs.update_one({"_id": first["_id"]}, {"$set": {"status": "failed", "progress.batches_done": 10,
                                                         "progress.offset": 0}})
        run = load_summary(self.archive, MEMBER, self.db, "summary", self.options)
        progress = run["progress"]
        self.assertEqual(run["status"], "completed")
        self.assertEqual(progress["docs_skipped"], 1_000)
        self.assertEqual(progress["duplicates"], 1_500)  # batches 10-24 were already present
        self.assertEqual(progress["inserted"], 2_500)
        self.assertEqual(self.db.summary.count_documents({}), len(SOURCE))

    def test_non_empty_target_without_matching_run_is_refused(self):
        self.db.summary.insert_one({"_id": 1})
        with self.assertRaisesRegex(LoadError, "already has documents"):
            load_summary(self.archive, MEMBER, self.db, "summary", self.options)

    def test_reconcile_detects_match_and_missing_documents(self):
        load_summary(self.archive, MEMBER, self.db, "summary", self.options)
        result = reconcile(self.archive, MEMBER, self.db, "summary", sample_size=200, seed=1)
        self.assertTrue(result["ok"])
        self.assertEqual(result["sample"]["identical_bytes"], 200)
        self.db.summary.delete_one({"collection": "cart"})
        result = reconcile(self.archive, MEMBER, self.db, "summary", sample_size=200, seed=1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["event_type_differences"]["cart"]["target"],
                         result["event_type_differences"]["cart"]["source"] - 1)


if __name__ == "__main__":
    unittest.main()
