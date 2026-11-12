"""Guard against overstating temporal inference from incomplete research windows."""
import unittest

from timing import classify


def anchor(kind="conflict", matches=None):
    """Create a synthetic selector with old URL value and newly selected value."""
    return {"_id": "a", "kind": kind, "key": "alloy", "product_id": "10", "store_id": "7",
            "selected_value": "new", "anchor_url_values": [] if kind == "missing_key" else ["old"],
            "device_id_available": True, "matches": matches or []}


def observation(seconds, value, selected=None):
    """Represent one ordered context observation without a device identifier."""
    return {"_id": str(seconds), "collection": "select_product_option", "seconds_from_anchor": seconds,
            "url_values_for_key": [] if value is None else [value],
            "selected_values_for_key": [] if selected is None else [selected]}


class TimingEvidenceTests(unittest.TestCase):
    def test_prior_old_then_successor_selected_supports_only_observed_transition(self):
        result = classify(anchor(matches=[observation(-5, "old"), observation(6, "new")]))
        self.assertEqual(result["status"], "confirmed_pre_to_selected")
        self.assertEqual(result["seconds_to_next_url"], 6)
        self.assertNotIn("configuration", result)

    def test_missing_future_is_inconclusive_not_a_contradiction(self):
        result = classify(anchor(matches=[observation(-5, "old")]))
        self.assertEqual(result["status"], "inconclusive_no_successor_url")

    def test_competing_delta_prevents_false_confirmation(self):
        result = classify(anchor(matches=[observation(-5, "old"), observation(1, None, "other"), observation(6, "new")]))
        self.assertEqual(result["status"], "inconclusive_intervening_selection")

    def test_timestamp_tie_is_not_broken_by_record_id(self):
        result = classify(anchor(matches=[observation(-5, "old"), observation(0, "old"), observation(6, "new")]))
        self.assertEqual(result["status"], "inconclusive_anchor_timestamp_tie")

    def test_one_old_successor_does_not_establish_persistence(self):
        result = classify(anchor(matches=[observation(-5, "old"), observation(1, "old")]))
        self.assertEqual(result["status"], "inconclusive_one_old_successor")

    def test_two_old_successors_are_counterevidence_to_url_catchup(self):
        result = classify(anchor(matches=[observation(-5, "old"), observation(1, "old"), observation(2, "old")]))
        self.assertEqual(result["status"], "persistent_old_url_counterevidence")

    def test_missing_key_support_is_not_a_complete_configuration(self):
        result = classify(anchor("missing_key", [observation(2, "new")]))
        self.assertEqual(result["status"], "missing_key_forward_support")

    def test_disagreeing_same_second_successors_are_inconclusive(self):
        result = classify(anchor(matches=[observation(-5, "old"), observation(2, "new"), observation(2, "other")]))
        self.assertEqual(result["status"], "inconclusive_successor_timestamp_tie")


if __name__ == "__main__":
    unittest.main()
