from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / ".github" / "workflows" / "sync.yml"
AI_REVIEW = ROOT / ".github" / "workflows" / "ai-review.yml"


class WorkflowContractTests(unittest.TestCase):
    def test_new_workflow_files_exist(self):
        self.assertTrue(SYNC.exists())
        self.assertTrue(AI_REVIEW.exists())

    def test_sync_keeps_trusted_issue_guard_and_read_only_issue_permission(self):
        text = SYNC.read_text(encoding="utf-8")
        self.assertIn("issues:", text)
        self.assertIn("author_association", text)
        self.assertIn("COLLABORATOR", text)
        self.assertIn("issues: read", text)
        self.assertNotIn("issues: write", text)

    def test_sync_is_ai_independent_and_validates_before_deploy(self):
        text = SYNC.read_text(encoding="utf-8")
        self.assertNotIn("AI_API_KEY", text)
        self.assertNotIn("scripts/ai/evaluate.py", text)
        self.assertIn("python3 scripts/validate_generated.py", text)
        self.assertIn("node --experimental-default-type=module --test tests/frontend/scoring.test.js", text)
        generated = next(line for line in text.splitlines() if "GENERATED=" in line)
        self.assertIn("docs/data/ideas.json", generated)
        self.assertNotIn("ai-insights.json", generated)

    def test_sync_retry_refreshes_latest_main(self):
        text = SYNC.read_text(encoding="utf-8")
        self.assertIn("git fetch origin main", text)
        self.assertIn("git reset --hard origin/main", text)
        self.assertIn("git push origin HEAD:main", text)

    def test_ai_review_has_issue_daily_and_manual_triggers(self):
        text = AI_REVIEW.read_text(encoding="utf-8")
        for value in ("issues:", "schedule:", "workflow_dispatch:"):
            self.assertIn(value, text)
        self.assertIn("opened", text)
        self.assertIn("edited", text)
        self.assertIn("python3 scripts/ai/evaluate.py", text)

    def test_ai_review_has_no_issue_write_permission_and_owns_only_sidecar(self):
        text = AI_REVIEW.read_text(encoding="utf-8")
        self.assertIn("issues: read", text)
        self.assertNotIn("issues: write", text)
        self.assertIn("docs/data/ai-insights.json", text)
        self.assertNotIn('docs/data/ideas.json"', text)

    def test_ai_review_explicitly_dispatches_sync_after_sidecar_change(self):
        self.assertTrue(AI_REVIEW.exists())
        text = AI_REVIEW.read_text(encoding="utf-8")
        self.assertIn("actions: write", text)
        self.assertIn("gh workflow run sync.yml --ref main", text)
        self.assertIn("steps.commit.outputs.changed", text)


if __name__ == "__main__":
    unittest.main()
