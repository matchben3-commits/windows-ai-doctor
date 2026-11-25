"""Real Windows CTRL_C_EVENT against an isolated console running the capture CLI.

Only stdin readiness is instrumented. No product function or exception is
replaced. Signal generation and the target's own fresh exit code are recorded.
"""
import argparse
import ctypes
import json
import os
import subprocess
import sys
import uuid
from ctypes import wintypes as W
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def kernel():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    for name, arguments, result in (
        ("CreateEventW", [W.LPVOID, W.BOOL, W.BOOL, W.LPCWSTR], W.HANDLE),
        ("OpenEventW", [W.DWORD, W.BOOL, W.LPCWSTR], W.HANDLE),
        ("SetEvent", [W.HANDLE], W.BOOL),
        ("WaitForSingleObject", [W.HANDLE, W.DWORD], W.DWORD),
        ("CloseHandle", [W.HANDLE], W.BOOL),
        ("FreeConsole", [], W.BOOL),
        ("AttachConsole", [W.DWORD], W.BOOL),
        ("SetConsoleCtrlHandler", [W.LPVOID, W.BOOL], W.BOOL),
        ("GenerateConsoleCtrlEvent", [W.DWORD, W.DWORD], W.BOOL)):
        fn = getattr(k, name)
        fn.argtypes, fn.restype = arguments, result
    return k


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path)
    p.add_argument("--child")
    p.add_argument("--signal", type=int)
    args = p.parse_args()
    k = kernel()
    if args.signal is not None:
        k.FreeConsole()
        attached = bool(k.AttachConsole(args.signal))
        ignored = bool(k.SetConsoleCtrlHandler(None, True)) if attached else False
        sent = bool(k.GenerateConsoleCtrlEvent(0, 0)) if ignored else False
        print(json.dumps({"attached": attached, "sender_ignores_ctrl_c": ignored, "CTRL_C_EVENT_sent": sent}))
        return 0 if sent else 1
    if args.child:
        sys.path.insert(0, str(ROOT))
        from windows_ai_doctor import cli
        ready = k.OpenEventW(2, False, args.child)
        original = sys.stdin
        class ReadyBuffer:
            def read(self, count):
                k.SetEvent(ready)
                return original.buffer.read(count)
        class ReadyInput:
            buffer = ReadyBuffer()
        sys.stdin = ReadyInput()
        try:
            return cli.main(["--capture", "--command", "codex", "--session-metadata-stdin"])
        finally:
            k.CloseHandle(ready)
    dest = args.evidence.absolute()
    dest.mkdir(parents=True, exist_ok=False)
    name = "Local\\WAD-dev2-interrupt-" + uuid.uuid4().hex
    event = k.CreateEventW(None, True, False, name)
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    command = [sys.executable, "-I", "-B", str(Path(__file__).absolute()), "--child", name]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=startup)
    try:
        ready = k.WaitForSingleObject(event, 15000) == 0
        if not ready:
            raise RuntimeError("child_not_ready")
        sender_command = [sys.executable, "-I", "-B", str(Path(__file__).absolute()), "--signal", str(proc.pid)]
        sender = subprocess.run(sender_command, capture_output=True, timeout=10)
        # Release the pipe read so the interpreter can handle pending SIGINT.
        proc.stdin.close()
        proc.stdin = None
        out, err = proc.communicate(timeout=15)
        (dest / "target.stdout").write_bytes(out)
        (dest / "target.stderr").write_bytes(err)
        (dest / "sender.stdout").write_bytes(sender.stdout)
        result = {"command": command, "sender_command": sender_command, "sender_exit": sender.returncode,
                  "stdin_read_ready": ready, "target_exit": proc.returncode,
                  "passed": sender.returncode == 0 and proc.returncode == 130 and b"Interrupted." in err,
                  "mechanism": "GenerateConsoleCtrlEvent(CTRL_C_EVENT) in separate hidden console; no injected exception",
                  "scope": "real process capture stdin interruption; shared CLI KeyboardInterrupt boundary"}
        (dest / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["passed"] else 1
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate()
        k.CloseHandle(event)


if __name__ == "__main__":
    raise SystemExit(main())
