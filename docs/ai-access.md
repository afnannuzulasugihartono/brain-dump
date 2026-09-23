# AI access to Brain Dump

GitHub Issues are the only authoritative write surface for Brain Dump. AI agents use the official GitHub REST API and GitHub authentication; `docs/data/ideas.json` is a generated, read-only discovery index.

## Authentication

Use a GitHub credential that has access to this repository and permission to read/write Issues. Never place the credential in an Issue, repository file, or client-side JavaScript.

If GitHub returns **401** or **403**, stop and report the authorization failure. Do not attempt an alternate write path.

## Sync eligibility

Brain Dump syncs Issues authored by the repository owner or an account GitHub identifies as a repository **COLLABORATOR** or **MEMBER**. Public outsider Issues are ignored by the generated Brain Dump index.

## Read endpoints

- `GET /repos/{owner}/{repo}/issues`
- `GET /repos/{owner}/{repo}/issues/{issue_number}`
- `GET /repos/{owner}/{repo}/issues/{issue_number}/comments`

For fast discovery an agent may read `docs/data/ideas.json`, but it must re-read the canonical Issue before a material update.

## Write endpoints

- `POST /repos/{owner}/{repo}/issues` — create an idea when the user asks.
- `PATCH /repos/{owner}/{repo}/issues/{issue_number}` — edit allowed fields while preserving human-authored content.
- `POST /repos/{owner}/{repo}/issues/{issue_number}/comments` — record a material AI change.

## Review intelligence

The public Brain Dump website is **read-only**. Its Review view derives deterministic, explainable scoring directly in the browser from `docs/data/ideas.json`; that score is not an AI judgment.

Optional AI analysis is stored separately in `docs/data/ai-insights.json`. The sidecar may be missing, stale, or unavailable without changing canonical Issue data or blocking Notes, Review, Board, Calendar, search, filters, or the ticker.

AI Review may recommend `keep-exploring`, `revisit`, `promote-candidate`, or `consider-archive`. These are recommendations only. `promote-candidate` does not authorize moving an Issue to Project, and `consider-archive` does not authorize archiving or closing it. The stage gates above remain authoritative.

AI provider credentials belong only in GitHub-managed Actions secrets/variables. Never place provider credentials in Issues, repository files, generated JSON, or client-side JavaScript.

## Generated data

`docs/data/ideas.json`, `docs/data/ai-insights.json`, README summaries, timeline files, and GitHub Pages are generated read views. Do not edit them as a substitute for editing the Issue.
