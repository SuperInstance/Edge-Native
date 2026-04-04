/**
 * NEXUS Wire Protocol Unit Tests — CRC-16/CCITT-FALSE
 *
 * Check value: crc16_ccitt("123456789", 9) == 0x29B1
 * Spec: specs/protocol/wire_protocol_spec.md §2.4
 */

#include "unity.h"
#include "crc16.h"
#include <string.h>

void setUp(void) {}
void tearDown(void) {}

void test_crc16_check_value(void)
{
    /* The canonical check value for CRC-16/CCITT-FALSE */
    const uint8_t data[] = "123456789";
    uint16_t crc = crc16_ccitt(data, 9);
    TEST_ASSERT_EQUAL_HEX16(0x29B1, crc);
}

void test_crc16_empty(void)
{
    uint16_t crc = crc16_ccitt(NULL, 0);
    TEST_ASSERT_EQUAL_HEX16(0xFFFF, crc);
}

void test_crc16_single_byte(void)
{
    uint8_t data[] = { 0x00 };
    uint16_t crc = crc16_ccitt(data, 1);
    /* CRC(0x00) with init 0xFFFF: 0xFFFF XOR 0x00<<8 = 0xFFFF,
       then 8 rounds of polynomial division */
    TEST_ASSERT_NOT_EQUAL(0x0000, crc);
    TEST_ASSERT_NOT_EQUAL(0xFFFF, crc);
}

void test_crc16_all_zeros(void)
{
    uint8_t data[8] = { 0 };
    uint16_t crc = crc16_ccitt(data, 8);
    TEST_ASSERT_NOT_EQUAL(0x0000, crc);
}

void test_crc16_all_ones(void)
{
    uint8_t data[4] = { 0xFF, 0xFF, 0xFF, 0xFF };
    uint16_t crc = crc16_ccitt(data, 4);
    TEST_ASSERT_NOT_EQUAL(0x0000, crc);
}

void test_crc16_detects_bit_flip(void)
{
    uint8_t data1[] = { 0x01, 0x02, 0x03, 0x04 };
    uint8_t data2[] = { 0x01, 0x02, 0x03, 0x05 };  /* last byte flipped */

    uint16_t crc1 = crc16_ccitt(data1, 4);
    uint16_t crc2 = crc16_ccitt(data2, 4);
    TEST_ASSERT_NOT_EQUAL(crc1, crc2);
}

void test_crc16_detects_byte_swap(void)
{
    uint8_t data1[] = { 0x01, 0x02 };
    uint8_t data2[] = { 0x02, 0x01 };  /* bytes swapped */

    uint16_t crc1 = crc16_ccitt(data1, 2);
    uint16_t crc2 = crc16_ccitt(data2, 2);
    TEST_ASSERT_NOT_EQUAL(crc1, crc2);
}

void test_crc16_detects_insertion(void)
{
    uint8_t data1[] = { 0x01, 0x02, 0x03 };
    uint8_t data2[] = { 0x01, 0x00, 0x02, 0x03 };  /* zero inserted */

    uint16_t crc1 = crc16_ccitt(data1, 3);
    uint16_t crc2 = crc16_ccitt(data2, 4);
    TEST_ASSERT_NOT_EQUAL(crc1, crc2);
}

void test_crc16_consistent(void)
{
    /* Same data must produce same CRC every time (determinism) */
    uint8_t data[] = { 0xDE, 0xAD, 0xBE, 0xEF };
    uint16_t crc1 = crc16_ccitt(data, 4);
    uint16_t crc2 = crc16_ccitt(data, 4);
    TEST_ASSERT_EQUAL_HEX16(crc1, crc2);
}

int main(void)
{
    UNITY_BEGIN();

    RUN_TEST(test_crc16_check_value);
    RUN_TEST(test_crc16_empty);
    RUN_TEST(test_crc16_single_byte);
    RUN_TEST(test_crc16_all_zeros);
    RUN_TEST(test_crc16_all_ones);
    RUN_TEST(test_crc16_detects_bit_flip);
    RUN_TEST(test_crc16_detects_byte_swap);
    RUN_TEST(test_crc16_detects_insertion);
    RUN_TEST(test_crc16_consistent);

    return UNITY_END();
}
