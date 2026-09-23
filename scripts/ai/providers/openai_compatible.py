from __future__ import annotations

import json
import urllib.request

SYSTEM_PROMPT = """You review a personal idea backlog.
Return exactly one JSON object and no Markdown.
The object must contain issueNumber, summary, suggestedAction, signals, confidence, and depth.
Allowed suggestedAction values: keep-exploring, revisit, promote-candidate, consider-archive.
Allowed depth values: brief, detailed.
Do not recommend automatic mutations. Keep summary concise. Use depth=brief unless the idea is clearly rich enough to justify strength/risk/nextStep."""


def parse_provider_content(content: str) -> dict:
    return json.loads(content.strip())


def request_insight(idea, *, base_url, api_key, model, timeout=30):
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(idea, ensure_ascii=False)},
        ],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.load(response)
    content = body["choices"][0]["message"]["content"]
    return parse_provider_content(content)
