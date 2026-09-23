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


def _require_string(item: dict, field: str, *, allow_empty: bool = True) -> str:
    value = item.get(field)
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        detail = "a non-empty string" if not allow_empty else "a string"
        raise ValueError(f"{field} must be {detail}")
    return value


def validate_ideas_document(data: dict) -> None:
    if data.get("source") != "GitHub Issues" or not isinstance(data.get("ideas"), list):
        raise ValueError("invalid ideas document")
    seen = set()
    for idea in data["ideas"]:
        if not isinstance(idea, dict):
            raise ValueError("idea must be an object")
        number = idea.get("number")
        if not isinstance(number, int):
            raise ValueError("issue number must be an integer")
        if number in seen:
            raise ValueError(f"duplicate issue number: {number}")
        seen.add(number)
        _require_string(idea, "title", allow_empty=False)
        _require_string(idea, "url", allow_empty=False)
        state = _require_string(idea, "state", allow_empty=False)
        if state not in {"open", "closed"}:
            raise ValueError("state must be open or closed")
        _require_string(idea, "stage", allow_empty=False)
        _require_string(idea, "category", allow_empty=False)
        _require_string(idea, "why")
        _require_string(idea, "idea")
        _require_string(idea, "aiNotes")
        _parse_iso(idea.get("createdAt"), "createdAt")
        _parse_iso(idea.get("updatedAt"), "updatedAt")
        closed_at = idea.get("closedAt")
        if closed_at is not None:
            _parse_iso(closed_at, "closedAt")


def validate_insights_document(data: dict) -> None:
    if data.get("source") != "AI review" or not isinstance(data.get("insights"), list):
        raise ValueError("invalid insights document")
    seen = set()
    for insight in data["insights"]:
        if not isinstance(insight, dict):
            raise ValueError("insight must be an object")
        number = insight.get("issueNumber")
        if not isinstance(number, int) or number in seen:
            raise ValueError("duplicate or invalid insight issueNumber")
        seen.add(number)
        _parse_iso(insight.get("evaluatedAt"), "evaluatedAt")
        _require_string(insight, "summary", allow_empty=False)
        if insight.get("suggestedAction") not in ALLOWED_ACTIONS:
            raise ValueError("invalid suggestedAction")
        signals = insight.get("signals")
        if not isinstance(signals, list) or not all(isinstance(item, str) for item in signals):
            raise ValueError("signals must be a list of strings")
        if insight.get("depth") not in ALLOWED_DEPTHS:
            raise ValueError("invalid depth")
        confidence = insight.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            raise ValueError("invalid confidence")
        for field in ("strength", "risk", "nextStep"):
            if field in insight and insight[field] is not None and not isinstance(insight[field], str):
                raise ValueError(f"{field} must be a string")


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
