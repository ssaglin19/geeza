import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fixtures
from boosh_flow import Flow, PageSpec, MatchSpec, Anchor, Step, load_flow, validate_flow


class TestSchema(unittest.TestCase):
    def test_example_flow_loads_and_validates(self):
        flow = load_flow(fixtures.example_flow_path())
        self.assertEqual(flow.name, "consumers-energy-pay")
        self.assertTrue(flow.spends)
        self.assertEqual(len(flow.pages), 3)
        self.assertEqual(validate_flow(flow), [])

    def test_spends_requires_confirm(self):
        flow = Flow(name="bad", entry_url="https://x", spends=True)
        flow.pages = [
            PageSpec(
                name="p",
                match=MatchSpec(url_contains="/x", anchors=[Anchor(selector="#a"),
                                                            Anchor(selector="#b"),
                                                            Anchor(text="Go")]),
                steps=[Step(action="click", params={"text": "Go"})],
            )
        ]
        errors = validate_flow(flow)
        self.assertTrue(any("confirm" in e for e in errors))

    def test_fewer_than_three_anchors_flagged(self):
        flow = Flow(name="thin", entry_url="https://x")
        flow.pages = [
            PageSpec(
                name="p",
                match=MatchSpec(url_contains="/x", anchors=[Anchor(selector="#a")]),
                steps=[Step(action="complete")],
            )
        ]
        errors = validate_flow(flow)
        self.assertTrue(any("anchors" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
