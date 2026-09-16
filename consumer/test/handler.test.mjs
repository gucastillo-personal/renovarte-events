import { test } from "node:test";
import assert from "node:assert/strict";
import { handler } from "../src/handler.mjs";

const SAMPLE_PAYLOAD = {
  generated_at: "2026-09-16T09:00:00Z",
  summary: { added: 1, removed: 0, price_up: 0, price_down: 0, total: 1 },
  changes: [{ kind: "added", id: "1", nombre: "A", old_price: null, new_price: 10 }],
};

function record(body, messageId = "msg-1") {
  return { messageId, body: JSON.stringify(body) };
}

test("procesa un batch exitoso sin fallas", async (t) => {
  process.env.DISCORD_WEBHOOK_URL = "https://discord.test/webhook";
  t.mock.method(globalThis, "fetch", async () => ({ ok: true, status: 204 }));

  const result = await handler({ Records: [record(SAMPLE_PAYLOAD)] });

  assert.deepEqual(result.batchItemFailures, []);
});

test("Discord devuelve error -> el mensaje cae en batchItemFailures", async (t) => {
  process.env.DISCORD_WEBHOOK_URL = "https://discord.test/webhook";
  t.mock.method(globalThis, "fetch", async () => ({ ok: false, status: 500 }));

  const result = await handler({ Records: [record(SAMPLE_PAYLOAD, "msg-2")] });

  assert.deepEqual(result.batchItemFailures, [{ itemIdentifier: "msg-2" }]);
});

test("un record con JSON corrupto no tumba el resto del batch", async (t) => {
  process.env.DISCORD_WEBHOOK_URL = "https://discord.test/webhook";
  t.mock.method(globalThis, "fetch", async () => ({ ok: true, status: 204 }));

  const badRecord = { messageId: "msg-bad", body: "{not json" };
  const goodRecord = record(SAMPLE_PAYLOAD, "msg-good");

  const result = await handler({ Records: [badRecord, goodRecord] });

  assert.deepEqual(result.batchItemFailures, [{ itemIdentifier: "msg-bad" }]);
});
