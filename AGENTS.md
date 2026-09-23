# Brain Dump Agent Contract

## Source of truth
GitHub Issues are the source of truth. All other representations are read-only views or source code derived from that canonical record.

## Data ownership
- Canonical data: GitHub Issues and their comments.
- Source code: `docs/index.html`, `docs/js/`, `docs/styles/`, `scripts/`, workflow files, and tests.
- Deterministic generated output: `docs/data/ideas.json`, the generated Recent ideas block in `README.md`, and `TIMELINE.md`.
- AI-generated optional output: `docs/data/ai-insights.json`.

Do not edit generated files manually as a substitute for changing their source. Edit the canonical Issue for idea content, or edit the relevant generator/evaluator for generated behavior.

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

Review suggestions such as `promote-candidate` and `consider-archive` are recommendations only. They never authorize a Project promotion, archive, or close operation.

## Audit trail
Put AI-added context under `## AI Notes` when practical. For material changes, add a short Issue comment describing what changed.

## API
Use GitHub REST API with official GitHub authentication and repository Issue permissions. On 401 or 403, stop and report the authorization failure. Do not attempt an alternate write path.

See `docs/ai-access.md` for endpoint and body examples.
