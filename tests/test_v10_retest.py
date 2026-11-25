import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from v10_snapshot_gate import authored
from windows_ai_doctor import snapshot, snapshot_schema
from windows_ai_doctor.discovery import Entry
from windows_ai_doctor.retest import retest_snapshots
from windows_ai_doctor.runner import Result


def captured_fixture(second, role, kind, path_present):
    snap = authored()
    stamp = f"2026-11-25T00:00:{second:02}Z"
    directory = "path_" + "1" * 64
    snap.update(captured_at=stamp, session_role=role, symptom="none" if role == "working" else "not_found")
    snap["command_result"]["recorded_at"] = stamp
    snap["environment"]["path"].update(status="observed", entries=[directory] if path_present else [])
    snap["persistent_environment"]["user"]["path"].update(status="observed", entries=[directory])
    snap["resolution"].update(status="observed", kind=kind, source="original_runspace_user_supplied")
    if kind == "application":
        snap["resolution"].update(preferred_code="path_" + "2" * 64, preferred_directory_code=directory)
    return snap


class RetestBoundaries(unittest.TestCase):
    def setUp(self):
        self.working = captured_fixture(1, "working", "application", True)
        self.before = captured_fixture(2, "failing", "missing", False)
        self.after = captured_fixture(4, "failing", "application", True)

    def report(self, *, key_available=True):
        current = {"status": "available" if key_available else "unavailable", "scope_code": self.working["scope"]["code"]}
        with patch("windows_ai_doctor.retest.current_scope", return_value=current):
            return retest_snapshots(*(snapshot_schema.validate_snapshot(s) for s in
                                      (self.working, self.before, self.after)), "zh")

    def test_path_history_with_fresh_failure(self):
        self.after["command_result"].update(status="failure", source="controlled_test",
                                            executed_at="2026-11-25T00:00:03Z", session_match="original")
        report = self.report()
        self.assertEqual(report["original_command_status"], "failure")
        self.assertEqual(report["explanation_reviews"][0]["assessment"], "no_longer_sufficient")
        self.assertEqual(report["path_transition"]["persistent_layers_observed_both_times"], ["user"])

    def test_old_or_other_session_result_never_becomes_fresh_success(self):
        self.working["command_result"].update(status="success", source="user_report", session_match="original")
        result = self.after["command_result"]
        result.update(status="success", source="controlled_test", executed_at=self.before["captured_at"], session_match="original")
        report = self.report()
        self.assertEqual(report["original_command_status"], "unverified")
        self.assertEqual(report["stale_command_result"], result)
        self.assertNotEqual(report["current"]["outcome"], "both_commands_succeeded")
        result.update(executed_at="2026-11-25T00:00:03Z", session_match="other")
        self.assertEqual(self.report()["original_command_status"], "unverified")

    def test_unknown_or_limited_does_not_disappear(self):
        self.after["resolution"]["scan_limited"] = True
        report = self.report()
        self.assertEqual(report["explanation_reviews"][0]["relation"], "unassessed")
        self.assertNotIn("path_transition", report)

    def test_limited_persistent_layer_does_not_support_path_history(self):
        self.after["persistent_environment"]["user"]["path"]["status"] = "limited"
        self.assertNotIn("path_transition", self.report())

    def test_incomparable_does_not_expose_nested_differences(self):
        for change, expected in (
            ({"command": "claude", "resolution": {**self.after["resolution"], "target": "claude"}}, "target_mismatch"),
            ({"scope": {**self.after["scope"], "code": "scope_" + "9" * 64}}, "scope_mismatch"),
            ({"algorithm": "lexical-windows-v2"}, "algorithm_mismatch"),
            ({"captured_at": self.before["captured_at"]}, "retest_not_newer"),
        ):
            with self.subTest(expected=expected):
                with patch.dict(self.after, change):
                    report = self.report()
                self.assertEqual(report["reason"], expected)
                self.assertIsNone(report["current"])
                self.assertIsNone(report["changes_since_before"])
                self.assertEqual(report["explanation_reviews"], [])
        self.assertEqual(self.report(key_available=False)["reason"], "key_unavailable")


class VersionObservation(unittest.TestCase):
    def test_only_opt_in_recognized_original_launcher_is_queried(self):
        path = Path(r"C:\fixture\codex.exe")
        entry = Entry(path, kind="native", group=str(path), argv=[str(path), "--version"])
        session = {"command": "codex", "kind": "application", "path": str(path)}
        with (patch.object(snapshot.KeyStore, "load", return_value=b"k" * 32),
              patch.object(snapshot, "capture_entries", return_value=([entry], False)),
              patch.object(snapshot, "persistent", return_value=snapshot.environment(b"k" * 32, {}, True)),
              patch.object(snapshot, "run_bounded", return_value=Result("ok", 0, "codex-cli 1.2.3")) as probe):
            snapshot.capture("codex", session=session)
            snapshot.capture("codex", session={**session, "kind": "function", "path": None}, probe_version=True)
            snapshot.capture("codex", session={**session, "path": r"C:\other\codex.exe"}, probe_version=True)
            probe.assert_not_called()
            captured = snapshot.capture("codex", session=session, probe_version=True)
            probe.assert_called_once_with(entry.argv)
        self.assertEqual(snapshot.preferred_version(captured), "1.2.3")
        self.assertEqual(captured["command_result"]["status"], "unverified")
        invalid = copy.deepcopy(captured)
        invalid["observations"]["tool_execution"] = "not_performed"
        with self.assertRaises(ValueError):
            snapshot_schema.validate_snapshot(invalid)
