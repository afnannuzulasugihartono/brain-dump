#!/usr/bin/env python3
"""Generate Brain Dump data, static README visuals, and timeline history."""
from __future__ import annotations

import calendar
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com"
START_MARKER = "<!-- TIMELINE:START -->"
END_MARKER = "<!-- TIMELINE:END -->"
ASSET_DIR = Path("assets")
HOME_LIMIT = 10

THEMES = {
    "light": {
        "bg": "#ffffff", "card": "#f6f8fa", "latest": "#f0f7ff",
        "border": "#d0d7de", "text": "#1f2328", "muted": "#656d76",
        "line": "#d0d7de", "accent": "#0969da", "open": "#1a7f37",
        "closed": "#8250df", "pill": "#eaeef2", "pill_text": "#57606a",
    },
    "dark": {
        "bg": "#0d1117", "card": "#161b22", "latest": "#111d2f",
        "border": "#30363d", "text": "#f0f6fc", "muted": "#8b949e",
        "line": "#30363d", "accent": "#58a6ff", "open": "#3fb950",
        "closed": "#a371f7", "pill": "#21262d", "pill_text": "#c9d1d9",
    },
}

def api_get(url: str, token: str):
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "brain-dump",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def get_issues(repo: str, token: str):
    issues, page = [], 1
    while True:
        batch = api_get(
            f"{API}/repos/{repo}/issues?state=all&sort=created&direction=asc&per_page=100&page={page}",
            token,
        )
        if not batch:
            break
        issues.extend(item for item in batch if "pull_request" not in item)
        if len(batch) < 100:
            break
        page += 1
    return issues

def display_title(value: str) -> str:
    title = " ".join((value or "Untitled idea").split())
    return title[7:].strip() if title.lower().startswith("[idea] ") else title

def parse_field(body: str, heading: str, fallback: str) -> str:
    match = re.search(
        rf"(?ims)^##\s+{re.escape(heading)}\s*\n+(.+?)(?=\n##\s+|\Z)",
        body or "",
    )
    if not match:
        return fallback
    value = match.group(1).strip().splitlines()[0].strip()
    return value or fallback

def parse_issues(issues):
    parsed = []
    for issue in issues:
        created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
        parsed.append((created, issue))
    return sorted(parsed, key=lambda item: item[0])

def human_date(value: datetime) -> str:
    return f"{value.day} {calendar.month_abbr[value.month]} {value.year}"

def state_label(issue) -> str:
    return "🟢 Open" if issue.get("state", "open") == "open" else "✅ Closed"

def truncate(value: str, limit: int) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[:limit - 1].rstrip() + "…"

def pill_width(value: str) -> int:
    return max(52, min(116, 18 + len(value) * 7))

def generate_svg(parsed, theme_name: str, limit=HOME_LIMIT):
    theme = THEMES[theme_name]
    rows = parsed[-limit:]
    width, header_h, row_h, footer_h = 920, 90, 102, 30
    height = header_h + max(1, len(rows)) * row_h + footer_h
    center, card_w, card_h = width // 2, 370, 76
    left_x, right_x = 28, width - 28 - card_w
    font = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

    total = len(parsed)
    open_count = sum(1 for _, issue in parsed if issue.get("state", "open") == "open")
    closed_count = total - open_count

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Brain Dump Idea Journey</title>',
        '<desc id="desc">Chronological timeline generated from GitHub Issues.</desc>',
        f'<rect width="100%" height="100%" rx="12" fill="{theme["bg"]}"/>',
        f'<text x="28" y="34" fill="{theme["text"]}" font-family="{font}" font-size="19" font-weight="700">Idea Journey</text>',
        f'<text x="28" y="56" fill="{theme["muted"]}" font-family="{font}" font-size="11">GitHub Issues · chronological view</text>',
        f'<text x="{width-28}" y="34" text-anchor="end" fill="{theme["muted"]}" font-family="{font}" font-size="10">{total} IDEAS · {open_count} OPEN · {closed_count} CLOSED</text>',
        f'<line x1="28" y1="70" x2="{width-28}" y2="70" stroke="{theme["border"]}"/>',
    ]

    if rows:
        line_top, line_bottom = header_h + 24, header_h + len(rows) * row_h - 25
        out.append(f'<line x1="{center}" y1="{line_top}" x2="{center}" y2="{line_bottom}" stroke="{theme["line"]}"/>')
        previous_month = None

        for index, (created, issue) in enumerate(rows):
            row_y = header_h + index * row_h
            node_y = row_y + 42
            left = index % 2 == 0
            card_x = left_x if left else right_x
            card_y = row_y + 4

            month_key = (created.year, created.month)
            if month_key != previous_month:
                label = f"{calendar.month_abbr[created.month].upper()} {created.year}"
                out += [
                    f'<rect x="{center-38}" y="{row_y-5}" width="76" height="18" rx="9" fill="{theme["card"]}" stroke="{theme["border"]}"/>',
                    f'<text x="{center}" y="{row_y+8}" text-anchor="middle" fill="{theme["accent"]}" font-family="{font}" font-size="9" font-weight="700">{label}</text>',
                ]
                card_y += 12
                node_y += 12
            previous_month = month_key

            state = issue.get("state", "open")
            state_color = theme["open"] if state == "open" else theme["closed"]
            title = html.escape(truncate(display_title(issue.get("title", "Untitled idea")), 40))
            body = issue.get("body") or ""
            stage = truncate(parse_field(body, "Initial stage", "Inbox"), 14).upper()
            category = truncate(parse_field(body, "Category", "Other"), 14).upper()
            latest = (created, issue) == parsed[-1]
            fill = theme["latest"] if latest else theme["card"]

            connector_start = card_x + card_w if left else center
            connector_end = center if left else card_x
            out += [
                f'<line x1="{connector_start}" y1="{node_y}" x2="{connector_end}" y2="{node_y}" stroke="{theme["line"]}"/>',
                f'<circle cx="{center}" cy="{node_y}" r="5" fill="{theme["bg"]}" stroke="{state_color}" stroke-width="2"/>',
                f'<rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="10" fill="{fill}" stroke="{theme["accent"] if latest else theme["border"]}"/>',
                f'<text x="{card_x+16}" y="{card_y+21}" fill="{theme["muted"]}" font-family="{font}" font-size="10">#{issue["number"]} · {human_date(created)}</text>',
                f'<text x="{card_x+16}" y="{card_y+42}" fill="{theme["text"]}" font-family="{font}" font-size="14" font-weight="700">{title}</text>',
            ]
            px = card_x + 16
            for label in (state.upper(), stage, category):
                pw = pill_width(label)
                fill_color = state_color if label in {"OPEN", "CLOSED"} else theme["pill"]
                text_color = theme["bg"] if label in {"OPEN", "CLOSED"} else theme["pill_text"]
                out += [
                    f'<rect x="{px}" y="{card_y+51}" width="{pw}" height="17" rx="8.5" fill="{fill_color}"/>',
                    f'<text x="{px+pw/2}" y="{card_y+63}" text-anchor="middle" fill="{text_color}" font-family="{font}" font-size="8" font-weight="700">{html.escape(label)}</text>',
                ]
                px += pw + 6
    else:
        out += [
            f'<rect x="190" y="120" width="540" height="62" rx="10" fill="{theme["card"]}" stroke="{theme["border"]}"/>',
            f'<text x="{center}" y="148" text-anchor="middle" fill="{theme["text"]}" font-family="{font}" font-size="14" font-weight="700">No ideas captured yet</text>',
            f'<text x="{center}" y="168" text-anchor="middle" fill="{theme["muted"]}" font-family="{font}" font-size="10">Create a GitHub Issue and it will appear here automatically.</text>',
        ]

    out.append(f'<text x="{center}" y="{height-11}" text-anchor="middle" fill="{theme["muted"]}" font-family="{font}" font-size="9">Generated automatically from GitHub Issue timestamps</text>')
    out.append("</svg>")
    return "\n".join(out)

def generate_ideas_json(parsed):
    ideas = []
    for _, issue in reversed(parsed):
        body = issue.get("body") or ""
        state = issue.get("state", "open")
        stage = parse_field(body, "Initial stage", "Inbox")
        if state == "closed" and stage.lower() not in {"project", "archived"}:
            stage = "Archived"
        ideas.append({
            "number": issue["number"],
            "title": display_title(issue.get("title", "Untitled idea")),
            "url": issue["html_url"],
            "state": state,
            "stage": stage,
            "category": parse_field(body, "Category", "Other"),
            "why": parse_field(body, "Why it might matter", ""),
            "createdAt": issue["created_at"],
            "updatedAt": issue.get("updated_at") or issue["created_at"],
            "closedAt": issue.get("closed_at"),
        })
    return json.dumps({
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "GitHub Issues",
        "ideas": ideas,
    }, ensure_ascii=False, indent=2) + "\n"

def table(parsed, limit=None, newest_first=False):
    rows = list(reversed(parsed)) if newest_first else list(parsed)
    if limit is not None:
        rows = rows[:limit]
    lines = ["| Date | Idea | State |", "| --- | --- | --- |"]
    for created, issue in rows:
        title = display_title(issue.get("title", "Untitled idea")).replace("|", "\\|")
        lines.append(f'| {human_date(created)} | [#{issue["number"]} — {title}]({issue["html_url"]}) | {state_label(issue)} |')
    return lines

def picture_block():
    return "\n".join([
        '<p align="center">',
        '  <picture>',
        '    <source media="(prefers-color-scheme: dark)" srcset="./assets/idea-journey-dark.svg">',
        '    <source media="(prefers-color-scheme: light)" srcset="./assets/idea-journey-light.svg">',
        '    <img alt="Brain Dump Idea Journey" src="./assets/idea-journey-light.svg" width="100%">',
        '  </picture>',
        '</p>',
    ])

def generate_full(parsed):
    lines = [
        "# 🕒 Brain Dump Timeline", "",
        "Complete chronological history generated from GitHub Issue creation timestamps.", "",
        picture_block(), "",
        "## 💭 All ideas", "",
    ]
    lines += table(parsed) if parsed else ["> No ideas have been captured yet."]
    lines += ["", "> Dates come directly from GitHub Issue creation timestamps.", ""]
    return "\n".join(lines)

def generate_home(parsed):
    total = len(parsed)
    open_count = sum(1 for _, issue in parsed if issue.get("state", "open") == "open")
    latest = parsed[-1] if parsed else None
    lines = [
        "## 📊 Snapshot", "",
        "| 💡 Ideas | 🟢 Open | ✅ Closed | 🕒 Latest |",
        "| ---: | ---: | ---: | --- |",
        f'| {total} | {open_count} | {total-open_count} | {human_date(latest[0]) if latest else "—"} |',
        "",
        "## 🧭 Idea Journey", "",
        picture_block(), "",
        "## 💭 Latest ideas", "",
    ]
    lines += table(parsed, limit=10, newest_first=True) if parsed else ["> No ideas captured yet."]
    if total > 10:
        lines += ["", f"_Showing 10 of {total} ideas. See [TIMELINE.md](TIMELINE.md) for the complete history._"]
    return "\n".join(lines)

def update_readme(block: str):
    path = Path("README.md")
    content = path.read_text(encoding="utf-8")
    if START_MARKER not in content or END_MARKER not in content:
        raise RuntimeError("README timeline markers are missing.")
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
    issues = [
        issue for issue in get_issues(repo, token)
        if issue.get("user", {}).get("login", "").lower() == owner
    ]
    parsed = parse_issues(issues)

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    (ASSET_DIR / "idea-journey-light.svg").write_text(generate_svg(parsed, "light"), encoding="utf-8")
    (ASSET_DIR / "idea-journey-dark.svg").write_text(generate_svg(parsed, "dark"), encoding="utf-8")
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/ideas.json").write_text(generate_ideas_json(parsed), encoding="utf-8")
    Path("TIMELINE.md").write_text(generate_full(parsed), encoding="utf-8")
    update_readme(generate_home(parsed))
    print(f"Generated Brain Dump from {len(parsed)} issue(s).")

if __name__ == "__main__":
    main()
