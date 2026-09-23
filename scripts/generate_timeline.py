#!/usr/bin/env python3
"""Generate the Brain Dump dashboard and chronological timeline."""
from __future__ import annotations
import calendar, json, os, sys, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com"
START_MARKER = "<!-- TIMELINE:START -->"
END_MARKER = "<!-- TIMELINE:END -->"

def api_get(url: str, token: str):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "brain-dump-dashboard",
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def get_issues(repo: str, token: str):
    issues, page = [], 1
    while True:
        url = f"{API}/repos/{repo}/issues?state=all&sort=created&direction=asc&per_page=100&page={page}"
        batch = api_get(url, token)
        if not batch:
            break
        issues.extend(item for item in batch if "pull_request" not in item)
        if len(batch) < 100:
            break
        page += 1
    return issues

def display_title(text: str) -> str:
    title = " ".join((text or "Untitled idea").split())
    if title.lower().startswith("[idea] "):
        title = title[7:].strip()
    return title or "Untitled idea"

def clean_mermaid(text: str, limit: int = 56) -> str:
    cleaned = display_title(text).replace(":", " - ").replace(",", " ")
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > limit:
        cleaned = cleaned[:limit-1].rstrip() + "…"
    return cleaned

def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")

def human_date(value: datetime) -> str:
    return f"{value.day} {calendar.month_abbr[value.month]} {value.year}"

def state_label(issue) -> str:
    return "🟢 Open" if issue.get("state", "open") == "open" else "✅ Closed"

def parse_issues(issues):
    parsed, groups = [], defaultdict(list)
    for issue in issues:
        created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
        parsed.append((created, issue))
        groups[(created.year, created.month)].append((created, issue))
    parsed.sort(key=lambda item: item[0])
    return parsed, groups

def generate_mermaid(groups):
    lines = [
        "```mermaid",
        "gantt",
        "    title Brain Dump — Ideas by creation date",
        "    dateFormat YYYY-MM-DD",
        "    axisFormat %d %b %Y",
    ]
    for year, month in sorted(groups):
        lines.append(f"    section {calendar.month_abbr[month]} {year}")
        for created, issue in groups[(year, month)]:
            title = clean_mermaid(issue.get("title", "Untitled idea"))
            number = issue["number"]
            day = created.strftime("%Y-%m-%d")
            lines.append(f"    #{number} {title} :milestone, idea{number}, {day}, 0d")
    lines.append("```")
    return lines

def generate_table(parsed, limit=None, newest_first=False):
    rows = list(reversed(parsed)) if newest_first else list(parsed)
    if limit is not None:
        rows = rows[:limit]
    lines = ["| Date | Idea | State |", "| --- | --- | --- |"]
    for created, issue in rows:
        date = human_date(created)
        title = markdown_escape(display_title(issue.get("title", "Untitled idea")))
        number = issue["number"]
        url = issue["html_url"]
        lines.append(f"| {date} | [#{number} — {title}]({url}) | {state_label(issue)} |")
    return lines

def generate_full(issues):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# 🕒 Brain Dump Timeline", "",
        "Complete chronological history generated from original GitHub Issue creation timestamps.", "",
        f"_Last generated: {now}_", ""
    ]
    if not issues:
        return "\n".join(lines + ["> No ideas have been captured yet.", ""])
    parsed, groups = parse_issues(issues)
    lines += generate_mermaid(groups)
    lines += ["", "## 💭 All ideas", ""]
    lines += generate_table(parsed)
    lines += ["", "> Dates come directly from GitHub Issue creation timestamps; no separate capture-date field is required.", ""]
    return "\n".join(lines)

def generate_home(issues):
    if not issues:
        return "\n".join([
            "## 📊 Snapshot", "",
            "| 💡 Total ideas | 🟢 Open | ✅ Closed | 🕒 Latest capture |",
            "| ---: | ---: | ---: | --- |",
            "| 0 | 0 | 0 | — |", "",
            "## ✨ Latest spark", "",
            "> Nothing here yet. [Capture the first idea](https://github.com/afnannuzulasugihartono/brain-dump/issues/new/choose).", "",
            "## 🗓️ Idea timeline", "",
            "> The timeline will appear automatically after the first idea is captured."
        ])
    parsed, groups = parse_issues(issues)
    total = len(parsed)
    open_count = sum(1 for _, issue in parsed if issue.get("state", "open") == "open")
    closed_count = total - open_count
    latest_date, latest_issue = parsed[-1]
    latest_title = markdown_escape(display_title(latest_issue.get("title", "Untitled idea")))
    latest_number = latest_issue["number"]
    latest_url = latest_issue["html_url"]
    lines = [
        "## 📊 Snapshot", "",
        "| 💡 Total ideas | 🟢 Open | ✅ Closed | 🕒 Latest capture |",
        "| ---: | ---: | ---: | --- |",
        f"| {total} | {open_count} | {closed_count} | {human_date(latest_date)} |", "",
        "## ✨ Latest spark", "",
        f"**[#{latest_number} — {latest_title}]({latest_url})**  ",
        f"Captured **{human_date(latest_date)}** · {state_label(latest_issue)}", "",
        "## 🗓️ Idea timeline", ""
    ]
    lines += generate_mermaid(groups)
    lines += ["", "## 💭 Latest ideas", ""]
    lines += generate_table(parsed, limit=10, newest_first=True)
    if total > 10:
        lines += ["", f"_Showing the latest 10 of {total} ideas. Open [TIMELINE.md](TIMELINE.md) for the complete history._"]
    return "\n".join(lines)

def update_readme(home_block):
    path = Path("README.md")
    text = path.read_text(encoding="utf-8")
    if START_MARKER not in text or END_MARKER not in text:
        raise RuntimeError("README timeline markers are missing.")
    before, rest = text.split(START_MARKER, 1)
    _, after = rest.split(END_MARKER, 1)
    path.write_text(before + START_MARKER + "\n" + home_block.rstrip() + "\n" + END_MARKER + after, encoding="utf-8")

def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo or not token:
        print("GITHUB_REPOSITORY and GITHUB_TOKEN are required.", file=sys.stderr)
        raise SystemExit(2)
    owner = repo.split("/", 1)[0].lower()
    issues = [issue for issue in get_issues(repo, token) if issue.get("user", {}).get("login", "").lower() == owner]
    Path("TIMELINE.md").write_text(generate_full(issues), encoding="utf-8")
    update_readme(generate_home(issues))
    print(f"Generated dashboard and timeline from {len(issues)} issue(s).")

if __name__ == "__main__":
    main()
