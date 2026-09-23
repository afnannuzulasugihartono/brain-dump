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
      if (Array.isArray(document.insights)) insights = document.insights;
    }
  } catch {
    insights = [];
  }

  return {
    ideas:[...canonical.ideas].sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt)),
    insightsByIssue:new Map(insights.map(item => [item.issueNumber, item])),
  };
}
