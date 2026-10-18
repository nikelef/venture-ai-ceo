import unittest
from ai_ceo.validation import COUNTS, assessment


class ValidationTests(unittest.TestCase):
    def fixture(self):
        return {"experiment": "agency-handoff-v1", "price_cents": 900, "currency": "EUR",
                **{key: 0 for key in COUNTS}, "collection_enabled": True, "acquisition_sources": []}

    def test_no_exposure_does_not_reject_demand(self):
        data = assessment(self.fixture())
        self.assertIn("distribution_unresolved", data["decision"])
        self.assertIsNone(data["verified_unique_visitors"])
        self.assertFalse(data["demand_validated"])

    def test_unverified_signups_and_high_session_counts_cannot_approve_development(self):
        sample = self.fixture()
        sample.update(candidate_relevant_sessions=1000, completed_evaluations=200, registrations=20,
                      willing_to_pay_unverified=10, acquisition_sources=[{"source": "organic", "sessions": 1000}])
        data = assessment(sample)
        self.assertIn("unverified_interest", data["decision"])
        self.assertFalse(data["demand_validated"])

    def test_independent_intent_triggers_review_and_does_not_claim_market_fit(self):
        sample = self.fixture()
        sample.update(registrations=3, willing_to_pay_unverified=3, independently_verified_willing_to_pay=3)
        data = assessment(sample)
        self.assertIn("review_customer_evidence", data["decision"])
        self.assertFalse(data["demand_validated"])

    def test_operator_gate_and_inconsistent_data_fail_closed(self):
        sample = self.fixture(); sample["collection_enabled"] = False
        self.assertIn("blocked", assessment(sample)["decision"])
        for change in ({"completed_evaluations": 1}, {"registrations": -1}, {"price_cents": 1}, {"registrations": True},
                       {"acquisition_sources": [{"source": "guide", "sessions": 1, "email": "forbidden"}]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                assessment({**self.fixture(), **change})


if __name__ == "__main__":
    unittest.main()
