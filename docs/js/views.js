export const esc = (value="") => String(value).replace(/[&<>"']/g, char => ({
  "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
}[char]));

export const tag = value => `#${esc(String(value || "").toLowerCase().replace(/\s+/g, "-"))}`;

export function dateParts(iso) {
  const date = new Date(iso);
  return {
    day:new Intl.DateTimeFormat("en",{day:"numeric"}).format(date),
    mon:new Intl.DateTimeFormat("en",{month:"short"}).format(date),
    year:date.getFullYear(),
    full:new Intl.DateTimeFormat("en",{day:"numeric",month:"short",year:"numeric"}).format(date),
    month:new Intl.DateTimeFormat("en",{month:"long",year:"numeric"}).format(date),
  };
}

const noteBody = idea => (idea.idea || idea.why || "").trim();

export function ideaCard(idea, {compact=false}={}) {
  const date = dateParts(idea.createdAt);
  const body = noteBody(idea);
  return `<article class="idea-card">
    <div class="card-kicker">#${idea.number} · ${date.full}</div>
    <a class="card-title" href="${esc(idea.url)}">${esc(idea.title)}</a>
    ${compact || !body ? "" : `<p class="card-copy">${esc(body)}</p>`}
    <div class="card-meta">
      <span>${tag(idea.stage)}</span>
      ${compact ? "" : `<span>${tag(idea.category)}</span>`}
      <a href="${esc(idea.url)}">GitHub</a>
    </div>
  </article>`;
}

export function renderNotes(root, ideas, emptyTemplate, visibleCount=5) {
  if (!ideas.length) {
    root.replaceChildren(emptyTemplate.content.cloneNode(true));
    return;
  }
  let currentMonth = "";
  let html = '<div class="notes">';
  const visibleIdeas = ideas.slice(0, visibleCount);
  visibleIdeas.forEach(idea => {
    const parts = dateParts(idea.createdAt);
    const body = noteBody(idea);
    if (parts.month !== currentMonth) {
      html += `<h2 class="month">${esc(parts.month)}</h2>`;
      currentMonth = parts.month;
    }
    html += `<article class="note">
      <div class="note-time">${parts.day} ${parts.mon} · ${parts.year}</div>
      <a class="note-title" href="${esc(idea.url)}">${esc(idea.title)}</a>
      ${body ? `<p class="note-copy">${esc(body)}</p>` : ""}
      <div class="note-meta">
        <span>${tag(idea.stage)}</span>
        <span>${tag(idea.category)}</span>
        ${idea.state !== "open" ? `<span>${tag(idea.state)}</span>` : ""}
        <a href="${esc(idea.url)}">View on GitHub</a>
      </div>
    </article>`;
  });
  html += "</div>";
  if (visibleIdeas.length < ideas.length) {
    html += '<button class="show-more-notes" data-action="show-more-notes" type="button">Show more</button>';
  }
  root.innerHTML = html;
}

export function renderBoard(root, ideas) {
  const stages = ["Inbox","Exploring","Promising","Project","Archived"];
  root.innerHTML = `<div class="board">${stages.map(stage => {
    const items = ideas.filter(idea => String(idea.stage).toLowerCase() === stage.toLowerCase());
    return `<section class="board-column">
      <div class="board-head"><strong>${stage}</strong><span>${items.length}</span></div>
      ${items.map(idea => ideaCard(idea,{compact:true})).join("") || '<div class="card-kicker">No notes</div>'}
    </section>`;
  }).join("")}</div>`;
}

export function renderCalendar(root, ideas, selected, onDateChange) {
  const year = selected.getFullYear();
  const month = selected.getMonth();
  const first = new Date(year, month, 1);
  const start = new Date(year, month, 1 - first.getDay());
  const days = Array.from({length:42}, (_, index) => {
    const date = new Date(start);
    date.setDate(start.getDate() + index);
    return date;
  });
  const byDay = new Map();
  ideas.forEach(idea => {
    const date = new Date(idea.createdAt);
    const key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
    if (!byDay.has(key)) byDay.set(key, []);
    byDay.get(key).push(idea);
  });
  const title = new Intl.DateTimeFormat("en",{month:"long",year:"numeric"}).format(selected);
  root.innerHTML = `<div class="calendar-shell">
    <div class="calendar-head"><h2>${title}</h2><div class="calendar-nav"><button id="prevMonth" aria-label="Previous month">‹</button><button id="nextMonth" aria-label="Next month">›</button></div></div>
    <div class="calendar-weekdays">${["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map(day => `<div>${day}</div>`).join("")}</div>
    <div class="calendar-grid">${days.map(date => {
      const key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
      const items = byDay.get(key) || [];
      return `<div class="calendar-day ${date.getMonth() !== month ? "outside" : ""}"><div class="day-number">${date.getDate()}</div>${items.map(idea => `<a class="day-idea" href="${esc(idea.url)}" title="${esc(idea.title)}">${esc(idea.title)}</a>`).join("")}</div>`;
    }).join("")}</div>
  </div>`;
  root.querySelector("#prevMonth").onclick = () => onDateChange(new Date(year, month - 1, 1));
  root.querySelector("#nextMonth").onclick = () => onDateChange(new Date(year, month + 1, 1));
}
