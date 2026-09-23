from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.ai.providers.openai_compatible import request_insight
from scripts.generate.issues import get_issue, is_trusted_issue, normalize_issue
from scripts.validate_generated import ALLOWED_ACTIONS, ALLOWED_DEPTHS, validate_insights_document

INSIGHTS_PATH = Path("docs/data/ai-insights.json")
IDEAS_PATH = Path("docs/data/ideas.json")


def validate_insight(candidate: dict, issue_number: int, evaluated_at: str) -> dict:
    if not isinstance(candidate, dict):
        raise ValueError("insight must be an object")
    if candidate.get("issueNumber") != issue_number:
        raise ValueError("insight issueNumber does not match")
    summary = candidate.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("summary must be a non-empty string")
    action = candidate.get("suggestedAction")
    if action not in ALLOWED_ACTIONS:
        raise ValueError("invalid suggestedAction")
    signals = candidate.get("signals")
    if not isinstance(signals, list) or not all(isinstance(item, str) for item in signals):
        raise ValueError("signals must be a list of strings")
    confidence = candidate.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
        raise ValueError("invalid confidence")
    depth = candidate.get("depth")
    if depth not in ALLOWED_DEPTHS:
        raise ValueError("invalid depth")

    normalized = {
        "issueNumber": issue_number,
        "evaluatedAt": evaluated_at,
        "summary": summary.strip(),
        "suggestedAction": action,
        "signals": [item.strip() for item in signals if item.strip()],
        "confidence": float(confidence),
        "depth": depth,
    }
    for field in ("strength", "risk", "nextStep"):
        value = candidate.get(field)
        if value is not None:
            if not isinstance(value, str):
                raise ValueError(f"{field} must be a string")
            if value.strip():
                normalized[field] = value.strip()
    return normalized


def merge_insights(existing: list[dict], updates: list[dict]) -> list[dict]:
    merged = {item["issueNumber"]: item for item in existing if isinstance(item, dict) and isinstance(item.get("issueNumber"), int)}
    for item in updates:
        merged[item["issueNumber"]] = item
    return [merged[number] for number in sorted(merged)]


def is_eligible(idea: dict) -> bool:
    return idea.get("state") == "open" and str(idea.get("stage") or "").lower() not in {"project", "archived"}


def _read_existing() -> list[dict]:
    if not INSIGHTS_PATH.exists():
        return []
    data = json.loads(INSIGHTS_PATH.read_text(encoding="utf-8"))
    validate_insights_document(data)
    return data["insights"]


def _load_batch_ideas() -> list[dict]:
    data = json.loads(IDEAS_PATH.read_text(encoding="utf-8"))
    return [idea for idea in data.get("ideas", []) if is_eligible(idea)]


def _load_issue_idea(issue_number: int, repo: str, token: str) -> list[dict]:
    issue = get_issue(repo, issue_number, token)
    owner = repo.split("/", 1)[0].lower()
    if not is_trusted_issue(issue, owner):
        print(f"Skipping untrusted issue #{issue_number}.")
        return []
    idea = normalize_issue(issue)
    return [idea] if is_eligible(idea) else []


def _write_document(insights: list[dict]) -> None:
    document = {"source": "AI review", "insights": insights}
    validate_insights_document(document)
    INSIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = INSIGHTS_PATH.with_suffix(".json.tmp")
    temp.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(INSIGHTS_PATH)



def evaluate_ideas(
    ideas: list[dict],
    existing: list[dict],
    *,
    evaluated_at: str,
    base_url: str,
    api_key: str,
    model: str,
    request_func=request_insight,
) -> tuple[list[dict], int]:
    updates = []
    for idea in ideas:
        try:
            raw = request_func(idea, base_url=base_url, api_key=api_key, model=model)
            updates.append(validate_insight(raw, idea["number"], evaluated_at))
        except Exception as exc:
            print(f"AI review failed for issue #{idea.get('number')}: {exc}", file=sys.stderr)
    return merge_insights(existing, updates), len(updates)

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-number", type=int)
    args = parser.parse_args(argv)

    base_url = os.environ.get("AI_BASE_URL", "").strip()
    api_key = os.environ.get("AI_API_KEY", "").strip()
    model = os.environ.get("AI_MODEL", "").strip()
    if not base_url or not api_key or not model:
        print("AI review degraded: provider configuration missing; preserving existing insights.")
        return 0

    existing = _read_existing()
    if args.issue_number is not None:
        repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if not repo or not token:
            print("GITHUB_REPOSITORY and GITHUB_TOKEN are required for issue mode.", file=sys.stderr)
            return 2
        ideas = _load_issue_idea(args.issue_number, repo, token)
    else:
        ideas = _load_batch_ideas()

    evaluated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    merged, update_count = evaluate_ideas(
        ideas,
        existing,
        evaluated_at=evaluated_at,
        base_url=base_url,
        api_key=api_key,
        model=model,
    )
    if merged != existing:
        _write_document(merged)
        print(f"AI review updated {update_count} insight(s).")
    else:
        print("AI review produced no changes; preserving existing insights.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
