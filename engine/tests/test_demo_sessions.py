"""Offline HTTP regressions: demo visitors cannot share approvals or notes."""
import http.client
import json
import threading
import unittest
from http.server import HTTPServer
from gateway.assistant import Assistant
from gateway.server import BooshGateway
from boosh_flow.nebius import MockClient


class DemoSessions(unittest.TestCase):
    def setUp(self):
        self.old = BooshGateway.config.copy()
        self.assistant = Assistant(MockClient())
        BooshGateway.config = {**self.old, "token": None, "assistant": self.assistant}
        self.server = HTTPServer(("127.0.0.1", 0), BooshGateway)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        BooshGateway.config = self.old

    def post(self, data, cookie=None, path="/message"):
        c = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        headers = {"Content-Type": "application/json"}
        if cookie:
            headers["Cookie"] = cookie
        c.request("POST", path, json.dumps(data), headers)
        r = c.getresponse()
        new_cookie = r.getheader("Set-Cookie")
        result = json.loads(r.read())
        status = r.status
        c.close()
        return status, result, (new_cookie.split(";")[0] if new_cookie else cookie)

    def message(self, text, cookie=None):
        return self.post({"text": text, "sender": "demo"}, cookie)

    def test_approval_belongs_to_browser_not_claimed_sender(self):
        _, _, a = self.message("pay my electric bill")
        _, r, b = self.message("YES")
        self.assertNotEqual(a, b)
        self.assertNotIn("paid", [x["type"] for x in r["actions"]])
        _, r, _ = self.message("YES", a)
        self.assertEqual(r["actions"][0]["type"], "approval")
        _, r, _ = self.message("YES", a)
        self.assertEqual(r["actions"][0]["type"], "paid")

    def test_scenario_and_pending_are_isolated(self):
        _, _, a = self.message("pay my electric bill")
        _, _, b = self.message("What do you remember?")
        self.post({"scenario": "suspicious"}, b, "/api/scenario")
        _, r, _ = self.message("YES", a)
        self.assertEqual(r["actions"][0]["type"], "approval")
        self.assertEqual(r["actions"][0]["amount"], "86.90")
        _, r, _ = self.message("Why is my electric bill so high?", b)
        self.assertTrue(r["actions"][0]["spike"])
        self.assertIn("$412.00", r["response"])
        _, r, _ = self.message("Why is my electric bill so high?", a)
        self.assertFalse(r["actions"][0]["spike"])

    def test_own_scenario_change_cancels_approval(self):
        _, _, a = self.message("pay my electric bill")
        self.message("YES", a)
        self.post({"scenario": "suspicious"}, a, "/api/scenario")
        _, r, _ = self.message("YES", a)
        self.assertNotIn("paid", [x["type"] for x in r["actions"]])
        self.message("pay my electric bill", a)
        _, r, _ = self.message("YES", a)
        self.assertEqual(r["actions"][0]["type"], "escalate")

    def test_saved_notes_do_not_leak(self):
        _, _, a = self.message("Remember that I like purple tea")
        self.message("YES", a)
        _, r, b = self.message("What do you remember?")
        self.assertNotIn("purple tea", r["response"])
        _, r, _ = self.message("What do you remember?", a)
        self.assertIn("purple tea", r["response"])

    def test_malformed_payload_returns_error_not_disconnection(self):
        for data in ([], "x", {"text": 12}, {"text": None}):
            status, _, _ = self.post(data)
            self.assertEqual(status, 400)
        status, _, _ = self.post({"scenario": "invalid"}, path="/api/scenario")
        self.assertEqual(status, 400)
        self.assertEqual(self.message("What do you remember?")[0], 200)

    def test_forged_cookie_is_replaced(self):
        _, _, a = self.message("pay my electric bill", "geeza_session=demo")
        self.assertNotEqual(a, "geeza_session=demo")
