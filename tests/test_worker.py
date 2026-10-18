import json
import tempfile
import unittest
from pathlib import Path
from ai_ceo.worker import render_landing, validate, write_results

SOURCES = [{"title": "Opportunity signal", "url": "https://example.org/signal"}]
IDEA = {"idea": "Small workflow tool", "audience": "small firms", "problem": "too much manual sorting",
 "product": "A small licensed web utility", "distribution_test": "opt-in landing page",
 "score": 63, "price_hypothesis_eur": 12.0, "evidence_urls": ["https://example.org/signal"],
 "counterarguments": ["Audience may be too small", "A competitor may solve this already"],
 "alternative_ideas": ["Another workflow", "A different utility"]}

class ResearchTests(unittest.TestCase):
    def test_valid_and_non_transactional_page(self):
        idea = validate(IDEA, SOURCES)
        page = render_landing(idea, "2026-10-18")
        self.assertIn("Research-only concept", page)
        self.assertNotIn("<form", page)
        scratch = Path(__file__).resolve().parents[1] / ".tmp" / "tests"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as d:
            write_results(idea, SOURCES, Path(d))
            saved = json.loads((Path(d) / "decision.json").read_text(encoding="utf-8"))
            self.assertFalse(saved["is_revenue"])
            self.assertFalse(saved["has_live_checkout"])
            self.assertTrue((Path(d) / "public" / "index.html").exists())

    def test_disallows_invented_sources(self):
        fake = {**IDEA, "evidence_urls": ["https://unknown.example/fake"]}
        with self.assertRaises(ValueError):
            validate(fake, SOURCES)

    def test_invalid_output_cannot_be_written_directly(self):
        scratch = Path(__file__).resolve().parents[1] / ".tmp" / "tests"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            with self.assertRaises(ValueError):
                write_results({**IDEA, "evidence_urls": ["javascript:alert(1)"]}, SOURCES, Path(directory))
            self.assertFalse((Path(directory) / "decision.json").exists())

    def test_escapes_model_html(self):
        idea = {**IDEA, "idea": "<script>alert(1)</script>"}
        page = render_landing(idea, "today")
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_no_checkout_control(self):
        self.assertNotIn("Checkout", render_landing(IDEA, "today"))

if __name__ == "__main__":
    unittest.main()
