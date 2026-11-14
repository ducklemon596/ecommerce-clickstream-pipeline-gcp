"""Optional local MongoDB test for Counter output and publication safeguards."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import uuid
from glamira_pipeline.ip_location.pipeline import enrich_collection
from glamira_pipeline.mongo import connect

URI = os.environ.get('GLAMIRA_TEST_MONGODB_URI')
BIN = Path('IP-COUNTRY-REGION-CITY.BIN')


@unittest.skipUnless(URI and BIN.is_file(), 'local MongoDB URI and BIN required')
class IpMongoIntegrationTests(unittest.TestCase):
    def test_counter_publish_and_existing_target_rejection(self):
        with connect(URI) as client:
            db = client['glamira_ip_sample_test_' + uuid.uuid4().hex]
            try:
                db.events.insert_many([{'ip': '8.8.8.8'}, {'ip': '8.8.8.8'}, {'ip': None}])
                with TemporaryDirectory() as directory:
                    output = Path(directory) / 'run'
                    result = enrich_collection(db.events, 'ip_locations', BIN, output)
                    self.assertEqual(result['events'], 3)
                    self.assertEqual(result['unique_valid_ips'], 1)
                    self.assertEqual(db.ip_locations.count_documents({}), 1)
                    location = db.ip_locations.find_one({})
                    self.assertNotIn('event_count', location)
                    self.assertIsNotNone(db.enrichment_runs.find_one({'_id': location['database_id']}))
                    with self.assertRaisesRegex(ValueError, 'already exists'):
                        enrich_collection(db.events, 'ip_locations', BIN, Path(directory) / 'other')
            finally:
                client.drop_database(db.name)
