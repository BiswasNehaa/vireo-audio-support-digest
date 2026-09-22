"""Runs every test_*.py in this directory as a plain script (no pytest
dependency) and reports pass/fail per file."""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    failures = []
    for test_file in sorted(here.glob("test_*.py")):
        print(f"--- {test_file.name} ---")
        result = subprocess.run([sys.executable, str(test_file)])
        if result.returncode != 0:
            failures.append(test_file.name)
    print()
    if failures:
        print(f"FAILED: {failures}")
        sys.exit(1)
    print("All test files passed.")
