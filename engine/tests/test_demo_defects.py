"""Regressions for live-demo defects found 2026-10-17: looping chat output, caregiver-note misroute,
bare YES with nothing pending, pasted scam text sent to the scam check."""
import unittest
from gateway.assistant import Assistant
from boosh_flow import assist
from boosh_flow.nebius import MockClient


class LoopingLive(MockClient):
    live = True
    def complete(self, messages, model=None, **kw):
        raise AssertionError("model must not be called for this input")


class Looping(MockClient):
    def complete(self, messages, model=None, **kw):
        return "Stay calm.\n" + "\n".join(["We are here.", "Always.", "We love you."] * 8)


class Defects(unittest.TestCase):
    def test_tame_collapses_loops(self):
        out = assist.tame("Stay calm.\n" + "\n".join(["We are here.", "Always."] * 20))
        self.assertEqual(out, "Stay calm. We are here. Always.")
        self.assertLessEqual(len(assist.tame("word " * 500)), 401)

    def test_chat_reply_is_tamed(self):
        a = Assistant(Looping())
        r = a.handle("how are you today my dear friend", "s")
        self.assertLessEqual(len(r["response"].split(".")), 5)
        self.assertEqual(r["response"].count("We are here."), 1)

    def test_bare_yes_with_nothing_pending(self):
        r = Assistant(LoopingLive()).handle("YES", "s")
        self.assertIn("nothing waiting", r["response"])

    def test_pasted_scam_goes_to_scam_check(self):
        r = Assistant(MockClient()).handle(
            "Your account is suspended. Buy gift cards and send me the codes today or lose access.", "s")
        self.assertEqual(r["tool"], "scam_check")
        self.assertIn("scam", r["response"].lower())
        self.assertLess(len(r["response"]), 400)

    def test_tell_sean_is_not_routed_as_groceries(self):
        a = Assistant(LoopingLive())
        self.assertIsNone(a._route("Tell Sean I need groceries", "s"))
        r = a.handle("Tell Sean I need groceries", "s")
        self.assertNotIn("cannot order", r["response"])
        self.assertEqual(r.get("tool"), "tell_caregiver")


if __name__ == "__main__":
    unittest.main()
