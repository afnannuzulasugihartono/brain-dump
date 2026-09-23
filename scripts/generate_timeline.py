#!/usr/bin/env python3
"""Generate Brain Dump data, README feed, and lightweight timeline assets."""
from __future__ import annotations

import calendar
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

API = "https://api.github.com"
START_MARKER = "<!-- TIMELINE:START -->"
END_MARKER = "<!-- TIMELINE:END -->"
ASSET_DIR = Path("assets")
RECENT_LIMIT = 8
TRUSTED_AUTHOR_ASSOCIATIONS = {"OWNER", "COLLABORATOR", "MEMBER"}

THEMES = {
    "light": {
        "bg": "#ffffff", "surface": "#f6f8fa", "border": "#d8dee4",
        "text": "#24292f", "muted": "#6e7781", "faint": "#8c959f",
        "accent": "#0969da", "accent_soft": "#ddf4ff",
        "green": "#1a7f37", "green_soft": "#dafbe1",
    },
    "dark": {
        "bg": "#0d1117", "surface": "#161b22", "border": "#30363d",
        "text": "#e6edf3", "muted": "#8b949e", "faint": "#6e7681",
        "accent": "#58a6ff", "accent_soft": "#13233a",
        "green": "#3fb950", "green_soft": "#12261a",
    },
}

from scripts.generate.issues import (
    display_title,
    effective_stage,
    get_issues,
    is_trusted_issue,
    normalize_issue,
    parse_field,
    parse_section,
)

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

def truncate(value: str, limit: int) -> str:
    value = " ".join((value or "").split())
    return value if len(value) <= limit else value[:limit - 1].rstrip() + "…"

def generate_ideas_json(parsed):
    ideas = [normalize_issue(issue) for _, issue in reversed(parsed)]
    return json.dumps({"source": "GitHub Issues", "ideas": ideas}, ensure_ascii=False, indent=2) + "\n"

#!/usr/bin/env python3
"""Generate Brain Dump data, README feed, and lightweight timeline assets."""
from __future__ import annotations

import calendar
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

API = "https://api.github.com"
START_MARKER = "<!-- TIMELINE:START -->"
END_MARKER = "<!-- TIMELINE:END -->"
ASSET_DIR = Path("assets")
RECENT_LIMIT = 8
TRUSTED_AUTHOR_ASSOCIATIONS = {"OWNER", "COLLABORATOR", "MEMBER"}

THEMES = {
    "light": {
        "bg": "#ffffff", "surface": "#f6f8fa", "border": "#d8dee4",
        "text": "#24292f", "muted": "#6e7781", "faint": "#8c959f",
        "accent": "#0969da", "accent_soft": "#ddf4ff",
        "green": "#1a7f37", "green_soft": "#dafbe1",
    },
    "dark": {
        "bg": "#0d1117", "surface": "#161b22", "border": "#30363d",
        "text": "#e6edf3", "muted": "#8b949e", "faint": "#6e7681",
        "accent": "#58a6ff", "accent_soft": "#13233a",
        "green": "#3fb950", "green_soft": "#12261a",
    },
}

from scripts.generate.issues import (
    display_title,
    effective_stage,
    get_issues,
    is_trusted_issue,
    normalize_issue,
    parse_field,
    parse_section,
)

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

def truncate(value: str, limit: int) -> str:
    value = " ".join((value or "").split())
    return value if len(value) <= limit else value[:limit - 1].rstrip() + "…"

def generate_ideas_json(parsed):
    ideas = []
    for _, issue in reversed(parsed):
        body = issue.get("body") or ""
        ideas.append({
            "number": issue["number"],
            "title": display_title(issue.get("title", "Untitled idea")),
            "url": issue["html_url"],
            "state": issue.get("state", "open"),
            "stage": effective_stage(issue),
            "category": parse_field(body, "Category", "Other"),
            "why": parse_field(body, "Why it might matter", ""),
            "idea": parse_section(body, "Idea", ""),
            "aiNotes": parse_section(body, "AI Notes", ""),
            "createdAt": issue["created_at"],
            "updatedAt": issue.get("updated_at") or issue["created_at"],
            "closedAt": issue.get("closed_at"),
        })
    return json.dumps({"source": "GitHub Issues", "ideas": ideas}, ensure_ascii=False, indent=2) + "\n"

def generate_svg(parsed, theme_name: str):
    theme = THEMES[theme_name]
    rows = parsed[-10:]
    width, header_h, row_h, footer_h = 920, 72, 82, 28
    height = header_h + max(1, len(rows)) * row_h + footer_h
    font = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
    total = len(parsed)
    open_count = sum(1 for _, issue in parsed if issue.get("state", "open") == "open")

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Brain Dump timeline</title>',
        '<desc id="desc">A compact chronological feed generated from GitHub Issues.</desc>',
        f'<rect width="100%" height="100%" rx="10" fill="{theme["bg"]}"/>',
        f'<text x="24" y="30" fill="{theme["text"]}" font-family="{font}" font-size="17" font-weight="700">Brain Dump timeline</text>',
        f'<text x="24" y="50" fill="{theme["muted"]}" font-family="{font}" font-size="10">Capture now. Organize later.</text>',
        f'<text x="{width-24}" y="30" text-anchor="end" fill="{theme["muted"]}" font-family="{font}" font-size="9">{total} IDEAS · {open_count} OPEN</text>',
        f'<line x1="24" y1="62" x2="{width-24}" y2="62" stroke="{theme["border"]}"/>',
    ]

    if rows:
        for idx, (created, issue) in enumerate(rows):
            y = header_h + idx * row_h
            state = issue.get("state", "open")
            stage = effective_stage(issue)
            category = parse_field(issue.get("body") or "", "Category", "Other")
            why = truncate(parse_field(issue.get("body") or "", "Why it might matter", ""), 82)
            title = html.escape(truncate(display_title(issue.get("title", "Untitled idea")), 58))
            latest = (created, issue) == parsed[-1]
            dot = theme["accent"] if latest else (theme["green"] if state == "open" else theme["muted"])
            fill = theme["accent_soft"] if latest else theme["bg"]

            out += [
                f'<rect x="14" y="{y+4}" width="{width-28}" height="{row_h-8}" rx="8" fill="{fill}"/>',
                f'<text x="28" y="{y+26}" fill="{theme["muted"]}" font-family="{font}" font-size="9">{created.day} {calendar.month_abbr[created.month]}</text>',
                f'<circle cx="100" cy="{y+22}" r="4" fill="{dot}"/>',
                f'<text x="118" y="{y+25}" fill="{theme["text"]}" font-family="{font}" font-size="13" font-weight="700">{title}</text>',
                f'<text x="118" y="{y+44}" fill="{theme["muted"]}" font-family="{font}" font-size="9">{html.escape(why or "No context added yet.")}</text>',
                f'<text x="118" y="{y+62}" fill="{theme["muted"]}" font-family="{font}" font-size="8">{html.escape(stage.upper())} · {html.escape(category.upper())} · {state.upper()}</text>',
                f'<line x1="100" y1="{y+70}" x2="{width-24}" y2="{y+70}" stroke="{theme["border"]}"/>',
            ]
    else:
        out += [
            f'<text x="{width/2}" y="118" text-anchor="middle" fill="{theme["text"]}" font-family="{font}" font-size="13" font-weight="700">No ideas captured yet</text>',
            f'<text x="{width/2}" y="138" text-anchor="middle" fill="{theme["muted"]}" font-family="{font}" font-size="9">Create an Issue and it will appear here automatically.</text>',
        ]

    out.append(f'<text x="{width/2}" y="{height-10}" text-anchor="middle" fill="{theme["faint"]}" font-family="{font}" font-size="8">Generated from GitHub Issue timestamps</text>')
    out.append("</svg>")
    return "\n".join(out)

def picture_block():
    return "\n".join([
        '<picture>',
        '  <source media="(prefers-color-scheme: dark)" srcset="./assets/idea-journey-dark.svg">',
        '  <source media="(prefers-color-scheme: light)" srcset="./assets/idea-journey-light.svg">',
        '  <img alt="Brain Dump timeline" src="./assets/idea-journey-light.svg" width="100%">',
        '</picture>',
    ])

def generate_home(parsed):
    total = len(parsed)
    open_count = sum(1 for _, issue in parsed if issue.get("state", "open") == "open")
    lines = [
        "## Recent ideas", "",
        f"_{total} idea{'s' if total != 1 else ''} · {open_count} open_",
        "",
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
                f"### {human_date(created)} · [#{issue['number']} {title}]({issue['html_url']})",
                "",
                why,
                "",
                f"**{stage}** · {category} · {state}",
                "",
            ]
        if total > RECENT_LIMIT:
            lines += [f"[View all {total} ideas →](TIMELINE.md)", ""]
    return "\n".join(lines)

def generate_full(parsed):
    lines = [
        "# Brain Dump timeline", "",
        "A complete chronological feed generated from GitHub Issues.", "",
        picture_block(), "",
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
                f"### {human_date(created)} · [#{issue['number']} {title}]({issue['html_url']})",
                "",
                why,
                "",
                f"**{stage}** · {category} · {state}",
                "",
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
    issues = [
        issue for issue in get_issues(repo, token)
        if is_trusted_issue(issue, owner)
    ]
    parsed = parse_issues(issues)

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    (ASSET_DIR / "idea-journey-light.svg").write_text(generate_svg(parsed, "light"), encoding="utf-8")
    (ASSET_DIR / "idea-journey-dark.svg").write_text(generate_svg(parsed, "dark"), encoding="utf-8")
    Path("docs/data").mkdir(parents=True, exist_ok=True)
    Path("docs/data/ideas.json").write_text(generate_ideas_json(parsed), encoding="utf-8")
    Path("TIMELINE.md").write_text(generate_full(parsed), encoding="utf-8")
    update_readme(generate_home(parsed))
    print(f"Generated Brain Dump from {len(parsed)} issue(s).")

if __name__ == "__main__":
    main()
