import json
import unittest
from datetime import datetime

from scripts.generate_timeline import effective_stage, generate_home, generate_ideas_json, is_trusted_issue, parse_section


def parse_iso(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def issue(**overrides):
    base = {
        "number": 7,
        "title": "[Idea] Human + AI access",
        "html_url": "https://github.com/example/brain-dump/issues/7",
        "state": "open",
        "body": """## Idea
Keep the original human idea.

## Why it might matter
It should be easy for both people and agents.

## Initial stage
Exploring

## Category
Software

## AI Notes
First line.
Second line.

## Brain-dump rule
- [x] This is a raw idea, not an approved implementation task.
""",
        "created_at": "2026-09-23T07:00:00Z",
        "updated_at": "2026-09-23T08:00:00Z",
        "closed_at": None,
    }
    base.update(overrides)
    return base


class GeneratorTests(unittest.TestCase):
    def test_parse_section_preserves_multiline_ai_notes(self):
        value = parse_section(issue()["body"], "AI Notes", "")
        self.assertEqual(value, "First line.\nSecond line.")

    def test_missing_ai_notes_is_empty(self):
        body = "## Idea\nOnly human content.\n\n## Initial stage\nInbox"
        self.assertEqual(parse_section(body, "AI Notes", ""), "")

    def test_issue_form_level_three_headings_are_parsed(self):
        body = """### Idea
Human-created note.

### Why it might matter
Created through GitHub Issue Forms.

### Initial stage
Exploring

### Category
Personal
"""
        self.assertEqual(parse_section(body, "Idea", ""), "Human-created note.")
        self.assertEqual(parse_section(body, "Why it might matter", ""), "Created through GitHub Issue Forms.")
        from scripts.generate_timeline import parse_field
        self.assertEqual(parse_field(body, "Initial stage", "Inbox"), "Exploring")
        self.assertEqual(parse_field(body, "Category", "Other"), "Personal")

    def test_generated_index_exposes_idea_and_ai_notes(self):
        parsed = [(parse_iso("2026-09-23T07:00:00Z"), issue())]
        data = json.loads(generate_ideas_json(parsed))
        item = data["ideas"][0]
        self.assertEqual(item["idea"], "Keep the original human idea.")
        self.assertEqual(item["aiNotes"], "First line.\nSecond line.")
        self.assertEqual(item["stage"], "Exploring")

    def test_closed_non_project_issue_is_archived(self):
        closed = issue(state="closed", body=issue()["body"].replace("Exploring", "Inbox"))
        self.assertEqual(effective_stage(closed), "Archived")

    def test_project_stage_survives_closed_state(self):
        closed = issue(state="closed", body=issue()["body"].replace("Exploring", "Project"))
        self.assertEqual(effective_stage(closed), "Project")

    def test_trusted_issue_accepts_owner_and_collaborator_but_rejects_outsider(self):
        owner_issue = issue(user={"login": "afnan"}, author_association="OWNER")
        collaborator_issue = issue(user={"login": "agent-user"}, author_association="COLLABORATOR")
        outsider_issue = issue(user={"login": "random-user"}, author_association="NONE")
        self.assertTrue(is_trusted_issue(owner_issue, "afnan"))
        self.assertTrue(is_trusted_issue(collaborator_issue, "afnan"))
        self.assertFalse(is_trusted_issue(outsider_issue, "afnan"))



    def test_new_canonical_issue_module_and_output_path_exist(self):
        self.assertTrue((ROOT / "scripts" / "generate" / "issues.py").exists())
        source = (ROOT / "scripts" / "generate_timeline.py").read_text(encoding="utf-8")
        self.assertIn('Path("docs/data/ideas.json")', source)
        self.assertNotIn('Path("docs/ideas.json")', source)

    def test_normalize_issue_exposes_canonical_fields(self):
        from scripts.generate.issues import normalize_issue
        item = normalize_issue(issue())
        self.assertEqual(item["number"], 7)
        self.assertEqual(item["title"], "Human + AI access")
        self.assertEqual(item["stage"], "Exploring")
        self.assertEqual(item["category"], "Software")
        self.assertEqual(item["idea"], "Keep the original human idea.")
        self.assertEqual(item["aiNotes"], "First line.\nSecond line.")

class HomeGenerationTests(unittest.TestCase):
    def test_home_avoids_dashboard_marketing_language(self):
        parsed = [(parse_iso("2026-09-23T07:00:00Z"), issue())]
        home = generate_home(parsed)
        self.assertNotIn("Snapshot", home)
        self.assertNotIn("## Overview", home)
        self.assertNotIn("Capture now. Organize later.", home)
        self.assertNotIn("Latest", home)
        self.assertIn("Recent ideas", home)

    def test_home_keeps_issue_as_canonical_link(self):
        parsed = [(parse_iso("2026-09-23T07:00:00Z"), issue())]
        home = generate_home(parsed)
        self.assertIn("https://github.com/example/brain-dump/issues/7", home)


if __name__ == "__main__":
    unittest.main()
