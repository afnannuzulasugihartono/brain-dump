from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class AIContractTests(unittest.TestCase):
    def test_agents_declares_source_of_truth_and_generated_json_read_only(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("GitHub Issues", text)
        self.assertIn("source of truth", text.lower())
        self.assertIn("docs/data/ideas.json", text)
        self.assertIn("read-only", text.lower())

    def test_agents_enforces_project_and_archive_gates(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
        self.assertIn("project", text)
        self.assertIn("explicit user instruction", text)
        self.assertIn("archive", text)
        self.assertIn("close", text)

    def test_agents_requires_reread_and_human_content_preservation(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
        self.assertIn("re-read", text)
        self.assertIn("preserve", text)
        self.assertIn("human", text)

    def test_api_doc_uses_official_issue_endpoints_and_stops_on_auth_failure(self):
        text = (ROOT / "docs" / "ai-access.md").read_text(encoding="utf-8")
        lowered = text.lower()
        self.assertIn("GET /repos/{owner}/{repo}/issues", text)
        self.assertIn("POST /repos/{owner}/{repo}/issues", text)
        self.assertIn("PATCH /repos/{owner}/{repo}/issues/{issue_number}", text)
        self.assertIn("POST /repos/{owner}/{repo}/issues/{issue_number}/comments", text)
        self.assertIn("401", text)
        self.assertIn("403", text)
        self.assertIn("stop", lowered)
        self.assertIn("do not attempt an alternate write path", lowered)

    def test_readme_links_to_ai_access_guide(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("[AI access](docs/ai-access.md)", text)

    def test_blank_issues_are_disabled_for_human_capture(self):
        text = (ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
        self.assertIn("blank_issues_enabled: false", text)

    def test_issue_template_stays_human_first_and_keeps_canonical_sections(self):
        text = (ROOT / ".github" / "ISSUE_TEMPLATE" / "idea.yml").read_text(encoding="utf-8")
        for label in ("Idea", "Why it might matter", "Initial stage", "Category", "Brain-dump rule"):
            self.assertIn(f"label: {label}", text)
        self.assertNotIn("label: AI Notes", text)

    def test_agents_names_generated_boundaries(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
        self.assertIn("docs/data/ideas.json", text)
        self.assertIn("docs/data/ai-insights.json", text)
        self.assertIn("do not edit", text)

    def test_ai_access_documents_sidecar_recommendations(self):
        text = (ROOT / "docs" / "ai-access.md").read_text(encoding="utf-8").lower()
        self.assertIn("ai-insights.json", text)
        self.assertIn("promote-candidate", text)
        self.assertIn("consider-archive", text)
        self.assertIn("read-only", text)


if __name__ == "__main__":
    unittest.main()
