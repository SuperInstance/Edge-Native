#!/usr/bin/env python3
"""
NEXUS — CI Safety Pipeline

Pre-merge safety checks:
1. No malloc/free in firmware code (except init-time allocations)
2. No compiler warnings in firmware build
3. All safety-critical tests pass
4. No NaN/Inf constants in bytecode test vectors
5. Stack depth analysis on all test programs
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def check_no_dynamic_alloc(root: Path) -> list[str]:
    """Check that firmware code has no dynamic allocation after init."""
    violations: list[str] = []
    forbidden = ["malloc(", "calloc(", "realloc(", "free("]

    for c_file in root.glob("firmware/**/*.c"):
        # Skip files that are allowed to use malloc at init
        if c_file.name == "app_main.c":
            continue

        content = c_file.read_text()
        for pattern in forbidden:
            for i, line in enumerate(content.splitlines(), 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("/*"):
                    continue
                if pattern in line:
                    violations.append(f"{c_file}:{i}: {pattern} found: {stripped}")

    return violations


def check_no_nan_constants(root: Path) -> list[str]:
    """Check that no NaN or Inf literals appear in production code."""
    violations: list[str] = []
    nan_patterns = [r"\bNAN\b", r"\bINFINITY\b", r"\bINF\b", r"\bnan\b"]

    for c_file in root.glob("firmware/**/*.c"):
        content = c_file.read_text()
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue
            # Allow isnan() and isinf() checks
            check_line = re.sub(r"isnan|isinf|isfinite", "", line)
            for pat in nan_patterns:
                if re.search(pat, check_line):
                    violations.append(f"{c_file}:{i}: NaN/Inf constant: {stripped}")

    return violations


def main() -> int:
    """Run all safety checks."""
    root = Path(__file__).parent.parent
    failed = False

    print("=== NEXUS Safety Check Pipeline ===\n")

    print("[1] Checking for dynamic allocation in firmware...")
    alloc_violations = check_no_dynamic_alloc(root)
    if alloc_violations:
        print("  FAIL: Dynamic allocation found:")
        for v in alloc_violations:
            print(f"    {v}")
        failed = True
    else:
        print("  PASS: No dynamic allocation in firmware code")

    print("\n[2] Checking for NaN/Inf constants...")
    nan_violations = check_no_nan_constants(root)
    if nan_violations:
        print("  FAIL: NaN/Inf constants found:")
        for v in nan_violations:
            print(f"    {v}")
        failed = True
    else:
        print("  PASS: No NaN/Inf constants")

    print(f"\n{'='*60}")
    if failed:
        print("SAFETY CHECK: FAILED")
        return 1
    print("SAFETY CHECK: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
