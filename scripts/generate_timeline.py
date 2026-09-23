#!/usr/bin/env python3
"""Generate a GitHub-rendered idea timeline from issue creation timestamps."""

from __future__ import annotations

import calendar
import json
import os
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


API = "https://api.github.com"


def api_get(url: str, token: str):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "brain-dump-timeline",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def get_issues(repo: str, token: str):
    issues = []
    page = 1
    while True:
        url = (
            f"{API}/repos/{repo}/issues"
            f"?state=all&sort=created&direction=asc&per_page=100&page={page}"
        )
        batch = api_get(url, token)
        if not batch:
            break
        issues.extend(item for item in batch if "pull_request" not in item)
        if len(batch) < 100:
            break
        page += 1
    return issues


def clean_mermaid(text: str, limit: int = 62) -> str:
    cleaned = " ".join(text.replace(":", " - ").replace(",", " ").split())
    if len(cleaned) > limit:
        cleaned = cleaned[: limit - 1].rstrip() + "…"
    return cleaned or "Untitled idea"


def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def generate(issues):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Brain Dump Timeline",
        "",
        "Automatically generated from the original GitHub Issue creation timestamps.",
        "",
        f"_Last generated: {now}_",
        "",
    ]

    if not issues:
        lines += [
            "> No ideas have been captured yet. Create an Issue using the **New idea** template and this timeline will update automatically.",
            "",
        ]
        return "\n".join(lines)

    groups = defaultdict(list)
    parsed = []
    for issue in issues:
        created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
        parsed.append((created, issue))
        groups[(created.year, created.month)].append((created, issue))

    lines += [
        "```mermaid",
        "gantt",
        "    title Brain Dump — Ideas by creation date",
        "    dateFormat YYYY-MM-DD",
        "    axisFormat %d %b %Y",
    ]

    for year, month in sorted(groups):
        section = f"{calendar.month_abbr[month]} {year}"
        lines.append(f"    section {section}")
        for created, issue in groups[(year, month)]:
            title = clean_mermaid(issue.get("title", "Untitled idea"))
            number = issue["number"]
            day = created.strftime("%Y-%m-%d")
            lines.append(
                f"    #{number} {title} :milestone, idea{number}, {day}, 0d"
            )

    lines += [
        "```",
        "",
        "## Ideas",
        "",
        "| Date | Idea | State |",
        "| --- | --- | --- |",
    ]

    for created, issue in parsed:
        date = created.strftime("%Y-%m-%d")
        title = markdown_escape(issue.get("title", "Untitled idea"))
        number = issue["number"]
        url = issue["html_url"]
        state = issue.get("state", "open").capitalize()
        lines.append(f"| {date} | [#{number} {title}]({url}) | {state} |")

    lines += [
        "",
        "> The date shown here is the immutable creation time of the GitHub Issue, so no separate capture-date field is required.",
        "",
    ]
    return "\n".join(lines)


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo or not token:
        print("GITHUB_REPOSITORY and GITHUB_TOKEN are required.", file=sys.stderr)
        raise SystemExit(2)

    owner = repo.split("/", 1)[0].lower()
    issues = [
        issue for issue in get_issues(repo, token)
        if issue.get("user", {}).get("login", "").lower() == owner
    ]
    Path("TIMELINE.md").write_text(generate(issues), encoding="utf-8")
    print(f"Generated TIMELINE.md from {len(issues)} issue(s).")


if __name__ == "__main__":
    main()
