#!/usr/bin/env bash
# NEXUS — ESP32-S3 Flash Script
#
# Usage: ./tools/flash.sh [port]
# Default port: /dev/ttyUSB0

set -euo pipefail

PORT="${1:-/dev/ttyUSB0}"
FIRMWARE_DIR="$(dirname "$0")/../firmware"

echo "=== NEXUS Flash Tool ==="
echo "Port: $PORT"
echo "Firmware: $FIRMWARE_DIR"

if [ ! -d "$FIRMWARE_DIR/build" ]; then
    echo "ERROR: No build directory found. Run 'cd firmware && idf.py build' first."
    exit 1
fi

cd "$FIRMWARE_DIR"

echo "Flashing ESP32-S3..."
idf.py -p "$PORT" flash

echo "Starting monitor..."
idf.py -p "$PORT" monitor
