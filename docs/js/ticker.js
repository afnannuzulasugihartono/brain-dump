import {needsReview} from "./scoring.js";
import {esc} from "./views.js";

export function buildTickerItems(ideas, insightsByIssue, now=new Date()) {
  const open = ideas.filter(idea => idea.state === "open").length;
  const due = ideas.filter(idea => needsReview(idea, now).due).length;
  const items = [
    `${ideas.length} idea${ideas.length === 1 ? "" : "s"}`,
    `${open} open`,
    `${due} review due`,
    "GitHub synced",
  ];
  ideas.slice(0, 4).forEach(idea => {
    items.push(idea.title);
    items.push(`#${String(idea.stage || "").toLowerCase().replace(/\s+/g, "-")}`);
  });
  if (insightsByIssue.size) items.push(`${insightsByIssue.size} AI insight${insightsByIssue.size === 1 ? "" : "s"}`);
  return items;
}

export function renderTicker(root, items) {
  const content = items.map(item => `<span class="ticker-item">${esc(item)}</span>`).join('<span aria-hidden="true"> · </span>');
  root.innerHTML = `
    <span class="ticker-sr">Brain Dump status: ${items.map(esc).join(", ")}</span>
    <div class="ticker-viewport" aria-hidden="true">
      <div class="ticker-track"><span>${content}</span><span>${content}</span></div>
    </div>`;
}
