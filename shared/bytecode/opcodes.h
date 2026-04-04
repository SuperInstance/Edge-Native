/**
 * NEXUS Shared — Opcode Definitions (C)
 *
 * Canonical opcode enum shared between firmware and host tools.
 * This file must be kept in sync with opcodes.py.
 *
 * Spec: specs/firmware/reflex_bytecode_vm_spec.md §2.4
 */

#ifndef NEXUS_OPCODES_H
#define NEXUS_OPCODES_H

/* Core opcodes (0x00-0x1F) */
#define NEXUS_OP_NOP            0x00
#define NEXUS_OP_PUSH_I8        0x01
#define NEXUS_OP_PUSH_I16       0x02
#define NEXUS_OP_PUSH_F32       0x03
#define NEXUS_OP_POP            0x04
#define NEXUS_OP_DUP            0x05
#define NEXUS_OP_SWAP           0x06
#define NEXUS_OP_ROT            0x07
#define NEXUS_OP_ADD_F          0x08
#define NEXUS_OP_SUB_F          0x09
#define NEXUS_OP_MUL_F          0x0A
#define NEXUS_OP_DIV_F          0x0B
#define NEXUS_OP_NEG_F          0x0C
#define NEXUS_OP_ABS_F          0x0D
#define NEXUS_OP_MIN_F          0x0E
#define NEXUS_OP_MAX_F          0x0F
#define NEXUS_OP_CLAMP_F        0x10
#define NEXUS_OP_EQ_F           0x11
#define NEXUS_OP_LT_F           0x12
#define NEXUS_OP_GT_F           0x13
#define NEXUS_OP_LTE_F          0x14
#define NEXUS_OP_GTE_F          0x15
#define NEXUS_OP_AND_B          0x16
#define NEXUS_OP_OR_B           0x17
#define NEXUS_OP_XOR_B          0x18
#define NEXUS_OP_NOT_B          0x19
#define NEXUS_OP_READ_PIN       0x1A
#define NEXUS_OP_WRITE_PIN      0x1B
#define NEXUS_OP_READ_TIMER_MS  0x1C
#define NEXUS_OP_JUMP           0x1D
#define NEXUS_OP_JUMP_IF_FALSE  0x1E
#define NEXUS_OP_JUMP_IF_TRUE   0x1F

/* A2A extension opcodes (0x20-0x5F) — NOP on ESP32 firmware */
#define NEXUS_OP_DECLARE_INTENT     0x20
#define NEXUS_OP_ASSERT_GOAL        0x21
#define NEXUS_OP_VERIFY_OUTCOME     0x22
#define NEXUS_OP_EXPLAIN_FAILURE    0x23
#define NEXUS_OP_TELL               0x30
#define NEXUS_OP_ASK                0x31
#define NEXUS_OP_DELEGATE           0x32
#define NEXUS_OP_REPORT_STATUS      0x33
#define NEXUS_OP_REQUEST_OVERRIDE   0x34
#define NEXUS_OP_REQUIRE_CAPABILITY 0x40
#define NEXUS_OP_DECLARE_SENSOR     0x41
#define NEXUS_OP_DECLARE_ACTUATOR   0x42
#define NEXUS_OP_TRUST_CHECK        0x50
#define NEXUS_OP_AUTONOMY_ASSERT    0x51
#define NEXUS_OP_SAFE_BOUNDARY      0x52
#define NEXUS_OP_RATE_LIMIT         0x53

/* Syscall IDs (via NOP + FLAGS_SYSCALL) */
#define NEXUS_SYSCALL_HALT             0x01
#define NEXUS_SYSCALL_PID_COMPUTE      0x02
#define NEXUS_SYSCALL_RECORD_SNAPSHOT  0x03
#define NEXUS_SYSCALL_EMIT_EVENT       0x04

/* Flags byte */
#define NEXUS_FLAGS_HAS_IMMEDIATE  (1 << 0)
#define NEXUS_FLAGS_IS_FLOAT       (1 << 1)
#define NEXUS_FLAGS_EXTENDED_CLAMP (1 << 2)
#define NEXUS_FLAGS_IS_CALL        (1 << 3)
#define NEXUS_FLAGS_SYSCALL        (1 << 7)

#endif /* NEXUS_OPCODES_H */
