"""Run only real file-link regressions in a caller-authorized privileged shell."""
import hashlib
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from run_tests import SafeResult


def main():
    destination = Path(sys.argv[1]).absolute()
    if destination.exists():
        return 2
    names = ["test_doctor.DoctorTests.test_config_link_to_auth_is_not_read",
             "test_v02.CompareJunctionTests.test_report_file_symlink_is_rejected_without_reading_target"]
    paths = [ROOT / "windows_ai_doctor/core.py", ROOT / "windows_ai_doctor/discovery.py",
             ROOT / "windows_ai_doctor/compare.py", ROOT / "tests/test_doctor.py", ROOT / "tests/test_v02.py"]
    before = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    result = SafeResult()
    unittest.defaultTestLoader.loadTestsFromNames(names).run(result)
    after = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    code = 0 if result.wasSuccessful() and result.testsRun == 2 and not result.skipped and before == after else 1
    record = {"generated_at": datetime.now(timezone.utc).isoformat(), "python": sys.version.split()[0],
              "exit_code": code, "tests_run": result.testsRun, "passed": sum(c["outcome"] == "PASS" for c in result.cases),
              "skipped": len(result.skipped), "failures": len(result.failures), "errors": len(result.errors),
              "run_type": "separate user-authorized file-symlink supplement; not a full suite",
              "source_sha256": before, "source_unchanged": before == after,
              "cases": result.cases}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
