#!/usr/bin/env python3
"""Generate Brain Dump data, README feed, and the full Markdown timeline."""
from __future__ import annotations

import calendar
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from scripts.generate.issues import (
    display_title,
    effective_stage,
    get_issues,
    is_trusted_issue,
    normalize_issue,
    parse_field,
    parse_section,
)

START_MARKER = "<!-- TIMELINE:START -->"
END_MARKER = "<!-- TIMELINE:END -->"
RECENT_LIMIT = 8


def parse_issues(issues):
    parsed = []
    for issue in issues:
        created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
        parsed.append((created, issue))
    return sorted(parsed, key=lambda item: item[0])


def human_date(value: datetime) -> str:
    return f"{value.day} {calendar.month_abbr[value.month]} {value.year}"


def escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def generate_ideas_json(parsed):
    ideas = [normalize_issue(issue) for _, issue in reversed(parsed)]
    return json.dumps({"source": "GitHub Issues", "ideas": ideas}, ensure_ascii=False, indent=2) + "\n"


def generate_home(parsed):
    total = len(parsed)
    open_count = sum(1 for _, issue in parsed if issue.get("state", "open") == "open")
    lines = [
        "## Recent ideas", "",
        f"_{total} idea{'s' if total != 1 else ''} · {open_count} open_", "",
    ]
    rows = list(reversed(parsed))[:RECENT_LIMIT]
    if not rows:
        lines += ["> No ideas captured yet."]
    else:
        for created, issue in rows:
            title = escape_md(display_title(issue.get("title", "Untitled idea")))
            why = escape_md(parse_field(issue.get("body") or "", "Why it might matter", "No context added yet."))
            stage = escape_md(effective_stage(issue))
            category = escape_md(parse_field(issue.get("body") or "", "Category", "Other"))
            state = issue.get("state", "open").capitalize()
            lines += [
                f"### {human_date(created)} · [#{issue['number']} {title}]({issue['html_url']})", "",
                why, "", f"**{stage}** · {category} · {state}", "",
            ]
        if total > RECENT_LIMIT:
            lines += [f"[View all {total} ideas →](TIMELINE.md)", ""]
    return "\n".join(lines)


def generate_full(parsed):
    lines = [
        "# Brain Dump timeline", "",
        "A complete chronological feed generated from GitHub Issues.", "",
        "## All ideas", "",
    ]
    if not parsed:
        lines += ["> No ideas captured yet."]
    else:
        for created, issue in reversed(parsed):
            title = escape_md(display_title(issue.get("title", "Untitled idea")))
            why = escape_md(parse_field(issue.get("body") or "", "Why it might matter", "No context added yet."))
            stage = effective_stage(issue)
            category = parse_field(issue.get("body") or "", "Category", "Other")
            state = issue.get("state", "open").capitalize()
            lines += [
                f"### {human_date(created)} · [#{issue['number']} {title}]({issue['html_url']})", "",
                why, "", f"**{stage}** · {category} · {state}", "",
            ]
    return "\n".join(lines)


def update_readme(block: str):
    path = Path("README.md")
    content = path.read_text(encoding="utf-8")
    if START_MARKER not in content or END_MARKER not in content:
        raise RuntimeError("README markers are missing.")
    before, rest = content.split(START_MARKER, 1)
    _, after = rest.split(END_MARKER, 1)
    path.write_text(before + START_MARKER + "\n" + block.rstrip() + "\n" + END_MARKER + after, encoding="utf-8")


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo or not token:
        print("GITHUB_REPOSITORY and GITHUB_TOKEN are required.", file=sys.stderr)
        raise SystemExit(2)

    owner = repo.split("/", 1)[0].lower()
    issues = [issue for issue in get_issues(repo, token) if is_trusted_issue(issue, owner)]
    parsed = parse_issues(issues)

    Path("docs/data").mkdir(parents=True, exist_ok=True)
    Path("docs/data/ideas.json").write_text(generate_ideas_json(parsed), encoding="utf-8")
    Path("TIMELINE.md").write_text(generate_full(parsed), encoding="utf-8")
    update_readme(generate_home(parsed))
    print(f"Generated Brain Dump from {len(parsed)} issue(s).")


if __name__ == "__main__":
    main()
