const state={ideas:[],filtered:[],view:"notes",query:"",category:"all",stage:"all",calendarDate:new Date()};
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const esc=(v="")=>String(v).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
const dateParts=iso=>{
  const d=new Date(iso);
  return {
    day:new Intl.DateTimeFormat("en",{day:"numeric"}).format(d),
    mon:new Intl.DateTimeFormat("en",{month:"short"}).format(d),
    year:d.getFullYear(),
    full:new Intl.DateTimeFormat("en",{day:"numeric",month:"short",year:"numeric"}).format(d),
    month:new Intl.DateTimeFormat("en",{month:"long",year:"numeric"}).format(d)
  };
};
const unique=values=>[...new Set(values.filter(Boolean))].sort();
const tag=v=>`#${esc(String(v||"").toLowerCase().replace(/\s+/g,"-"))}`;

function fillSelect(selector,values){
  const el=$(selector);
  unique(values).forEach(v=>{const option=document.createElement("option");option.value=v;option.textContent=v;el.appendChild(option)});
}

function noteBody(i){
  return (i.idea||i.why||"").trim();
}

function renderNotes(){
  const root=$("#notesView");
  if(!state.filtered.length){root.replaceChildren($("#emptyTemplate").content.cloneNode(true));return}
  let currentMonth="",html='<div class="notes">';
  state.filtered.forEach(i=>{
    const p=dateParts(i.createdAt),body=noteBody(i);
    if(p.month!==currentMonth){html+=`<h2 class="month">${esc(p.month)}</h2>`;currentMonth=p.month}
    html+=`<article class="note">
      <div class="note-time">${p.day} ${p.mon} · ${p.year}</div>
      <a class="note-title" href="${i.url}">${esc(i.title)}</a>
      ${body?`<p class="note-copy">${esc(body)}</p>`:""}
      ${i.why&&i.why.trim()!==body?`<p class="note-context">${esc(i.why)}</p>`:""}
      <div class="note-meta">
        <span>${tag(i.stage)}</span>
        <span>${tag(i.category)}</span>
        ${i.state!=="open"?`<span>${tag(i.state)}</span>`:""}
        <a href="${i.url}">View on GitHub</a>
      </div>
    </article>`;
  });
  root.innerHTML=html+"</div>";
}

function ideaCard(i,{compact=false}={}){
  const p=dateParts(i.createdAt),body=noteBody(i);
  return `<article class="idea-card">
    <div class="card-kicker">#${i.number} · ${p.full}</div>
    <a class="card-title" href="${i.url}">${esc(i.title)}</a>
    ${compact?"":body?`<p class="card-copy">${esc(body)}</p>`:""}
    <div class="card-meta">
      <span>${tag(i.stage)}</span>
      ${compact?"":`<span>${tag(i.category)}</span>`}
      <a href="${i.url}">GitHub</a>
    </div>
  </article>`;
}

function renderCards(){
  const root=$("#cardsView");
  if(!state.filtered.length){root.replaceChildren($("#emptyTemplate").content.cloneNode(true));return}
  root.innerHTML=`<div class="card-grid">${state.filtered.map(i=>ideaCard(i)).join("")}</div>`;
}

function renderBoard(){
  const stages=["Inbox","Exploring","Promising","Project","Archived"];
  $("#boardView").innerHTML=`<div class="board">${stages.map(stage=>{
    const ideas=state.filtered.filter(i=>i.stage.toLowerCase()===stage.toLowerCase());
    return `<section class="board-column"><div class="board-head"><strong>${stage}</strong><span>${ideas.length}</span></div>${ideas.map(i=>ideaCard(i,{compact:true})).join("")||'<div class="card-kicker">No notes</div>'}</section>`;
  }).join("")}</div>`;
}

function renderCalendar(){
  const root=$("#calendarView"),selected=state.calendarDate,year=selected.getFullYear(),month=selected.getMonth();
  const first=new Date(year,month,1),start=new Date(year,month,1-first.getDay());
  const days=Array.from({length:42},(_,n)=>{const d=new Date(start);d.setDate(start.getDate()+n);return d});
  const byDay=new Map();
  state.filtered.forEach(i=>{const d=new Date(i.createdAt),key=`${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;if(!byDay.has(key))byDay.set(key,[]);byDay.get(key).push(i)});
  const title=new Intl.DateTimeFormat("en",{month:"long",year:"numeric"}).format(selected);
  root.innerHTML=`<div class="calendar-shell"><div class="calendar-head"><h2>${title}</h2><div class="calendar-nav"><button id="prevMonth" aria-label="Previous month">‹</button><button id="nextMonth" aria-label="Next month">›</button></div></div><div class="calendar-weekdays">${["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map(x=>`<div>${x}</div>`).join("")}</div><div class="calendar-grid">${days.map(d=>{const key=`${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`,items=byDay.get(key)||[];return `<div class="calendar-day ${d.getMonth()!==month?"outside":""}"><div class="day-number">${d.getDate()}</div>${items.map(i=>`<a class="day-idea" href="${i.url}" title="${esc(i.title)}">${esc(i.title)}</a>`).join("")}</div>`}).join("")}</div></div>`;
  $("#prevMonth").onclick=()=>{state.calendarDate=new Date(year,month-1,1);renderCalendar()};
  $("#nextMonth").onclick=()=>{state.calendarDate=new Date(year,month+1,1);renderCalendar()};
}

function renderActive(){
  if(state.view==="notes")renderNotes();
  else if(state.view==="cards")renderCards();
  else if(state.view==="board")renderBoard();
  else renderCalendar();
}

function applyFilters(){
  const q=state.query.trim().toLowerCase();
  state.filtered=state.ideas.filter(i=>{
    const hay=[i.title,i.idea,i.why,i.aiNotes,i.category,i.stage].join(" ").toLowerCase();
    return (!q||hay.includes(q))&&(state.category==="all"||i.category===state.category)&&(state.stage==="all"||i.stage===state.stage);
  });
  const active=[];
  if(state.query)active.push(`“${esc(state.query)}”`);
  if(state.category!=="all")active.push(esc(state.category));
  if(state.stage!=="all")active.push(esc(state.stage));
  $("#activeFilters").hidden=!active.length;
  $("#activeFilters").innerHTML=active.length?`${state.filtered.length} result${state.filtered.length===1?"":"s"} · ${active.join(" · ")}`:"";
  renderActive();
}

function setView(view){
  state.view=view;
  $$(".tab").forEach(x=>x.classList.toggle("active",x.dataset.view===view));
  $$(".view").forEach(x=>x.classList.remove("active"));
  $("#"+view+"View").classList.add("active");
  renderActive();
  history.replaceState(null,"","#"+view);
}

function initTheme(){
  const saved=localStorage.getItem("brain-dump-theme");
  document.documentElement.dataset.theme=saved||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");
  $("#themeToggle").onclick=()=>{
    const next=document.documentElement.dataset.theme==="dark"?"light":"dark";
    document.documentElement.dataset.theme=next;
    localStorage.setItem("brain-dump-theme",next);
  };
}

async function init(){
  initTheme();
  try{
    const res=await fetch("./ideas.json",{cache:"no-store"});
    if(!res.ok)throw new Error(String(res.status));
    const data=await res.json();
    state.ideas=[...data.ideas].sort((a,b)=>new Date(b.createdAt)-new Date(a.createdAt));
    state.filtered=[...state.ideas];
    if(state.ideas[0])state.calendarDate=new Date(state.ideas[0].createdAt);
    fillSelect("#categoryFilter",state.ideas.map(x=>x.category));
    fillSelect("#stageFilter",state.ideas.map(x=>x.stage));
    $("#searchInput").oninput=e=>{state.query=e.target.value;applyFilters()};
    $("#categoryFilter").onchange=e=>{state.category=e.target.value;applyFilters()};
    $("#stageFilter").onchange=e=>{state.stage=e.target.value;applyFilters()};
    $$(".tab").forEach(x=>x.onclick=()=>setView(x.dataset.view));
    const requested=location.hash.slice(1);
    setView(["notes","cards","board","calendar"].includes(requested)?requested:"notes");
  }catch(error){
    console.error(error);
    $("#notesView").innerHTML='<div class="empty"><strong>Could not load notes.</strong><span>Refresh the page or check the sync workflow.</span></div>';
  }
}
init();
