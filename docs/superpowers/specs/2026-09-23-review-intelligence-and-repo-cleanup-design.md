# Brain Dump Review Intelligence, Ticker, and Conservative Repo Cleanup

Date: 2026-09-23
Status: Design approved in brainstorming; awaiting written-spec review

## 1. Purpose

Evolve Brain Dump without losing the light, Memos-like character that already works.

The next version should:
- stay fast, quiet, and human-first;
- keep GitHub Issues as the only source of truth;
- add lightweight idea-management intelligence without turning the site into a productivity dashboard;
- add a subtle moving ticker at the bottom;
- introduce a Review view for neglected and potentially useful ideas;
- use deterministic browser-side scoring as the baseline;
- add optional asynchronous AI insight that can fail safely;
- keep the public website read-only;
- reorganize the repository so humans and coding agents can understand one area at a time;
- preserve the current Human + AI GitHub workflow and safety gates.

## 2. Product direction

The selected direction is a hybrid personal notes workspace plus lightweight idea management.

Notes remain the primary experience. Review adds assistance without replacing the chronological note feed.

Main navigation:
- Notes
- Review
- Board
- Calendar

Cards leaves the primary navigation because it overlaps with Notes and does not provide enough unique value.

## 3. Architectural approach

Use a static-first architecture with an optional AI sidecar.

No new backend, database, custom OAuth layer, frontend framework migration, or client-side AI credential is introduced.

Data flow:

Human or AI → GitHub Issues → sync workflow → generated issue index + README/TIMELINE + GitHub Pages.

Issue changes and a daily schedule → AI review workflow → generated AI insight index.

GitHub Pages → browser → Notes / Review / Board / Calendar / deterministic scoring / ticker.

GitHub Issues remain canonical. Generated files are outputs only.

## 4. Generated data boundaries

Generated issue data moves to docs/data/ideas.json.

Optional AI-derived data lives separately at docs/data/ai-insights.json.

ideas.json contains factual Issue-derived fields:
- issue number;
- title;
- URL;
- open/closed state;
- stage;
- category;
- idea body;
- Why/context;
- AI Notes;
- created, updated, and closed timestamps.

ai-insights.json contains optional derived analysis only and never becomes canonical.

Frontend reads both independently. Failure to load AI insights must not block any core view.

## 5. Review system

### 5.1 Needs review

Ideas become due for review based on stage and time since the canonical Issue was last updated:
- Inbox: 7 days
- Exploring: 14 days
- Promising: 30 days
- Project: excluded
- Archived: excluded

Order longest-untouched first. This rule is deterministic and browser-side.

### 5.2 Worth revisiting

Worth revisiting uses a transparent rule-based score computed in the browser.

Initial baseline:
- Promising stage: +3
- non-empty AI Notes: +2
- non-empty Why/context: +1
- rich idea/context content: +1
- Issue still open: +1
- age greater than 14 days: +1
- Archived: excluded

Interpretation:
- 0–3: normal
- 4–5: mildly interesting
- 6 or more: show in Worth revisiting

The UI must expose the score signals in text. The score is deterministic, not an AI judgment.

The exact rich-content threshold may be tuned during implementation, but it must remain deterministic, documented, and tested.

### 5.3 Random rediscovery

Review shows one older idea as a daily rediscovery candidate.

Eligibility:
- not Archived;
- at least 7 days old;
- not updated on the current day.

Selection is deterministic for the current date. The same data and date must produce the same candidate.

## 6. AI-assisted review

AI is optional enhancement, never the primary ranking system.

### 6.1 Schedule

AI evaluation runs:
- when a trusted Issue is created or materially edited;
- once daily for eligible active ideas;
- manually through workflow dispatch.

### 6.2 Allowed output

AI may provide:
- a short explanation of why an idea may be worth another look;
- a suggested next action;
- useful signals;
- optional deeper context for high-scoring ideas.

Allowed suggested actions:
- keep-exploring
- revisit
- promote-candidate
- consider-archive

Recommendations only. AI must never automatically promote to Project, archive, close, or overwrite human-authored content. Existing AGENTS.md gates remain authoritative.

### 6.3 Adaptive depth

Default insight is brief: one short reason plus one suggested action.

For stronger candidates, insight may add strength, risk, and next step. Deeper detail stays collapsed until requested.

### 6.4 Insight schema

Each insight contains:
- issueNumber
- evaluatedAt
- summary
- suggestedAction
- signals
- confidence
- depth

Detailed entries may also contain strength, risk, and nextStep.

AI does not write the deterministic score.

### 6.5 Provider strategy

AI review uses a provider boundary instead of spreading provider-specific logic throughout the repo.

Conceptual interface: evaluate_idea(idea) → insight.

Prefer a free or generous-quota provider when practical.

If the provider is unavailable, rate-limited, times out, or produces invalid output:
- the main site still deploys;
- deterministic Review logic still works;
- old valid insight may be retained;
- otherwise AI insight may be omitted;
- generated JSON must remain valid.

AI is a sidecar, not a deployment dependency.

## 7. Review interactions

The website remains read-only.

Review cards may expose:
- Open in GitHub
- Review in GitHub
- Promote candidate
- Consider archive

These navigate to the canonical Issue or relevant GitHub flow. They do not mutate Issue state from the browser.

Direct web actions are deferred to a future phase.

## 8. Ticker

The bottom ticker is a hybrid stream of real system status and real idea snippets.

Possible items:
- total idea count;
- open idea count;
- number due for review;
- selected idea titles;
- selected stage/category tags;
- GitHub sync status when derivable;
- AI insight availability when useful.

It is not marketing copy.

### 8.1 Desktop

Ticker:
- fixed to the bottom viewport;
- about 28–32 px high;
- follows current theme;
- uses a thin top border;
- moves horizontally slowly;
- pauses on hover and keyboard focus;
- avoids glow, gradient, blur, and decorative effects.

### 8.2 Mobile

Ticker is not fixed. It becomes a normal footer-area ticker after main content.

### 8.3 Reduced motion

When prefers-reduced-motion: reduce is active, movement is disabled and content remains readable as static text.

Use CSS animation where practical; no animation library.

## 9. UI composition

Keep the current visual identity:
- system fonts;
- content width around 760 px;
- one accent;
- light borders;
- restrained surfaces;
- generous whitespace;
- almost no shadows;
- dark/light theme;
- mobile-first behavior.

Top-level structure:

Brain Dump | theme | New note

What's on your mind? | Write a note…

Search | Category | Stage

Notes | Review | Board | Calendar

### 9.1 Notes

Notes remains default, chronological, quiet, and focused on reading/capture.

### 9.2 Review

Review should feel editorial, not analytical.

No large KPI cards, charts, productivity scores, progress rings, gamification, or dashboard-style analytics.

Sections:
- Needs review
- Worth revisiting
- Rediscover

### 9.3 Board and Calendar

Board and Calendar remain secondary organizational views. Cleanup may refactor them without changing their purpose.

## 10. Repository cleanup

Cleanup is deep but conservative.

Only refactors with clear maintenance benefit are included. Do not add dependencies or frameworks merely to reorganize code.

Target boundary map:

.github/
- ISSUE_TEMPLATE/
- workflows/sync.yml
- workflows/ai-review.yml

docs/
- index.html
- styles/base.css
- styles/layout.css
- styles/notes.css
- styles/review.css
- styles/board.css
- styles/calendar.css
- styles/ticker.css
- js/app.js
- js/state.js
- js/data.js
- js/scoring.js
- js/notes.js
- js/review.js
- js/board.js
- js/calendar.js
- js/ticker.js
- js/theme.js
- data/ideas.json
- data/ai-insights.json
- ai-access.md
- superpowers/

scripts/
- generate/
- ai/
- ai/providers/

tests/
- frontend/
- generator/
- ai/
- workflow/

root:
- AGENTS.md
- README.md
- TIMELINE.md

This is a boundary map, not a mandate to maximize file count.

During implementation:
- combine files when separation adds ceremony without clarity;
- split when responsibilities are meaningfully independent;
- keep bootstrap/orchestration small;
- keep scoring separate from rendering;
- keep AI evaluation separate from canonical generation;
- keep generated data separate from source code.

## 11. Workflow boundaries

### 11.1 Main sync workflow

sync.yml responsibilities:
- trusted Issue event or relevant push trigger;
- run tests;
- generate canonical Issue-derived outputs;
- generate README/TIMELINE;
- commit generated output when changed;
- deploy GitHub Pages.

It must not depend on an AI provider.

### 11.2 AI review workflow

ai-review.yml responsibilities:
- trusted Issue opened/edited trigger;
- daily schedule;
- manual dispatch;
- read trusted canonical data;
- evaluate eligible ideas;
- validate AI output;
- update only AI insight generated data.

It must not edit GitHub Issues. Its failure must not block main sync/deploy.

## 12. Agent contract updates

AGENTS.md must explicitly distinguish:
- canonical Issue data;
- source frontend code;
- generated deterministic data;
- generated AI insight data.

Generated files are outputs and must not be edited manually as a substitute for their source.

Existing gates remain:
- AI may move Inbox → Exploring → Promising;
- Project requires explicit user instruction;
- Archived requires explicit user instruction;
- close requires explicit user instruction;
- human-authored content must be preserved.

## 13. Error handling

If canonical issue data cannot load:
- show a simple Could not load notes state;
- expose a link to GitHub Issues;
- do not render misleading empty Review/Board data.

If AI insight data is absent, invalid, stale, or unavailable:
- Notes works;
- rule-based Review works;
- Board works;
- Calendar works;
- ticker works;
- AI content is omitted or shown subtly as unavailable.

No blocking modal or permanent spinner.

Generated data schema/content validation runs before deployment. Invalid canonical data should fail before broken Pages output is deployed.

## 14. Testing strategy

Generator tests cover:
- Issue Form parsing;
- trusted-author filtering;
- stage mapping;
- canonical JSON schema;
- archive/closed behavior;
- new docs/data/ideas.json output path.

Scoring tests cover:
- Inbox 7-day threshold;
- Exploring 14-day threshold;
- Promising 30-day threshold;
- Project exclusion;
- Archived exclusion;
- deterministic Worth revisiting scoring;
- deterministic daily rediscovery.

AI tests cover:
- insight schema validation;
- missing-provider fallback;
- timeout/rate-limit fallback;
- invalid model response rejection;
- no Issue mutation path;
- safe retention of old valid insight where applicable.

Frontend tests cover:
- Notes default;
- Review three sections;
- search/filter regression;
- ticker from real data;
- reduced-motion behavior;
- mobile ticker non-fixed;
- no client-side GitHub credential;
- no client-side GitHub write API path.

Workflow tests cover:
- sync does not require AI availability;
- AI workflow has Issue event, daily schedule, and manual trigger;
- AI workflow cannot write Issues;
- generated data validation occurs before deploy.

## 15. Accessibility

Ticker:
- honors reduced motion;
- pauses on hover/focus;
- uses readable speed;
- does not depend on motion to convey essential information.

Navigation:
- correct button/link semantics;
- accessible active-view state;
- natural keyboard flow.

Review:
- score explained in text, not color alone;
- clear action labels;
- deeper AI context progressively disclosed.

Light and dark themes must retain readable contrast.

## 16. Acceptance criteria

Implementation is complete only when:
- Notes remains default and Memos-like;
- nav is Notes / Review / Board / Calendar;
- Cards leaves main nav;
- Review contains Needs review, Worth revisiting, and Rediscover;
- stage-age thresholds match this design;
- deterministic scoring runs in browser;
- score reasons are visible;
- daily rediscovery is deterministic;
- AI review is asynchronous and optional;
- AI insight follows the allowed-action policy;
- AI failure does not break site or main deployment;
- ticker combines real status and idea content;
- ticker is fixed on desktop and non-fixed on mobile;
- reduced-motion disables ticker movement;
- frontend contains no GitHub write credential or direct mutation path;
- GitHub Issues remain sole source of truth;
- deterministic and AI generated data have clear boundaries;
- main sync and AI review workflows are independent;
- repo modules are easier to understand without unnecessary dependencies;
- obsolete/duplicate files are removed only after replacement verification;
- regression tests pass;
- production GitHub Pages acceptance is performed after integration;
- final UI feels like an evolution of current Brain Dump, not a replacement of its identity.

## 17. Non-goals

This phase does not include:
- direct write actions from GitHub Pages;
- custom authentication;
- custom backend/database;
- frontend framework migration;
- AI-generated canonical scoring;
- automatic Project promotion;
- automatic archive/close;
- charts, productivity metrics, gamification, or dashboard analytics;
- replacing GitHub Issues as source of truth.

## 18. Implementation principle

Prefer the smallest architecture that satisfies the approved behavior.

Repo cleanup must reduce cognitive load, not merely move code into more files.

When an abstraction or file split does not improve isolation, testing, or readability, keep the simpler structure.
