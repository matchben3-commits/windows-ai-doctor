"""Compare code/docs/tests to a caller-specified preserved release snapshot."""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def hashes(root):
    result = {}
    for folder, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "evidence", ".task-build", "dist", "build", "__pycache__") and not d.endswith(".egg-info")]
        for name in names:
            p = Path(folder) / name
            if name == "SHA256SUMS.txt":
                continue
            if p.suffix in (".py", ".md", ".toml", ".txt", ".in", ".yml") or name in (".gitignore", "LICENSE"):
                result[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


if __name__ == "__main__":
    baseline = Path(sys.argv[1]).absolute()
    old, new = hashes(baseline), hashes(ROOT)
    record = {"generated_at": datetime.now(timezone.utc).isoformat(), "baseline": "preserved public v0.1.0 release snapshot",
              "release_record_commit": "aa99e952d77f418e7bbf932e6219c44707abd4f7", "remote_reverified": False,
              "scope": "code/docs/tests and text fixtures, excluding evidence, manifests, dist and temporary build dirs",
              "baseline_sha256": old,
              "changed": [{"file": p, "before": old[p], "after": new[p]} for p in sorted(old.keys() & new.keys()) if old[p] != new[p]],
              "added": [{"file": p, "sha256": new[p]} for p in sorted(new.keys() - old.keys())],
              "removed": sorted(old.keys() - new.keys()),
              "unchanged_count": sum(old[p] == new[p] for p in old.keys() & new.keys())}
    (ROOT / "evidence/v02-baseline.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("baseline recorded; original snapshot read only")
