const state={ideas:[],filtered:[],view:"journey",query:"",category:"all",stage:"all",calendarDate:new Date()};
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const esc=(v="")=>v.replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
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
const stageClass=s=>s.toLowerCase()==="promising"?"meta-promising":"";
const stateClass=s=>s==="open"?"meta-open":"";
const unique=v=>[...new Set(v.filter(Boolean))].sort();

function summary(){
  const total=state.ideas.length;
  const open=state.ideas.filter(x=>x.state==="open").length;
  const promising=state.ideas.filter(x=>x.stage.toLowerCase()==="promising").length;
  const promoted=state.ideas.filter(x=>x.stage.toLowerCase()==="project").length;
  $("#summary").innerHTML=`<strong>${total}</strong> idea${total===1?"":"s"} · <strong>${open}</strong> open · <strong>${promising}</strong> promising · <strong>${promoted}</strong> promoted`;
}

function fillSelect(selector,values){
  const el=$(selector);
  unique(values).forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;el.appendChild(o)});
}

function ideaCard(i,{latest=false,compact=false}={}){
  const p=dateParts(i.createdAt);
  return `<article class="idea-card ${latest?"latest":""}">
    <div class="card-kicker">#${i.number} · ${p.full}</div>
    <a class="card-title" href="${i.url}">${esc(i.title)}</a>
    ${compact?"":`<p class="card-why">${esc(i.why||"No context added yet.")}</p>`}
    <div class="pills">
      <span class="pill ${i.state==="open"?"pill-open":""}">${i.state}</span>
      <span class="pill ${i.stage.toLowerCase()==="promising"?"pill-promising":""}">${esc(i.stage)}</span>
      ${compact?"":`<span class="pill">${esc(i.category)}</span>`}
    </div>
  </article>`;
}

function renderJourney(){
  const root=$("#journeyView");
  if(!state.filtered.length){root.replaceChildren($("#emptyTemplate").content.cloneNode(true));return}
  const latest=state.ideas[0]?.number;
  let current="",html='<div class="feed">';
  [...state.filtered].reverse().forEach(i=>{
    const p=dateParts(i.createdAt);
    if(p.month!==current){html+=`<div class="month">${p.month.toUpperCase()}</div>`;current=p.month}
    const isLatest=i.number===latest;
    html+=`<article class="memo">
      <div class="memo-date"><strong>${p.day} ${p.mon}</strong>${p.year}</div>
      <div class="memo-body">
        <div class="memo-head">
          <a class="memo-title" href="${i.url}">${esc(i.title)}</a>
          ${isLatest?'<span class="latest-badge">Latest</span>':""}
        </div>
        <p class="memo-why">${esc(i.why||"No context added yet.")}</p>
        <div class="memo-foot">
          <span class="meta ${stateClass(i.state)}">${i.state}</span>
          <span class="meta ${stageClass(i.stage)}">${esc(i.stage)}</span>
          <span class="meta">${esc(i.category)}</span>
          <a class="open-link" href="${i.url}">Open →</a>
        </div>
      </div>
    </article>`;
  });
  root.innerHTML=html+"</div>";
}

function renderCards(){
  const root=$("#cardsView");
  if(!state.filtered.length){root.replaceChildren($("#emptyTemplate").content.cloneNode(true));return}
  const latest=state.ideas[0]?.number;
  root.innerHTML=`<div class="card-grid">${state.filtered.map(i=>ideaCard(i,{latest:i.number===latest})).join("")}</div>`;
}

function renderBoard(){
  const stages=["Inbox","Exploring","Promising","Project","Archived"];
  $("#boardView").innerHTML=`<div class="board">${stages.map(s=>{
    const ideas=state.filtered.filter(i=>i.stage.toLowerCase()===s.toLowerCase());
    return `<section class="board-column"><div class="board-head"><strong>${s}</strong><span class="board-count">${ideas.length}</span></div>${ideas.map(i=>ideaCard(i,{compact:true})).join("")||'<div class="card-kicker">No ideas</div>'}</section>`;
  }).join("")}</div>`;
}

function renderCalendar(){
  const root=$("#calendarView"),selected=state.calendarDate,year=selected.getFullYear(),month=selected.getMonth();
  const first=new Date(year,month,1),start=new Date(year,month,1-first.getDay());
  const days=Array.from({length:42},(_,n)=>{const d=new Date(start);d.setDate(start.getDate()+n);return d});
  const byDay=new Map();
  state.filtered.forEach(i=>{const d=new Date(i.createdAt),k=`${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;if(!byDay.has(k))byDay.set(k,[]);byDay.get(k).push(i)});
  const title=new Intl.DateTimeFormat("en",{month:"long",year:"numeric"}).format(selected);
  root.innerHTML=`<div class="calendar-shell"><div class="calendar-head"><h2>${title}</h2><div class="calendar-nav"><button id="prevMonth" aria-label="Previous month">‹</button><button id="nextMonth" aria-label="Next month">›</button></div></div><div class="calendar-weekdays">${["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map(x=>`<div>${x}</div>`).join("")}</div><div class="calendar-grid">${days.map(d=>{const k=`${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`,items=byDay.get(k)||[];return `<div class="calendar-day ${d.getMonth()!==month?"outside":""}"><div class="day-number">${d.getDate()}</div>${items.map(i=>`<a class="day-idea" href="${i.url}" title="${esc(i.title)}">${esc(i.title)}</a>`).join("")}</div>`}).join("")}</div></div>`;
  $("#prevMonth").onclick=()=>{state.calendarDate=new Date(year,month-1,1);renderCalendar()};
  $("#nextMonth").onclick=()=>{state.calendarDate=new Date(year,month+1,1);renderCalendar()};
}

function renderActive(){
  if(state.view==="journey")renderJourney();
  else if(state.view==="cards")renderCards();
  else if(state.view==="board")renderBoard();
  else renderCalendar();
}

function applyFilters(){
  const q=state.query.trim().toLowerCase();
  state.filtered=state.ideas.filter(i=>{
    const hay=[i.title,i.category,i.stage,i.why].join(" ").toLowerCase();
    return (!q||hay.includes(q))&&(state.category==="all"||i.category===state.category)&&(state.stage==="all"||i.stage===state.stage);
  });
  const active=[];
  if(state.query)active.push(`search “${esc(state.query)}”`);
  if(state.category!=="all")active.push(state.category);
  if(state.stage!=="all")active.push(state.stage);
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
    summary();
    $("#searchInput").oninput=e=>{state.query=e.target.value;applyFilters()};
    $("#categoryFilter").onchange=e=>{state.category=e.target.value;applyFilters()};
    $("#stageFilter").onchange=e=>{state.stage=e.target.value;applyFilters()};
    $$(".tab").forEach(x=>x.onclick=()=>setView(x.dataset.view));
    const requested=location.hash.slice(1);
    setView(["journey","cards","board","calendar"].includes(requested)?requested:"journey");
  }catch(error){
    console.error(error);
    $("#journeyView").innerHTML='<div class="empty"><strong>Could not load ideas.</strong><span>Refresh the page or check the sync workflow.</span></div>';
  }
}
init();