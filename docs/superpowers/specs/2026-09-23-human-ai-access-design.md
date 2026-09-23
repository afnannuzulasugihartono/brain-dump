# Brain Dump Human + AI Access Design

**Date:** 23 September 2026  
**Status:** Implemented on main; Human + AI Issue/API acceptance verified on 23 September 2026.

**Supersession note:** The later Review Intelligence design replaces the former Cards secondary view with Review and moves the generated index to `docs/data/ideas.json`.

## Intent

Brain Dump should work well for two audiences without adding a second source of truth:

- **Humans** browse, search, and review ideas through the lightweight GitHub Pages interface, then create or edit through GitHub Issues.
- **AI agents** read and write ideas through GitHub's official REST API using GitHub authentication and repository permissions.

GitHub Issues remain authoritative.

## Goals

- Keep the system lightweight and easy to maintain.
- Preserve a Memos-like, reader-first human interface.
- Give AI a deterministic, documented read/write contract.
- Preserve the user's original wording and intent.
- Keep material AI changes auditable.
- Avoid a custom backend, database, custom auth flow, or MCP in this phase.

## Architecture

```text
Human ──read──> GitHub Pages
Human ─write──> GitHub Issues
AI ──read/write──> GitHub REST API
                         │
                         ▼
                   GitHub Issues
                  source of truth
                         │
                         ▼
                    sync workflow
                  ┌──────┴──────┐
                  ▼             ▼
          docs/data/ideas.json   README/TIMELINE
                  │
                  ▼
             GitHub Pages
```

`docs/data/ideas.json` is a generated read index, never a write target.

## Human Access

The website remains read-only and should provide:

- chronological notes/feed;
- search;
- stage/category filters;
- secondary Review, Board, and Calendar views when useful;
- links to the canonical GitHub Issue.

Create and edit actions open GitHub Issues. The public website must not perform authenticated writes.

## AI Access

AI uses GitHub REST API directly.

Typical reads:

- list repository Issues;
- fetch one Issue;
- fetch Issue comments.

Typical writes:

- create an Issue;
- update an Issue;
- add an Issue comment.

Write authority is controlled by GitHub authentication and repository permissions. Brain Dump introduces no separate credential system.

## Canonical Idea Structure

The existing Issue structure remains canonical:

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

AI-added material should use:

```markdown
## AI Notes
Add AI-provided context, clarification, or research here.
```

## AI Write Policy

AI may:

- create a new idea when explicitly asked;
- read ideas available to its GitHub credentials;
- add context without deleting original human content;
- improve wording only when meaning is preserved;
- update Category;
- move `Inbox → Exploring → Promising`;
- add or update `AI Notes`;
- leave a concise comment for material changes;
- recommend promotion, merge, revisit, or archive.

AI must not:

- delete the user's original idea or context;
- silently change the user's intent;
- move an idea to `Project` without explicit user instruction;
- close an Issue autonomously;
- move an idea to `Archived` autonomously;
- remove the audit trail for material AI changes;
- place secrets or credentials in public repository content.

## Project Promotion

`Project` is a deliberate boundary between brainstorming material and an approved project/spec candidate.

AI may recommend promotion, but may perform it only after explicit user instruction for that idea.

## Archive Policy

AI may recommend archive/close but may not execute it without explicit user instruction.

A recommendation can be recorded in a comment, for example:

```text
Candidate for archive: duplicate / stale / no longer relevant.
```

## Audit Trail

Material AI changes should remain visible.

- AI-added context belongs under `## AI Notes` when practical.
- Material changes receive a short Issue comment summarizing the change.
- Minor formatting-only fixes do not require a comment.

Example:

```text
AI update:
- added comparison context
- category changed from Other to Software
- stage moved from Inbox to Exploring
```

## Agent Guidance

Implementation should add a root `AGENTS.md` that tells agents:

- GitHub Issues are the source of truth;
- generated JSON is read-only;
- canonical Issue fields;
- allowed and forbidden AI operations;
- stage transition rules;
- audit requirements;
- where to find detailed API guidance.

Detailed GitHub API usage belongs in `docs/ai-access.md`.

## Website Direction

The human interface should remain Memos-like:

- note-first rather than dashboard-first;
- no marketing hero;
- compact header;
- simple GitHub-linked new-note affordance;
- chronological feed as the primary view;
- low-contrast metadata;
- minimal badges;
- search visible but quiet;
- secondary views visually subordinate;
- mobile-friendly;
- no new UI framework required.

There are no AI controls on the public website.

## Sync Flow

1. Human or authenticated AI changes a GitHub Issue.
2. Existing GitHub Actions sync runs.
3. Generator rebuilds `docs/data/ideas.json`, README generated content, timeline content, and lightweight assets.
4. GitHub Pages deploys the read-only human interface.

A sync failure must not change the canonical Issue data.

## Conflict and Failure Handling

- If GitHub rejects a write, AI reports the failure and does not bypass permissions.
- Before a material edit, AI should re-read the Issue when stale data or concurrent changes are possible.
- New human content must be preserved during AI updates.
- Promotion to `Project` and archive/close require explicit user authorization.
- Generated-file failures are repaired by rerunning sync; Issues remain authoritative.

## Security Model

- Public Pages UI: read-only.
- GitHub Issues: canonical write surface.
- AI writes: GitHub-authenticated only.
- No write credential in client-side JavaScript.
- No anonymous write endpoint.
- No custom backend auth system.

## Expected Implementation Files

Likely implementation changes:

- create `AGENTS.md`;
- create `docs/ai-access.md`;
- update `.github/ISSUE_TEMPLATE/idea.yml`;
- update README guidance;
- update the generator if needed;
- refine `docs/index.html`, `docs/js/`, and `docs/styles/` to the approved Memos-like human design;
- change the sync workflow only if verification proves necessary.

No new runtime dependency is required.

## Verification Requirements

Implementation must verify:

1. humans can browse and search from Pages;
2. website create/edit actions go to GitHub rather than writing directly;
3. an API-created Issue appears in generated data after sync;
4. AI Notes survive regeneration;
5. audit comments remain intact;
6. generated JSON is never used as a write target;
7. no client-side source contains a write credential;
8. closed Issues are represented consistently;
9. mobile UI remains usable;
10. sync failures do not mutate Issue content.

## Success Criteria

The system succeeds when:

- humans have a lightweight, pleasant reader and use GitHub UI for writes;
- an authenticated AI can understand the repository rules without guessing;
- AI can create and safely enrich ideas through GitHub API;
- original human content remains preserved;
- material AI changes are auditable;
- promotion and archive boundaries remain controlled by the user;
- GitHub Issues remain the only authoritative data source;
- no custom backend, database, or custom authentication system is added.
