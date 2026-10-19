import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT))
from boosh_flow import bill_extract as be
from gateway import demo_data
from gateway.assistant import Assistant
from boosh_flow.nebius import MockClient

KN = demo_data.KNOWN_PAYEES


def A(v, c=1.0, p=0.0):
    return {"value": v, "confidence": c, "p_null": p}


def resp(vendor="Lakeshore Power", amt=86.9, date="2026-01-28", **over):
    a = {"vendor": A(vendor), "amount_due": A(amt), "due_date": A(date)}
    a.update(over)
    return {"answers": a}


def run(r, last=84.0, text="Amount due: $86.90 due Jan 28 from Lakeshore Power"):
    be._calls = 0
    return be.extract(text, last, KN, "2026-01-10", call=lambda b: r)


class TestExtract(unittest.TestCase):
    def test_ok_case(self):
        r = run(resp())
        self.assertEqual(r["status"], "ok")

    def test_failures_go_to_review(self):
        bad = {
            "spike": resp(amt=412.0),
            "lookalike": resp(vendor="Lakeshore Power Co-Op"),
            "nan": resp(amt=float("nan")),
            "inf": resp(amt=float("inf")),
            "negative": resp(amt=-86.9),
            "bool": resp(amt=True),
            "string amount": resp(amt="86.90"),
            "null amount": resp(amt=None, amount_due=A(None, 0.4, 1)),
            "low conf": resp(amount_due=A(86.9, 0.5, 0.0)),
            "high pnull": resp(amount_due=A(86.9, 1.0, 0.5)),
            "nan conf": resp(amount_due=A(86.9, float("nan"), 0.0)),
            "missing field": {"answers": {"vendor": A("Lakeshore Power")}},
            "bad date": resp(date="Jan 28"),
            "answers not dict": {"answers": []},
            "no answers": {},
            "vendor not str": resp(vendor=5),
        }
        for name, r in bad.items():
            with self.subTest(name):
                self.assertEqual(run(r)["status"], "review")

    def test_call_errors_and_guards(self):
        be._calls = 0
        def boom(b): raise RuntimeError("x")
        self.assertEqual(be.extract("t", 84.0, KN, "2026-01-10", call=boom)["status"], "review")
        self.assertEqual(be.extract("", 84.0, KN, "2026-01-10", call=boom)["status"], "review")
        self.assertEqual(be.extract("x" * 5000, 84.0, KN, "2026-01-10", call=boom)["status"], "review")

    def test_off_by_default(self):
        be._calls = 0
        self.assertEqual(be.extract("Amount due 5", 84.0, KN, "2026-01-10")["status"], "review")

    def test_call_budget(self):
        be._calls = be.MAX_CALLS
        n = []
        r = be.extract("Amount due 5", 84.0, KN, "2026-01-10", call=lambda b: n.append(1) or resp())
        self.assertEqual((r["status"], n), ("review", []))
        be._calls = 0

    def test_request_is_text_only(self):
        seen = []
        be._calls = 0
        be.extract("Amount due $5", 84.0, KN, "2026-01-10", call=lambda b: seen.append(b) or resp())
        self.assertNotIn("images", seen[0])


class TestAssistant(unittest.TestCase):
    BILL = "Lakeshore Power statement. Amount due: $86.90, due 2026-01-28. Pay from your account page."

    def _a(self, r, enabled=True):
        a = Assistant(MockClient())
        orig_en, orig_ex = be.enabled, be.extract
        be.enabled = lambda: enabled
        op = be.paste_enabled
        be.paste_enabled = lambda: enabled
        self.addCleanup(setattr, be, "paste_enabled", op)
        be.extract = lambda *x, **k: orig_ex(*x, **k, call=lambda b: r)
        self.addCleanup(setattr, be, "enabled", orig_en)
        self.addCleanup(setattr, be, "extract", orig_ex)
        be._calls = 0
        return a

    def test_ok_never_starts_payment(self):
        a = self._a(resp())
        out = a.handle(self.BILL)
        self.assertEqual(out["actions"][0]["status"], "ok")
        self.assertEqual(a.pending, {})
        self.assertIn("There is nothing waiting", a.handle("yes")["response"])

    def test_bad_goes_to_review(self):
        a = self._a(resp(amt=float("nan")))
        out = a.handle(self.BILL)
        self.assertEqual(out["actions"][0]["status"], "review")
        self.assertIn("Sean", out["response"])
        self.assertEqual(a.pending, {})

    def test_disabled_keeps_old_path(self):
        a = self._a(resp(), enabled=False)
        out = a.handle(self.BILL)
        self.assertNotIn("bill_text_read", [x.get("type") for x in out["actions"]])


if __name__ == "__main__":
    unittest.main()


class TestPayFlowCrosscheck(unittest.TestCase):
    def _a(self, r):
        a = Assistant(MockClient())
        oe, ox = be.enabled, be.extract
        be.enabled = lambda: True
        be.extract = lambda *x, **k: ox(*x[:4], call=lambda b: r)
        self.addCleanup(setattr, be, "enabled", oe)
        self.addCleanup(setattr, be, "extract", ox)
        be._calls = 0
        be._CACHE.clear()
        self.addCleanup(be._CACHE.clear)
        return a

    def _offer(self, a):
        a.handle("pay my electric bill")
        return a.handle("yes")

    def test_agreeing_reader_keeps_two_yes(self):
        a = self._a(resp())
        out = self._offer(a)
        self.assertEqual(out["actions"][0]["type"], "approval")
        self.assertIn("Paid", a.handle("yes")["response"])

    def test_mismatch_stops(self):
        a = self._a(resp(amt=95.0))
        out = self._offer(a)
        self.assertEqual(out["actions"][0]["type"], "escalate")
        self.assertEqual(a.pending, {})

    def test_reader_failure_stops(self):
        a = self._a({"answers": {}})
        self.assertEqual(self._offer(a)["actions"][0]["type"], "escalate")

    def test_cache_bounds_calls(self):
        a = self._a(resp())
        for _ in range(5):
            self._offer(a); a.pending.clear()
        self.assertEqual(be._calls, 1)

    def test_disabled_unchanged(self):
        a = Assistant(MockClient())
        self.assertEqual(self._offer(a)["actions"][0]["type"], "approval")
