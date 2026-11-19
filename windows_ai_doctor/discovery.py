"""Narrow PATH inspection. Never execute a wrapper through a shell."""
import json
import os
import re
import stat
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .npm_shims import known_wrapper

PACKAGES = {"codex": "@openai/codex", "claude": "@anthropic-ai/claude-code"}
MAX_FILE = 1024 * 1024


def local_absolute(path):
    p = Path(path)
    if not p.is_absolute() or str(p).startswith(("\\\\", "//")):
        return False
    return fixed_drive(p.anchor) if os.name == "nt" else True


@lru_cache(maxsize=32)
def fixed_drive(anchor):
    import ctypes
    # Avoid UNC, mapped network drives and removable media during diagnosis.
    return ctypes.windll.kernel32.GetDriveTypeW(str(anchor)) in (3, 6)


def checked_stat(path):
    """lstat root to leaf; never query a descendant of a rejected component.

    No resolve/is_file/stat call is allowed before this check. Concurrent hostile
    replacement and hard links are outside this conservative inspection model.
    """
    p = Path(path)
    if not local_absolute(p):
        raise ValueError("nonlocal_path")
    if ".." in p.parts or (os.name == "nt" and any(":" in v for v in p.parts[1:])):
        raise ValueError("unsupported_path")
    for part in (*reversed(p.parents), p):
        st = part.lstat()
        if stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & 0x400:
            raise ValueError("linked_path")
        if part != p and not stat.S_ISDIR(st.st_mode):
            raise NotADirectoryError("not_directory")
    return st


def bounded_read(path, limit=MAX_FILE):
    """Reject links/reparse points (including ancestors), devices and huge files."""
    p = Path(path)
    st = checked_stat(p)
    if not stat.S_ISREG(st.st_mode) or st.st_size > limit:
        raise ValueError("file_limit")
    with p.open("rb") as stream:
        st = os.fstat(stream.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_size > limit:
            raise ValueError("file_limit")
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("file_limit")
    return data


def is_native(path):
    try:
        p = Path(path)
        if not stat.S_ISREG(checked_stat(p).st_mode):
            return False
        with p.open("rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                return False
            magic = stream.read(4)
        return magic[:2] == b"MZ" if os.name == "nt" else magic == b"\x7fELF" or magic in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf")
    except (OSError, ValueError):
        return False


@dataclass
class Entry:
    path: Path
    kind: str = "unknown"
    group: str = ""
    argv: list = field(default_factory=list)
    node: Path | None = None
    engine: str | None = None
    path_access: str = "checked"
    node_status: str = "not_checked"


def path_dirs(env):
    dirs, seen = [], set()
    pieces = env.get("PATH", "").split(os.pathsep)
    limited = len(pieces) > 512
    for value in pieces[:512]:
        value = value.strip().strip('"')
        if not value or not local_absolute(value):
            continue  # never include implicit CWD or remote shares
        key = os.path.normcase(os.path.abspath(value))
        if key not in seen:
            dirs.append(Path(value))
            seen.add(key)
    return dirs, limited


def inspect_node(directory, dirs):
    name = "node.exe" if os.name == "nt" else "node"
    for folder in [directory, *dirs]:
        candidate = folder / name
        try:
            st = checked_stat(candidate)
        except FileNotFoundError:
            continue
        except (OSError, ValueError):
            return None, "blocked"  # never bypass an inaccessible earlier runtime
        if not stat.S_ISREG(st.st_mode):
            return None, "unrecognized"
        if is_native(candidate):
            return candidate, "found"
        return None, "unrecognized"  # present but broken first Node shadows later Node
    return None, "missing"


def find_node(directory, dirs):
    return inspect_node(directory, dirs)[0]


def classify(path, tool, dirs):
    path = Path(path)
    entry = Entry(path, group=os.path.normcase(str(path)))
    try:
        if not stat.S_ISREG(checked_stat(path).st_mode):
            return entry
    except (OSError, ValueError):
        entry.path_access = "blocked"
        return entry
    if is_native(path):
        entry.kind, entry.argv = "native", [str(path), "--version"]
        return entry
    # Recognize a local npm layout only when both package metadata and wrapper
    # target agree. Metadata is a clue, not a publisher signature.
    package = path.parent / "node_modules" / PACKAGES[tool]
    try:
        metadata = json.loads(bounded_read(package / "package.json", 65536))
        if metadata.get("name") != PACKAGES[tool]:
            return entry
        bins = metadata.get("bin")
        target = bins.get(tool) if isinstance(bins, dict) else bins
        if not isinstance(target, str) or not re.fullmatch(r"[\w./-]{1,120}", target):
            return entry
        # Pure lexical containment, without following any package/target link.
        if any(v in ("", ".", "..") for v in target.split("/")):
            return entry
        target_path = package / target
        wrapper = bounded_read(path, 65536).decode("utf-8", errors="strict")
        marker = f"node_modules/{PACKAGES[tool]}/{target}"
        node_target = target_path.suffix in (".js", ".mjs", ".cjs")
        if not known_wrapper(wrapper, path.suffix, marker, node=node_target):
            return entry
        if not stat.S_ISREG(checked_stat(target_path).st_mode):
            return entry
        if is_native(target_path):
            if node_target:
                return entry  # a Node shim must not be treated as a native launch
            entry.kind, entry.argv = "npm-native", [str(target_path), "--version"]
            entry.group = os.path.normcase(str(target_path))
        elif node_target:
            # Read only a bounded entry header, rejecting link redirection.
            bounded_read(target_path)
            entry.kind = "npm-js"
            entry.group = os.path.normcase(str(package))
            entry.node, entry.node_status = inspect_node(path.parent, dirs)
            engines = metadata.get("engines", {})
            requirement = engines.get("node") if isinstance(engines, dict) else None
            # Never export arbitrary package metadata strings.
            if isinstance(requirement, str) and re.fullmatch(r">=\d{1,4}(?:\.\d{1,4}){0,2}", requirement):
                entry.engine = requirement
            if entry.node:
                entry.argv = [str(entry.node), str(target_path), "--version"]
    except (OSError, ValueError, TypeError, AttributeError, RecursionError):
        pass
    return entry


def discover(tool, env):
    dirs, limited = path_dirs(env)
    if os.name == "nt":
        extensions = [v.lower() for v in env.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")
                      if v.lower() in (".com", ".exe", ".bat", ".cmd")]
        extensions = list(dict.fromkeys(extensions))
        observed = list(dict.fromkeys([*extensions, ".ps1", ""]))
    else:
        extensions, observed = [""], [""]
    entries = []
    seen = set()
    for directory in dirs:
        for suffix in observed:
            path = directory / (tool + suffix)
            try:
                if not stat.S_ISREG(checked_stat(path).st_mode):
                    continue
                key = os.path.normcase(str(path.absolute()))
                if key in seen:
                    continue
                seen.add(key)
                entries.append(classify(path, tool, dirs))
                if len(entries) >= 32:
                    limited = True
                    break
            except FileNotFoundError:
                continue
            except (OSError, ValueError):
                # Existence inside an inaccessible/reparse directory is unknown.
                # Retain its place in PATH; do not silently choose a later tool.
                entries.append(Entry(path, group=os.path.normcase(str(directory)), path_access="blocked"))
                if len(entries) >= 32:
                    limited = True
                    break
        if len(entries) >= 32:
            break
    cmd = next((e for e in entries if e.path.suffix.lower() in extensions), None)
    ps = None
    if os.name == "nt":
        # This is a PATH-only prediction; actual aliases/functions/policies vary.
        for directory in dirs:
            options = [e for e in entries if e.path.parent == directory]
            ps = next((e for suffix in [".ps1", *extensions] for e in options
                       if e.path.suffix.lower() == suffix), None)
            if ps:
                break
    return entries, cmd, ps, limited
