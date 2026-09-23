import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def canonical_idea(**overrides):
    item = {
        "number": 1,
        "title": "Example",
        "url": "https://github.com/example/repo/issues/1",
        "state": "open",
        "stage": "Inbox",
        "category": "Other",
        "why": "",
        "idea": "Example idea",
        "aiNotes": "",
        "createdAt": "2026-09-01T00:00:00Z",
        "updatedAt": "2026-09-01T00:00:00Z",
        "closedAt": None,
    }
    item.update(overrides)
    return item


class GeneratedValidationTests(unittest.TestCase):
    def test_checked_in_ai_sidecar_is_valid_json_and_schema(self):
        import json
        from scripts.validate_generated import validate_insights_document
        data = json.loads((ROOT / "docs" / "data" / "ai-insights.json").read_text(encoding="utf-8"))
        validate_insights_document(data)

    def test_validator_module_exists(self):
        self.assertTrue((ROOT / "scripts" / "validate_generated.py").exists())

    def test_duplicate_issue_numbers_fail(self):
        from scripts.validate_generated import validate_ideas_document
        data = {"source":"GitHub Issues","ideas":[
            canonical_idea(number=1),
            canonical_idea(number=1, createdAt="2026-09-02T00:00:00Z", updatedAt="2026-09-02T00:00:00Z"),
        ]}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_ideas_document(data)

    def test_malformed_timestamp_fails(self):
        from scripts.validate_generated import validate_ideas_document
        data = {"source":"GitHub Issues","ideas":[canonical_idea(createdAt="bad")]}
        with self.assertRaisesRegex(ValueError, "createdAt"):
            validate_ideas_document(data)

    def test_missing_required_canonical_field_fails(self):
        from scripts.validate_generated import validate_ideas_document
        item = canonical_idea()
        del item["title"]
        data = {"source":"GitHub Issues","ideas":[item]}
        with self.assertRaisesRegex(ValueError, "title"):
            validate_ideas_document(data)

    def test_malformed_ai_sidecar_entry_fails(self):
        from scripts.validate_generated import validate_insights_document
        data = {"source":"AI review","insights":[{
            "issueNumber":1,"evaluatedAt":"2026-09-01T00:00:00Z",
            "suggestedAction":"revisit","confidence":0.5,"depth":"brief"
        }]}
        with self.assertRaisesRegex(ValueError, "summary"):
            validate_insights_document(data)
