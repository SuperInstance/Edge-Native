#!/usr/bin/env python3
"""
NEXUS — Test Orchestration Script

Runs all test suites: C unit tests (host), Python unit tests, and optionally HIL tests.

Usage:
    python tools/test_runner.py              # Run all host tests
    python tools/test_runner.py --hil        # Include HIL tests
    python tools/test_runner.py --firmware   # C tests only
    python tools/test_runner.py --jetson     # Python tests only
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a command and return exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def run_firmware_tests(root: Path) -> int:
    """Build and run C unit tests on host."""
    build_dir = root / "build"
    build_dir.mkdir(exist_ok=True)

    rc = run_cmd(["cmake", "-DNEXUS_HOST_TEST=ON", ".."], cwd=build_dir)
    if rc != 0:
        return rc

    rc = run_cmd(["make", "-j4"], cwd=build_dir)
    if rc != 0:
        return rc

    return run_cmd(["ctest", "--output-on-failure", "-j4"], cwd=build_dir)


def run_jetson_tests(root: Path, include_hil: bool = False) -> int:
    """Run Python unit tests."""
    cmd = ["pytest", "tests/unit/jetson/", "-v", "--tb=short"]
    if include_hil:
        cmd = ["pytest", "tests/", "-v", "--tb=short"]
    return run_cmd(cmd, cwd=root)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="NEXUS Test Runner")
    parser.add_argument("--firmware", action="store_true", help="Run C tests only")
    parser.add_argument("--jetson", action="store_true", help="Run Python tests only")
    parser.add_argument("--hil", action="store_true", help="Include HIL tests")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    results: list[tuple[str, int]] = []

    run_all = not args.firmware and not args.jetson

    if args.firmware or run_all:
        rc = run_firmware_tests(root)
        results.append(("Firmware (C)", rc))

    if args.jetson or run_all:
        rc = run_jetson_tests(root, include_hil=args.hil)
        results.append(("Jetson (Python)", rc))

    print(f"\n{'='*60}")
    print("RESULTS:")
    for name, rc in results:
        status = "PASS" if rc == 0 else "FAIL"
        print(f"  {name}: {status}")
    print(f"{'='*60}")

    return 0 if all(rc == 0 for _, rc in results) else 1


if __name__ == "__main__":
    sys.exit(main())
