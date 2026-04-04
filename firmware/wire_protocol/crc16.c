/**
 * NEXUS Wire Protocol — CRC-16/CCITT-FALSE Implementation
 *
 * Reference implementation from build-specification.md §2.1
 * Check value: crc16_ccitt("123456789", 9) == 0x29B1
 */

#include "crc16.h"

uint16_t crc16_ccitt(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000)
                crc = (crc << 1) ^ 0x1021;
            else
                crc = crc << 1;
        }
    }
    return crc;
}
