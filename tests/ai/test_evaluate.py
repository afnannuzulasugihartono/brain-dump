import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class AIReviewTests(unittest.TestCase):
    def test_ai_modules_exist(self):
        self.assertTrue((ROOT / "scripts" / "ai" / "evaluate.py").exists())
        self.assertTrue((ROOT / "scripts" / "ai" / "providers" / "openai_compatible.py").exists())

    def test_rejects_unknown_action_and_wrong_issue_number(self):
        from scripts.ai.evaluate import validate_insight
        raw = {
            "issueNumber": 99,
            "summary": "Useful.",
            "suggestedAction": "delete-it",
            "signals": ["context"],
            "confidence": 0.8,
            "depth": "brief",
        }
        with self.assertRaises(ValueError):
            validate_insight(raw, 7, "2026-09-23T12:00:00Z")

    def test_rejects_confidence_outside_range(self):
        from scripts.ai.evaluate import validate_insight
        raw = {
            "issueNumber": 7,
            "summary": "Useful.",
            "suggestedAction": "revisit",
            "signals": [],
            "confidence": 1.5,
            "depth": "brief",
        }
        with self.assertRaises(ValueError):
            validate_insight(raw, 7, "2026-09-23T12:00:00Z")

    def test_missing_update_preserves_old_valid_insight(self):
        from scripts.ai.evaluate import merge_insights
        old = {"issueNumber":7,"summary":"Old","suggestedAction":"revisit",
               "signals":[],"confidence":0.7,"depth":"brief",
               "evaluatedAt":"2026-09-22T12:00:00Z"}
        self.assertEqual(merge_insights([old], []), [old])

    def test_timeout_preserves_old_valid_insight(self):
        from scripts.ai.evaluate import evaluate_ideas
        old = {"issueNumber":7,"summary":"Old","suggestedAction":"revisit",
               "signals":[],"confidence":0.7,"depth":"brief",
               "evaluatedAt":"2026-09-22T12:00:00Z"}
        idea = {"number":7,"title":"Idea"}

        def timeout(*args, **kwargs):
            raise TimeoutError("provider timeout")

        merged, updated = evaluate_ideas(
            [idea], [old],
            evaluated_at="2026-09-23T12:00:00Z",
            base_url="https://example.test", api_key="key", model="model",
            request_func=timeout,
        )
        self.assertEqual(merged, [old])
        self.assertEqual(updated, 0)

    def test_rate_limit_preserves_old_valid_insight(self):
        from scripts.ai.evaluate import evaluate_ideas
        old = {"issueNumber":7,"summary":"Old","suggestedAction":"revisit",
               "signals":[],"confidence":0.7,"depth":"brief",
               "evaluatedAt":"2026-09-22T12:00:00Z"}
        idea = {"number":7,"title":"Idea"}

        def rate_limit(*args, **kwargs):
            raise HTTPError("https://example.test", 429, "Too Many Requests", None, None)

        merged, updated = evaluate_ideas(
            [idea], [old],
            evaluated_at="2026-09-23T12:00:00Z",
            base_url="https://example.test", api_key="key", model="model",
            request_func=rate_limit,
        )
        self.assertEqual(merged, [old])
        self.assertEqual(updated, 0)

    @patch.dict(os.environ, {"AI_BASE_URL":"", "AI_API_KEY":"", "AI_MODEL":""})
    @patch("scripts.ai.evaluate._write_document")
    def test_missing_provider_exits_cleanly_without_writing(self, write_document):
        from scripts.ai.evaluate import main
        self.assertEqual(main([]), 0)
        write_document.assert_not_called()

    def test_markdown_fenced_provider_json_is_rejected(self):
        from scripts.ai.providers.openai_compatible import parse_provider_content
        with self.assertRaises(json.JSONDecodeError):
            parse_provider_content('~~~json\n{"issueNumber":7}\n~~~')


if __name__ == "__main__":
    unittest.main()
