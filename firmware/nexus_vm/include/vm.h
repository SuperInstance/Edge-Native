/**
 * NEXUS Bytecode VM — Public Interface
 *
 * 32-opcode stack machine for ESP32-S3. All memory statically allocated.
 * Spec reference: specs/firmware/reflex_bytecode_vm_spec.md
 */

#ifndef NEXUS_VM_H
#define NEXUS_VM_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ── Constants (from spec §4) ─────────────────────────────────────────── */

#define VM_STACK_SIZE         256
#define VM_CALL_STACK_SIZE     16
#define VM_VAR_COUNT          256
#define VM_SENSOR_COUNT        64
#define VM_ACTUATOR_COUNT      64
#define VM_PID_COUNT            8
#define VM_SNAPSHOT_COUNT      16
#define VM_EVENT_RING_SIZE     32
#define VM_MAX_CYCLE_BUDGET 100000
#define VM_DEFAULT_CYCLE_BUDGET 10000
#define VM_MAX_BYTECODE_SIZE 102400  /* 100 KB */

/* ── Instruction Format (8 bytes, packed) ─────────────────────────────── */

typedef struct __attribute__((packed)) {
    uint8_t  opcode;    /* Byte 0: 0x00-0x1F (core), 0x20+ (A2A extension) */
    uint8_t  flags;     /* Byte 1: bit field */
    uint16_t operand1;  /* Bytes 2-3: uint16 (little-endian) */
    uint32_t operand2;  /* Bytes 4-7: uint32 (little-endian) */
} instruction_t;

_Static_assert(sizeof(instruction_t) == 8, "instruction_t must be exactly 8 bytes");

/* Flags byte bit definitions */
#define FLAGS_HAS_IMMEDIATE   (1 << 0)
#define FLAGS_IS_FLOAT        (1 << 1)
#define FLAGS_EXTENDED_CLAMP  (1 << 2)
#define FLAGS_IS_CALL         (1 << 3)
#define FLAGS_SYSCALL         (1 << 7)

/* ── Opcodes (spec §2.4) ─────────────────────────────────────────────── */

typedef enum {
    /* Stack (0x00-0x07) */
    OP_NOP       = 0x00,
    OP_PUSH_I8   = 0x01,
    OP_PUSH_I16  = 0x02,
    OP_PUSH_F32  = 0x03,
    OP_POP       = 0x04,
    OP_DUP       = 0x05,
    OP_SWAP      = 0x06,
    OP_ROT       = 0x07,

    /* Arithmetic (0x08-0x10) */
    OP_ADD_F     = 0x08,
    OP_SUB_F     = 0x09,
    OP_MUL_F     = 0x0A,
    OP_DIV_F     = 0x0B,
    OP_NEG_F     = 0x0C,
    OP_ABS_F     = 0x0D,
    OP_MIN_F     = 0x0E,
    OP_MAX_F     = 0x0F,
    OP_CLAMP_F   = 0x10,

    /* Comparison (0x11-0x15) */
    OP_EQ_F      = 0x11,
    OP_LT_F      = 0x12,
    OP_GT_F      = 0x13,
    OP_LTE_F     = 0x14,
    OP_GTE_F     = 0x15,

    /* Logic (0x16-0x19) */
    OP_AND_B     = 0x16,
    OP_OR_B      = 0x17,
    OP_XOR_B     = 0x18,
    OP_NOT_B     = 0x19,

    /* I/O (0x1A-0x1C) */
    OP_READ_PIN      = 0x1A,
    OP_WRITE_PIN     = 0x1B,
    OP_READ_TIMER_MS = 0x1C,

    /* Control (0x1D-0x1F) */
    OP_JUMP          = 0x1D,
    OP_JUMP_IF_FALSE = 0x1E,
    OP_JUMP_IF_TRUE  = 0x1F,

    OP_COUNT         = 0x20,  /* Number of core opcodes */
} opcode_t;

/* Syscall IDs (NOP with FLAGS_SYSCALL) */
typedef enum {
    SYSCALL_HALT            = 0x01,
    SYSCALL_PID_COMPUTE     = 0x02,
    SYSCALL_RECORD_SNAPSHOT = 0x03,
    SYSCALL_EMIT_EVENT      = 0x04,
} syscall_id_t;

/* ── Error Codes ──────────────────────────────────────────────────────── */

typedef enum {
    VM_OK = 0,
    ERR_STACK_UNDERFLOW,
    ERR_STACK_OVERFLOW,
    ERR_INVALID_OPCODE,
    ERR_INVALID_OPERAND,
    ERR_JUMP_OUT_OF_BOUNDS,
    ERR_CALL_STACK_OVERFLOW,
    ERR_CALL_STACK_UNDERFLOW,
    ERR_CYCLE_BUDGET_EXCEEDED,
    ERR_INVALID_SYSCALL,
    ERR_INVALID_PID,
    ERR_DIVISION_BY_ZERO,
    ERR_NAN_DETECTED,
    ERR_NO_BYTECODE,
} vm_error_t;

/* ── PID Controller State (32 bytes) ──────────────────────────────────── */

typedef struct {
    float Kp, Ki, Kd;
    float integral;
    float prev_error;
    float integral_limit;
    float output_min, output_max;
} pid_state_t;

/* ── VM Snapshot (128 bytes) ──────────────────────────────────────────── */

typedef struct {
    uint32_t tick_ms;
    uint32_t cycle_count;
    uint32_t current_state;
    uint32_t variables[15];
    uint32_t sensors[14];
} vm_snapshot_t;

_Static_assert(sizeof(vm_snapshot_t) == 128, "vm_snapshot_t must be 128 bytes");

/* ── VM Event (8 bytes) ───────────────────────────────────────────────── */

typedef struct {
    uint32_t tick_ms;
    uint16_t event_id;
    uint16_t event_data;
} vm_event_t;

_Static_assert(sizeof(vm_event_t) == 8, "vm_event_t must be 8 bytes");

/* ── VM State ─────────────────────────────────────────────────────────── */

typedef struct {
    /* Data stack */
    uint32_t stack[VM_STACK_SIZE];
    uint16_t sp;

    /* Program counter */
    uint32_t pc;

    /* Variable space */
    uint32_t vars[VM_VAR_COUNT];

    /* Sensor registers (read-only from VM, populated by host before tick) */
    uint32_t sensors[VM_SENSOR_COUNT];

    /* Actuator registers (write-only from VM, drained by host after tick) */
    uint32_t actuators[VM_ACTUATOR_COUNT];

    /* Execution state */
    uint32_t flags;
    uint32_t cycle_count;
    uint32_t cycle_budget;
    uint32_t tick_count_ms;
    float    tick_period_sec;

    /* Call stack */
    struct {
        uint32_t return_addr;
        uint16_t frame_pointer;
    } call_stack[VM_CALL_STACK_SIZE];
    uint16_t csp;

    /* PID controllers */
    pid_state_t pid[VM_PID_COUNT];

    /* Snapshot buffer */
    vm_snapshot_t snapshots[VM_SNAPSHOT_COUNT];
    uint8_t next_snapshot;

    /* Event ring buffer */
    vm_event_t events[VM_EVENT_RING_SIZE];
    uint16_t event_head;
    uint16_t event_tail;

    /* Error/halt state */
    vm_error_t last_error;
    bool halted;

    /* Bytecode pointer and size (set at load time) */
    const uint8_t *bytecode;
    uint32_t bytecode_size;
} vm_state_t;

/* ── Public API ───────────────────────────────────────────────────────── */

/** Initialize VM state to safe defaults. */
void vm_init(vm_state_t *vm);

/** Reset VM for a new tick (preserves bytecode, sensors, PIDs). */
void vm_reset_tick(vm_state_t *vm);

/** Load bytecode into VM. Returns VM_OK or error. */
vm_error_t vm_load_bytecode(vm_state_t *vm, const uint8_t *code, uint32_t size);

/** Execute one tick of the VM. Returns VM_OK or error code. */
vm_error_t vm_execute_tick(vm_state_t *vm);

/** Validate bytecode before execution. Returns VM_OK or error code. */
vm_error_t vm_validate_bytecode(const uint8_t *code, uint32_t size);

/** Get human-readable error string. */
const char *vm_error_str(vm_error_t err);

#ifdef __cplusplus
}
#endif

#endif /* NEXUS_VM_H */
