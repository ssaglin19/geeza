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
        for text in ("", "   ", None, [], "```json\n\n```"):
            with self.subTest(text=text):
                c = NebiusClient(api_key="k", opener=opener_ok(text)[0])
                with patch("sys.stderr", new_callable=io.StringIO) as log:
                    c.complete([{"role": "user", "content": "hi"}])
                self.assertEqual(c.status()["exception_class"], "ValueError")
                self.assertTrue(c.used_fallback)
                self.assertEqual(log.getvalue(), "Geeza model fallback exception_class=ValueError\n")

    def test_fenced_json_content_is_unwrapped(self):
        content = '{"tool": "explain_bill"}'
        c = NebiusClient(api_key="k", opener=opener_ok("```json\n" + content + "\n```")[0])
        self.assertEqual(json.loads(c.complete([])), {"tool": "explain_bill"})
        self.assertFalse(c.used_fallback)

    def test_single_fenced_envelope_is_parsed(self):
        envelope = json.dumps({"choices": [{"message": {"content": "hello"}}]})
        c = NebiusClient(api_key="k", opener=lambda *a, **kw: FakeResp(("```json\n" + envelope + "\n```").encode()))
        self.assertEqual(c.complete([]), "hello")
        self.assertFalse(c.used_fallback)

    def test_non_json_or_malformed_envelope_falls_back_safely(self):
        for payload in ("secret response body", "", "null", "[]", '{}',
                        '{"choices": null}', '{"choices": [null]}',
                        '{"choices": [{"message": null}]}',
                        'prose {"choices": []}', '```json\n{}\n``` trailing prose'):
            with self.subTest(payload=payload):
                c = NebiusClient(api_key="secret-key", opener=lambda *a, **kw: FakeResp(payload.encode()))
                with patch("sys.stderr", new_callable=io.StringIO) as log:
                    c.complete([])
                self.assertTrue(c.used_fallback)
                self.assertEqual(c.status()["exception_class"], "ValueError")
                self.assertEqual(log.getvalue(), "Geeza model fallback exception_class=ValueError\n")
                self.assertNotIn("secret", json.dumps(c.status()) + log.getvalue())

    def test_non_json_assistant_prose_remains_valid(self):
        c = NebiusClient(api_key="k", opener=opener_ok("Your bill includes an adjustment.")[0])
        self.assertEqual(c.complete([]), "Your bill includes an adjustment.")
        self.assertFalse(c.used_fallback)

    def test_embedded_fence_is_not_extracted(self):
        text = 'Please use this: ```json\n{"tool": "pay_bill"}\n```'
        c = NebiusClient(api_key="k", opener=opener_ok(text)[0])
        self.assertEqual(c.complete([]), text)


if __name__ == "__main__":
    unittest.main()
