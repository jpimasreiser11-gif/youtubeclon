"""
YouTube Automation Pro setup helper.
Installs dependencies, runs smoke checks, and prints next-step status.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(cmd: list[str], cwd: Path | None = None) -> int:
    if cmd and cmd[0] == "npm" and sys.platform.startswith("win"):
        cmd = [shutil.which("npm.cmd") or "npm.cmd", *cmd[1:]]
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(cwd or ROOT)).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup YouTube Automation Pro")
    parser.add_argument("--skip-frontend", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    if run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]) != 0:
        return 1

    if not args.skip_frontend:
        if run(["npm", "install"], cwd=ROOT / "frontend") != 0:
            return 1

    if not args.skip_tests:
        if run([sys.executable, "tests/run_phase7_checks.py"]) != 0:
            return 1

    print("\nSetup complete.")
    print("- Run API: python run.py server")
    print("- Run frontend: cd frontend && npm run dev")
    print("- Test report: tests/reports/phase7-report.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

