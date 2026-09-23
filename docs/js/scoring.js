const DAY_MS = 86_400_000;
const REVIEW_THRESHOLDS = {inbox:7, exploring:14, promising:30};
const RICH_CONTEXT_CHARS = 240;

const utcDay = value => Date.UTC(value.getUTCFullYear(), value.getUTCMonth(), value.getUTCDate());

export function ageDays(fromIso, now = new Date()) {
  const from = new Date(fromIso);
  return Math.floor((now.getTime() - from.getTime()) / DAY_MS);
}

function isSameUtcDay(iso, now = new Date()) {
  const value = new Date(iso);
  return utcDay(value) === utcDay(now);
}

export function needsReview(idea, now = new Date()) {
  const threshold = REVIEW_THRESHOLDS[String(idea.stage || "").toLowerCase()] ?? null;
  const daysUntouched = ageDays(idea.updatedAt, now);
  return {due: threshold !== null && daysUntouched >= threshold, daysUntouched, threshold};
}

export function scoreIdea(idea, now = new Date()) {
  if (String(idea.stage || "").toLowerCase() === "archived") return {score:0, signals:[], eligible:false};
  let score = 0;
  const signals = [];
  const stage = String(idea.stage || "").toLowerCase();
  if (stage === "promising") { score += 3; signals.push("promising"); }
  if (String(idea.aiNotes || "").trim()) { score += 2; signals.push("ai-notes"); }
  if (String(idea.why || "").trim()) { score += 1; signals.push("context"); }
  const richLength = (String(idea.idea || "") + " " + String(idea.why || "")).trim().length;
  if (richLength >= RICH_CONTEXT_CHARS) { score += 1; signals.push("rich-context"); }
  if (idea.state === "open") { score += 1; signals.push("open"); }
  if (ageDays(idea.createdAt, now) > 14) { score += 1; signals.push("older-than-14-days"); }
  return {score, signals, eligible:true};
}

export function selectRediscovery(ideas, now = new Date()) {
  const candidates = ideas
    .filter(idea => String(idea.stage || "").toLowerCase() !== "archived")
    .filter(idea => ageDays(idea.createdAt, now) >= 7)
    .filter(idea => !isSameUtcDay(idea.updatedAt, now))
    .sort((a,b) => a.number - b.number);
  if (!candidates.length) return null;
  const key = [now.getUTCFullYear(), String(now.getUTCMonth()+1).padStart(2,"0"), String(now.getUTCDate()).padStart(2,"0")].join("-");
  const checksum = [...key].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return candidates[checksum % candidates.length];
}
