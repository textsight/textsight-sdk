import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from textsight import (
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    TextSight,
)

CALLS = []
PLAN = {}  # path -> list of (status, body) to return in order


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.endswith("/slow"):
            import time as _t
            _t.sleep(1.5)
        if self.path.endswith("/html"):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<html>oops</html>")
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        CALLS.append((self.path, dict(self.headers), body))
        queue = PLAN.get(self.path) or [(200, {"ok": True})]
        status, resp = queue.pop(0) if len(queue) > 1 else queue[0]
        data = json.dumps(resp).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        if status == 429:
            self.send_header("Retry-After", "0")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


class ClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}/v2"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        CALLS.clear()
        PLAN.clear()
        self.ts = TextSight("sk_test_123", base_url=self.base, max_retries=2)

    def test_detect_sends_auth_and_text(self):
        PLAN["/v2/detect"] = [(200, {"verdict": "ai", "humanization_score": 12})]
        out = self.ts.detect("hello world")
        self.assertEqual(out["verdict"], "ai")
        path, headers, body = CALLS[0]
        self.assertEqual(path, "/v2/detect")
        self.assertEqual(headers["Authorization"], "Bearer sk_test_123")
        self.assertEqual(body, {"text": "hello world"})

    def test_rewrite_options(self):
        PLAN["/v2/rewrite"] = [(200, {"rewritten": "hi"})]
        self.ts.rewrite("text", tone="academic", strength=5, preserve=["Smith 2020"])
        self.assertEqual(
            CALLS[0][2],
            {"text": "text", "tone": "academic", "strength": 5, "preserve": ["Smith 2020"]},
        )

    def test_score(self):
        PLAN["/v2/score"] = [(200, {"humanization_score": 90})]
        self.assertEqual(self.ts.score("x")["humanization_score"], 90)

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.ts.detect("   ")
        with self.assertRaises(ValueError):
            self.ts.rewrite("x", tone="pirate")
        with self.assertRaises(ValueError):
            self.ts.rewrite("x", strength=9)
        with self.assertRaises(ValueError):
            self.ts.detect("a" * 50_001)
        self.assertEqual(CALLS, [])

    def test_errors_mapped(self):
        PLAN["/v2/detect"] = [(401, {"error": {"code": "unauthorized", "message": "bad key"}})]
        with self.assertRaises(AuthenticationError) as c:
            self.ts.detect("x")
        self.assertEqual(c.exception.status, 401)
        self.assertEqual(c.exception.code, "unauthorized")
        PLAN["/v2/detect"] = [(403, {"error": "quota_exhausted"})]
        with self.assertRaises(PermissionDeniedError):
            self.ts.detect("x")

    def test_retries_then_succeeds(self):
        PLAN["/v2/detect"] = [(429, {"error": "rate_limited"}), (200, {"verdict": "human"})]
        self.assertEqual(self.ts.detect("x")["verdict"], "human")
        self.assertEqual(len(CALLS), 2)

    def test_retry_gives_up(self):
        PLAN["/v2/detect"] = [(429, {"error": "rate_limited"})]
        with self.assertRaises(RateLimitError):
            self.ts.detect("x")
        self.assertEqual(len(CALLS), 3)

    def test_timeout_is_wrapped_and_retried(self):
        from textsight import TextSightError
        ts = TextSight("k", base_url=self.base, timeout=0.3, max_retries=1)
        with self.assertRaises(TextSightError):
            ts._post("/slow", {"text": "x"})

    def test_non_json_success_raises(self):
        from textsight import APIError
        with self.assertRaises(APIError):
            self.ts._post("/html", {"text": "x"})

    def test_preserve_string_not_split(self):
        self.ts.rewrite("x", preserve="ACME Inc.")
        self.assertEqual(CALLS[0][2]["preserve"], ["ACME Inc."])

    def test_bool_strength_rejected(self):
        with self.assertRaises(ValueError):
            self.ts.rewrite("x", strength=True)

    def test_missing_key(self):
        import os
        old = os.environ.pop("TEXTSIGHT_API_KEY", None)
        try:
            with self.assertRaises(AuthenticationError):
                TextSight()
        finally:
            if old:
                os.environ["TEXTSIGHT_API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
