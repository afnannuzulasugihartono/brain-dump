import {loadBrainDumpData} from "./data.js";
import {renderNotes, renderBoard, renderCalendar, esc} from "./views.js";
import {renderReview} from "./review.js";
import {initTheme} from "./theme.js";

const state={ideas:[],filtered:[],insightsByIssue:new Map(),view:"notes",query:"",category:"all",stage:"all",calendarDate:new Date()};
const $=selector=>document.querySelector(selector);
const $$=selector=>[...document.querySelectorAll(selector)];
const unique=values=>[...new Set(values.filter(Boolean))].sort();

function fillSelect(selector, values) {
  const element = $(selector);
  unique(values).forEach(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    element.appendChild(option);
  });
}

function renderActive() {
  if (state.view === "notes") renderNotes($("#notesView"), state.filtered, $("#emptyTemplate"));
  else if (state.view === "review") renderReview($("#reviewView"), state.filtered, state.insightsByIssue);
  else if (state.view === "board") renderBoard($("#boardView"), state.filtered);
  else renderCalendar($("#calendarView"), state.filtered, state.calendarDate, next => {state.calendarDate=next;renderActive();});
}

function applyFilters() {
  const query = state.query.trim().toLowerCase();
  state.filtered = state.ideas.filter(idea => {
    const haystack = [idea.title,idea.idea,idea.why,idea.aiNotes,idea.category,idea.stage].join(" ").toLowerCase();
    return (!query || haystack.includes(query)) && (state.category === "all" || idea.category === state.category) && (state.stage === "all" || idea.stage === state.stage);
  });
  const active=[];
  if (state.query) active.push(`“${esc(state.query)}”`);
  if (state.category !== "all") active.push(esc(state.category));
  if (state.stage !== "all") active.push(esc(state.stage));
  $("#activeFilters").hidden = !active.length;
  $("#activeFilters").innerHTML = active.length ? `${state.filtered.length} result${state.filtered.length===1?"":"s"} · ${active.join(" · ")}` : "";
  renderActive();
}

function setView(view) {
  state.view = view;
  $$(".tab").forEach(tab => {
    const active = tab.dataset.view === view;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
  });
  $$(".view").forEach(section => section.classList.remove("active"));
  $("#" + view + "View").classList.add("active");
  renderActive();
  history.replaceState(null,"","#"+view);
}

async function init() {
  initTheme($("#themeToggle"));
  try {
    const data = await loadBrainDumpData();
    state.ideas = data.ideas;
    state.filtered = [...data.ideas];
    state.insightsByIssue = data.insightsByIssue;
    if (state.ideas[0]) state.calendarDate = new Date(state.ideas[0].createdAt);
    fillSelect("#categoryFilter", state.ideas.map(item => item.category));
    fillSelect("#stageFilter", state.ideas.map(item => item.stage));
    $("#searchInput").oninput = event => {state.query=event.target.value;applyFilters();};
    $("#categoryFilter").onchange = event => {state.category=event.target.value;applyFilters();};
    $("#stageFilter").onchange = event => {state.stage=event.target.value;applyFilters();};
    $$(".tab").forEach(tab => tab.onclick = () => setView(tab.dataset.view));
    const requested = location.hash.slice(1);
    setView(["notes","review","board","calendar"].includes(requested) ? requested : "notes");
  } catch (error) {
    console.error(error);
    $("#notesView").innerHTML = '<div class="empty"><strong>Could not load notes.</strong><span>Refresh the page or <a href="https://github.com/afnannuzulasugihartono/brain-dump/issues">open GitHub Issues</a>.</span></div>';
  }
}

init();
