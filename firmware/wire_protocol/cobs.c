/**
 * NEXUS Wire Protocol — COBS Implementation
 *
 * Reference implementation from build-specification.md §2.1
 * Spec: specs/protocol/wire_protocol_spec.md §2.2-§2.3
 */

#include "cobs.h"

size_t cobs_encode(const uint8_t *src, size_t src_len,
                   uint8_t *dst, size_t dst_max)
{
    size_t src_idx = 0;
    size_t dst_idx = 0;
    size_t code_idx = 0;
    uint8_t code = 0x01;

    if (dst_max < src_len + 1) return 0;

    dst[0] = 0x01;  /* placeholder for first code byte */
    dst_idx = 1;

    while (src_idx < src_len) {
        if (src[src_idx] == 0x00) {
            dst[code_idx] = code;
            code = 0x01;
            code_idx = dst_idx++;
            if (dst_idx >= dst_max) return 0;
        } else {
            dst[dst_idx++] = src[src_idx];
            if (dst_idx >= dst_max) return 0;
            code++;
            if (code == 0xFF) {
                dst[code_idx] = code;
                code = 0x01;
                code_idx = dst_idx++;
                if (dst_idx >= dst_max) return 0;
            }
        }
        src_idx++;
    }

    dst[code_idx] = code;
    return dst_idx;
}

size_t cobs_decode(const uint8_t *src, size_t src_len,
                   uint8_t *dst, size_t dst_max)
{
    size_t src_idx = 0;
    size_t dst_idx = 0;

    while (src_idx < src_len) {
        uint8_t code = src[src_idx++];
        if (src_idx + code - 1 > src_len) return 0;

        for (uint8_t i = 1; i < code; i++) {
            if (dst_idx >= dst_max) return 0;
            dst[dst_idx++] = src[src_idx++];
        }

        if (code < 0xFF && src_idx < src_len) {
            if (dst_idx >= dst_max) return 0;
            dst[dst_idx++] = 0x00;
        }
    }

    return dst_idx;
}
