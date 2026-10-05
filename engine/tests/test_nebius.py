import io
import json
import sys
import unittest
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

    def test_empty_completion_falls_back(self):
        op, _ = opener_ok("   ")
        c = NebiusClient(api_key="k", opener=op)
        c.complete([{"role": "user", "content": "hi"}])
        self.assertTrue(c.used_fallback)


if __name__ == "__main__":
    unittest.main()
