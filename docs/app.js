const state={ideas:[],filtered:[],view:"journey",query:"",category:"all",stage:"all",calendarDate:new Date()};
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const esc=(v="")=>v.replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
const fmt=iso=>new Intl.DateTimeFormat("en",{day:"numeric",month:"short",year:"numeric"}).format(new Date(iso));
const monthLabel=iso=>new Intl.DateTimeFormat("en",{month:"short",year:"numeric"}).format(new Date(iso)).toUpperCase();
const stageClass=s=>s.toLowerCase()==="promising"?"pill-promising":"";
const stateClass=s=>s==="open"?"pill-open":"";

function card(idea,{latest=false,compact=false}={}){
  return `<article class="idea-card ${latest?"latest":""}">
    <div class="card-kicker">#${idea.number} · ${fmt(idea.createdAt)}</div>
    <a class="card-title" href="${idea.url}">${esc(idea.title)}</a>
    <div class="pills">
      <span class="pill ${stateClass(idea.state)}">${idea.state}</span>
      <span class="pill ${stageClass(idea.stage)}">${esc(idea.stage)}</span>
      ${compact?"":`<span class="pill">${esc(idea.category)}</span>`}
    </div>
  </article>`;
}
function emptyNode(){return $("#emptyTemplate").content.cloneNode(true)}
function unique(values){return [...new Set(values.filter(Boolean))].sort()}
function fillSelect(selector,values){
  const el=$(selector);
  unique(values).forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;el.appendChild(o)});
}
function renderStats(){
  const total=state.ideas.length;
  const open=state.ideas.filter(x=>x.state==="open").length;
  const promising=state.ideas.filter(x=>x.stage.toLowerCase()==="promising").length;
  const projects=state.ideas.filter(x=>x.stage.toLowerCase()==="project").length;
  $("#stats").innerHTML=[
    ["Ideas",total,"captured"],
    ["Open",open,"active"],
    ["Promising",promising,"worth pushing"],
    ["Projects",projects,"promoted"]
  ].map(([l,v,n])=>`<div class="stat"><span class="stat-label">${l}</span><strong class="stat-value">${v}</strong><small>${n}</small></div>`).join("");
}
function renderOverview(){
  const latest=state.ideas[0];
  $("#latestSpark").innerHTML=latest?`<div class="panel-label">Latest Spark</div>
    <a class="spotlight-title" href="${latest.url}">${esc(latest.title)}</a>
    <div class="meta-row"><span>#${latest.number}</span><span>·</span><span>${fmt(latest.createdAt)}</span><span class="pill ${stageClass(latest.stage)}">${esc(latest.stage)}</span><span class="pill">${esc(latest.category)}</span></div>`
    :'<div class="panel-label">Latest Spark</div><div class="spotlight-title">Waiting for the first idea.</div>';

  const cutoff=Date.now()-30*86400000;
  const stale=state.ideas.filter(x=>x.state==="open"&&["inbox","exploring"].includes(x.stage.toLowerCase())&&new Date(x.updatedAt).getTime()<cutoff);
  $("#reviewPanel").innerHTML=`<div class="panel-label">Worth Revisiting</div><div class="review-number">${stale.length}</div><div class="review-copy">${stale.length?"older ideas waiting for another look.":"Nothing is gathering dust."}</div><button id="reviewIdeas" class="inline-link" type="button">Browse inbox →</button>`;
  $("#reviewIdeas").onclick=()=>{$("#stageFilter").value="Inbox";state.stage="Inbox";applyFilters();setView("cards");$(".workspace").scrollIntoView()};
}
function applyFilters(){
  const q=state.query.trim().toLowerCase();
  state.filtered=state.ideas.filter(i=>{
    const text=[i.title,i.category,i.stage,i.why].join(" ").toLowerCase();
    return (!q||text.includes(q))&&(state.category==="all"||i.category===state.category)&&(state.stage==="all"||i.stage===state.stage);
  });
  const active=[];
  if(state.query)active.push(`search “${esc(state.query)}”`);
  if(state.category!=="all")active.push(state.category);
  if(state.stage!=="all")active.push(state.stage);
  $("#activeFilters").hidden=!active.length;
  $("#activeFilters").innerHTML=active.length?`${state.filtered.length} result${state.filtered.length===1?"":"s"} · ${active.join(" · ")}`:"";
  renderActive();
}
function renderJourney(){
  const root=$("#journeyView");
  if(!state.filtered.length){root.replaceChildren(emptyNode());return}
  const latest=state.ideas[0]?.number;
  let current="",html='<div class="journey">';
  [...state.filtered].reverse().forEach(i=>{
    const m=monthLabel(i.createdAt);
    if(m!==current){html+=`<div class="month-marker">${m}</div>`;current=m}
    const isLatest=i.number===latest;
    html+=`<div class="journey-item">${card(i,{latest:isLatest})}<span class="journey-node ${isLatest?"latest":""}"></span></div>`;
  });
  root.innerHTML=html+"</div>";
}
function renderCards(){
  const root=$("#cardsView");
  if(!state.filtered.length){root.replaceChildren(emptyNode());return}
  const latest=state.ideas[0]?.number;
  root.innerHTML=`<div class="card-grid">${state.filtered.map(i=>card(i,{latest:i.number===latest})).join("")}</div>`;
}
function renderBoard(){
  const stages=["Inbox","Exploring","Promising","Project","Archived"];
  $("#boardView").innerHTML=`<div class="board">${stages.map(s=>{
    const ideas=state.filtered.filter(i=>i.stage.toLowerCase()===s.toLowerCase());
    return `<section class="board-column"><div class="board-head"><strong>${s}</strong><span class="board-count">${ideas.length}</span></div>${ideas.map(i=>card(i,{compact:true})).join("")||'<div class="review-copy">No ideas</div>'}</section>`;
  }).join("")}</div>`;
}
function renderCalendar(){
  const root=$("#calendarView"),selected=state.calendarDate,year=selected.getFullYear(),month=selected.getMonth();
  const first=new Date(year,month,1),start=new Date(year,month,1-first.getDay());
  const days=Array.from({length:42},(_,n)=>{const d=new Date(start);d.setDate(start.getDate()+n);return d});
  const byDay=new Map();
  state.filtered.forEach(i=>{const d=new Date(i.createdAt),k=`${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;if(!byDay.has(k))byDay.set(k,[]);byDay.get(k).push(i)});
  const title=new Intl.DateTimeFormat("en",{month:"long",year:"numeric"}).format(selected);
  root.innerHTML=`<div class="calendar-shell"><div class="calendar-head"><h2>${title}</h2><div class="calendar-nav"><button id="prevMonth">‹</button><button id="nextMonth">›</button></div></div><div class="calendar-weekdays">${["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map(x=>`<div>${x}</div>`).join("")}</div><div class="calendar-grid">${days.map(d=>{const k=`${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`,items=byDay.get(k)||[];return `<div class="calendar-day ${d.getMonth()!==month?"outside":""}"><div class="day-number">${d.getDate()}</div>${items.map(i=>`<a class="day-idea" href="${i.url}" title="${esc(i.title)}">${esc(i.title)}</a>`).join("")}</div>`}).join("")}</div></div>`;
  $("#prevMonth").onclick=()=>{state.calendarDate=new Date(year,month-1,1);renderCalendar()};
  $("#nextMonth").onclick=()=>{state.calendarDate=new Date(year,month+1,1);renderCalendar()};
}
function renderActive(){
  if(state.view==="journey")renderJourney();
  else if(state.view==="cards")renderCards();
  else if(state.view==="board")renderBoard();
  else renderCalendar();
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
    document.documentElement.dataset.theme=next;localStorage.setItem("brain-dump-theme",next);
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
    renderStats();renderOverview();
    $("#searchInput").oninput=e=>{state.query=e.target.value;applyFilters()};
    $("#categoryFilter").onchange=e=>{state.category=e.target.value;applyFilters()};
    $("#stageFilter").onchange=e=>{state.stage=e.target.value;applyFilters()};
    $$(".tab").forEach(x=>x.onclick=()=>setView(x.dataset.view));
    const requested=location.hash.slice(1);
    setView(["journey","cards","board","calendar"].includes(requested)?requested:"journey");
  }catch(err){
    console.error(err);
    $("#journeyView").innerHTML='<div class="empty"><strong>Could not load ideas.</strong><span>Refresh or check the repository workflow.</span></div>';
  }
}
init();