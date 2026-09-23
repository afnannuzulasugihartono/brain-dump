from __future__ import annotations

import json
import re
import urllib.request

API = "https://api.github.com"
TRUSTED_AUTHOR_ASSOCIATIONS = {"OWNER", "COLLABORATOR", "MEMBER"}


def api_get(url: str, token: str):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "brain-dump",
    })
    with urllib.request.urlopen(req, timeout=30) as response:
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


def get_issue(repo: str, issue_number: int, token: str):
    return api_get(f"{API}/repos/{repo}/issues/{issue_number}", token)


def display_title(value: str) -> str:
    title = " ".join((value or "Untitled idea").split())
    return title[7:].strip() if title.lower().startswith("[idea] ") else title


def parse_field(body: str, heading: str, fallback: str) -> str:
    match = re.search(
        rf"(?ims)^#{{2,6}}\s+{re.escape(heading)}\s*\n+(.+?)(?=\n#{{2,6}}\s+|\Z)",
        body or "",
    )
    if not match:
        return fallback
    value = " ".join(match.group(1).strip().splitlines()[0].split())
    return value or fallback


def parse_section(body: str, heading: str, fallback: str = "") -> str:
    match = re.search(
        rf"(?ims)^#{{2,6}}\s+{re.escape(heading)}\s*\n+(.+?)(?=\n#{{2,6}}\s+|\Z)",
        body or "",
    )
    if not match:
        return fallback
    value = match.group(1).strip()
    return value or fallback


def is_trusted_issue(issue: dict, owner: str) -> bool:
    login = issue.get("user", {}).get("login", "").lower()
    association = (issue.get("author_association") or "").upper()
    return login == owner.lower() or association in TRUSTED_AUTHOR_ASSOCIATIONS


def effective_stage(issue: dict) -> str:
    stage = parse_field(issue.get("body") or "", "Initial stage", "Inbox")
    if issue.get("state") == "closed" and stage.lower() not in {"project", "archived"}:
        return "Archived"
    return stage


def normalize_issue(issue: dict) -> dict:
    body = issue.get("body") or ""
    return {
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
    }
