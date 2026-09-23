import {needsReview, scoreIdea, selectRediscovery} from "./scoring.js";
import {esc, tag} from "./views.js";

const actionLabel = value => ({
  "keep-exploring":"Keep exploring",
  "revisit":"Revisit",
  "promote-candidate":"Promote candidate",
  "consider-archive":"Consider archive",
}[value] || "Review");

function reviewCard(idea, extra, insight) {
  const action = insight ? actionLabel(insight.suggestedAction) : "Review";
  return `<article class="review-card">
    <a class="review-title" href="${esc(idea.url)}">${esc(idea.title)}</a>
    <p class="review-reason">${esc(extra)}</p>
    <div class="review-meta"><span>${tag(idea.stage)}</span><span>${tag(idea.category)}</span></div>
    ${insight ? `<div class="ai-insight">
      <span class="ai-label">AI insight</span>
      <p>${esc(insight.summary)}</p>
      <span class="ai-action">Suggested: ${esc(action)}</span>
      ${insight.depth === "detailed" ? `<details><summary>More context</summary>
        ${insight.strength ? `<p><strong>Strength:</strong> ${esc(insight.strength)}</p>` : ""}
        ${insight.risk ? `<p><strong>Risk:</strong> ${esc(insight.risk)}</p>` : ""}
        ${insight.nextStep ? `<p><strong>Next:</strong> ${esc(insight.nextStep)}</p>` : ""}
      </details>` : ""}
    </div>` : ""}
    <a class="review-link" href="${esc(idea.url)}">${esc(action)} in GitHub →</a>
  </article>`;
}

export function renderReview(root, ideas, insightsByIssue, now=new Date()) {
  const due = ideas
    .map(idea => ({idea, review:needsReview(idea, now)}))
    .filter(item => item.review.due)
    .sort((a,b) => b.review.daysUntouched - a.review.daysUntouched);

  const worth = ideas
    .map(idea => ({idea, result:scoreIdea(idea, now)}))
    .filter(item => item.result.eligible && item.result.score >= 6)
    .sort((a,b) => b.result.score - a.result.score);

  const rediscovered = selectRediscovery(ideas, now);
  const section = (title, subtitle, body) => `<section class="review-section"><header><h2>${title}</h2><p>${subtitle}</p></header>${body || '<p class="review-empty">Nothing here right now.</p>'}</section>`;

  root.innerHTML =
    section("Needs review", "Ideas that have been sitting for a while.", due.map(({idea,review}) => reviewCard(idea, `Untouched for ${review.daysUntouched} days · threshold ${review.threshold} days`, insightsByIssue.get(idea.number))).join("")) +
    section("Worth revisiting", "Ideas with useful deterministic signals.", worth.map(({idea,result}) => reviewCard(idea, `Score ${result.score} · ${result.signals.join(" · ")}`, insightsByIssue.get(idea.number))).join("")) +
    section("Rediscover", "One older idea for today.", rediscovered ? reviewCard(rediscovered, "A deterministic daily rediscovery.", insightsByIssue.get(rediscovered.number)) : "");
}
