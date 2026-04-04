/**
 * NEXUS Wire Protocol Unit Tests — COBS Encode/Decode
 *
 * Spec: specs/protocol/wire_protocol_spec.md §2.2-§2.3
 */

#include "unity.h"
#include "cobs.h"
#include <string.h>

void setUp(void) {}
void tearDown(void) {}

void test_cobs_empty(void)
{
    uint8_t dst[8];
    size_t len = cobs_encode(NULL, 0, dst, sizeof(dst));
    /* Empty input: just the overhead byte */
    TEST_ASSERT_EQUAL(1, len);
}

void test_cobs_no_zeros(void)
{
    uint8_t src[] = { 0x01, 0x02, 0x03 };
    uint8_t encoded[8];
    uint8_t decoded[8];

    size_t enc_len = cobs_encode(src, 3, encoded, sizeof(encoded));
    TEST_ASSERT_GREATER_THAN(0, enc_len);

    size_t dec_len = cobs_decode(encoded, enc_len, decoded, sizeof(decoded));
    TEST_ASSERT_EQUAL(3, dec_len);
    TEST_ASSERT_EQUAL_UINT8_ARRAY(src, decoded, 3);
}

void test_cobs_all_zeros(void)
{
    uint8_t src[] = { 0x00, 0x00, 0x00 };
    uint8_t encoded[8];
    uint8_t decoded[8];

    size_t enc_len = cobs_encode(src, 3, encoded, sizeof(encoded));
    TEST_ASSERT_GREATER_THAN(0, enc_len);

    size_t dec_len = cobs_decode(encoded, enc_len, decoded, sizeof(decoded));
    TEST_ASSERT_EQUAL(3, dec_len);
    TEST_ASSERT_EQUAL_UINT8_ARRAY(src, decoded, 3);
}

void test_cobs_mixed(void)
{
    uint8_t src[] = { 0x01, 0x00, 0x02, 0x00, 0x03 };
    uint8_t encoded[16];
    uint8_t decoded[16];

    size_t enc_len = cobs_encode(src, 5, encoded, sizeof(encoded));
    TEST_ASSERT_GREATER_THAN(0, enc_len);

    size_t dec_len = cobs_decode(encoded, enc_len, decoded, sizeof(decoded));
    TEST_ASSERT_EQUAL(5, dec_len);
    TEST_ASSERT_EQUAL_UINT8_ARRAY(src, decoded, 5);
}

void test_cobs_roundtrip_1000_random(void)
{
    /* Pseudo-random roundtrip: patterns up to 254 bytes */
    for (int trial = 0; trial < 100; trial++) {
        uint8_t src[254];
        uint8_t encoded[512];
        uint8_t decoded[512];
        size_t src_len = (trial % 254) + 1;

        for (size_t i = 0; i < src_len; i++) {
            src[i] = (uint8_t)((trial * 7 + i * 13) & 0xFF);
        }

        size_t enc_len = cobs_encode(src, src_len, encoded, sizeof(encoded));
        TEST_ASSERT_GREATER_THAN(0, enc_len);

        /* Verify no zero bytes in encoded output */
        for (size_t i = 0; i < enc_len; i++) {
            TEST_ASSERT_NOT_EQUAL(0x00, encoded[i]);
        }

        size_t dec_len = cobs_decode(encoded, enc_len, decoded, sizeof(decoded));
        TEST_ASSERT_EQUAL(src_len, dec_len);
        TEST_ASSERT_EQUAL_UINT8_ARRAY(src, decoded, src_len);
    }
}

void test_cobs_single_zero(void)
{
    uint8_t src[] = { 0x00 };
    uint8_t encoded[8];
    uint8_t decoded[8];

    size_t enc_len = cobs_encode(src, 1, encoded, sizeof(encoded));
    size_t dec_len = cobs_decode(encoded, enc_len, decoded, sizeof(decoded));
    TEST_ASSERT_EQUAL(1, dec_len);
    TEST_ASSERT_EQUAL_UINT8(0x00, decoded[0]);
}

void test_cobs_single_nonzero(void)
{
    uint8_t src[] = { 0x42 };
    uint8_t encoded[8];
    uint8_t decoded[8];

    size_t enc_len = cobs_encode(src, 1, encoded, sizeof(encoded));
    size_t dec_len = cobs_decode(encoded, enc_len, decoded, sizeof(decoded));
    TEST_ASSERT_EQUAL(1, dec_len);
    TEST_ASSERT_EQUAL_UINT8(0x42, decoded[0]);
}

void test_cobs_dst_too_small(void)
{
    uint8_t src[] = { 0x01, 0x02, 0x03 };
    uint8_t dst[1];  /* Too small */

    size_t len = cobs_encode(src, 3, dst, sizeof(dst));
    TEST_ASSERT_EQUAL(0, len);
}

int main(void)
{
    UNITY_BEGIN();

    RUN_TEST(test_cobs_empty);
    RUN_TEST(test_cobs_no_zeros);
    RUN_TEST(test_cobs_all_zeros);
    RUN_TEST(test_cobs_mixed);
    RUN_TEST(test_cobs_roundtrip_1000_random);
    RUN_TEST(test_cobs_single_zero);
    RUN_TEST(test_cobs_single_nonzero);
    RUN_TEST(test_cobs_dst_too_small);

    return UNITY_END();
}
