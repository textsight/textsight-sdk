import { test, before, after, beforeEach } from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { TextSight, TextSightError } from "../index.js";

const calls = [];
const plan = {};
let server, base;

before(async () => {
  server = http.createServer((req, res) => {
    let raw = "";
    req.on("data", (c) => (raw += c));
    req.on("end", () => {
      calls.push({ path: req.url, headers: req.headers, body: JSON.parse(raw) });
      if (req.url.includes("/html")) return res.writeHead(200).end("<html>oops</html>");
      const q = plan[req.url] || [[200, { ok: true }]];
      const [status, body] = q.length > 1 ? q.shift() : q[0];
      const headers = { "Content-Type": "application/json" };
      if (status === 429) headers["Retry-After"] = "0";
      res.writeHead(status, headers).end(JSON.stringify(body));
    });
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  base = `http://127.0.0.1:${server.address().port}/v2`;
});
after(() => server.close());
beforeEach(() => {
  calls.length = 0;
  for (const k of Object.keys(plan)) delete plan[k];
});

const client = () => new TextSight({ apiKey: "sk_test_123", baseUrl: base });

test("detect sends auth and text", async () => {
  plan["/v2/detect"] = [[200, { verdict: "ai" }]];
  const out = await client().detect("hello");
  assert.equal(out.verdict, "ai");
  assert.equal(calls[0].headers.authorization, "Bearer sk_test_123");
  assert.deepEqual(calls[0].body, { text: "hello" });
});

test("rewrite options", async () => {
  await client().rewrite("t", { tone: "email", strength: 2, preserve: ["ACME"] });
  assert.equal(calls[0].path, "/v2/rewrite");
  assert.deepEqual(calls[0].body, { text: "t", tone: "email", strength: 2, preserve: ["ACME"] });
});

test("validation", () => {
  assert.throws(() => client().detect(""), TypeError);
  assert.throws(() => client().rewrite("x", { tone: "pirate" }), RangeError);
  assert.throws(() => client().rewrite("x", { strength: 7 }), RangeError);
  assert.equal(calls.length, 0);
});

test("errors mapped", async () => {
  plan["/v2/detect"] = [[401, { error: { code: "unauthorized", message: "bad key" } }]];
  await assert.rejects(client().detect("x"), (e) => {
    assert.ok(e instanceof TextSightError);
    assert.equal(e.status, 401);
    assert.equal(e.code, "unauthorized");
    assert.equal(e.message, "bad key");
    return true;
  });
});

test("retries 429 then succeeds", async () => {
  plan["/v2/score"] = [[429, { error: "rate_limited" }], [200, { humanization_score: 88 }]];
  const out = await client().score("x");
  assert.equal(out.humanization_score, 88);
  assert.equal(calls.length, 2);
});

test("missing key throws", () => {
  const old = process.env.TEXTSIGHT_API_KEY;
  delete process.env.TEXTSIGHT_API_KEY;
  assert.throws(() => new TextSight(), TextSightError);
  if (old) process.env.TEXTSIGHT_API_KEY = old;
});

test("preserve string is not split into characters", async () => {
  await client().rewrite("x", { preserve: "ACME Inc." });
  assert.deepEqual(calls[0].body.preserve, ["ACME Inc."]);
});

test("non-JSON success body throws", async () => {
  const ts = new TextSight({ apiKey: "k", baseUrl: base.replace("/v2", "/v2/html"), maxRetries: 0 });
  await assert.rejects(ts.detect("x"), TextSightError);
});
