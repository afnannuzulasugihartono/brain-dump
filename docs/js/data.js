const ALLOWED_ACTIONS = new Set(["keep-exploring", "revisit", "promote-candidate", "consider-archive"]);
const ALLOWED_DEPTHS = new Set(["brief", "detailed"]);

function validInsight(item) {
  return item &&
    Number.isInteger(item.issueNumber) &&
    typeof item.evaluatedAt === "string" && !Number.isNaN(Date.parse(item.evaluatedAt)) &&
    typeof item.summary === "string" && item.summary.trim().length > 0 &&
    ALLOWED_ACTIONS.has(item.suggestedAction) &&
    Array.isArray(item.signals) && item.signals.every(signal => typeof signal === "string") &&
    typeof item.confidence === "number" && Number.isFinite(item.confidence) && item.confidence >= 0 && item.confidence <= 1 &&
    ALLOWED_DEPTHS.has(item.depth) &&
    ["strength", "risk", "nextStep"].every(field => item[field] === undefined || item[field] === null || typeof item[field] === "string");
}

export async function loadBrainDumpData() {
  const response = await fetch("./data/ideas.json", {cache:"no-store"});
  if (!response.ok) throw new Error(`ideas:${response.status}`);
  const canonical = await response.json();
  if (!Array.isArray(canonical.ideas)) throw new Error("ideas:invalid");

  let insights = [];
  try {
    const optional = await fetch("./data/ai-insights.json", {cache:"no-store"});
    if (optional.ok) {
      const document = await optional.json();
      if (document?.source === "AI review" && Array.isArray(document.insights)) {
        insights = document.insights.filter(validInsight);
      }
    }
  } catch {
    insights = [];
  }

  return {
    ideas:[...canonical.ideas].sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt)),
    insightsByIssue:new Map(insights.map(item => [item.issueNumber, item])),
  };
}
