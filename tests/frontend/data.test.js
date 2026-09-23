import test from "node:test";
import assert from "node:assert/strict";

async function dataModule() {
  try { return await import("../../docs/js/data.js"); }
  catch { return null; }
}

test("data module exposes loader", async () => {
  const mod = await dataModule();
  assert.equal(typeof mod?.loadBrainDumpData, "function");
});

test("missing AI sidecar does not block canonical ideas", async () => {
  const {loadBrainDumpData} = await dataModule() ?? {};
  assert.equal(typeof loadBrainDumpData, "function");
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async url => {
    if (String(url).includes("ideas.json")) return {ok:true, json:async () => ({ideas:[{number:1,title:"One",createdAt:"2026-09-01T00:00:00Z"}]})};
    throw new Error("sidecar unavailable");
  };
  try {
    const result = await loadBrainDumpData();
    assert.equal(result.ideas.length, 1);
    assert.equal(result.insightsByIssue.size, 0);
  } finally { globalThis.fetch = originalFetch; }
});

test("invalid AI sidecar shape degrades to no insights", async () => {
  const {loadBrainDumpData} = await dataModule() ?? {};
  assert.equal(typeof loadBrainDumpData, "function");
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async url => {
    if (String(url).includes("ideas.json")) return {ok:true, json:async () => ({ideas:[{number:1,title:"One",createdAt:"2026-09-01T00:00:00Z"}]})};
    return {ok:true, json:async () => ({insights:"invalid"})};
  };
  try {
    const result = await loadBrainDumpData();
    assert.equal(result.insightsByIssue.size, 0);
  } finally { globalThis.fetch = originalFetch; }
});
