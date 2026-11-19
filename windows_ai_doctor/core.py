import json
import os
import re
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .discovery import bounded_read, discover, is_native, local_absolute
from .messages import message
from .privacy import Privacy, safe_version
from .runner import run_bounded


class Doctor:
    def __init__(self, *, env=None, home=None, lang="zh", tools=("codex", "claude"),
                 timeout=3.0, versions=True, project=None, wsl_list=False, runner=run_bounded):
        self.env = dict(os.environ if env is None else env)
        self.home = Path(home) if home is not None else Path.home()
        self.lang, self.tools = lang, tools
        self.timeout, self.versions, self.project = timeout, versions, project
        self.wsl_list, self.runner = wsl_list, runner
        self.privacy, self.findings = Privacy(), []

    def add(self, id, target, status, text, evidence=None, review="review_scope"):
        self.findings.append({"id": id, "target": target, "status": status,
            "summary": message(text, self.lang), "evidence": evidence or {},
            "recommendation": message(review, self.lang),
            "recheck": message(review, self.lang)})

    def probe(self, argv):
        return self.runner(argv, timeout=self.timeout, env=self.env)

    def run(self):
        self.add("system.platform", "system", "pass" if os.name == "nt" else "warn", "platform",
                 {"os": "Windows" if os.name == "nt" else "Darwin" if sys.platform == "darwin" else "Linux" if sys.platform.startswith("linux") else "Other",
                  "python": ".".join(map(str, sys.version_info[:3])),
                  "windows_target": os.name == "nt"})
        for tool in self.tools:
            self.check_tool(tool)
            self.check_configs(tool)
        self.check_wsl()
        self.add("scope.unchecked", "system", "skipped", "scope")
        counts = {state: sum(f["status"] == state for f in self.findings)
                  for state in ("pass", "warn", "error", "unknown", "skipped")}
        return {"schema_version": "1.0", "doctor_version": __version__,
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "language": self.lang, "summary": counts,
                "privacy": {"paths": "opaque_references", "raw_output": False,
                            "config_values": False, "credentials_read": False},
                "findings": self.findings}

    def check_tool(self, tool):
        entries, selected, ps, limited = discover(tool, self.env)
        groups = {}
        public_entries = []
        for entry in entries:
            groups.setdefault(entry.group, len(groups) + 1)
            public_entries.append({"path": self.privacy.path(entry.path),
                                   "command_name": tool + entry.path.suffix.lower(),
                                   "installation_group": groups[entry.group], "kind": entry.kind,
                                   "path_access": entry.path_access,
                                   "existence_verified": entry.path_access == "checked"})
        evidence = {"entries": public_entries, "installation_groups": len(groups),
                    "cmd_path_candidate": self.privacy.path(selected.path) if selected else None,
                    "powershell_path_candidate": self.privacy.path(ps.path) if ps else None,
                    "resolution_model": "PATH+PATHEXT; excludes CWD, aliases and functions",
                    "scan_limited": limited}
        status = "warn" if not selected or len(groups) > 1 or limited or any(e.path_access == "blocked" for e in entries) else "pass"
        self.add(f"{tool}.path", tool, status,
                 "paths_blocked" if any(e.path_access == "blocked" for e in entries) else
                 "missing" if not selected else "duplicate" if len(groups) > 1 else "paths",
                 evidence, "review_path")
        self.add(f"{tool}.install", tool,
                 "pass" if selected and selected.kind != "unknown" else "unknown", "install",
                 {"kind": selected.kind if selected else "not_found",
                  "publisher_verified": False}, "review_path")
        self.check_dependency(tool, selected)
        if not self.versions:
            result = {"reason": "disabled"}
            status = "skipped"
        elif not selected or not selected.argv:
            result = {"reason": "unrecognized_or_missing_runtime"}
            status = "unknown"
        else:
            probe = self.probe(selected.argv)
            version = safe_version(probe.output, tool) if probe.reason == "ok" and probe.returncode == 0 else None
            result = {"reason": probe.reason if probe.reason != "ok" else
                      "nonzero_exit" if probe.returncode != 0 else
                      "version_parsed" if version else "unrecognized_response",
                      "returncode": probe.returncode, "version": version,
                      "captured_bytes": probe.captured_bytes, "timeout_seconds": self.timeout}
            status = "pass" if version else "unknown"
        self.add(f"{tool}.version", tool, status, "version", result, "review_version")

    def check_dependency(self, tool, selected):
        evidence = {"runtime": "unknown"}
        status = "unknown"
        if selected and selected.kind in ("native", "npm-native"):
            status, evidence = "pass", {"runtime": "native", "node_required": False,
                                        "scope": "launcher_only; optional feature dependencies not checked"}
        elif selected and selected.kind == "npm-js":
            evidence = {"runtime": "node", "node_found": selected.node is not None,
                        "node_path_check": selected.node_status,
                        "documented_package_engine": selected.engine}
            if not selected.node:
                status = "error" if selected.node_status == "missing" else "unknown"
            elif not self.versions:
                evidence["reason"] = "version_probe_disabled"
            else:
                result = self.probe([str(selected.node), "--version"])
                version = safe_version(result.output, "node") if result.reason == "ok" and result.returncode == 0 else None
                evidence.update({"version": version, "probe_reason": result.reason})
                if version and selected.engine:
                    required = tuple(int(v) for v in selected.engine[2:].split("."))
                    required += (0,) * (3 - len(required))
                    status = "pass" if tuple(map(int, version.split("."))) >= required else "error"
                elif version:
                    evidence["reason"] = "package_engine_range_not_supported"
        self.add(f"{tool}.dependency", tool, status, "dependency", evidence, "review_version")

    def check_configs(self, tool):
        variable, dirname, filename = (("CODEX_HOME", ".codex", "config.toml") if tool == "codex"
                                      else ("CLAUDE_CONFIG_DIR", ".claude", "settings.json"))
        override = self.env.get(variable)
        root = Path(override) if override else self.home / dirname
        self.check_file(f"{tool}.config.user", tool, root / filename,
                        {"layer": "user", "location_source": variable if override else "default_home"})
        if self.project is not None:
            project = Path(self.project)
            self.check_file(f"{tool}.config.project", tool, project / dirname / filename,
                            {"layer": "project", "effective_loading": "not_evaluated"})
            if tool == "claude":
                self.check_file("claude.config.local", tool, project / dirname / "settings.local.json",
                                {"layer": "project_local", "effective_loading": "not_evaluated"})

    def check_file(self, id, tool, path, evidence):
        evidence = {**evidence, "path": self.privacy.path(path),
                    "format": "TOML" if tool == "codex" else "JSON"}
        try:
            raw = bounded_read(path)
            content = raw.decode("utf-8")  # BOM and non-UTF-8 are deliberately not accepted
            if tool == "codex":
                parsed = tomllib.loads(content)
            else:
                def reject_constant(_):
                    raise ValueError("non_json_constant")
                parsed = json.loads(content, parse_constant=reject_constant)
            if not isinstance(parsed, dict):
                raise ValueError("root_not_object")
            status, text = "pass", "config"
            evidence["syntax"] = "valid"
        except FileNotFoundError:
            status, text = "skipped", "config_missing"
            evidence["syntax"] = "absent"
        except (json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
            status, text = "error", "config_bad"
            evidence["syntax"] = "invalid"
            line = getattr(exc, "lineno", None)
            if isinstance(line, int):
                evidence["line"] = line
        except UnicodeError:
            status, text = "unknown", "config_unreadable"
            evidence["syntax"] = "encoding_not_supported"
        except (ValueError, RecursionError) as exc:
            # Only fixed classifications, never str(exc), repr(exc), or traceback.
            invalid = exc.args in (("root_not_object",), ("non_json_constant",))
            status, text = ("error", "config_bad") if invalid else ("unknown", "config_unreadable")
            evidence["syntax"] = "invalid_structure" if invalid else "safety_limit"
        except OSError:
            status, text = "unknown", "config_unreadable"
            evidence["syntax"] = "unreadable"
        self.add(id, tool, status, text, evidence, "review_config")

    def check_wsl(self):
        if os.name != "nt":
            self.add("wsl.launcher", "wsl", "skipped", "wsl_launcher", {"reason": "not_windows"}, "review_wsl")
            self.add("wsl.inventory", "wsl", "skipped", "wsl_inventory", review="review_wsl")
            self.add("wsl.running", "wsl", "skipped", "wsl_state", review="review_wsl")
        else:
            # GetWindowsDirectoryW, not a PATH-provided wsl.exe.
            launcher = system_wsl_launcher()
            present = launcher is not None and is_native(launcher)
            self.add("wsl.launcher", "wsl", "pass" if present else "warn", "wsl_launcher",
                     {"present": present, "component_health": "not_checked"}, "review_wsl")
            count, reason = registered_distributions()
            self.add("wsl.inventory", "wsl", "pass" if count is not None else "unknown", "wsl_inventory",
                     {"registered_count": count, "reason": reason}, "review_wsl")
            state = {"reason": "not_requested", "running_count": None}
            status = "skipped"
            if self.wsl_list and present:
                result = self.probe([str(launcher), "--list", "--running", "--quiet"])
                # Names are private. Nonzero results/messages are not interpreted.
                if result.reason == "ok" and result.returncode == 0:
                    names = [v.strip() for v in result.output.splitlines() if v.strip()]
                    valid = all(re.fullmatch(r"[\w .()-]{1,120}", v) for v in names)
                    if valid:
                        state = {"reason": "list_succeeded", "running_count": len(names)}
                        status = "pass"
                    else:
                        state, status = {"reason": "unrecognized_response", "running_count": None}, "unknown"
                else:
                    state, status = {"reason": result.reason if result.reason != "ok" else "nonzero_exit", "returncode": result.returncode,
                                     "running_count": None}, "unknown"
            self.add("wsl.running", "wsl", status, "wsl_state", state, "review_wsl")
        self.add("wsl.internal", "wsl", "skipped", "wsl_inside", review="review_wsl")


def registered_distributions():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Lxss") as key:
            count = 0
            total = winreg.QueryInfoKey(key)[0]
            if total > 256:
                return None, "inventory_limit"
            for i in range(total):
                name = winreg.EnumKey(key, i)
                if re.fullmatch(r"\{[0-9a-fA-F-]{36}\}", name):
                    count += 1
            return count, "registry_observation"
    except FileNotFoundError:
        return 0, "registration_key_absent"
    except OSError:
        return None, "registry_unreadable"


def system_wsl_launcher():
    import ctypes
    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer))
    if not 0 < length < len(buffer):
        return None
    # 32-bit Python must use Sysnative to reach the 64-bit WSL launcher.
    folder = "Sysnative" if sys.maxsize <= 2**32 and os.environ.get("PROCESSOR_ARCHITEW6432") else "System32"
    return Path(buffer.value) / folder / "wsl.exe"
