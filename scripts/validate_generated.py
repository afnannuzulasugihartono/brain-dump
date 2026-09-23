from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ALLOWED_ACTIONS = {"keep-exploring", "revisit", "promote-candidate", "consider-archive"}
ALLOWED_DEPTHS = {"brief", "detailed"}


def _parse_iso(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO timestamp")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO timestamp") from exc


def validate_ideas_document(data: dict) -> None:
    if data.get("source") != "GitHub Issues" or not isinstance(data.get("ideas"), list):
        raise ValueError("invalid ideas document")
    seen = set()
    for idea in data["ideas"]:
        number = idea.get("number")
        if not isinstance(number, int):
            raise ValueError("issue number must be an integer")
        if number in seen:
            raise ValueError(f"duplicate issue number: {number}")
        seen.add(number)
        _parse_iso(idea.get("createdAt"), "createdAt")
        _parse_iso(idea.get("updatedAt"), "updatedAt")


def validate_insights_document(data: dict) -> None:
    if not isinstance(data.get("insights"), list):
        raise ValueError("invalid insights document")
    seen = set()
    for insight in data["insights"]:
        number = insight.get("issueNumber")
        if not isinstance(number, int) or number in seen:
            raise ValueError("duplicate or invalid insight issueNumber")
        seen.add(number)
        _parse_iso(insight.get("evaluatedAt"), "evaluatedAt")
        if insight.get("suggestedAction") not in ALLOWED_ACTIONS:
            raise ValueError("invalid suggestedAction")
        if insight.get("depth") not in ALLOWED_DEPTHS:
            raise ValueError("invalid depth")
        confidence = insight.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError("invalid confidence")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ideas", default="docs/data/ideas.json")
    parser.add_argument("--insights", default="docs/data/ai-insights.json")
    args = parser.parse_args()
    validate_ideas_document(json.loads(Path(args.ideas).read_text(encoding="utf-8")))
    if Path(args.insights).exists():
        validate_insights_document(json.loads(Path(args.insights).read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
