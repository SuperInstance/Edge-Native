"""
HIL Test: Safety System Response Time

Measures kill switch and safety system response times on real hardware.
Requires oscilloscope on actuator outputs and kill switch GPIO.

Sprint 0.1 skeleton — actual implementation in Sprint 1.1.
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="HIL: requires safety hardware setup")
class TestSafetyResponse:
    """Verify safety system timing on real hardware."""

    def test_kill_switch_response(self) -> None:
        """Kill switch triggers actuator safe-state within 1ms."""
        # TODO Sprint 1.1: Trigger kill switch GPIO
        # Measure time on oscilloscope until all actuator outputs
        # reach safe state (0V / low)
        # Assert: response time < 1ms (0.93ms per spec)

    def test_watchdog_reset(self) -> None:
        """Hardware watchdog resets MCU within timeout period."""
        # TODO Sprint 1.1: Stop feeding watchdog
        # Measure time until MCU reset
        # Assert: reset occurs within configured WDT timeout

    def test_overcurrent_trip(self) -> None:
        """INA219 overcurrent detection triggers within 10ms."""
        # TODO Sprint 1.1: Apply overcurrent condition to test load
        # Measure time until safety system disables output
        # Assert: trip time < 10ms
