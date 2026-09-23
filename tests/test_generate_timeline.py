import json
import unittest
from datetime import datetime

from scripts.generate_timeline import effective_stage, generate_ideas_json, parse_section


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


if __name__ == "__main__":
    unittest.main()
