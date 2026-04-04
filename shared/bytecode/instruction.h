/**
 * NEXUS Shared — 8-Byte Fixed Instruction Format (C)
 *
 * Canonical instruction struct shared between firmware and host tools.
 * Spec: specs/firmware/reflex_bytecode_vm_spec.md §2
 */

#ifndef NEXUS_INSTRUCTION_H
#define NEXUS_INSTRUCTION_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct __attribute__((packed)) {
    uint8_t  opcode;    /* Byte 0: opcode */
    uint8_t  flags;     /* Byte 1: flags bit field */
    uint16_t operand1;  /* Bytes 2-3: uint16 (little-endian on ESP32) */
    uint32_t operand2;  /* Bytes 4-7: uint32 (little-endian on ESP32) */
} nexus_instruction_t;

_Static_assert(sizeof(nexus_instruction_t) == 8,
               "nexus_instruction_t must be exactly 8 bytes");

#ifdef __cplusplus
}
#endif

#endif /* NEXUS_INSTRUCTION_H */
