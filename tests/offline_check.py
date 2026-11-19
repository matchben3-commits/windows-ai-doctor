"""Run the real CLI while Python network operations are denied by audit hook.

This does not disconnect the host adapter or sandbox third-party executables.
"""
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def deny_network(event, args):
    if event.startswith("socket."):
        raise RuntimeError("network_denied_for_offline_check")


sys.addaudithook(deny_network)
# This validation intentionally launches no third-party version commands.
sys.argv = [str(ROOT / "doctor.py"), "--no-version", *sys.argv[1:]]
runpy.run_path(str(ROOT / "doctor.py"), run_name="__main__")
