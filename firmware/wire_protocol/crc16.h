/**
 * NEXUS Wire Protocol — CRC-16/CCITT-FALSE
 *
 * Polynomial: 0x1021, Init: 0xFFFF, Final XOR: 0x0000
 * No reflection. Check value for "123456789": 0x29B1
 *
 * Spec: specs/protocol/wire_protocol_spec.md §2.4
 */

#ifndef NEXUS_CRC16_H
#define NEXUS_CRC16_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Compute CRC-16/CCITT-FALSE over data buffer. */
uint16_t crc16_ccitt(const uint8_t *data, size_t len);

#ifdef __cplusplus
}
#endif

#endif /* NEXUS_CRC16_H */
