#!/usr/bin/env python3
"""Run offline engine and gateway tests without optional model downloads."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "engine"), str(ROOT)]
loader = unittest.TestLoader()
suite = unittest.TestSuite()
for path in sorted((ROOT / "engine" / "tests").glob("test_*.py")):
    if path.stem == "test_gliner_eval":
        continue  # optional model evaluation downloads weights; not an offline regression
    suite.addTests(loader.loadTestsFromName("engine.tests." + path.stem))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
