# Brain Dump Agent Contract

## Source of truth
GitHub Issues are the source of truth. `docs/ideas.json`, README summaries, timeline files, and Pages output are generated read-only views. Never write to generated data as a substitute for editing an Issue.

## Before changing an idea
Re-read the canonical Issue immediately before a material edit. Preserve all human-authored content, including content added after an earlier read.

## Allowed without additional approval
- Read Issues and comments.
- Create an idea when the user asks for one.
- Add context under `## AI Notes`.
- Improve wording without changing intent.
- Update Category.
- Move `Inbox → Exploring → Promising`.
- Leave a concise audit comment for material changes.

## Requires explicit user instruction
- Move an idea to `Project`.
- Move an idea to `Archived`.
- Close an Issue.
- Remove or replace human-authored content.

## Audit trail
Put AI-added context under `## AI Notes` when practical. For material changes, add a short Issue comment describing what changed.

## API
Use GitHub REST API with official GitHub authentication and repository Issue permissions. On 401 or 403, stop and report the authorization failure. Do not attempt an alternate write path.

See `docs/ai-access.md` for endpoint and body examples.
