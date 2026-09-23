const state = {
  ideas: [],
  filtered: [],
  view: "journey",
  query: "",
  category: "all",
  stage: "all",
  calendarDate: new Date(),
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

const fmtDate = (iso, opts = {}) => {
  const d = new Date(iso);
  return new Intl.DateTimeFormat("en", { day: "numeric", month: "short", year: "numeric", ...opts }).format(d);
};

const monthKey = (iso) => {
  const d = new Date(iso);
  return new Intl.DateTimeFormat("en", { month: "short", year: "numeric" }).format(d).toUpperCase();
};

const escapeHtml = (value = "") => value.replace(/[&<>"']/g, (m) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
}[m]));

const stageClass = (stage = "") => stage.toLowerCase() === "promising" ? "pill-promising" : "";
const stateClass = (value) => value === "open" ? "pill-open" : "";

function ideaCard(idea, { latest = false, compact = false } = {}) {
  return `
    <article class="idea-card ${latest ? "latest" : ""}">
      <div class="card-kicker">#${idea.number} · ${fmtDate(idea.createdAt)}</div>
      <a class="card-title" href="${idea.url}" target="_blank" rel="noreferrer">${escapeHtml(idea.title)}</a>
      <div class="pills">
        <span class="pill ${stateClass(idea.state)}">${idea.state}</span>
        <span class="pill ${stageClass(idea.stage)}">${escapeHtml(idea.stage)}</span>
        ${compact ? "" : `<span class="pill">${escapeHtml(idea.category)}</span>`}
      </div>
    </article>
  `;
}

function emptyState() {
  return $("#emptyTemplate").content.cloneNode(true);
}

function fillSelect(selector, values, label) {
  const el = $(selector);
  [...new Set(values)].filter(Boolean).sort().forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    el.appendChild(option);
  });
}

function renderStats() {
  const total = state.ideas.length;
  const open = state.ideas.filter((x) => x.state === "open").length;
  const promising = state.ideas.filter((x) => x.stage.toLowerCase() === "promising").length;
  const projects = state.ideas.filter((x) => x.stage.toLowerCase() === "project").length;
  const items = [
    ["Ideas", total, "captured sparks"],
    ["Open", open, "still alive"],
    ["Promising", promising, "worth pushing"],
    ["Projects", projects, "promoted ideas"],
  ];
  $("#stats").innerHTML = items.map(([label, value, note]) => `
    <div class="stat"><span class="stat-label">${label}</span><strong class="stat-value">${value}</strong><small>${note}</small></div>
  `).join("");
}

function renderSpotlights() {
  const latest = state.ideas[0];
  $("#latestSpark").innerHTML = latest ? `
    <div class="panel-label">✨ Latest Spark</div>
    <a class="spotlight-title" href="${latest.url}" target="_blank" rel="noreferrer">${escapeHtml(latest.title)}</a>
    <div class="meta-row">
      <span>#${latest.number}</span><span>·</span><span>${fmtDate(latest.createdAt)}</span>
      <span class="pill ${stageClass(latest.stage)}">${escapeHtml(latest.stage)}</span>
      <span class="pill">${escapeHtml(latest.category)}</span>
    </div>
  ` : `<div class="panel-label">✨ Latest Spark</div><div class="spotlight-title">Waiting for the first idea.</div>`;

  const now = Date.now();
  const stale = state.ideas.filter((idea) => {
    if (idea.state !== "open") return false;
    if (!["inbox", "exploring"].includes(idea.stage.toLowerCase())) return false;
    return now - new Date(idea.updatedAt).getTime() > 30 * 86400000;
  });
  const reviewCount = stale.length;
  $("#reviewPanel").innerHTML = `
    <div class="panel-label">🌱 Worth Revisiting</div>
    <div class="review-number">${reviewCount}</div>
    <div class="review-copy">${reviewCount ? "older ideas are waiting for another look." : "Nothing is gathering dust right now."}</div>
    <button class="inline-link" id="reviewIdeas" type="button">${reviewCount ? "Review ideas →" : "Browse inbox →"}</button>
  `;
  $("#reviewIdeas")?.addEventListener("click", () => {
    state.stage = reviewCount ? "Inbox" : "Inbox";
    $("#stageFilter").value = state.stage;
    applyFilters();
    setView("cards");
    $(".workspace").scrollIntoView({ behavior: "smooth" });
  });
}

function applyFilters() {
  const q = state.query.trim().toLowerCase();
  state.filtered = state.ideas.filter((idea) => {
    const haystack = [idea.title, idea.category, idea.stage, idea.why].join(" ").toLowerCase();
    return (!q || haystack.includes(q))
      && (state.category === "all" || idea.category === state.category)
      && (state.stage === "all" || idea.stage === state.stage);
  });
  const active = [];
  if (state.query) active.push(`search: “${escapeHtml(state.query)}”`);
  if (state.category !== "all") active.push(state.category);
  if (state.stage !== "all") active.push(state.stage);
  $("#activeFilters").hidden = !active.length;
  $("#activeFilters").innerHTML = active.length ? `Showing ${state.filtered.length} idea${state.filtered.length === 1 ? "" : "s"} · ${active.join(" · ")}` : "";
  renderActiveView();
}

function renderJourney() {
  const root = $("#journeyView");
  if (!state.filtered.length) { root.replaceChildren(emptyState()); return; }
  const latestNumber = state.ideas[0]?.number;
  let currentMonth = "";
  let html = '<div class="journey">';
  state.filtered.slice().reverse().forEach((idea, index) => {
    const month = monthKey(idea.createdAt);
    if (month !== currentMonth) {
      html += `<div class="month-marker">${month}</div>`;
      currentMonth = month;
    }
    const latest = idea.number === latestNumber;
    html += `
      <div class="journey-item">
        ${ideaCard(idea, { latest })}
        <span class="journey-node ${latest ? "latest" : ""}" title="${fmtDate(idea.createdAt)}"></span>
      </div>
    `;
  });
  html += "</div>";
  root.innerHTML = html;
}

function renderCards() {
  const root = $("#cardsView");
  if (!state.filtered.length) { root.replaceChildren(emptyState()); return; }
  const latestNumber = state.ideas[0]?.number;
  root.innerHTML = `<div class="card-grid">${state.filtered.map((idea) => ideaCard(idea, { latest: idea.number === latestNumber })).join("")}</div>`;
}

function renderBoard() {
  const root = $("#boardView");
  const stages = ["Inbox", "Exploring", "Promising", "Project", "Archived"];
  root.innerHTML = '<div class="board">' + stages.map((stage) => {
    const ideas = state.filtered.filter((idea) => idea.stage.toLowerCase() === stage.toLowerCase());
    return `
      <section class="board-column">
        <div class="board-head"><strong>${stage}</strong><span class="board-count">${ideas.length}</span></div>
        ${ideas.map((idea) => ideaCard(idea, { compact: true })).join("") || '<div class="review-copy">No ideas</div>'}
      </section>
    `;
  }).join("") + "</div>";
}

function renderCalendar() {
  const root = $("#calendarView");
  const selected = state.calendarDate;
  const year = selected.getFullYear();
  const month = selected.getMonth();
  const first = new Date(year, month, 1);
  const gridStart = new Date(year, month, 1 - first.getDay());
  const days = Array.from({ length: 42 }, (_, i) => {
    const d = new Date(gridStart);
    d.setDate(gridStart.getDate() + i);
    return d;
  });
  const ideasByDay = new Map();
  state.filtered.forEach((idea) => {
    const d = new Date(idea.createdAt);
    const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
    if (!ideasByDay.has(key)) ideasByDay.set(key, []);
    ideasByDay.get(key).push(idea);
  });
  const monthLabel = new Intl.DateTimeFormat("en", { month: "long", year: "numeric" }).format(selected);
  root.innerHTML = `
    <div class="calendar-shell">
      <div class="calendar-head">
        <h2>${monthLabel}</h2>
        <div class="calendar-nav"><button id="prevMonth" aria-label="Previous month">‹</button><button id="nextMonth" aria-label="Next month">›</button></div>
      </div>
      <div class="calendar-weekdays">${["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map((d) => `<div>${d}</div>`).join("")}</div>
      <div class="calendar-grid">
        ${days.map((d) => {
          const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
          const dayIdeas = ideasByDay.get(key) || [];
          return `
            <div class="calendar-day ${d.getMonth() !== month ? "outside" : ""}">
              <div class="day-number">${d.getDate()}</div>
              ${dayIdeas.map((idea) => `<a class="day-idea" href="${idea.url}" title="${escapeHtml(idea.title)}">${escapeHtml(idea.title)}</a>`).join("")}
            </div>`;
        }).join("")}
      </div>
    </div>
  `;
  $("#prevMonth").onclick = () => { state.calendarDate = new Date(year, month - 1, 1); renderCalendar(); };
  $("#nextMonth").onclick = () => { state.calendarDate = new Date(year, month + 1, 1); renderCalendar(); };
}

function renderActiveView() {
  if (state.view === "journey") renderJourney();
  if (state.view === "cards") renderCards();
  if (state.view === "board") renderBoard();
  if (state.view === "calendar") renderCalendar();
}

function setView(view) {
  state.view = view;
  $$(".view-tab").forEach((el) => el.classList.toggle("active", el.dataset.view === view));
  $$(".view").forEach((el) => el.classList.remove("active"));
  $(`#${view}View`).classList.add("active");
  renderActiveView();
  history.replaceState(null, "", `#${view}`);
}

function initTheme() {
  const saved = localStorage.getItem("brain-dump-theme");
  const preferredDark = matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.dataset.theme = saved || (preferredDark ? "dark" : "light");
  $("#themeToggle").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("brain-dump-theme", next);
  });
}

async function init() {
  initTheme();
  try {
    const response = await fetch("./ideas.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`ideas.json returned ${response.status}`);
    const data = await response.json();
    state.ideas = [...data.ideas].sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt));
    state.filtered = [...state.ideas];
    const latest = state.ideas[0];
    if (latest) state.calendarDate = new Date(latest.createdAt);

    fillSelect("#categoryFilter", state.ideas.map((x) => x.category));
    fillSelect("#stageFilter", state.ideas.map((x) => x.stage));
    renderStats();
    renderSpotlights();

    $("#searchInput").addEventListener("input", (e) => { state.query = e.target.value; applyFilters(); });
    $("#categoryFilter").addEventListener("change", (e) => { state.category = e.target.value; applyFilters(); });
    $("#stageFilter").addEventListener("change", (e) => { state.stage = e.target.value; applyFilters(); });
    $$(".view-tab").forEach((tab) => tab.addEventListener("click", () => setView(tab.dataset.view)));

    const requested = location.hash.replace("#", "");
    setView(["journey","cards","board","calendar"].includes(requested) ? requested : "journey");
  } catch (error) {
    console.error(error);
    $("#journeyView").innerHTML = '<div class="empty-state"><span>!</span><h3>Could not load ideas</h3><p>Refresh the page or check the repository workflow.</p></div>';
  }
}

init();