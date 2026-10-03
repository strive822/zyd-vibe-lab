import assert from "node:assert/strict";
import { test } from "node:test";
import { readCalculationResponse } from "../lib/calculation.ts";

const success = {
  c_model: { ndx: 0.5, csi500: 0.3, gold: 0.2 },
  rigorous_model: { ndx: 0.4, csi500: 0.35, gold: 0.25 },
  assets: ["ndx", "csi500", "gold"].map((key) => ({
    key, name: key, data_time: "2026-10-03 10:00 CST", source: "SYNTHETIC TEST ONLY",
  })),
};

test("preserves the backend's Chinese data failure reason", async () => {
  const detail = "当前无法完成计算：黄金最新报价获取失败。";
  await assert.rejects(readCalculationResponse(Response.json({ detail }, { status: 502 })),
    { message: detail });
});

test("HTML gateway failures retain the HTTP status", async () => {
  await assert.rejects(readCalculationResponse(new Response("<html>Unavailable</html>", { status: 503 })),
    { message: "请求失败（HTTP 503）" });
});

test("complete weights and asset metadata are accepted", async () => {
  assert.deepEqual(await readCalculationResponse(Response.json(success)), success);
});

test("incomplete, negative, or unnormalized weights never become displayed results", async () => {
  for (const weights of [{ ndx: 0.5 }, { ndx: -0.1, csi500: 0.5, gold: 0.6 },
    { ndx: 0.2, csi500: 0.2, gold: 0.2 }]) {
    await assert.rejects(readCalculationResponse(Response.json({ ...success, c_model: weights })));
  }
});

test("missing or duplicated asset metadata is rejected", async () => {
  for (const assets of [[], [success.assets[0], success.assets[0], success.assets[2]]]) {
    await assert.rejects(readCalculationResponse(Response.json({ ...success, assets })));
  }
});
