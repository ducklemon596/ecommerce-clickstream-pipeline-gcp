"""Synthetic tests for IP normalization, lookup statuses and BIN metadata."""
from pathlib import Path
from types import SimpleNamespace
import unittest

from glamira_pipeline.ip_location.lookup import bin_metadata, event_address, lookup_address
from glamira_pipeline.ip_location.source import local_client


class Reader:
    def __init__(self, _path=None, mode="FILE_IO"):
        self.mode = mode
        self.calls = []

    def get_all(self, address):
        self.calls.append(address)
        if address == "1.1.1.1":
            return SimpleNamespace(country_short="-", country_long="-", region="-", city="-")
        if address == "9.9.9.9":
            raise OSError("lookup failed")
        return SimpleNamespace(country_short="US", country_long="United States", region="California", city="Mountain View")

    def close(self):
        pass


class IpLocationTests(unittest.TestCase):
    def test_event_classification_uses_only_ip(self):
        self.assertEqual(event_address({"ip": None})[0], "null")
        self.assertEqual(event_address({"user_ip": "8.8.8.8"})[0], "missing")
        self.assertEqual(event_address({"ip": "bad"})[0], "invalid_format")
        self.assertEqual(event_address({"ip": 123})[0], "invalid_type")
        self.assertEqual(event_address({"ip": "  "})[0], "empty")
        self.assertEqual(event_address({})[0], "missing")
        self.assertEqual(event_address({"ip": "2001:4860:4860:0:0:0:0:8888"})[1], "2001:4860:4860::8888")

    def test_lookup_outcomes(self):
        reader = Reader()
        self.assertEqual(lookup_address(reader, "8.8.8.8", False)["status"], "resolved")
        self.assertEqual(lookup_address(reader, "1.1.1.1", False)["status"], "no_match")
        self.assertEqual(lookup_address(reader, "9.9.9.9", False)["status"], "lookup_failed")
        self.assertEqual(lookup_address(reader, "10.0.0.1", False)["status"], "not_public")
        self.assertEqual(lookup_address(reader, "2001:4860:4860::8888", False)["status"], "unsupported_ipv6")

    def test_loopback_uri_only(self):
        with self.assertRaises(ValueError):
            local_client("mongodb://example.com:27017/")
        with self.assertRaises(ValueError):
            local_client("mongodb+srv://example.com/")
        client = local_client("mongodb://127.0.0.1:27017/")
        client.close()

    def test_real_bin_header_if_available(self):
        path = Path("IP-COUNTRY-REGION-CITY.BIN")
        if not path.exists():
            self.skipTest("local IP2Location BIN not present")
        info = bin_metadata(path)
        self.assertEqual(info["edition"], 3)
        self.assertFalse(info["ipv6_supported"])


if __name__ == "__main__":
    unittest.main()
