import test from "node:test";
import assert from "node:assert/strict";

async function scoring() {
  try {
    return await import("../../docs/js/scoring.js");
  } catch {
    return null;
  }
}

const now = new Date("2026-09-23T12:00:00Z");
const idea = (overrides={}) => ({
  number:10, title:"Example", state:"open", stage:"Inbox", category:"Other",
  idea:"A useful idea with enough context to explain the concept and its intended use clearly.",
  why:"It solves a recurring problem and has a clear motivation.",
  aiNotes:"",
  createdAt:"2026-09-01T12:00:00Z",
  updatedAt:"2026-09-16T12:00:00Z",
  ...overrides,
});

test("scoring module exposes review functions", async () => {
  const mod = await scoring();
  assert.equal(typeof mod?.needsReview, "function");
  assert.equal(typeof mod?.scoreIdea, "function");
  assert.equal(typeof mod?.selectRediscovery, "function");
});

test("thresholds are inclusive and stage specific", async () => {
  const {needsReview} = await scoring() ?? {};
  assert.equal(typeof needsReview, "function");
  assert.equal(needsReview(idea(), now).due, true);
  assert.equal(needsReview(idea({stage:"Exploring",updatedAt:"2026-09-09T12:00:00Z"}), now).due, true);
  assert.equal(needsReview(idea({stage:"Promising",updatedAt:"2026-08-24T12:00:00Z"}), now).due, true);
  assert.equal(needsReview(idea({stage:"Project"}), now).due, false);
  assert.equal(needsReview(idea({stage:"Archived"}), now).due, false);
});

test("score exposes deterministic signals", async () => {
  const {scoreIdea} = await scoring() ?? {};
  assert.equal(typeof scoreIdea, "function");
  const result = scoreIdea(idea({stage:"Promising",aiNotes:"Compared several approaches."}), now);
  assert.ok(result.score >= 6);
  assert.ok(result.signals.includes("promising"));
  assert.ok(result.signals.includes("ai-notes"));
});

test("empty rediscovery returns null", async () => {
  const {selectRediscovery} = await scoring() ?? {};
  assert.equal(typeof selectRediscovery, "function");
  assert.equal(selectRediscovery([idea({stage:"Archived"})], now), null);
});

test("rediscovery is stable for the same UTC day", async () => {
  const {selectRediscovery} = await scoring() ?? {};
  assert.equal(typeof selectRediscovery, "function");
  const ideas = [idea({number:1}), idea({number:2}), idea({number:3})];
  assert.equal(selectRediscovery(ideas, now)?.number, selectRediscovery(ideas, now)?.number);
});
