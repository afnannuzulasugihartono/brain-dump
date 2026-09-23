# AI access to Brain Dump

GitHub Issues are the only authoritative write surface for Brain Dump. AI agents use the official GitHub REST API and GitHub authentication; `docs/ideas.json` is a generated, read-only discovery index.

## Authentication

Use a GitHub credential that has access to this repository and permission to read/write Issues. Never place the credential in an Issue, repository file, or client-side JavaScript.

Example read request:

```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/{owner}/{repo}/issues
```

If GitHub returns **401** or **403**, stop and report the authorization failure. Do not attempt an alternate write path.

## Sync eligibility

Brain Dump syncs Issues authored by the repository owner or an account GitHub identifies as a repository **COLLABORATOR** or **MEMBER**. Public outsider Issues are ignored by the generated Brain Dump index.

## Read endpoints

- `GET /repos/{owner}/{repo}/issues`
- `GET /repos/{owner}/{repo}/issues/{issue_number}`
- `GET /repos/{owner}/{repo}/issues/{issue_number}/comments`

For fast discovery an agent may read `docs/ideas.json`, but it must re-read the canonical Issue before a material update.

## Write endpoints

- `POST /repos/{owner}/{repo}/issues` — create an idea when the user asks.
- `PATCH /repos/{owner}/{repo}/issues/{issue_number}` — edit allowed fields while preserving human-authored content.
- `POST /repos/{owner}/{repo}/issues/{issue_number}/comments` — record a material AI change.

## Canonical Issue body

```markdown
## Idea
Write the original human idea here.

## Why it might matter
Write the context or motivation here.

## Initial stage
Inbox

## Category
Other

## Brain-dump rule
- [x] This is a raw idea, not an approved implementation task.
```

AI-added context may be appended as:

```markdown
## AI Notes
Add AI-provided context, clarification, or research here.
```

## Safe update algorithm

Before any material PATCH:

1. `GET` the Issue again immediately before editing.
2. Parse the current sections from that fresh response.
3. Preserve all human-authored sections exactly unless the user explicitly asked for a wording change.
4. Change only the permitted field or append/update `## AI Notes`.
5. `PATCH` the complete merged body.
6. For a material change, add a concise audit comment describing what changed.

This prevents an AI from overwriting human content that appeared after an earlier read.

## Stage rules

An AI may move an idea through:

`Inbox → Exploring → Promising`

Moving an idea to `Project` requires explicit user instruction for that idea.

Moving an idea to `Archived` or closing the Issue also requires explicit user instruction. Without that instruction, the AI may only recommend archive/close in a comment.

## Audit comments

Example material-change comment:

```text
AI update:
- added comparison context
- category changed from Other to Software
- stage moved from Inbox to Exploring
```

Minor formatting-only edits that do not change meaning do not need a comment.

## Create example

Use `POST /repos/{owner}/{repo}/issues` with a body like:

```json
{
  "title": "[Idea] Example",
  "body": "## Idea\nExample idea.\n\n## Why it might matter\nUseful context.\n\n## Initial stage\nInbox\n\n## Category\nOther\n\n## Brain-dump rule\n- [x] This is a raw idea, not an approved implementation task."
}
```

## Generated data

`docs/ideas.json`, README summaries, timeline files, and GitHub Pages are generated read views. Do not edit them as a substitute for editing the Issue.
