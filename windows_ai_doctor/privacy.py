"""Reports carry opaque path references, never configuration or process output."""
import re


class Privacy:
    def __init__(self):
        self._paths = {}

    def path(self, value):
        key = str(value).replace("/", "\\").casefold()
        if key not in self._paths:
            self._paths[key] = f"<PATH:{len(self._paths) + 1}>"
        return self._paths[key]


def safe_version(text, tool):
    """Accept only a complete, short version response. Discard everything else."""
    patterns = {
        "codex": r"codex-cli (\d{1,4}\.\d{1,4}\.\d{1,4}(?:-[a-zA-Z0-9.]{1,32})?)",
        "claude": r"(\d{1,4}\.\d{1,4}\.\d{1,4}(?:-[a-zA-Z0-9.]{1,32})?)(?: \(Claude Code\))?",
        "node": r"v(\d{1,4}\.\d{1,4}\.\d{1,4})",
    }
    match = re.fullmatch(patterns[tool], text.strip()) if len(text) < 160 else None
    return match.group(1) if match else None
