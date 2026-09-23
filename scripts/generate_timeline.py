#!/usr/bin/env python3
"""Generate the Brain Dump README dashboard, SVG idea journey, and history."""
from __future__ import annotations

import calendar
import html
import json
import os
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com"
START_MARKER = "<!-- TIMELINE:START -->"
END_MARKER = "<!-- TIMELINE:END -->"
ASSET_DIR = Path("assets")
HOME_LIMIT = 10

THEMES = {
    "light": {
        "bg": "#ffffff",
        "card": "#f6f8fa",
        "card_latest": "#f0f7ff",
        "border": "#d0d7de",
        "text": "#1f2328",
        "muted": "#656d76",
        "line": "#d8dee4",
        "accent": "#0969da",
        "accent2": "#8250df",
        "open": "#1a7f37",
        "closed": "#8250df",
        "pill": "#eaeef2",
        "pill_text": "#57606a",
        "month_bg": "#ddf4ff",
        "month_text": "#0969da",
    },
    "dark": {
        "bg": "#0d1117",
        "card": "#161b22",
        "card_latest": "#111d2f",
        "border": "#30363d",
        "text": "#f0f6fc",
        "muted": "#8b949e",
        "line": "#30363d",
        "accent": "#58a6ff",
        "accent2": "#a371f7",
        "open": "#3fb950",
        "closed": "#a371f7",
        "pill": "#21262d",
        "pill_text": "#c9d1d9",
        "month_bg": "#13233a",
        "month_text": "#79c0ff",
    },
}

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

def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")

def human_date(value: datetime) -> str:
    return f"{value.day} {calendar.month_abbr[value.month]} {value.year}"

def state_label(issue) -> str:
    return "🟢 Open" if issue.get("state", "open") == "open" else "✅ Closed"

def parse_field(body: str, heading: str, fallback: str) -> str:
    if not body:
        return fallback
    pattern = rf"(?ims)^##\s+{re.escape(heading)}\s*\n+(.+?)(?=\n##\s+|\Z)"
    match = re.search(pattern, body)
    if not match:
        return fallback
    value = match.group(1).strip().splitlines()[0].strip()
    return value or fallback

def parse_issues(issues):
    parsed = []
    for issue in issues:
        created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
        parsed.append((created, issue))
    parsed.sort(key=lambda item: item[0])
    return parsed

def truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit - 1].rstrip() + "…"

def svg_text(value: str) -> str:
    return html.escape(value, quote=True)

def pill_width(text: str) -> int:
    return max(54, min(124, 18 + len(text) * 7))

def generate_svg(parsed, theme_name: str, limit=HOME_LIMIT):
    theme = THEMES[theme_name]
    rows = parsed[-limit:]
    width = 960
    header_h = 118
    row_h = 116
    footer_h = 34
    height = header_h + max(1, len(rows)) * row_h + footer_h
    center = width // 2
    card_w = 390
    card_h = 84
    left_x = 38
    right_x = width - 38 - card_w
    font = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

    total = len(parsed)
    open_count = sum(1 for _, issue in parsed if issue.get("state", "open") == "open")
    closed_count = total - open_count

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Brain Dump Idea Journey</title>',
        '<desc id="desc">Chronological timeline of captured ideas from GitHub Issues.</desc>',
        "<defs>",
        f'<linearGradient id="accent" x1="0" x2="1"><stop offset="0%" stop-color="{theme["accent"]}"/><stop offset="100%" stop-color="{theme["accent2"]}"/></linearGradient>',
        "</defs>",
        f'<rect width="100%" height="100%" rx="18" fill="{theme["bg"]}"/>',
        f'<text x="38" y="40" fill="{theme["text"]}" font-family="{font}" font-size="22" font-weight="700">Idea Journey</text>',
        f'<text x="38" y="66" fill="{theme["muted"]}" font-family="{font}" font-size="13">A chronological stream of captured thoughts</text>',
        f'<rect x="38" y="82" width="884" height="1" fill="{theme["border"]}"/>',
        f'<text x="922" y="38" text-anchor="end" fill="{theme["muted"]}" font-family="{font}" font-size="12">{total} IDEAS  ·  {open_count} OPEN  ·  {closed_count} CLOSED</text>',
    ]

    if not rows:
        out += [
            f'<rect x="210" y="135" width="540" height="76" rx="14" fill="{theme["card"]}" stroke="{theme["border"]}"/>',
            f'<text x="480" y="172" text-anchor="middle" fill="{theme["text"]}" font-family="{font}" font-size="15" font-weight="600">No ideas captured yet</text>',
            f'<text x="480" y="194" text-anchor="middle" fill="{theme["muted"]}" font-family="{font}" font-size="12">Create a GitHub Issue and it will appear here automatically.</text>',
        ]
    else:
        line_top = header_h + 24
        line_bottom = header_h + len(rows) * row_h - 30
        out.append(f'<rect x="{center - 1}" y="{line_top}" width="2" height="{max(2, line_bottom - line_top)}" rx="1" fill="{theme["line"]}"/>')

        previous_month = None
        for idx, (created, issue) in enumerate(rows):
            row_y = header_h + idx * row_h
            node_y = row_y + 52
            is_left = idx % 2 == 0
            card_x = left_x if is_left else right_x
            card_y = row_y + 10
            connector_x1 = card_x + card_w if is_left else center
            connector_x2 = center if is_left else card_x

            month_key = (created.year, created.month)
            if month_key != previous_month:
                month = f"{calendar.month_abbr[created.month].upper()} {created.year}"
                mw = 82
                out += [
                    f'<rect x="{center - mw/2:.1f}" y="{row_y - 4}" width="{mw}" height="22" rx="11" fill="{theme["month_bg"]}"/>',
                    f'<text x="{center}" y="{row_y + 11}" text-anchor="middle" fill="{theme["month_text"]}" font-family="{font}" font-size="10" font-weight="700">{month}</text>',
                ]
                card_y += 14
                node_y += 14
            previous_month = month_key

            state = issue.get("state", "open")
            state_color = theme["open"] if state == "open" else theme["closed"]
            state_text = "OPEN" if state == "open" else "CLOSED"
            title = truncate(display_title(issue.get("title", "Untitled idea")), 42)
            number = issue["number"]
            body = issue.get("body") or ""
            stage = truncate(parse_field(body, "Initial stage", "Inbox"), 16)
            category = truncate(parse_field(body, "Category", "Other"), 16)
            latest = (created, issue) == parsed[-1]
            card_fill = theme["card_latest"] if latest else theme["card"]
            card_stroke = theme["accent"] if latest else theme["border"]
            stroke_w = 1.6 if latest else 1

            out += [
                f'<line x1="{connector_x1}" y1="{node_y}" x2="{connector_x2}" y2="{node_y}" stroke="{theme["line"]}" stroke-width="2"/>',
                f'<circle cx="{center}" cy="{node_y}" r="7" fill="{theme["bg"]}" stroke="{state_color}" stroke-width="3"/>',
                f'<circle cx="{center}" cy="{node_y}" r="2.5" fill="{state_color}"/>',
                f'<rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="14" fill="{card_fill}" stroke="{card_stroke}" stroke-width="{stroke_w}"/>',
                f'<rect x="{card_x}" y="{card_y}" width="4" height="{card_h}" rx="2" fill="{state_color}"/>',
                f'<text x="{card_x + 20}" y="{card_y + 25}" fill="{theme["muted"]}" font-family="{font}" font-size="11" font-weight="600">#{number}  ·  {human_date(created)}</text>',
                f'<text x="{card_x + 20}" y="{card_y + 48}" fill="{theme["text"]}" font-family="{font}" font-size="15" font-weight="700">{svg_text(title)}</text>',
            ]

            px = card_x + 20
            for label in (state_text, stage.upper(), category.upper()):
                pw = pill_width(label)
                fill = state_color if label == state_text else theme["pill"]
                txt = theme["bg"] if label == state_text else theme["pill_text"]
                out += [
                    f'<rect x="{px}" y="{card_y + 60}" width="{pw}" height="17" rx="8.5" fill="{fill}"/>',
                    f'<text x="{px + pw/2}" y="{card_y + 72}" text-anchor="middle" fill="{txt}" font-family="{font}" font-size="9" font-weight="700">{svg_text(label)}</text>',
                ]
                px += pw + 7

            if latest:
                badge_w = 46
                badge_x = card_x + card_w - badge_w - 12
                out += [
                    f'<rect x="{badge_x}" y="{card_y + 8}" width="{badge_w}" height="18" rx="9" fill="url(#accent)"/>',
                    f'<text x="{badge_x + badge_w/2}" y="{card_y + 21}" text-anchor="middle" fill="#ffffff" font-family="{font}" font-size="9" font-weight="700">LATEST</text>',
                ]

    out.append(f'<text x="480" y="{height - 14}" text-anchor="middle" fill="{theme["muted"]}" font-family="{font}" font-size="10">Generated automatically from GitHub Issue creation timestamps</text>')
    out.append("</svg>")
    return "\n".join(out)

def generate_table(parsed, limit=None, newest_first=False):
    rows = list(reversed(parsed)) if newest_first else list(parsed)
    if limit is not None:
        rows = rows[:limit]
    lines = ["| Date | Idea | State |", "| --- | --- | --- |"]
    for created, issue in rows:
        title = markdown_escape(display_title(issue.get("title", "Untitled idea")))
        lines.append(f'| {human_date(created)} | [#{issue["number"]} — {title}]({issue["html_url"]}) | {state_label(issue)} |')
    return lines

def picture_block():
    return "\n".join([
        '<p align="center">',
        '  <picture>',
        '    <source media="(prefers-color-scheme: dark)" srcset="./assets/idea-journey-dark.svg">',
        '    <source media="(prefers-color-scheme: light)" srcset="./assets/idea-journey-light.svg">',
        '    <img alt="Brain Dump Idea Journey timeline" src="./assets/idea-journey-light.svg" width="100%">',
        '  </picture>',
        '</p>',
    ])

def generate_full(parsed):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# 🕒 Brain Dump Timeline", "",
        "Complete chronological history generated from original GitHub Issue creation timestamps.", "",
        picture_block(), "",
        f"_Last generated: {now}_", "",
        "## 💭 All ideas", "",
    ]
    if parsed:
        lines += generate_table(parsed)
    else:
        lines += ["> No ideas have been captured yet."]
    lines += ["", "> Dates come directly from GitHub Issue creation timestamps; no separate capture-date field is required.", ""]
    return "\n".join(lines)

def generate_home(parsed):
    total = len(parsed)
    open_count = sum(1 for _, issue in parsed if issue.get("state", "open") == "open")
    closed_count = total - open_count
    latest = parsed[-1] if parsed else None

    lines = [
        "## 📊 Snapshot", "",
        "| 💡 Total ideas | 🟢 Open | ✅ Closed | 🕒 Latest capture |",
        "| ---: | ---: | ---: | --- |",
        f'| {total} | {open_count} | {closed_count} | {human_date(latest[0]) if latest else "—"} |',
        "",
        "## ✨ Latest spark", "",
    ]

    if latest:
        created, issue = latest
        title = markdown_escape(display_title(issue.get("title", "Untitled idea")))
        lines += [
            f'**[#{issue["number"]} — {title}]({issue["html_url"]})**  ',
            f'Captured **{human_date(created)}** · {state_label(issue)}',
        ]
    else:
        lines += ["> Nothing here yet. [Capture the first idea](https://github.com/afnannuzulasugihartono/brain-dump/issues/new/choose)."]

    lines += ["", "## 🧭 Idea Journey", "", picture_block(), "", "## 💭 Latest ideas", ""]
    if parsed:
        lines += generate_table(parsed, limit=10, newest_first=True)
    else:
        lines += ["> No ideas captured yet."]
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
    parsed = parse_issues(issues)

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    (ASSET_DIR / "idea-journey-light.svg").write_text(generate_svg(parsed, "light"), encoding="utf-8")
    (ASSET_DIR / "idea-journey-dark.svg").write_text(generate_svg(parsed, "dark"), encoding="utf-8")
    Path("TIMELINE.md").write_text(generate_full(parsed), encoding="utf-8")
    update_readme(generate_home(parsed))
    print(f"Generated dashboard, SVG journey, and timeline from {len(parsed)} issue(s).")

if __name__ == "__main__":
    main()
