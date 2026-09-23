import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GeneratedValidationTests(unittest.TestCase):
    def test_validator_module_exists(self):
        self.assertTrue((ROOT / "scripts" / "validate_generated.py").exists())

    def test_duplicate_issue_numbers_fail(self):
        from scripts.validate_generated import validate_ideas_document
        data = {"source":"GitHub Issues","ideas":[
            {"number":1,"createdAt":"2026-09-01T00:00:00Z","updatedAt":"2026-09-01T00:00:00Z"},
            {"number":1,"createdAt":"2026-09-02T00:00:00Z","updatedAt":"2026-09-02T00:00:00Z"},
        ]}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_ideas_document(data)

    def test_malformed_timestamp_fails(self):
        from scripts.validate_generated import validate_ideas_document
        data = {"source":"GitHub Issues","ideas":[
            {"number":1,"createdAt":"bad","updatedAt":"2026-09-01T00:00:00Z"}
        ]}
        with self.assertRaisesRegex(ValueError, "createdAt"):
            validate_ideas_document(data)
