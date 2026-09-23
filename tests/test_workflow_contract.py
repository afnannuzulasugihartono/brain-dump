from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sync-brain-dump.yml"


class WorkflowContractTests(unittest.TestCase):
    def test_issue_events_trigger_sync(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("issues:", text)
        for event in ("opened", "edited", "closed", "reopened"):
            self.assertIn(event, text)

    def test_workflow_never_needs_issue_write_permission(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("issues: read", text)
        self.assertNotIn("issues: write", text)

    def test_generated_push_refreshes_from_latest_main_before_retry(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("git fetch origin main", text)
        self.assertIn("git reset --hard origin/main", text)
        self.assertIn("python3 scripts/generate_timeline.py", text)
        self.assertIn("git push origin HEAD:main", text)


if __name__ == "__main__":
    unittest.main()
