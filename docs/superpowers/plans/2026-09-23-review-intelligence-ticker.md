# Review Intelligence, Ticker, and Conservative Repo Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Add a lightweight Review system, deterministic browser-side scoring, optional asynchronous AI insight, a subtle adaptive ticker, and conservative repository cleanup without changing GitHub Issues as Brain Dump's source of truth.

**Architecture:** Keep the site static-first. Python normalizes trusted GitHub Issues into docs/data/ideas.json, native browser ES modules calculate Review signals, and an independent GitHub Actions sidecar may generate docs/data/ai-insights.json. AI failure never blocks canonical sync or Pages deployment.

**Tech Stack:** GitHub Pages, vanilla HTML/CSS, native browser ES modules, Python 3 standard library, GitHub Actions, Python unittest, Node built-in test runner.

**Spec:** docs/superpowers/specs/2026-09-23-review-intelligence-and-repo-cleanup-design.md

**Implementation status (reconciled 23 September 2026):** Core implementation is merged on `main` through PRs #4–#8. Canonical Sync, production Pages, deterministic Review, ticker wiring, modular frontend, cleanup, and safe-degraded AI Review have been accepted. A final closeout pass adds explicit missing-provider/timeout/rate-limit regression coverage. Live desktop ticker behavior and a clean browser console were observed; live mobile viewport resizing and reduced-motion emulation were unavailable in the browser harness, so those remain verified through deployed CSS and regression tests. Real AI insight generation remains intentionally inactive until `AI_BASE_URL`, `AI_MODEL`, and `AI_API_KEY` are configured. Historical unchecked boxes below are retained as the original TDD execution recipe, not as the current status tracker.


## Global Constraints

- GitHub Issues remain the sole source of truth.
- Notes stays the default Memos-like view.
- Navigation becomes Notes / Review / Board / Calendar; Cards leaves main navigation.
- Needs Review thresholds: Inbox 7 days, Exploring 14 days, Promising 30 days; Project and Archived excluded.
- Worth Revisiting is deterministic browser-side scoring; AI never writes the canonical score.
- AI is optional and asynchronous; provider failure must not block the site or main deployment.
- Provider credentials live only in GitHub-managed secrets/variables.
- Pages remains read-only with no GitHub write credential or mutation path.
- Ticker is fixed on desktop, non-fixed on mobile, and honors prefers-reduced-motion.
- Native ES modules only; no bundler, package manager, frontend framework, backend, database, or custom OAuth.
- Cleanup is deep but conservative.
- Existing AGENTS.md gates for Project, Archived, close, and human-content preservation remain unchanged.

## Review Focus

1. Exactly 7/14/30 UTC days since updatedAt is due for Review, not one day later.
2. No eligible rediscovery candidate returns null and renders an empty state instead of throwing.
3. Malformed timestamps or duplicate Issue numbers in canonical generated data fail validation before deploy.
4. AI output with wrong issueNumber, unknown suggestedAction, invalid JSON, or confidence outside 0..1 is rejected while the last valid insight is preserved.
5. Missing/invalid ai-insights.json never blocks Notes, rule-based Review, Board, Calendar, search/filter, or ticker.

## File Map

Canonical data:
- Create scripts/generate/__init__.py.
- Create scripts/generate/issues.py for parsing, trust checks, GitHub reads, effective stage, normalize_issue.
- Modify scripts/generate_timeline.py to render/write outputs and target docs/data/ideas.json.
- Create scripts/validate_generated.py.
- Create docs/data/ideas.json and docs/data/ai-insights.json.
- Remove docs/ideas.json after replacement passes.

Frontend:
- Create docs/js/data.js, scoring.js, views.js, review.js, ticker.js, theme.js, app.js.
- Create docs/styles/base.css, app.css, review.css, ticker.css.
- Modify docs/index.html.
- Remove docs/app.js and docs/styles.css after replacement passes.

AI:
- Create scripts/ai/evaluate.py and scripts/ai/providers/openai_compatible.py plus package markers.

Workflows/docs:
- Rename .github/workflows/sync-brain-dump.yml to .github/workflows/sync.yml.
- Create .github/workflows/ai-review.yml.
- Modify AGENTS.md, docs/ai-access.md, README.md.
- Remove legacy idea-journey SVGs only if reference check proves they are obsolete.

Tests:
- Final Python groups: tests/generator, tests/frontend, tests/ai, tests/workflow, tests/policy.
- JavaScript scoring tests: tests/frontend/scoring.test.js.

---

### Task 1: Canonical Issue Contract and Data Boundary

**Files:**
- Create: scripts/generate/__init__.py
- Create: scripts/generate/issues.py
- Modify: scripts/generate_timeline.py
- Create: scripts/validate_generated.py
- Create: docs/data/ideas.json
- Create: docs/data/ai-insights.json
- Modify: tests/test_generate_timeline.py
- Create: tests/test_validate_generated.py
- Delete after GREEN: docs/ideas.json

**Interfaces:**
- Consumes: raw GitHub Issue REST dictionaries.
- Produces: normalize_issue(issue: dict) -> canonical idea dict.
- Produces: get_issue(repo, issue_number, token) and get_issues(repo, token).
- Produces: validate_ideas_document(data) and validate_insights_document(data), raising ValueError on invalid data.

- [ ] **Step 1: Write failing normalization and output-path tests**

At the top of tests/test_generate_timeline.py add:

~~~python
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
~~~

Then add:

~~~python
from scripts.generate.issues import normalize_issue

def test_normalize_issue_exposes_canonical_fields(self):
    item = normalize_issue(issue())
    self.assertEqual(item["number"], 7)
    self.assertEqual(item["title"], "Human + AI access")
    self.assertEqual(item["stage"], "Exploring")
    self.assertEqual(item["category"], "Software")
    self.assertEqual(item["idea"], "Keep the original human idea.")
    self.assertEqual(item["aiNotes"], "First line.\nSecond line.")

def test_generator_targets_docs_data(self):
    text = (ROOT / "scripts" / "generate_timeline.py").read_text(encoding="utf-8")
    self.assertIn('Path("docs/data/ideas.json")', text)
    self.assertNotIn('Path("docs/ideas.json")', text)
~~~

- [ ] **Step 2: Run RED**

~~~bash
python3 -m unittest tests.test_generate_timeline -v
~~~

Expected: FAIL because scripts.generate.issues does not exist and the old output path remains.

- [ ] **Step 3: Extract canonical Issue helpers**

Create scripts/generate/issues.py with these exact public functions:

~~~python
API = "https://api.github.com"
TRUSTED_AUTHOR_ASSOCIATIONS = {"OWNER", "COLLABORATOR", "MEMBER"}

def get_issue(repo: str, issue_number: int, token: str):
    return api_get(f"{API}/repos/{repo}/issues/{issue_number}", token)

def is_trusted_issue(issue: dict, owner: str) -> bool:
    login = issue.get("user", {}).get("login", "").lower()
    association = (issue.get("author_association") or "").upper()
    return login == owner.lower() or association in TRUSTED_AUTHOR_ASSOCIATIONS

def normalize_issue(issue: dict) -> dict:
    body = issue.get("body") or ""
    return {
        "number": issue["number"],
        "title": display_title(issue.get("title", "Untitled idea")),
        "url": issue["html_url"],
        "state": issue.get("state", "open"),
        "stage": effective_stage(issue),
        "category": parse_field(body, "Category", "Other"),
        "why": parse_field(body, "Why it might matter", ""),
        "idea": parse_section(body, "Idea", ""),
        "aiNotes": parse_section(body, "AI Notes", ""),
        "createdAt": issue["created_at"],
        "updatedAt": issue.get("updated_at") or issue["created_at"],
        "closedAt": issue.get("closed_at"),
    }
~~~

Move existing api_get, get_issues, display_title, parse_field, parse_section, is_trusted_issue, and effective_stage implementations into this module without changing behavior. scripts/generate_timeline.py imports them and writes docs/data/ideas.json.

- [ ] **Step 4: Write validator RED tests**

~~~python
import unittest
from scripts.validate_generated import validate_ideas_document

class GeneratedValidationTests(unittest.TestCase):
    def test_duplicate_issue_numbers_fail(self):
        data = {"source":"GitHub Issues","ideas":[
            {"number":1,"createdAt":"2026-09-01T00:00:00Z","updatedAt":"2026-09-01T00:00:00Z"},
            {"number":1,"createdAt":"2026-09-02T00:00:00Z","updatedAt":"2026-09-02T00:00:00Z"},
        ]}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_ideas_document(data)

    def test_malformed_timestamp_fails(self):
        data = {"source":"GitHub Issues","ideas":[
            {"number":1,"createdAt":"bad","updatedAt":"2026-09-01T00:00:00Z"}
        ]}
        with self.assertRaisesRegex(ValueError, "createdAt"):
            validate_ideas_document(data)
~~~

Run:

~~~bash
python3 -m unittest tests.test_validate_generated -v
~~~

Expected: FAIL because validator does not exist.

- [ ] **Step 5: Implement validators and empty AI sidecar**

scripts/validate_generated.py must:
- require source == GitHub Issues and ideas list for canonical data;
- reject duplicate/non-integer numbers;
- parse createdAt/updatedAt as ISO timestamps;
- validate AI insights list, unique integer issueNumber, ISO evaluatedAt, allowed actions, allowed depth, and confidence 0..1;
- expose a CLI defaulting to docs/data/ideas.json and docs/data/ai-insights.json.

Create docs/data/ai-insights.json:

~~~json
{
  "source": "AI review",
  "insights": []
}
~~~

- [ ] **Step 6: Verify GREEN**

~~~bash
python3 -m unittest tests.test_generate_timeline tests.test_validate_generated -v
python3 -m py_compile scripts/generate_timeline.py scripts/generate/issues.py scripts/validate_generated.py
python3 scripts/validate_generated.py
~~~

Expected: all PASS.

- [ ] **Step 7: Commit**

~~~bash
git add scripts/generate scripts/generate_timeline.py scripts/validate_generated.py docs/data tests/test_generate_timeline.py tests/test_validate_generated.py
git rm docs/ideas.json
git commit -m "refactor: define canonical generated data boundary"
~~~

---

### Task 2: Deterministic Review Scoring

**Files:**
- Create: docs/js/scoring.js
- Create: tests/frontend/scoring.test.js

**Interfaces:**
- needsReview(idea, now) -> {due, daysUntouched, threshold}
- scoreIdea(idea, now) -> {score, signals, eligible}
- selectRediscovery(ideas, now) -> idea|null

- [ ] **Step 1: Write RED scoring tests**

~~~javascript
import test from "node:test";
import assert from "node:assert/strict";
import {needsReview, scoreIdea, selectRediscovery} from "../../docs/js/scoring.js";

const now = new Date("2026-09-23T12:00:00Z");
const idea = (overrides={}) => ({
  number:10, title:"Example", state:"open", stage:"Inbox", category:"Other",
  idea:"A useful idea with enough context to explain the concept and its intended use clearly.",
  why:"It solves a recurring problem and has a clear motivation.",
  aiNotes:"",
  createdAt:"2026-09-01T12:00:00Z",
  updatedAt:"2026-09-16T12:00:00Z",
  ...overrides,
});

test("thresholds are inclusive and stage specific", () => {
  assert.equal(needsReview(idea(), now).due, true);
  assert.equal(needsReview(idea({stage:"Exploring",updatedAt:"2026-09-09T12:00:00Z"}), now).due, true);
  assert.equal(needsReview(idea({stage:"Promising",updatedAt:"2026-08-24T12:00:00Z"}), now).due, true);
  assert.equal(needsReview(idea({stage:"Project"}), now).due, false);
  assert.equal(needsReview(idea({stage:"Archived"}), now).due, false);
});

test("score exposes deterministic signals", () => {
  const result = scoreIdea(idea({stage:"Promising",aiNotes:"Compared several approaches."}), now);
  assert.ok(result.score >= 6);
  assert.ok(result.signals.includes("promising"));
  assert.ok(result.signals.includes("ai-notes"));
});

test("empty rediscovery returns null", () => {
  assert.equal(selectRediscovery([idea({stage:"Archived"})], now), null);
});

test("rediscovery is stable for the same UTC day", () => {
  const ideas = [idea({number:1}), idea({number:2}), idea({number:3})];
  assert.equal(selectRediscovery(ideas, now)?.number, selectRediscovery(ideas, now)?.number);
});
~~~

- [ ] **Step 2: Run RED**

~~~bash
node --experimental-default-type=module --test tests/frontend/scoring.test.js
~~~

Expected: FAIL because scoring.js is missing.

- [ ] **Step 3: Implement scoring.js**

Use:
- UTC day arithmetic;
- thresholds {inbox:7, exploring:14, promising:30};
- rich-content threshold = 240 combined idea+why characters;
- Promising +3, AI Notes +2, Why +1, rich context +1, open +1, age >14 +1;
- Archived eligible=false;
- rediscovery excludes Archived, requires age >=7 and updated before today, sorts by Issue number, then chooses a checksum(dateKey) modulo candidate count.

- [ ] **Step 4: Run GREEN**

~~~bash
node --experimental-default-type=module --test tests/frontend/scoring.test.js
~~~

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add docs/js/scoring.js tests/frontend/scoring.test.js
git commit -m "feat: add deterministic review scoring"
~~~

---

### Task 3: Modular Frontend and Review View

**Files:**
- Create: docs/js/data.js, views.js, review.js, theme.js, app.js
- Create: docs/styles/base.css, app.css, review.css
- Modify: docs/index.html
- Modify: tests/test_static_ui.py
- Create: tests/frontend/data.test.js
- Delete after GREEN: docs/app.js, docs/styles.css

**Interfaces:**
- loadBrainDumpData() -> Promise<{ideas, insightsByIssue}>
- renderNotes(root, ideas), renderBoard(root, ideas), renderCalendar(root, ideas, date, onDateChange)
- renderReview(root, ideas, insightsByIssue, now)
- initTheme(button)

- [ ] **Step 1: Add RED static tests**

~~~python
def test_review_replaces_cards_and_uses_modules(self):
    html = HTML.read_text(encoding="utf-8")
    self.assertIn('data-view="review"', html)
    self.assertNotIn('data-view="cards"', html)
    self.assertIn('type="module"', html)
    self.assertIn('./js/app.js', html)

def test_review_source_has_three_sections(self):
    text = (ROOT / "docs" / "js" / "review.js").read_text(encoding="utf-8")
    for label in ("Needs review", "Worth revisiting", "Rediscover"):
        self.assertIn(label, text)

def test_frontend_uses_new_data_paths(self):
    text = (ROOT / "docs" / "js" / "data.js").read_text(encoding="utf-8")
    self.assertIn("./data/ideas.json", text)
    self.assertIn("./data/ai-insights.json", text)
~~~

Run:

~~~bash
python3 -m unittest tests.test_static_ui -v
~~~

Expected: FAIL.

- [ ] **Step 2: Implement optional data loading**

docs/js/data.js:

~~~javascript
export async function loadBrainDumpData() {
  const response = await fetch("./data/ideas.json", {cache:"no-store"});
  if (!response.ok) throw new Error("ideas:" + response.status);
  const canonical = await response.json();
  if (!Array.isArray(canonical.ideas)) throw new Error("ideas:invalid");

  let insights = [];
  try {
    const optional = await fetch("./data/ai-insights.json", {cache:"no-store"});
    if (optional.ok) {
      const document = await optional.json();
      if (Array.isArray(document.insights)) insights = document.insights;
    }
  } catch {
    insights = [];
  }

  return {
    ideas:[...canonical.ideas].sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt)),
    insightsByIssue:new Map(insights.map(item => [item.issueNumber, item])),
  };
}
~~~

- [ ] **Step 3: Add and pass optional-sidecar resilience test**

Create tests/frontend/data.test.js:

~~~javascript
import test from "node:test";
import assert from "node:assert/strict";
import {loadBrainDumpData} from "../../docs/js/data.js";

test("missing AI sidecar does not block canonical ideas", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async url => {
    if (String(url).includes("ideas.json")) {
      return {ok:true, json:async () => ({ideas:[{
        number:1, title:"One", createdAt:"2026-09-01T00:00:00Z"
      }]})};
    }
    throw new Error("sidecar unavailable");
  };
  try {
    const result = await loadBrainDumpData();
    assert.equal(result.ideas.length, 1);
    assert.equal(result.insightsByIssue.size, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("invalid AI sidecar shape degrades to no insights", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async url => {
    if (String(url).includes("ideas.json")) {
      return {ok:true, json:async () => ({ideas:[{
        number:1, title:"One", createdAt:"2026-09-01T00:00:00Z"
      }]})};
    }
    return {ok:true, json:async () => ({insights:"invalid"})};
  };
  try {
    const result = await loadBrainDumpData();
    assert.equal(result.insightsByIssue.size, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
~~~

Run:

~~~bash
node --experimental-default-type=module --test tests/frontend/data.test.js
~~~

Expected: PASS after Step 2 data.js implementation.

- [ ] **Step 4: Extract current Notes/Board/Calendar behavior into views.js**

Export esc, tag, dateParts, ideaCard, renderNotes, renderBoard, renderCalendar. Copy the current rendering behavior, replacing global state reads with explicit function arguments. Keep current visual wording such as View on GitHub.

- [ ] **Step 5: Implement Review UI**

docs/js/review.js imports scoring.js and views.js. It must:
- order Needs Review by longest untouched;
- show Worth Revisiting only for score >=6;
- show score and signal labels as text;
- render Rediscover or a quiet empty state;
- render optional AI summary when present and escape all AI/Issue text before innerHTML;
- use details/summary for detailed strength/risk/nextStep;
- render an action-aware GitHub link: Keep exploring in GitHub, Revisit in GitHub, Promote candidate in GitHub, or Consider archive in GitHub when AI suggests that action; otherwise Review in GitHub;
- every action-aware link points only to idea.url and never performs POST/PATCH.

Core decision logic:

~~~javascript
const due = ideas
  .map(idea => ({idea, review:needsReview(idea, now)}))
  .filter(item => item.review.due)
  .sort((a,b) => b.review.daysUntouched - a.review.daysUntouched);

const worth = ideas
  .map(idea => ({idea, result:scoreIdea(idea, now)}))
  .filter(item => item.result.eligible && item.result.score >= 6)
  .sort((a,b) => b.result.score - a.result.score);

const rediscovered = selectRediscovery(ideas, now);
~~~

- [ ] **Step 6: Create small app.js and theme.js**

app.js owns only state, filters, active-view routing, and calls into imported modules. State:

~~~javascript
const state = {
  ideas:[],
  filtered:[],
  insightsByIssue:new Map(),
  view:"notes",
  query:"",
  category:"all",
  stage:"all",
  calendarDate:new Date(),
};
~~~

Allowed hashes: notes, review, board, calendar. Unknown hash falls back to notes.

Canonical data load failure renders Could not load notes plus a link to GitHub Issues.

- [ ] **Step 7: Update index.html and split CSS**

index.html:
- Cards tab → Review tab;
- cardsView → reviewView;
- four stylesheet links: base.css, app.css, review.css, ticker.css;
- module script ./js/app.js.

base.css receives variables/reset/global control styles. app.css receives current topbar/composer/search/tabs/Notes/Board/Calendar/footer styles. review.css stays editorial: thin borders, restrained typography, no KPI cards/charts/gradients/blur.

- [ ] **Step 8: Verify and remove old monoliths**

~~~bash
python3 -m unittest tests.test_static_ui -v
node --check docs/js/app.js
node --check docs/js/data.js
node --check docs/js/views.js
node --check docs/js/review.js
node --check docs/js/theme.js
node --experimental-default-type=module --test tests/frontend/scoring.test.js tests/frontend/data.test.js
~~~

Expected: PASS, then:

~~~bash
git rm docs/app.js docs/styles.css
git add docs/index.html docs/js docs/styles tests/test_static_ui.py
git commit -m "feat: add modular Review workspace"
~~~

---

### Task 4: Adaptive Hybrid Ticker

**Files:**
- Create: docs/js/ticker.js
- Create/modify: docs/styles/ticker.css
- Modify: docs/js/app.js, docs/index.html, tests/test_static_ui.py

**Interfaces:**
- buildTickerItems(ideas, insightsByIssue, now) -> string[]
- renderTicker(root, items) -> void

- [ ] **Step 1: Add RED ticker tests**

~~~python
def test_ticker_contract(self):
    html = HTML.read_text(encoding="utf-8")
    js = (ROOT / "docs" / "js" / "ticker.js").read_text(encoding="utf-8")
    css = (ROOT / "docs" / "styles" / "ticker.css").read_text(encoding="utf-8")
    self.assertIn('id="ticker"', html)
    self.assertIn("buildTickerItems", js)
    self.assertIn("prefers-reduced-motion", css)
    self.assertIn(":hover", css)
    self.assertIn(":focus-within", css)
    self.assertIn("@media(max-width:620px)", css)
~~~

- [ ] **Step 2: Run RED**

~~~bash
python3 -m unittest tests.test_static_ui -v
~~~

Expected: FAIL.

- [ ] **Step 3: Implement data-driven ticker**

buildTickerItems includes:
- total ideas;
- open count;
- Needs Review count;
- GitHub synced;
- up to four newest titles and stage tags;
- AI insight count only when nonzero.

Escape Issue-derived text before innerHTML.

renderTicker creates one screen-reader status string and two aria-hidden visual copies for seamless motion.

- [ ] **Step 4: Implement adaptive CSS**

Desktop:
- fixed bottom;
- 30px height;
- thin border;
- 42s linear ticker-scroll;
- pause on hover/focus-within;
- body bottom padding 30px.

Reduced motion:
- animation:none;
- hide duplicate visual copy.

Mobile <=620px:
- position:relative;
- no persistent body padding;
- ticker follows footer content.

- [ ] **Step 5: Verify and commit**

~~~bash
python3 -m unittest tests.test_static_ui -v
node --check docs/js/ticker.js
git add docs/index.html docs/js/ticker.js docs/js/app.js docs/styles/ticker.css tests/test_static_ui.py
git commit -m "feat: add adaptive Brain Dump ticker"
~~~

---

### Task 5: Optional AI Review Sidecar

**Files:**
- Create: scripts/ai/__init__.py
- Create: scripts/ai/evaluate.py
- Create: scripts/ai/providers/__init__.py
- Create: scripts/ai/providers/openai_compatible.py
- Create: tests/test_ai_evaluate.py
- Modify: scripts/validate_generated.py
- Modify/generated: docs/data/ai-insights.json

**Interfaces:**
- parse_provider_content(content: str) -> dict
- request_insight(idea, base_url, api_key, model, timeout=30) -> dict
- validate_insight(candidate, issue_number, evaluated_at) -> dict
- merge_insights(existing, updates) -> list[dict]
- Issue mode reads live trusted Issue via get_issue + normalize_issue.
- Batch mode reads docs/data/ideas.json.

- [ ] **Step 1: Write RED validation/preservation tests**

~~~python
def test_rejects_unknown_action_and_wrong_issue_number(self):
    raw = {
        "issueNumber":99, "summary":"Useful.", "suggestedAction":"delete-it",
        "signals":["context"], "confidence":0.8, "depth":"brief",
    }
    with self.assertRaises(ValueError):
        validate_insight(raw, 7, "2026-09-23T12:00:00Z")

def test_rejects_confidence_outside_range(self):
    raw = {
        "issueNumber":7, "summary":"Useful.", "suggestedAction":"revisit",
        "signals":[], "confidence":1.5, "depth":"brief",
    }
    with self.assertRaises(ValueError):
        validate_insight(raw, 7, "2026-09-23T12:00:00Z")

def test_missing_update_preserves_old_valid_insight(self):
    old = {"issueNumber":7,"summary":"Old","suggestedAction":"revisit",
           "signals":[],"confidence":0.7,"depth":"brief",
           "evaluatedAt":"2026-09-22T12:00:00Z"}
    self.assertEqual(merge_insights([old], []), [old])
~~~

- [ ] **Step 2: Run RED**

~~~bash
python3 -m unittest tests.test_ai_evaluate -v
~~~

Expected: FAIL.

- [ ] **Step 3: Pin malformed provider JSON behavior**

Add to tests/test_ai_evaluate.py:

~~~python
import json
from scripts.ai.providers.openai_compatible import parse_provider_content

def test_markdown_fenced_provider_json_is_rejected(self):
    with self.assertRaises(json.JSONDecodeError):
        parse_provider_content('~~~json\n{"issueNumber":7}\n~~~')
~~~

Run:

~~~bash
python3 -m unittest tests.test_ai_evaluate -v
~~~

Expected: FAIL because provider parser does not exist.

- [ ] **Step 4: Implement OpenAI-compatible provider boundary**

Use urllib.request only. Endpoint = AI_BASE_URL.rstrip("/") + "/chat/completions". Send model, temperature 0.2, system instruction, and JSON-serialized idea.

System instruction must allow only:
keep-exploring, revisit, promote-candidate, consider-archive.

Expose:

~~~python
def parse_provider_content(content: str) -> dict:
    return json.loads(content.strip())
~~~

request_insight must call parse_provider_content on the model response. Markdown-fenced/non-JSON output is invalid and must not be silently repaired.

- [ ] **Step 5: Implement evaluator and degraded mode**

evaluate.py must:
- validate Issue number, summary, list[str] signals, action whitelist, confidence 0..1, depth brief/detailed;
- accept optional strength/risk/nextStep only as strings;
- consider only open, non-Project, non-Archived ideas;
- if AI_API_KEY, AI_BASE_URL, or AI_MODEL is absent: exit 0 without overwriting a valid sidecar;
- catch provider failure per idea;
- preserve existing valid insight when an update fails;
- atomically replace docs/data/ai-insights.json only after validation;
- support --issue-number N for Issue events and no argument for batch daily/manual mode.

- [ ] **Step 6: Verify and commit**

~~~bash
python3 -m unittest tests.test_ai_evaluate tests.test_validate_generated -v
python3 -m py_compile scripts/ai/evaluate.py scripts/ai/providers/openai_compatible.py
python3 scripts/validate_generated.py
git add scripts/ai scripts/validate_generated.py tests/test_ai_evaluate.py docs/data/ai-insights.json
git commit -m "feat: add optional AI review sidecar"
~~~

---

### Task 6: Independent Sync and AI Workflows

**Files:**
- Rename: .github/workflows/sync-brain-dump.yml -> .github/workflows/sync.yml
- Create: .github/workflows/ai-review.yml
- Modify: tests/test_workflow_contract.py

**Interfaces:**
- sync.yml owns canonical generation + Pages.
- ai-review.yml owns only docs/data/ai-insights.json.
- AI vars: vars.AI_BASE_URL, vars.AI_MODEL; secret: secrets.AI_API_KEY.
- AI sidecar commit may trigger sync.yml; sync canonical GENERATED list must exclude ai-insights.json.

- [ ] **Step 1: Write RED workflow tests**

~~~python
def test_sync_is_ai_independent(self):
    text = SYNC.read_text(encoding="utf-8")
    self.assertNotIn("AI_API_KEY", text)
    self.assertNotIn("scripts/ai/evaluate.py", text)
    self.assertIn("python3 scripts/validate_generated.py", text)

def test_ai_review_has_issue_daily_and_manual_triggers(self):
    text = AI_REVIEW.read_text(encoding="utf-8")
    for value in ("issues:", "schedule:", "workflow_dispatch:"):
        self.assertIn(value, text)

def test_ai_review_has_no_issue_write_permission(self):
    text = AI_REVIEW.read_text(encoding="utf-8")
    self.assertIn("issues: read", text)
    self.assertNotIn("issues: write", text)
~~~

- [ ] **Step 2: Run RED**

~~~bash
python3 -m unittest tests.test_workflow_contract -v
~~~

Expected: FAIL.

- [ ] **Step 3: Update sync.yml**

Keep trusted-author guard, retry behavior, Pages deployment, and brain-dump-sync concurrency.

Add:
- Python unittest;
- Node scoring test;
- canonical generation;
- python3 scripts/validate_generated.py before commit/deploy;
- GENERATED list contains README.md TIMELINE.md docs/data/ideas.json only.

No AI vars/secrets or evaluator call.

- [ ] **Step 4: Create ai-review.yml**

Triggers:

~~~yaml
on:
  issues:
    types: [opened, edited]
  schedule:
    - cron: "17 2 * * *"
  workflow_dispatch:
~~~

Permissions:

~~~yaml
permissions:
  contents: write
  issues: read
~~~

Use trusted-author guard for Issue events. For Issue events run evaluator with --issue-number ${{ github.event.issue.number }}; for schedule/manual run batch mode. Validate and commit only docs/data/ai-insights.json. Missing provider config with no change exits success.

- [ ] **Step 5: Verify and commit**

~~~bash
python3 -m unittest tests.test_workflow_contract -v
ruby -e 'require "yaml"; ARGV.each { |p| YAML.load_file(p); puts "#{p} OK" }' .github/workflows/sync.yml .github/workflows/ai-review.yml
git add .github/workflows/sync.yml .github/workflows/ai-review.yml tests/test_workflow_contract.py
git rm .github/workflows/sync-brain-dump.yml
git commit -m "ci: separate sync and AI review workflows"
~~~

---

### Task 7: Conservative Cleanup and Policy Documentation

**Files:**
- Modify: AGENTS.md, docs/ai-access.md, README.md, scripts/generate_timeline.py
- Reorganize tests into generator/frontend/ai/workflow/policy packages
- Delete legacy SVG assets only after reference check

**Interfaces:** No new runtime interfaces; this task documents ownership and removes proven legacy only.

- [ ] **Step 1: Add RED policy tests**

~~~python
def test_agents_names_generated_boundaries(self):
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
    self.assertIn("docs/data/ideas.json", text)
    self.assertIn("docs/data/ai-insights.json", text)
    self.assertIn("do not edit", text)

def test_ai_access_documents_sidecar_recommendations(self):
    text = (ROOT / "docs" / "ai-access.md").read_text(encoding="utf-8").lower()
    self.assertIn("ai-insights.json", text)
    self.assertIn("promote-candidate", text)
    self.assertIn("consider-archive", text)
    self.assertIn("read-only", text)
~~~

- [ ] **Step 2: Update policy/docs**

AGENTS.md must distinguish:
- GitHub Issues canonical source;
- source code;
- deterministic generated output;
- AI generated output;
- generated files not manually edited;
- AI recommendations never imply authorization for Project/Archived/close.

docs/ai-access.md documents rule-based scoring, optional stale/missing AI sidecar, recommendation-only actions, and secret boundaries.

README stays concise and non-marketing.

- [ ] **Step 3: Remove old timeline SVG only if obsolete**

Run:

~~~bash
grep -R "idea-journey" -n README.md TIMELINE.md docs scripts tests .github || true
~~~

If only generate_svg/picture_block/TIMELINE generated references remain, remove that legacy path and delete assets/idea-journey-light.svg and assets/idea-journey-dark.svg. Otherwise retain and explain why.

- [ ] **Step 4: Reorganize tests and verify discovery**

Move Python tests into:
- tests/generator
- tests/frontend
- tests/ai
- tests/workflow
- tests/policy

Add __init__.py in each Python package.

For moved tests that resolve repository files, set:

~~~python
ROOT = Path(__file__).resolve().parents[2]
~~~

This applies to the moved frontend/static, workflow, and policy tests; do not leave parents[1], which would resolve to the tests directory.

Run:

~~~bash
python3 -m unittest discover -s tests -v
node --experimental-default-type=module --test tests/frontend/scoring.test.js
~~~

Expected: PASS.

- [ ] **Step 5: Full syntax/security verification**

~~~bash
python3 -m py_compile scripts/generate_timeline.py scripts/generate/issues.py scripts/validate_generated.py scripts/ai/evaluate.py scripts/ai/providers/openai_compatible.py
node --check docs/js/app.js
node --check docs/js/data.js
node --check docs/js/scoring.js
node --check docs/js/views.js
node --check docs/js/review.js
node --check docs/js/ticker.js
node --check docs/js/theme.js
python3 scripts/validate_generated.py
grep -RniE 'authorization: bearer|github_token|AI_API_KEY' docs/js docs/index.html || true
~~~

Expected: all syntax/validation commands exit 0; frontend credential scan has no match.

- [ ] **Step 6: Commit**

~~~bash
git add AGENTS.md README.md TIMELINE.md docs/ai-access.md scripts/generate_timeline.py tests
git add -u
git commit -m "chore: finish conservative Brain Dump cleanup"
~~~

---

### Task 8: Whole-Branch Review and Production Acceptance

**Files:** No planned product-code changes unless review/acceptance reveals a defect.

**Interfaces:** Validates GitHub Issues -> canonical sync -> Pages, plus optional AI sidecar.

- [ ] **Step 1: Run fresh full verification**

~~~bash
python3 -m unittest discover -s tests -v
node --experimental-default-type=module --test tests/frontend/scoring.test.js
python3 scripts/validate_generated.py
~~~

Expected: PASS.

- [ ] **Step 2: Request whole-branch review**

Review the branch against:
- approved spec;
- deterministic thresholds/scoring;
- safe AI degradation;
- workflow ownership;
- frontend read-only/credential boundary;
- reduced-motion/mobile ticker behavior;
- no unnecessary dependency/framework.

Important/Critical findings require a new failing test before a fix.

- [ ] **Step 3: Integrate through PR after review approval**

Do not direct-push product code to main.

- [ ] **Step 4: Verify merged main workflow**

Confirm on merged SHA:
- Python tests PASS;
- Node scoring tests PASS;
- canonical generation PASS;
- generated validation PASS;
- Pages deploy PASS.

- [ ] **Step 5: Live Pages acceptance**

Verify:
- Notes default;
- Notes / Review / Board / Calendar only;
- Review three sections;
- textual score reasons;
- search/filter regression;
- Board/Calendar regression;
- New note direct idea.yml link;
- real-data ticker;
- desktop fixed ticker;
- mobile non-fixed ticker;
- reduced-motion CSS active when emulated;
- empty/missing AI insights do not block UI.

- [ ] **Step 6: AI acceptance**

If AI provider vars/secrets are actually configured, verify AI Review produces valid insight and Pages later displays it.

If provider config is absent, verify workflow safe degraded mode and report AI as not configured. Do not claim live AI insight.

- [ ] **Step 7: Final report**

Report merged SHA, test totals, workflow results, Pages checks, AI configured/degraded state, retained legacy with reason if any, and deferred Minor findings.
