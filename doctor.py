"""Source checkout entry point; also works with Windows embeddable Python."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
if sys.version_info < (3, 11):
    raise SystemExit("需要 Python 3.11+ / Python 3.11+ is required.")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from windows_ai_doctor.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
