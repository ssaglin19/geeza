"""Evaluate GLiNER2 vs anchor-based page matching for control scoring."""
import unittest
from gliner import GLiNER
from boosh_flow.control_scorer import Control, extract_controls, TfidfScorer


class TestGLiNERControlScoring(unittest.TestCase):
    """Compare GLiNER2 entity extraction vs TF-IDF for control matching."""

    @classmethod
    def setUpClass(cls):
        # Load the smallest GLiNER2 model for testing
        cls.model = GLiNER.from_pretrained("fastino/gliner2-multi-v1")
        cls.tfidf = TfidfScorer()

    def test_gliner_finds_pay_button(self):
        """GLiNER should identify 'Pay Now' as a payment-related control."""
        text = "Pay Now Contact Us Sign In Home"
        labels = ["payment action", "navigation link", "login button"]
        
        entities = self.model.predict_entities(text, labels)
        
        # GLiNER should find "Pay Now" as a payment action
        payment_entities = [e for e in entities if e["label"] == "payment action"]
        self.assertTrue(any("pay" in e["text"].lower() for e in payment_entities))

    def test_gliner_vs_tfidf_on_fixture_page(self):
        """Compare GLiNER and TF-IDF on a realistic page snapshot."""
        # Simulate a bill pay page
        elements = [
            {"selector": "#pay-btn", "text": "Pay Bill"},
            {"selector": "#history", "text": "Payment History"},
            {"selector": "#settings", "text": "Account Settings"},
            {"selector": "#logout", "text": "Sign Out"},
        ]
        controls = extract_controls({"elements": elements})
        
        # TF-IDF approach
        tfidf_scores = self.tfidf.score(controls, "pay bill")
        tfidf_best = tfidf_scores[0] if tfidf_scores else None
        
        # GLiNER approach
        page_text = " ".join(e["text"] for e in elements)
        labels = ["payment button", "history link", "settings link", "logout button"]
        gliner_entities = self.model.predict_entities(page_text, labels)
        gliner_payment = [e for e in gliner_entities if e["label"] == "payment button"]
        
        # Both should identify the pay button
        self.assertIsNotNone(tfidf_best)
        self.assertEqual(tfidf_best.control.text, "Pay Bill")
        self.assertTrue(any("pay" in e["text"].lower() for e in gliner_payment))

    def test_gliner_handles_synonyms(self):
        """GLiNER should match semantic equivalents, not just keywords."""
        # "Submit payment" vs "pay bill" — different words, same meaning
        elements = [
            {"selector": "#submit", "text": "Submit Payment"},
            {"selector": "#cancel", "text": "Cancel"},
        ]
        controls = extract_controls({"elements": elements})
        
        # TF-IDF might miss this (no "pay" keyword)
        tfidf_scores = self.tfidf.score(controls, "pay bill")
        tfidf_best_score = tfidf_scores[0].score if tfidf_scores else 0
        
        # GLiNER should catch the semantic similarity
        page_text = " ".join(e["text"] for e in elements)
        labels = ["payment action", "cancel action"]
        gliner_entities = self.model.predict_entities(page_text, labels)
        gliner_payment = [e for e in gliner_entities if e["label"] == "payment action"]
        
        # GLiNER should find it even if TF-IDF scores low
        self.assertTrue(any("submit" in e["text"].lower() for e in gliner_payment))


if __name__ == "__main__":
    unittest.main()
