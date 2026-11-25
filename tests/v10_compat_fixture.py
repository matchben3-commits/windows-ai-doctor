"""Run the real CLI on authored observations, with an explicit import boundary.

With no --source-root the isolated interpreter imports only its installed wheel.
The fixture never probes the host. It cannot be used as live-host evidence.
"""
import argparse
import copy
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--observations", required=True, type=Path)
    options, arguments = parser.parse_known_args()
    if options.source_root:
        sys.path.insert(0, str(options.source_root))
    from windows_ai_doctor import __version__, cli

    document = json.loads(options.observations.read_text(encoding="utf-8"))

    class AuthoredDoctor:
        def __init__(self, **kwargs):
            self.lang = kwargs["lang"]

        def run(self):
            report = copy.deepcopy(document)
            report.update(doctor_version=__version__, language=self.lang)
            return report

    cli.Doctor = AuthoredDoctor
    return cli.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
