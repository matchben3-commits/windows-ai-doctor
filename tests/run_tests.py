"""No test framework dependency. Writes sanitized per-case run evidence."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import argparse
import json
import time
import unittest
from datetime import datetime, timezone


class SafeResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.cases = []

    def startTest(self, test):
        super().startTest(test)
        self.started = time.monotonic()

    def record(self, test, outcome):
        self.cases.append({"test": test.id(), "outcome": outcome,
                           "seconds": round(time.monotonic() - self.started, 3)})
        print(f"{outcome}: {test.id()}", flush=True)

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, "PASS")

    def addFailure(self, test, err):
        self.failures.append((test, "Assertion failed; values and traceback withheld."))
        self.record(test, "FAIL")

    def addError(self, test, err):
        self.errors.append((test, "Test error; values and traceback withheld."))
        self.record(test, "ERROR")

    def addSkip(self, test, reason):
        super().addSkip(test, "Optional fixture compiler or privilege unavailable.")
        self.record(test, "SKIP")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path)
    args = p.parse_args()
    result = SafeResult()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    started = time.monotonic()
    suite.run(result)
    code = 0 if result.wasSuccessful() else 1
    evidence = {"generated_at": datetime.now(timezone.utc).isoformat(),
                "python": ".".join(map(str, sys.version_info[:3])),
                "command": "python tests/run_tests.py --evidence evidence/tests.json",
                "exit_code": code, "tests_run": result.testsRun,
                "passed": sum(c["outcome"] == "PASS" for c in result.cases),
                "skipped": len(result.skipped), "failures": len(result.failures),
                "errors": len(result.errors), "seconds": round(time.monotonic() - started, 3),
                "cases": result.cases}
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"tests={result.testsRun}, failures={len(result.failures)}, errors={len(result.errors)}, skipped={len(result.skipped)}, exit={code}")
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError):
        print("Test evidence export incomplete; details withheld.", file=sys.stderr)
        raise SystemExit(2)
