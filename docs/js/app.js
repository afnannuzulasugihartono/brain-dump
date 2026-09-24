import {loadBrainDumpData} from "./data.js";
import {renderNotes, renderBoard, renderCalendar, esc} from "./views.js";
import {renderReview} from "./review.js";
import {initTheme} from "./theme.js";
import {buildTickerItems, renderTicker} from "./ticker.js";

const state={ideas:[],filtered:[],insightsByIssue:new Map(),view:"notes",query:"",category:"all",stage:"all",calendarDate:new Date()};
const $=selector=>document.querySelector(selector);
const $$=selector=>[...document.querySelectorAll(selector)];
const unique=values=>[...new Set(values.filter(Boolean))].sort();
const SIDEBAR_STORAGE_KEY="brainDumpSidebarCollapsed";
const BOOT_SESSION_KEY="brainDumpBootSeen";

function greetingForHour(hour) {
  if (hour >= 5 && hour < 12) return {title:"Good morning",subtitle:"Ready to capture a thought?"};
  if (hour >= 12 && hour < 17) return {title:"Good afternoon",subtitle:"What are you thinking about?"};
  if (hour >= 17 && hour < 21) return {title:"Good evening",subtitle:"Anything worth saving before the day ends?"};
  return {title:"Good night",subtitle:"A quiet place for late-night thoughts."};
}

function initGreeting() {
  const greeting = greetingForHour(new Date().getHours());
  $("#greetingTitle").textContent = greeting.title;
  $("#greetingSubtitle").textContent = greeting.subtitle;
}

function initSidebar() {
  const sidebar = $("#sidebar");
  const collapseButton = $("#sidebarToggle");
  const brandToggle = $("#sidebarBrandToggle");
  if (!sidebar || !collapseButton || !brandToggle) return;

  const readCollapsed = () => {
    try { return localStorage.getItem(SIDEBAR_STORAGE_KEY) === "1"; }
    catch { return false; }
  };
  const setCollapsed = collapsed => {
    sidebar.classList.toggle("is-collapsed", collapsed);
    collapseButton.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
    collapseButton.title = collapsed ? "Expand sidebar" : "Collapse sidebar";
    brandToggle.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
    brandToggle.title = collapsed ? "Expand sidebar" : "Collapse sidebar";
    try { localStorage.setItem(SIDEBAR_STORAGE_KEY, collapsed ? "1" : "0"); } catch {}
  };

  setCollapsed(readCollapsed());
  collapseButton.onclick = () => setCollapsed(!sidebar.classList.contains("is-collapsed"));
  brandToggle.onclick = () => setCollapsed(!sidebar.classList.contains("is-collapsed"));
}

function initBootIntro() {
  const intro = $("#bootIntro");
  if (!intro) return;
  const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  let seen = false;
  try { seen = sessionStorage.getItem(BOOT_SESSION_KEY) === "1"; } catch {}
  if (reduceMotion || seen) {
    intro.hidden = true;
    return;
  }
  try { sessionStorage.setItem(BOOT_SESSION_KEY, "1"); } catch {}
  intro.hidden = false;
  intro.classList.add("is-active");
  document.body.classList.add("boot-sequence");
  intro.addEventListener("animationend", event => {
    if (event.target !== intro || event.animationName !== "boot-dismiss") return;
    intro.hidden = true;
    intro.classList.remove("is-active");
    document.body.classList.remove("boot-sequence");
  });
}

function initShellUi() {
  initGreeting();
  initSidebar();
  initBootIntro();
}


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
  $$(".view-link").forEach(control => {
    const active = control.dataset.view === view;
    control.classList.toggle("active", active);
    if (active) control.setAttribute("aria-current", "page");
    else control.removeAttribute("aria-current");
  });
  $$(".view").forEach(section => section.classList.remove("active"));
  $("#" + view + "View").classList.add("active");
  renderActive();
  history.replaceState(null,"","#"+view);
}

async function init() {
  initShellUi();
  $(".theme-toggle").forEach(initTheme);
  try {
    const data = await loadBrainDumpData();
    state.ideas = data.ideas;
    state.filtered = [...data.ideas];
    state.insightsByIssue = data.insightsByIssue;
    renderTicker($("#ticker"), buildTickerItems(state.ideas, state.insightsByIssue));
    if (state.ideas[0]) state.calendarDate = new Date(state.ideas[0].createdAt);
    fillSelect("#categoryFilter", state.ideas.map(item => item.category));
    fillSelect("#stageFilter", state.ideas.map(item => item.stage));
    $("#searchInput").oninput = event => {state.query=event.target.value;applyFilters();};
    $("#categoryFilter").onchange = event => {state.category=event.target.value;applyFilters();};
    $("#stageFilter").onchange = event => {state.stage=event.target.value;applyFilters();};
    $$(".view-link").forEach(control => control.onclick = () => setView(control.dataset.view));
    const requested = location.hash.slice(1);
    setView(["notes","review","board","calendar"].includes(requested) ? requested : "notes");
  } catch (error) {
    console.error(error);
    $("#notesView").innerHTML = '<div class="empty"><strong>Could not load notes.</strong><span>Refresh the page or <a href="https://github.com/afnannuzulasugihartono/brain-dump/issues">open GitHub Issues</a>.</span></div>';
  }
}

init();
