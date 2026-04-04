/**
 * NEXUS Wire Protocol — COBS (Consistent Overhead Byte Stuffing)
 *
 * Spec: specs/protocol/wire_protocol_spec.md §2.2-§2.3
 * Worst-case overhead: 1 byte per 254 bytes (0.4%)
 */

#ifndef NEXUS_COBS_H
#define NEXUS_COBS_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * COBS encode: source -> destination.
 * dst must be at least src_len + (src_len / 254) + 2 bytes.
 * Returns encoded length, or 0 on error.
 */
size_t cobs_encode(const uint8_t *src, size_t src_len,
                   uint8_t *dst, size_t dst_max);

/**
 * COBS decode: source -> destination.
 * dst must be at least src_len bytes.
 * Returns decoded length, or 0 on error.
 */
size_t cobs_decode(const uint8_t *src, size_t src_len,
                   uint8_t *dst, size_t dst_max);

#ifdef __cplusplus
}
#endif

#endif /* NEXUS_COBS_H */
