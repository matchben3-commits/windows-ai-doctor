"""Bounded process tree, capped capture, no shell, no inherited credentials.

Windows: create suspended, assign to kill-on-close Job, then resume. A failure
to contain the child fails closed. POSIX: a separate process group.
"""
import os
import signal
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Result:
    reason: str
    returncode: int | None = None
    output: str = ""
    captured_bytes: int = 0


def clean_env(root, source):
    """Allowlist OS plumbing; all HOME/config/cache locations point to scratch."""
    env = {k: v for k, v in source.items()
           if k.upper() in {"SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "PATHEXT", "PATH"}}
    for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP",
                "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME",
                "CODEX_HOME", "CLAUDE_CONFIG_DIR"):
        value = str(Path(root) / key.lower())
        Path(value).mkdir()
        env[key] = value
    env.update({"DISABLE_AUTOUPDATER": "1", "DISABLE_UPDATES": "1",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                "DISABLE_TELEMETRY": "1", "DISABLE_ERROR_REPORTING": "1",
                "DO_NOT_TRACK": "1", "NO_COLOR": "1", "CI": "1",
                "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
                "ALL_PROXY": "http://127.0.0.1:9", "NO_PROXY": ""})
    return env


def run_bounded(argv, *, timeout=3.0, limit=16384, env=None):
    if not 0.1 <= timeout <= 30 or not 128 <= limit <= 1048576:
        raise ValueError("invalid resource bound")
    if not argv or not Path(argv[0]).is_absolute():
        return Result("unsafe_command")
    try:
        with tempfile.TemporaryDirectory(prefix="ai-doctor-probe-") as scratch:
            isolated = clean_env(scratch, os.environ if env is None else env)
            if os.name == "nt":
                return _windows(argv, isolated, scratch, timeout, limit)
            return _posix(argv, isolated, scratch, timeout, limit)
    except (OSError, ValueError):
        return Result("launch_error")


def _capture(fd, limit, chunks, overflow, terminate):
    size = 0
    try:
        while True:
            part = os.read(fd, min(4096, limit + 1 - size))
            if not part:
                break
            chunks.append(part)
            size += len(part)
            if size > limit:
                overflow.set()
                terminate()
                break
    except OSError:
        pass
    finally:
        os.close(fd)


def _result(chunks, overflow, timed_out, code):
    data = b"".join(chunks)
    reason = "output_limit" if overflow.is_set() else "timeout" if timed_out else "ok"
    # UTF-16 is used by wsl.exe; other probes generally emit UTF-8/ASCII.
    encoding = "utf-16-le" if b"\x00" in data[:100] else "utf-8-sig"
    return Result(reason, code, data.decode(encoding, errors="replace"), len(data))


def _posix(argv, env, cwd, timeout, limit):
    proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env, cwd=cwd,
                            start_new_session=True, shell=False)
    chunks, overflow = [], threading.Event()

    def stop():
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    fd = os.dup(proc.stdout.fileno())
    proc.stdout.close()
    reader = threading.Thread(target=_capture, args=(fd, limit, chunks, overflow, stop), daemon=True)
    reader.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
    finally:
        stop()  # also removes descendants after a successful parent exit
        proc.wait(timeout=2)
        reader.join(timeout=2)
    return _result(chunks, overflow, timed_out, proc.returncode)


def _windows(argv, env, cwd, timeout, limit):
    import ctypes as c
    from ctypes import wintypes as w
    import msvcrt

    class SECURITY(c.Structure):
        _fields_ = [("length", w.DWORD), ("descriptor", w.LPVOID), ("inherit", w.BOOL)]

    class STARTUP(c.Structure):
        _fields_ = [("cb", w.DWORD), ("reserved", w.LPWSTR), ("desktop", w.LPWSTR),
                    ("title", w.LPWSTR), ("x", w.DWORD), ("y", w.DWORD),
                    ("cx", w.DWORD), ("cy", w.DWORD), ("charsx", w.DWORD),
                    ("charsy", w.DWORD), ("fill", w.DWORD), ("flags", w.DWORD),
                    ("show", w.WORD), ("reserved2size", w.WORD), ("reserved2", w.LPVOID),
                    ("stdin", w.HANDLE), ("stdout", w.HANDLE), ("stderr", w.HANDLE)]

    class PROCESS(c.Structure):
        _fields_ = [("process", w.HANDLE), ("thread", w.HANDLE),
                    ("pid", w.DWORD), ("tid", w.DWORD)]

    class BASIC(c.Structure):
        _fields_ = [("process_time", c.c_longlong), ("job_time", c.c_longlong),
                    ("flags", w.DWORD), ("min_work", c.c_size_t), ("max_work", c.c_size_t),
                    ("active", w.DWORD), ("affinity", c.c_size_t),
                    ("priority", w.DWORD), ("scheduling", w.DWORD)]

    class EXTENDED(c.Structure):
        _fields_ = [("basic", BASIC), ("io", c.c_ulonglong * 6),
                    ("process_memory", c.c_size_t), ("job_memory", c.c_size_t),
                    ("peak_process", c.c_size_t), ("peak_job", c.c_size_t)]

    kernel = c.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateJobObjectW": ([w.LPVOID, w.LPCWSTR], w.HANDLE),
        "SetInformationJobObject": ([w.HANDLE, c.c_int, w.LPVOID, w.DWORD], w.BOOL),
        "CreatePipe": ([c.POINTER(w.HANDLE), c.POINTER(w.HANDLE), c.POINTER(SECURITY), w.DWORD], w.BOOL),
        "SetHandleInformation": ([w.HANDLE, w.DWORD, w.DWORD], w.BOOL),
        "CreateFileW": ([w.LPCWSTR, w.DWORD, w.DWORD, c.POINTER(SECURITY), w.DWORD, w.DWORD, w.HANDLE], w.HANDLE),
        "CreateProcessW": ([w.LPCWSTR, w.LPWSTR, w.LPVOID, w.LPVOID, w.BOOL,
                            w.DWORD, w.LPVOID, w.LPCWSTR, c.POINTER(STARTUP), c.POINTER(PROCESS)], w.BOOL),
        "AssignProcessToJobObject": ([w.HANDLE, w.HANDLE], w.BOOL),
        "ResumeThread": ([w.HANDLE], w.DWORD),
        "TerminateProcess": ([w.HANDLE, w.UINT], w.BOOL),
        "TerminateJobObject": ([w.HANDLE, w.UINT], w.BOOL),
        "WaitForSingleObject": ([w.HANDLE, w.DWORD], w.DWORD),
        "GetExitCodeProcess": ([w.HANDLE, c.POINTER(w.DWORD)], w.BOOL),
        "CloseHandle": ([w.HANDLE], w.BOOL),
    }
    for name, (args, ret) in signatures.items():
        getattr(kernel, name).argtypes = args
        getattr(kernel, name).restype = ret
    handles = []
    proc = PROCESS()
    reader = None
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        return Result("containment_error")
    handles.append(job)
    try:
        info = EXTENDED()
        info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(job, 9, c.byref(info), c.sizeof(info)):
            return Result("containment_error")
        security = SECURITY(c.sizeof(SECURITY), None, True)
        read, write = w.HANDLE(), w.HANDLE()
        if not kernel.CreatePipe(c.byref(read), c.byref(write), c.byref(security), 0):
            return Result("launch_error")
        handles.extend([read.value, write.value])
        if not kernel.SetHandleInformation(read, 1, 0):
            return Result("launch_error")
        null = kernel.CreateFileW("NUL", 0x80000000, 3, c.byref(security), 3, 0, None)
        if null == c.c_void_p(-1).value:
            return Result("launch_error")
        handles.append(null)
        startup = STARTUP()
        startup.cb, startup.flags = c.sizeof(STARTUP), 0x100
        startup.stdin, startup.stdout, startup.stderr = null, write, write
        block = c.create_unicode_buffer("\0".join(f"{k}={v}" for k, v in sorted(env.items())) + "\0\0")
        command = c.create_unicode_buffer(subprocess.list2cmdline([str(a) for a in argv]))
        if not kernel.CreateProcessW(str(argv[0]), command, None, None, True,
                                     0x08000000 | 0x400 | 0x4, block, cwd,
                                     c.byref(startup), c.byref(proc)):
            return Result("launch_error")
        handles.extend([proc.process, proc.thread])
        if not kernel.AssignProcessToJobObject(job, proc.process):
            kernel.TerminateProcess(proc.process, 1)
            kernel.WaitForSingleObject(proc.process, 2000)
            return Result("containment_error")
        fd = msvcrt.open_osfhandle(read.value, os.O_RDONLY | os.O_BINARY)
        handles.remove(read.value)  # fd now owns the handle
        chunks, overflow = [], threading.Event()
        reader = threading.Thread(target=_capture,
            args=(fd, limit, chunks, overflow, lambda: kernel.TerminateJobObject(job, 1)), daemon=True)
        reader.start()
        kernel.CloseHandle(write.value)
        handles.remove(write.value)
        if kernel.ResumeThread(proc.thread) == 0xFFFFFFFF:
            return Result("launch_error")
        waited = kernel.WaitForSingleObject(proc.process, int(timeout * 1000))
        kernel.TerminateJobObject(job, 1)  # kill remaining descendants, including on success
        kernel.WaitForSingleObject(proc.process, 2000)
        code = w.DWORD()
        kernel.GetExitCodeProcess(proc.process, c.byref(code))
        reader.join(timeout=2)
        if waited == 0xFFFFFFFF:
            return Result("containment_error")
        return _result(chunks, overflow, waited == 258, code.value)
    finally:
        kernel.TerminateJobObject(job, 1)
        if reader is not None:
            reader.join(timeout=2)
        for handle in reversed(handles):
            kernel.CloseHandle(handle)
