"""
HIL Test: Wire Protocol Round-Trip Latency

Measures end-to-end wire protocol latency between Jetson and ESP32.
Requires RS-422 connection between Jetson and ESP32-S3.

Sprint 0.1 skeleton — actual implementation in Sprint 0.3.
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="HIL: requires ESP32-S3 + RS-422 hardware")
class TestWireRoundTrip:
    """Verify wire protocol latency on real hardware."""

    def test_heartbeat_rtt(self) -> None:
        """HEARTBEAT round-trip time < 5ms."""
        # TODO Sprint 0.3: Send HEARTBEAT from Jetson
        # Measure time until ACK received from ESP32
        # Assert: RTT < 5ms (mean of 1000 samples)

    def test_reflex_deploy_rtt(self) -> None:
        """REFLEX_DEPLOY round-trip time < 50ms for 1KB reflex."""
        # TODO Sprint 0.3: Deploy 1KB reflex via REFLEX_DEPLOY
        # Measure time until COMMAND_ACK received
        # Assert: RTT < 50ms

    def test_throughput(self) -> None:
        """Sustained throughput > 100 KB/s at 921600 baud."""
        # TODO Sprint 0.3: Send 100KB of data in back-to-back frames
        # Measure wall-clock time for all ACKs
        # Assert: throughput > 100 KB/s
