# Brain Dump Human + AI Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Brain Dump a lightweight human-readable notes app on GitHub Pages while giving authenticated AI agents a clear, safe read/write contract through the GitHub REST API.

**Architecture:** GitHub Issues remain the only authoritative data source. Humans read through a static Memos-like GitHub Pages UI and write through GitHub Issue UI; AI reads/writes Issues through authenticated GitHub REST API. The existing generator produces a read-only `docs/data/ideas.json` index plus README/timeline views, and the sync workflow deploys Pages.

**Tech Stack:** GitHub Issues, GitHub REST API, GitHub Actions, GitHub Pages, Python 3 standard library, static HTML/CSS/JavaScript, Python `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-23-human-ai-access-design.md`

**Implementation status (reconciled 23 September 2026):** Implemented and accepted on `main`. The temporary API acceptance Issue was created, edited with an audit comment, archived, and closed. The later Review Intelligence plan superseded the old monolithic frontend paths and renamed `sync-brain-dump.yml` to `sync.yml`. The unchecked step boxes below are retained as the original execution recipe rather than retroactively claiming that every historical RED/GREEN command was run exactly as written.


## Global Constraints

- GitHub Issues remain the single source of truth.
- `docs/data/ideas.json` is generated read-only data and must never be an AI write target.
- Human writes happen through GitHub Issues; the public Pages UI remains read-only.
- AI writes require official GitHub authentication and repository Issues permission.
- Preserve original human-written idea/context; AI-added material belongs under `## AI Notes` when practical.
- AI may move `Inbox → Exploring → Promising`; `Project` requires explicit user instruction.
- Archive/close requires explicit user instruction; AI may only recommend it otherwise.
- Material AI changes leave an Issue comment audit trail.
- No custom backend, database, custom OAuth flow, MCP server, frontend write token, external UI framework, or new runtime dependency.
- Keep the human UI Memos-like: note-first, compact, low-contrast metadata, minimal badges, mobile-friendly.

## Review Focus

1. **Concurrent human/AI edits:** an agent must re-read before material updates and preserve human content added since its previous read; contract tests must explicitly require this behavior in `AGENTS.md` and `docs/ai-access.md`.
2. **Unauthorized writes:** API guidance must stop on 401/403 and must not describe bypass/fallback writes; tests must pin this wording.
3. **Closed Issues:** generator must continue representing a closed non-Project/non-Archived Issue as `Archived`, with regression coverage.
4. **AI Notes parsing:** missing, empty, and multiline `## AI Notes` must not break generation; the generated read index should expose useful AI notes without modifying canonical Issue content.
5. **Frontend secret/write regression:** static UI tests must fail if client code introduces GitHub write API calls, authorization headers, token-like config, or removes the GitHub-linked human write flow.

---

### Task 1: Establish the Repository-Level AI Contract

**Files:**
- Create: `AGENTS.md`
- Create: `docs/ai-access.md`
- Modify: `.github/ISSUE_TEMPLATE/idea.yml`
- Create: `tests/test_ai_contract.py`

**Interfaces:**
- Consumes: policy defined in `docs/superpowers/specs/2026-09-23-human-ai-access-design.md`.
- Produces: a root-level contract agents can discover automatically, detailed REST guidance, and a canonical Issue template that remains compatible with the generator.

- [ ] **Step 1: Write the failing AI contract tests**

Create `tests/test_ai_contract.py`:

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AIContractTests(unittest.TestCase):
    def test_agents_declares_source_of_truth_and_generated_json_read_only(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("GitHub Issues", text)
        self.assertIn("source of truth", text.lower())
        self.assertIn("docs/ideas.json", text)
        self.assertIn("read-only", text.lower())

    def test_agents_enforces_project_and_archive_gates(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
        self.assertIn("project", text)
        self.assertIn("explicit user instruction", text)
        self.assertIn("archive", text)
        self.assertIn("close", text)

    def test_agents_requires_reread_and_human_content_preservation(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
        self.assertIn("re-read", text)
        self.assertIn("preserve", text)
        self.assertIn("human", text)

    def test_api_doc_uses_official_issue_endpoints_and_stops_on_auth_failure(self):
        text = (ROOT / "docs" / "ai-access.md").read_text(encoding="utf-8")
        lowered = text.lower()
        self.assertIn("GET /repos/{owner}/{repo}/issues", text)
        self.assertIn("POST /repos/{owner}/{repo}/issues", text)
        self.assertIn("PATCH /repos/{owner}/{repo}/issues/{issue_number}", text)
        self.assertIn("POST /repos/{owner}/{repo}/issues/{issue_number}/comments", text)
        self.assertIn("401", text)
        self.assertIn("403", text)
        self.assertIn("stop", lowered)
        self.assertIn("do not attempt an alternate write path", lowered)

    def test_issue_template_stays_human_first_and_keeps_canonical_sections(self):
        text = (ROOT / ".github" / "ISSUE_TEMPLATE" / "idea.yml").read_text(encoding="utf-8")
        for label in ("Idea", "Why it might matter", "Initial stage", "Category", "Brain-dump rule"):
            self.assertIn(f"label: {label}", text)
        self.assertNotIn("label: AI Notes", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the contract tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_ai_contract -v
```

Expected: FAIL because `AGENTS.md` and `docs/ai-access.md` do not exist yet.

- [ ] **Step 3: Create `AGENTS.md` with the concise agent rules**

Write the root file with these exact sections:

```markdown
# Brain Dump Agent Contract

## Source of truth
GitHub Issues are the source of truth. `docs/data/ideas.json`, README summaries, timeline files, and Pages output are generated read-only views. Never write to generated data as a substitute for editing an Issue.

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
```

- [ ] **Step 4: Create `docs/ai-access.md` with concrete GitHub REST examples**

Document:
- read list/get/comments endpoints;
- create/update/comment endpoints;
- required authentication;
- canonical Issue body;
- safe append/update algorithm: fetch → parse → preserve original sections → update allowed field/AI Notes → PATCH → add audit comment;
- stage rules;
- archive/project gates;
- 401/403 stop behavior;
- note that `docs/data/ideas.json` is discovery-only.

Use request examples that never embed a real token. Example shell shape:

```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/{owner}/{repo}/issues
```

For writes, show JSON bodies with placeholders such as `"title": "[Idea] Example"` and a canonical Markdown body. State that an agent must re-read the Issue immediately before a material PATCH.

- [ ] **Step 5: Keep the Issue form human-first**

Do not expose an `AI Notes` field in the human Issue form. AI appends `## AI Notes` through the GitHub API only when it actually contributes context.

Simplify the top-level template copy without changing canonical field labels:

```yaml
name: New idea
description: Add a note or idea.
title: "[Idea] "
```

Change the Idea placeholder to:

```yaml
placeholder: What's on your mind?
```

Keep the existing `Idea`, `Why it might matter`, `Initial stage`, `Category`, `Related links or context`, and `Brain-dump rule` fields intact.

- [ ] **Step 6: Run the AI contract tests**

Run:

```bash
python3 -m unittest tests.test_ai_contract -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit the AI contract**

```bash
git add AGENTS.md docs/ai-access.md .github/ISSUE_TEMPLATE/idea.yml tests/test_ai_contract.py
git commit -m "docs: define Brain Dump AI access contract"
```

---

### Task 2: Expose AI Notes Safely in the Generated Read Index

**Files:**
- Modify: `scripts/generate_timeline.py`
- Create: `tests/test_generate_timeline.py`

**Interfaces:**
- Consumes: canonical GitHub Issue Markdown sections.
- Produces: each `docs/data/ideas.json` item keeps existing keys and adds `idea` and `aiNotes`; existing Pages fields remain backward compatible.

- [ ] **Step 1: Write generator regression tests**

Create `tests/test_generate_timeline.py`:

```python
import json
import unittest

from scripts.generate_timeline import effective_stage, generate_ideas_json, parse_field, parse_section


def issue(**overrides):
    base = {
        "number": 7,
        "title": "[Idea] Human + AI access",
        "html_url": "https://github.com/example/brain-dump/issues/7",
        "state": "open",
        "body": """## Idea
Keep the original human idea.

## Why it might matter
It should be easy for both people and agents.

## Initial stage
Exploring

## Category
Software

## AI Notes
First line.
Second line.

## Brain-dump rule
- [x] This is a raw idea, not an approved implementation task.
""",
        "created_at": "2026-09-23T07:00:00Z",
        "updated_at": "2026-09-23T08:00:00Z",
        "closed_at": None,
    }
    base.update(overrides)
    return base


class GeneratorTests(unittest.TestCase):
    def test_parse_section_preserves_multiline_ai_notes(self):
        value = parse_section(issue()["body"], "AI Notes", "")
        self.assertEqual(value, "First line.\nSecond line.")

    def test_missing_ai_notes_is_empty(self):
        body = "## Idea\nOnly human content.\n\n## Initial stage\nInbox"
        self.assertEqual(parse_section(body, "AI Notes", ""), "")

    def test_generated_index_exposes_idea_and_ai_notes(self):
        parsed = [(parse_iso("2026-09-23T07:00:00Z"), issue())]
        data = json.loads(generate_ideas_json(parsed))
        item = data["ideas"][0]
        self.assertEqual(item["idea"], "Keep the original human idea.")
        self.assertEqual(item["aiNotes"], "First line.\nSecond line.")
        self.assertEqual(item["stage"], "Exploring")

    def test_closed_non_project_issue_is_archived(self):
        closed = issue(state="closed", body=issue()["body"].replace("Exploring", "Inbox"))
        self.assertEqual(effective_stage(closed), "Archived")

    def test_project_stage_survives_closed_state(self):
        closed = issue(state="closed", body=issue()["body"].replace("Exploring", "Project"))
        self.assertEqual(effective_stage(closed), "Project")


def parse_iso(value):
    from datetime import datetime
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the generator tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_generate_timeline -v
```

Expected: FAIL because `parse_section`, `idea`, and `aiNotes` are not implemented.

- [ ] **Step 3: Add multiline section parsing without breaking single-line fields**

In `scripts/generate_timeline.py`, keep `parse_field()` for first-line fields and add:

```python
def parse_section(body: str, heading: str, fallback: str = "") -> str:
    match = re.search(
        rf"(?ims)^##\s+{re.escape(heading)}\s*\n+(.+?)(?=\n##\s+|\Z)",
        body or "",
    )
    if not match:
        return fallback
    value = match.group(1).strip()
    return value or fallback
```

- [ ] **Step 4: Add `idea` and `aiNotes` to generated JSON**

Inside `generate_ideas_json()`, add:

```python
"idea": parse_section(body, "Idea", ""),
"aiNotes": parse_section(body, "AI Notes", ""),
```

Keep all existing JSON keys unchanged.

- [ ] **Step 5: Run generator and contract tests**

Run:

```bash
python3 -m unittest tests.test_generate_timeline tests.test_ai_contract -v
python3 -m py_compile scripts/generate_timeline.py
```

Expected: all tests PASS and compile exits 0.

- [ ] **Step 6: Commit the generator change**

```bash
git add scripts/generate_timeline.py tests/test_generate_timeline.py
git commit -m "feat: expose AI notes in generated idea index"
```

---

### Task 3: Replace the AI-Slop Dashboard Feel with a Human Memos-Like Reader

**Files:**
- Modify: `docs/index.html`
- Modify: `docs/styles.css`
- Modify: `docs/app.js`
- Create: `tests/test_static_ui.py`

**Interfaces:**
- Consumes: `docs/data/ideas.json` with existing fields plus optional `idea` and `aiNotes`.
- Produces: a read-only human interface whose primary view is `Notes`; all writes route to GitHub.

- [ ] **Step 1: Write static UI regression tests**

Create `tests/test_static_ui.py`:

```python
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs" / "index.html"
JS = ROOT / "docs" / "app.js"
CSS = ROOT / "docs" / "styles.css"


class StaticUITests(unittest.TestCase):
    def test_human_write_actions_link_to_github(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("/issues/new/choose", html)
        self.assertIn("New note", html)
        self.assertIn("What's on your mind?", html)

    def test_default_language_is_notes_not_journey_or_marketing(self):
        html = HTML.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        combined = html + "\n" + js
        self.assertIn('data-view="notes"', html)
        self.assertIn('view:"notes"', js)
        self.assertNotIn("Capture now. Organize later.", combined)
        self.assertNotIn("Capture an idea", combined)
        self.assertNotIn("Latest", combined)

    def test_client_contains_no_write_api_or_credentials(self):
        text = (HTML.read_text(encoding="utf-8") + "\n" + JS.read_text(encoding="utf-8")).lower()
        forbidden = (
            "authorization: bearer",
            "github_token",
            "api.github.com/repos/",
            'method:"post"',
            'method:"patch"',
        )
        for token in forbidden:
            self.assertNotIn(token, text)

    def test_metadata_is_not_rendered_as_uppercase_status_pills_in_notes(self):
        js = JS.read_text(encoding="utf-8")
        self.assertNotIn("latest-badge", js)
        self.assertIn("note-meta", js)
        self.assertIn("View on GitHub", js)

    def test_css_has_no_heavy_effects(self):
        css = CSS.read_text(encoding="utf-8").lower()
        self.assertNotIn("backdrop-filter", css)
        self.assertNotIn("linear-gradient", css)
        self.assertNotIn("radial-gradient", css)
        self.assertNotIn("@keyframes", css)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run static UI tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_static_ui -v
```

Expected: FAIL on the old marketing copy, `Journey` default, Latest badge, and old capture card.

- [ ] **Step 3: Simplify the HTML shell**

Change `docs/index.html` to this hierarchy:

```html
<header class="topbar">
  <div class="shell topbar-inner">
    <a class="brand" href="./"><strong>Brain Dump</strong></a>
    <div class="top-actions">
      <button id="themeToggle" class="icon-button" type="button" aria-label="Toggle theme">◐</button>
      <a class="new-button" href="https://github.com/afnannuzulasugihartono/brain-dump/issues/new/choose">New note</a>
    </div>
  </div>
</header>

<main class="shell main">
  <a class="composer" href="https://github.com/afnannuzulasugihartono/brain-dump/issues/new/choose">
    <span>What's on your mind?</span>
    <small>Write a note…</small>
  </a>

  <div class="tools">
    <label class="search">
      <span>⌕</span>
      <input id="searchInput" type="search" placeholder="Search" autocomplete="off">
    </label>
    <div class="filters">
      <select id="categoryFilter" aria-label="Filter by category"><option value="all">Category</option></select>
      <select id="stageFilter" aria-label="Filter by stage"><option value="all">Stage</option></select>
    </div>
  </div>

  <nav class="tabs" aria-label="Idea views">
    <button class="tab active" data-view="notes">Notes</button>
    <button class="tab" data-view="cards">Cards</button>
    <button class="tab" data-view="board">Board</button>
    <button class="tab" data-view="calendar">Calendar</button>
  </nav>

  <p id="activeFilters" class="filter-note" hidden></p>
  <section id="notesView" class="view active"></section>
  <section id="cardsView" class="view"></section>
  <section id="boardView" class="view"></section>
  <section id="calendarView" class="view"></section>
</main>
```

Remove:
- tagline;
- emoji logo block;
- KPI summary;
- promotional capture card;
- marketing-style footer copy.

Keep a very small footer only if useful for `Issues · Project · Repository`.

- [ ] **Step 4: Replace Journey rendering with a plain Notes feed**

Set initial state to:

```javascript
const state={ideas:[],filtered:[],view:"notes",query:"",category:"all",stage:"all",calendarDate:new Date()};
```

Render notes newest-first, grouped by month, without a Latest badge:

```javascript
function renderNotes(){
  const root=$("#notesView");
  if(!state.filtered.length){
    root.replaceChildren($("#emptyTemplate").content.cloneNode(true));
    return;
  }

  let currentMonth="";
  let html='<div class="notes">';
  state.filtered.forEach(i=>{
    const p=dateParts(i.createdAt);
    if(p.month!==currentMonth){
      html+=`<h2 class="month">${p.month}</h2>`;
      currentMonth=p.month;
    }
    const body=i.idea||i.why||"";
    html+=`<article class="note">
      <div class="note-time">${p.day} ${p.mon} · ${p.year}</div>
      <a class="note-title" href="${i.url}">${esc(i.title)}</a>
      ${body?`<p class="note-copy">${esc(body)}</p>`:""}
      ${i.why&&i.why!==body?`<p class="note-context">${esc(i.why)}</p>`:""}
      <div class="note-meta">
        <span>#${esc(i.stage.toLowerCase())}</span>
        <span>#${esc(i.category.toLowerCase())}</span>
        <a href="${i.url}">View on GitHub</a>
      </div>
    </article>`;
  });
  root.innerHTML=html+"</div>";
}
```

Do not surface AI Notes in the main feed by default; the canonical Issue remains one click away. AI Notes stay available in `ideas.json` for machine readers.

- [ ] **Step 5: Make secondary views subordinate**

Keep Cards, Board, and Calendar functional, but:
- remove Latest styling;
- remove bright status pills from Cards;
- use plain lowercase metadata;
- do not add new visual effects;
- preserve filter/search behavior across all views.

Update `renderActive()`, `setView()`, and hash handling from `journey` to `notes`.

- [ ] **Step 6: Rewrite CSS around a quiet 720–760px notes column**

Use:
- shell width around `760px`;
- system font only;
- one blue accent;
- borders and whitespace instead of card shadows;
- note rows separated by a thin border;
- normal-case metadata;
- no gradients, glow, blur, large shadows, or animations;
- responsive stacking below `620px`.

The primary note styles should be structurally similar to:

```css
.shell{width:min(760px,calc(100% - 28px));margin-inline:auto}
.main{padding:20px 0 48px}
.composer{display:grid;gap:2px;padding:14px 0;border-bottom:1px solid var(--border)}
.composer>span{font-size:14px;color:var(--text)}
.composer small{font-size:11px;color:var(--muted)}
.notes{padding-top:8px}
.month{margin:22px 0 6px;font-size:11px;font-weight:600;color:var(--muted)}
.note{padding:14px 0 16px;border-bottom:1px solid var(--border)}
.note-time{font-size:10px;color:var(--faint)}
.note-title{display:inline-block;margin-top:5px;font-size:14px;font-weight:600}
.note-copy,.note-context{margin:6px 0 0;font-size:12px;line-height:1.55}
.note-context{color:var(--muted)}
.note-meta{display:flex;gap:8px;margin-top:9px;font-size:10px;color:var(--muted)}
.note-meta a{margin-left:auto;color:var(--accent)}
```

- [ ] **Step 7: Run static and generator tests**

Run:

```bash
python3 -m unittest discover -s tests -v
```

Expected: all tests PASS.

- [ ] **Step 8: Perform local browser smoke verification**

Serve the static site:

```bash
python3 -m http.server 8000 --directory docs
```

Verify at desktop and narrow/mobile width:
- Brain Dump title is compact;
- `What's on your mind?` opens GitHub new-Issue flow;
- Notes is the default view;
- no tagline/KPI/Latest badge is visible;
- search filters notes;
- category and stage filters work;
- Cards/Board/Calendar remain usable;
- theme toggle works;
- each note has `View on GitHub`.

- [ ] **Step 9: Commit the human UI redesign**

```bash
git add docs/index.html docs/styles.css docs/app.js tests/test_static_ui.py
git commit -m "refactor: make Brain Dump a human Memos-like reader"
```

---

### Task 4: Align README and Generated Repository Views with the Same Human Tone

**Files:**
- Modify: `README.md`
- Modify: `scripts/generate_timeline.py`
- Modify: `tests/test_generate_timeline.py`

**Interfaces:**
- Consumes: parsed Issues and the same lifecycle used by the Pages UI.
- Produces: README/timeline output that is compact, human, and links to AI access documentation without turning the repo page into a dashboard.

- [ ] **Step 1: Add failing README-generation tests**

Append to `tests/test_generate_timeline.py`:

```python
from scripts.generate_timeline import generate_home


class HomeGenerationTests(unittest.TestCase):
    def test_home_avoids_dashboard_marketing_language(self):
        parsed = [(parse_iso("2026-09-23T07:00:00Z"), issue())]
        home = generate_home(parsed)
        self.assertNotIn("Snapshot", home)
        self.assertNotIn("Capture now. Organize later.", home)
        self.assertNotIn("Latest", home)
        self.assertIn("Recent ideas", home)

    def test_home_keeps_issue_as_canonical_link(self):
        parsed = [(parse_iso("2026-09-23T07:00:00Z"), issue())]
        home = generate_home(parsed)
        self.assertIn("https://github.com/example/brain-dump/issues/7", home)
```

Also add a static assertion in `tests/test_ai_contract.py` that README links to `docs/ai-access.md`.

- [ ] **Step 2: Run tests and verify the new README link test fails**

Run:

```bash
python3 -m unittest tests.test_generate_timeline tests.test_ai_contract -v
```

Expected: FAIL because README does not yet link to the AI access guide.

- [ ] **Step 3: Simplify README copy outside generated markers**

Use:

```markdown
# 🧠 Brain Dump

A small place for notes and ideas.

[Open Brain Dump](https://afnannuzulasugihartono.github.io/brain-dump/) · [New note](https://github.com/afnannuzulasugihartono/brain-dump/issues/new/choose) · [Issues](https://github.com/afnannuzulasugihartono/brain-dump/issues) · [AI access](docs/ai-access.md)

---
<!-- TIMELINE:START -->
...generated recent ideas...
<!-- TIMELINE:END -->

## Workflow

Inbox → Exploring → Promising → Project → Archived

GitHub Issues are the source of truth. See [AGENTS.md](AGENTS.md) for the AI write policy.
```

Remove marketing slogans and dashboard-style explanatory copy.

- [ ] **Step 4: Keep `generate_home()` feed-like**

Keep only:
- a compact count line if useful;
- `## Recent ideas`;
- recent Issue links;
- context and subdued stage/category/state metadata.

Do not regenerate marketing taglines, large metric tables, or a Latest badge.

- [ ] **Step 5: Run all tests**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/generate_timeline.py
```

Expected: PASS.

- [ ] **Step 6: Commit repository presentation changes**

```bash
git add README.md scripts/generate_timeline.py tests/test_generate_timeline.py tests/test_ai_contract.py
git commit -m "docs: align Brain Dump repository with human AI access model"
```

---

### Task 5: Make Sync Robust and Verify the Full Human + AI Flow

**Files:**
- Modify: `.github/workflows/sync-brain-dump.yml`
- Create: `tests/test_workflow_contract.py`
- Modify if verification requires a correction: `docs/ai-access.md`

**Interfaces:**
- Consumes: Issue events from humans or authenticated AI, generator output from Tasks 2–4.
- Produces: race-resistant generated-content commits and a deployed read-only Pages site.

- [ ] **Step 1: Write workflow contract tests**

Create `tests/test_workflow_contract.py`:

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sync-brain-dump.yml"


class WorkflowContractTests(unittest.TestCase):
    def test_issue_events_trigger_sync(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("issues:", text)
        for event in ("opened", "edited", "closed", "reopened"):
            self.assertIn(event, text)

    def test_workflow_never_needs_issue_write_permission(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("issues: read", text)
        self.assertNotIn("issues: write", text)

    def test_generated_push_refreshes_from_latest_main_before_retry(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("git fetch origin main", text)
        self.assertIn("git reset --hard origin/main", text)
        self.assertIn("python3 scripts/generate_timeline.py", text)
        self.assertIn("git push origin HEAD:main", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the workflow tests and verify the rebase assertion fails**

Run:

```bash
python3 -m unittest tests.test_workflow_contract -v
```

Expected: FAIL because the current workflow pushes generated commits without refreshing from a concurrently updated `main`.

- [ ] **Step 3: Make the generated-content push race-resistant**

Replace the push section after committing generated output with a bounded retry:

```yaml
      - name: Commit generated content when changed
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          GENERATED="README.md TIMELINE.md docs/ideas.json assets/idea-journey-light.svg assets/idea-journey-dark.svg"
          git add $GENERATED
          if git diff --cached --quiet; then
            echo "Generated content unchanged."
            exit 0
          fi

          git commit -m "docs: sync brain dump"

          for attempt in 1 2 3; do
            if git push origin HEAD:main; then
              exit 0
            fi

            echo "Push attempt $attempt failed; refreshing from latest main."
            git fetch origin main
            git reset --hard origin/main
            python3 scripts/generate_timeline.py
            git add $GENERATED

            if git diff --cached --quiet; then
              echo "Latest main already contains equivalent generated content."
              exit 0
            fi

            git commit -m "docs: sync brain dump"
            sleep $((attempt * 2))
          done

          echo "Could not push generated content after 3 attempts."
          exit 1
```

Keep:
- `issues: read`, not write;
- Pages permissions;
- current issue-owner guard;
- current deployment steps.

- [ ] **Step 4: Run the complete local test suite**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/generate_timeline.py
```

Expected: all tests PASS.

- [ ] **Step 5: Commit workflow hardening**

```bash
git add .github/workflows/sync-brain-dump.yml tests/test_workflow_contract.py
git commit -m "ci: harden Brain Dump sync against concurrent updates"
```

- [ ] **Step 6: Perform live authenticated GitHub API acceptance**

Using the connected GitHub account or a GitHub token with Issue permission, create one temporary Issue through the official API:

Title:

```text
[Idea] AI access verification
```

Body:

```markdown
## Idea
Verify that an authenticated AI can create an idea through the GitHub API.

## Why it might matter
Brain Dump should be usable by both humans and AI without a custom backend.

## Initial stage
Inbox

## Category
Software

## AI Notes
Created as a temporary end-to-end verification of the documented AI path.

## Brain-dump rule
- [x] This is a raw idea, not an approved implementation task.
```

Then wait for the sync workflow and verify:
- the workflow succeeds;
- the Issue appears in `docs/data/ideas.json`;
- `idea` and `aiNotes` are present in generated JSON;
- Pages shows the note in Notes view;
- README recent ideas links to the Issue.

- [ ] **Step 7: Verify an authenticated AI edit and audit trail**

Re-read the temporary Issue, then:
- change stage from `Inbox` to `Exploring` while preserving all existing human/AI content;
- add an Issue comment:

```text
AI update:
- stage moved from Inbox to Exploring
- original idea and context preserved
```

Verify after sync that:
- stage is `Exploring` in `docs/data/ideas.json`;
- comment remains on the Issue;
- Pages still renders correctly.

- [ ] **Step 8: Verify the human-facing UI in production**

Open the deployed Pages site and verify:
- compact `Brain Dump` header;
- `New note` and `What's on your mind?` both route to GitHub;
- Notes is default;
- no marketing tagline, KPI strip, Latest badge, gradients, glow, or continuous animation;
- search works;
- stage/category filters work;
- Cards, Board, Calendar still work;
- mobile/narrow layout is readable;
- no browser console errors;
- client source contains no GitHub write credential or API write code.

- [ ] **Step 9: Explicitly clean up the temporary acceptance Issue**

This cleanup is part of the user-approved implementation plan and therefore counts as explicit authorization for this one temporary verification Issue only.

Re-read the Issue, set its stage to `Archived`, add:

```text
Verification complete. Closing this temporary acceptance-test idea.
```

Then close the temporary Issue. Do not close any other Issue.

Verify the next sync succeeds and that the closed test Issue is represented consistently as `Archived`.

- [ ] **Step 10: Final repository and workflow verification**

Run or inspect:
- latest `Sync Brain Dump` workflow conclusion = success;
- `AGENTS.md` and `docs/ai-access.md` are present on `main`;
- `docs/data/ideas.json` is generated, not manually edited;
- GitHub Pages is live;
- all Python tests pass;
- no generated file is treated as authoritative in docs.

No additional implementation commit is needed unless this step reveals a concrete defect; if it does, fix only that defect, rerun its owning task's tests, and commit the minimal fix.
