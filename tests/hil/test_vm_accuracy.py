"""
HIL Test: VM Tick Timing Accuracy

Measures VM tick execution timing on real ESP32-S3 hardware.
Requires oscilloscope-connected GPIO for timing measurement.

Sprint 0.1 skeleton — actual implementation in Sprint 0.2.
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="HIL: requires ESP32-S3 hardware")
class TestVMTimingAccuracy:
    """Verify VM tick timing on real hardware."""

    def test_tick_period_1ms(self) -> None:
        """VM tick executes within 1ms ± 50μs."""
        # TODO Sprint 0.2: Connect oscilloscope to GPIO toggle pin
        # Measure period of VM tick task toggle
        # Assert: mean period = 1.000ms ± 0.050ms
        # Assert: max jitter < 100μs

    def test_opcode_cycle_counts(self) -> None:
        """Measured cycle counts match published spec values within 10%."""
        # TODO Sprint 0.2: Run each opcode 10,000 times
        # Measure wall-clock time via DWT cycle counter
        # Compare to published cycle counts in spec §5

    def test_worst_case_tick(self) -> None:
        """Worst-case program (10,000 cycles) completes within 1ms."""
        # TODO Sprint 0.2: Deploy a program that uses exactly
        # 10,000 cycles and verify it completes within the tick period
