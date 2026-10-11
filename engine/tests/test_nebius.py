import io
import json
import sys
import unittest
import urllib.error
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from boosh_flow.nebius import BASE_URL, MODELS, NebiusClient


class FakeResp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False


def opener_ok(text):
    seen = {}
    def op(req, timeout=None):
        seen["url"], seen["auth"], seen["body"] = req.full_url, req.get_header("Authorization"), json.loads(req.data)
        return FakeResp(json.dumps({"choices": [{"message": {"content": text}}]}).encode())
    return op, seen


class TestClient(unittest.TestCase):
    def test_no_key_uses_mock(self):
        c = NebiusClient(api_key="")
        out = c.complete([{"role": "user", "content": "hi"}])
        self.assertTrue(c.used_fallback)
        self.assertIn("mock", out)

    def test_live_call_shape(self):
        op, seen = opener_ok(" hello ")
        c = NebiusClient(api_key="k", opener=op)
        self.assertEqual(c.complete([{"role": "user", "content": "hi"}]), "hello")
        self.assertFalse(c.used_fallback)
        self.assertEqual(seen["url"], BASE_URL + "chat/completions")
        self.assertEqual(seen["auth"], "Bearer k")
        self.assertEqual(seen["body"]["model"], MODELS["fast"])

    def test_failure_falls_back_without_leaking_key(self):
        def boom(req, timeout=None): raise OSError("secret-k in message")
        c = NebiusClient(api_key="secret-k", opener=boom)
        c.complete([{"role": "user", "content": "hi"}])
        self.assertTrue(c.used_fallback)
        self.assertNotIn("secret-k", c.last_error or "")

    def test_status_does_not_call_model_or_claim_healthy_on_start(self):
        def forbidden(*args, **kwargs): raise AssertionError("status called model")
        c = NebiusClient(api_key="secret", opener=forbidden)
        self.assertEqual(c.status(), {"configured": True, "state": "not_attempted", "exception_class": None})
        self.assertNotIn("secret", json.dumps(c.status()))

    def test_exception_class_only_in_status_and_log(self):
        def fail(req, timeout=None):
            raise urllib.error.HTTPError("https://secret-url", 401, "secret error body", {"Authorization": "secret"}, None)
        c = NebiusClient(api_key="secret-key", opener=fail)
        with patch("sys.stderr", new_callable=io.StringIO) as log:
            c.complete([{"role": "user", "content": "hi"}])
        self.assertEqual(c.status(), {"configured": True, "state": "fallback", "exception_class": "HTTPError"})
        self.assertEqual(log.getvalue(), "Geeza model fallback exception_class=HTTPError\n")
        self.assertNotIn("secret", json.dumps(c.status()) + log.getvalue())

    def test_success_clears_prior_error(self):
        c = NebiusClient(api_key="k", opener=lambda *a, **kw: (_ for _ in ()).throw(OSError("private")))
        with patch("sys.stderr", new_callable=io.StringIO):
            c.complete([{"role": "user", "content": "hi"}])
        c._open = opener_ok("hello")[0]
        c.complete([{"role": "user", "content": "hi"}])
        self.assertEqual(c.status(), {"configured": True, "state": "ok", "exception_class": None})

    def test_empty_completion_falls_back(self):
        op, _ = opener_ok("   ")
        c = NebiusClient(api_key="k", opener=op)
        c.complete([{"role": "user", "content": "hi"}])
        self.assertTrue(c.used_fallback)


if __name__ == "__main__":
    unittest.main()
