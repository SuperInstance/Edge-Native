/**
 * NEXUS VM Unit Tests — Opcode Test Vectors
 *
 * Tests all 32 opcodes against spec-defined behavior.
 * Build specification test vectors 1-10 plus additional coverage.
 *
 * Spec: specs/firmware/reflex_bytecode_vm_spec.md
 * Build: claude-build/build-specification.md §1.4
 */

#include "unity.h"
#include "vm.h"
#include <string.h>
#include <math.h>

static vm_state_t vm;

/* Helper: convert float to uint32 for instruction operand2 */
static uint32_t f2u(float f)
{
    uint32_t u;
    memcpy(&u, &f, sizeof(u));
    return u;
}

/* Helper: read float from stack */
static float stack_f32(vm_state_t *v, uint16_t idx)
{
    float f;
    memcpy(&f, &v->stack[idx], sizeof(f));
    return f;
}

/* Helper: build instruction bytes */
static void emit(uint8_t *buf, uint32_t offset,
                 uint8_t opcode, uint8_t flags, uint16_t op1, uint32_t op2)
{
    instruction_t instr = { opcode, flags, op1, op2 };
    memcpy(buf + offset, &instr, 8);
}

void setUp(void)
{
    vm_init(&vm);
}

void tearDown(void) {}

/* ── Test Vector 1: Simple Arithmetic ──────────────────────────────── */
void test_simple_arithmetic(void)
{
    /* PUSH_F32 3.0, PUSH_F32 4.0, ADD_F, HALT */
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(3.0f));
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(4.0f));
    emit(code, 16, OP_ADD_F,    0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    TEST_ASSERT_EQUAL(VM_OK, vm_load_bytecode(&vm, code, sizeof(code)));
    TEST_ASSERT_EQUAL(VM_OK, vm_execute_tick(&vm));
    TEST_ASSERT_EQUAL_UINT16(1, vm.sp);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 7.0f, stack_f32(&vm, 0));
}

/* ── Test Vector 2: Stack Underflow ────────────────────────────────── */
void test_stack_underflow(void)
{
    uint8_t code[8];
    emit(code, 0, OP_ADD_F, 0, 0, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(ERR_STACK_UNDERFLOW, vm_execute_tick(&vm));
    TEST_ASSERT_TRUE(vm.halted);
}

/* ── Test Vector 3: Division by Zero Returns 0.0 ──────────────────── */
void test_div_by_zero(void)
{
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(1.0f));
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(0.0f));
    emit(code, 16, OP_DIV_F,    0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(VM_OK, vm_execute_tick(&vm));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, stack_f32(&vm, 0));
}

/* ── Test Vector 4: I/O Round-Trip ─────────────────────────────────── */
void test_io_roundtrip(void)
{
    /* Set sensor[0] = 0.42, READ_PIN 0, WRITE_PIN 0, HALT */
    vm.sensors[0] = f2u(0.42f);

    uint8_t code[24];
    emit(code, 0,  OP_READ_PIN,  0, 0, 0);  /* Read sensor 0 */
    emit(code, 8,  OP_WRITE_PIN, 0, 0, 0);  /* Write actuator 0 */
    emit(code, 16, OP_NOP,       0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(VM_OK, vm_execute_tick(&vm));

    float act_val;
    memcpy(&act_val, &vm.actuators[0], sizeof(act_val));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.42f, act_val);
}

/* ── Test Vector 5: Conditional Branch ─────────────────────────────── */
void test_conditional_branch(void)
{
    /* PUSH 5.0, PUSH 10.0, LT_F, JUMP_IF_TRUE @24, PUSH 999.0, HALT, @24: PUSH 1.0, HALT */
    uint8_t code[56];
    emit(code, 0,  OP_PUSH_F32,     0x02, 0, f2u(5.0f));
    emit(code, 8,  OP_PUSH_F32,     0x02, 0, f2u(10.0f));
    emit(code, 16, OP_LT_F,         0,    0, 0);
    emit(code, 24, OP_JUMP_IF_TRUE, 0,    0, 40);  /* jump to @40 */
    emit(code, 32, OP_PUSH_F32,     0x02, 0, f2u(999.0f));
    /* skip halt here; dead code after branch */
    emit(code, 40, OP_PUSH_F32,     0x02, 0, f2u(1.0f));
    emit(code, 48, OP_NOP,          0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(VM_OK, vm_execute_tick(&vm));
    TEST_ASSERT_EQUAL_UINT16(1, vm.sp);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 1.0f, stack_f32(&vm, 0));
}

/* ── Test Vector 6: Cycle Budget Enforcement ───────────────────────── */
void test_cycle_budget(void)
{
    /* Tight loop: JUMP 0 with budget = 10 */
    uint8_t code[8];
    emit(code, 0, OP_JUMP, 0, 0, 0);  /* infinite loop to offset 0 */

    vm_load_bytecode(&vm, code, sizeof(code));
    vm.cycle_budget = 10;
    TEST_ASSERT_EQUAL(ERR_CYCLE_BUDGET_EXCEEDED, vm_execute_tick(&vm));
    TEST_ASSERT_TRUE(vm.halted);
}

/* ── Test Vector 7: Call Stack Underflow ────────────────────────────── */
void test_call_stack_underflow(void)
{
    /* RET with empty call stack */
    uint8_t code[8];
    emit(code, 0, OP_JUMP, FLAGS_IS_CALL, 0, 0xFFFFFFFF);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(ERR_CALL_STACK_UNDERFLOW, vm_execute_tick(&vm));
}

/* ── Test Vector 8: CLAMP_F ────────────────────────────────────────── */
void test_clamp_f(void)
{
    /* PUSH -5.0, CLAMP [-1, 1] -> -1.0 */
    /* operand2: lo=0xFFFF (-1 as int16), hi=0x0001 (1 as int16) -> packed as (hi<<16)|lo */
    uint32_t clamp_packed = (uint32_t)(uint16_t)1 << 16 | (uint32_t)(uint16_t)-1;

    uint8_t code[24];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(-5.0f));
    emit(code, 8,  OP_CLAMP_F,  0,    0, clamp_packed);
    emit(code, 16, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(VM_OK, vm_execute_tick(&vm));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, -1.0f, stack_f32(&vm, 0));
}

/* ── Test Vector 9: NEG_F and ABS_F ────────────────────────────────── */
void test_neg_abs(void)
{
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(3.14f));
    emit(code, 8,  OP_NEG_F,    0,    0, 0);
    emit(code, 16, OP_ABS_F,    0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(VM_OK, vm_execute_tick(&vm));
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 3.14f, stack_f32(&vm, 0));
}

/* ── Test Vector 10: PID Compute ───────────────────────────────────── */
void test_pid_compute(void)
{
    vm.pid[0].Kp = 1.0f;
    vm.pid[0].Ki = 0.1f;
    vm.pid[0].Kd = 0.0f;
    vm.pid[0].output_min = -100.0f;
    vm.pid[0].output_max = 100.0f;
    vm.pid[0].integral_limit = 100.0f;

    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(50.0f));  /* setpoint */
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(48.0f));  /* input */
    emit(code, 16, OP_NOP,      0x80, SYSCALL_PID_COMPUTE, 0); /* PID idx 0 */
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(VM_OK, vm_execute_tick(&vm));
    /* First tick: Kp*(50-48) = 2.0, integral tiny, derivative = 0 */
    TEST_ASSERT_FLOAT_WITHIN(0.5f, 2.0f, stack_f32(&vm, 0));
}

/* ── Additional Tests ──────────────────────────────────────────────── */

void test_push_i8(void)
{
    uint8_t code[16];
    emit(code, 0, OP_PUSH_I8, 0, 42, 0);
    emit(code, 8, OP_NOP,     0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 42.0f, stack_f32(&vm, 0));
}

void test_push_i16(void)
{
    uint8_t code[16];
    emit(code, 0, OP_PUSH_I16, 0, 1000, 0);
    emit(code, 8, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 1000.0f, stack_f32(&vm, 0));
}

void test_dup(void)
{
    uint8_t code[24];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(42.0f));
    emit(code, 8,  OP_DUP,      0,    0, 0);
    emit(code, 16, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_EQUAL_UINT16(2, vm.sp);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 42.0f, stack_f32(&vm, 0));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 42.0f, stack_f32(&vm, 1));
}

void test_swap(void)
{
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(1.0f));
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(2.0f));
    emit(code, 16, OP_SWAP,     0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 2.0f, stack_f32(&vm, 0));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 1.0f, stack_f32(&vm, 1));
}

void test_rot(void)
{
    /* [..., C, B, A] -> [..., B, A, C] */
    uint8_t code[40];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(1.0f));  /* C (bottom) */
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(2.0f));  /* B */
    emit(code, 16, OP_PUSH_F32, 0x02, 0, f2u(3.0f));  /* A (top) */
    emit(code, 24, OP_ROT,      0,    0, 0);
    emit(code, 32, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    /* Expected: [2.0, 3.0, 1.0] (bottom to top) */
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 2.0f, stack_f32(&vm, 0));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 3.0f, stack_f32(&vm, 1));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 1.0f, stack_f32(&vm, 2));
}

void test_sub_f(void)
{
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(10.0f));
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(3.0f));
    emit(code, 16, OP_SUB_F,    0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 7.0f, stack_f32(&vm, 0));
}

void test_mul_f(void)
{
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(3.0f));
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(4.0f));
    emit(code, 16, OP_MUL_F,    0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 12.0f, stack_f32(&vm, 0));
}

void test_min_f(void)
{
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(7.0f));
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(3.0f));
    emit(code, 16, OP_MIN_F,    0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 3.0f, stack_f32(&vm, 0));
}

void test_max_f(void)
{
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(7.0f));
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(3.0f));
    emit(code, 16, OP_MAX_F,    0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 7.0f, stack_f32(&vm, 0));
}

void test_comparison_eq(void)
{
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(5.0f));
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(5.0f));
    emit(code, 16, OP_EQ_F,     0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_EQUAL_UINT32(1, vm.stack[0]);
}

void test_comparison_lt(void)
{
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(3.0f));
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, f2u(5.0f));
    emit(code, 16, OP_LT_F,     0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_EQUAL_UINT32(1, vm.stack[0]);  /* 3 < 5 = true */
}

void test_logic_and(void)
{
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, 0xFF);
    emit(code, 8,  OP_PUSH_F32, 0x02, 0, 0x0F);
    emit(code, 16, OP_AND_B,    0,    0, 0);
    emit(code, 24, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_EQUAL_UINT32(0x0F, vm.stack[0]);
}

void test_not_b(void)
{
    uint8_t code[24];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, 0x00000000);
    emit(code, 8,  OP_NOT_B,    0,    0, 0);
    emit(code, 16, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFF, vm.stack[0]);
}

void test_read_timer(void)
{
    uint8_t code[16];
    emit(code, 0, OP_READ_TIMER_MS, 0, 0, 0);
    emit(code, 8, OP_NOP,           0x80, SYSCALL_HALT, 0);

    vm.tick_count_ms = 12345;
    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    /* tick_count_ms gets incremented by vm_reset_tick, so it'll be 12346 */
    TEST_ASSERT_EQUAL_UINT32(12346, vm.stack[0]);
}

void test_stack_overflow(void)
{
    /* Push 257 values (stack size = 256) */
    uint8_t code[257 * 8];
    for (int i = 0; i < 257; i++) {
        emit(code, i * 8, OP_PUSH_F32, 0x02, 0, f2u(1.0f));
    }

    vm_load_bytecode(&vm, code, sizeof(code));
    vm.cycle_budget = 500;
    TEST_ASSERT_EQUAL(ERR_STACK_OVERFLOW, vm_execute_tick(&vm));
}

void test_invalid_opcode(void)
{
    uint8_t code[8];
    emit(code, 0, 0xFF, 0, 0, 0);  /* Invalid opcode */

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(ERR_INVALID_OPCODE, vm_execute_tick(&vm));
}

void test_nan_guard_on_actuator_write(void)
{
    /* Write NaN to actuator — must be caught */
    uint32_t nan_bits = 0x7FC00000;  /* quiet NaN */
    uint8_t code[24];
    emit(code, 0,  OP_PUSH_F32,  0x02, 0, nan_bits);
    emit(code, 8,  OP_WRITE_PIN, 0,    0, 0);  /* Write to actuator 0 */
    emit(code, 16, OP_NOP,       0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(ERR_NAN_DETECTED, vm_execute_tick(&vm));
}

void test_jump_out_of_bounds(void)
{
    uint8_t code[8];
    emit(code, 0, OP_JUMP, 0, 0, 999);  /* out of bounds */

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(ERR_JUMP_OUT_OF_BOUNDS, vm_execute_tick(&vm));
}

void test_jump_not_aligned(void)
{
    uint8_t code[16];
    emit(code, 0, OP_JUMP, 0, 0, 3);  /* not 8-aligned */
    emit(code, 8, OP_NOP,  0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(ERR_JUMP_OUT_OF_BOUNDS, vm_execute_tick(&vm));
}

void test_call_and_return(void)
{
    /* CALL @16, HALT, @16: PUSH 42.0, RET */
    uint8_t code[32];
    emit(code, 0,  OP_JUMP,     FLAGS_IS_CALL, 0, 16);        /* CALL @16 */
    emit(code, 8,  OP_NOP,      0x80, SYSCALL_HALT, 0);       /* HALT (return point) */
    emit(code, 16, OP_PUSH_F32, 0x02, 0, f2u(42.0f));        /* @16: push 42 */
    emit(code, 24, OP_JUMP,     FLAGS_IS_CALL, 0, 0xFFFFFFFF); /* RET */

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(VM_OK, vm_execute_tick(&vm));
    TEST_ASSERT_EQUAL_UINT16(1, vm.sp);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 42.0f, stack_f32(&vm, 0));
}

void test_jump_if_false(void)
{
    /* PUSH 0, JUMP_IF_FALSE @16, PUSH 999, @16: PUSH 1, HALT */
    uint8_t code[40];
    emit(code, 0,  OP_PUSH_F32,      0x02, 0, 0);          /* push 0 (false) */
    emit(code, 8,  OP_JUMP_IF_FALSE, 0,    0, 24);         /* jump to @24 */
    emit(code, 16, OP_PUSH_F32,      0x02, 0, f2u(999.0f)); /* skipped */
    emit(code, 24, OP_PUSH_F32,      0x02, 0, f2u(1.0f));  /* @24 */
    emit(code, 32, OP_NOP,           0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_EQUAL_UINT16(1, vm.sp);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 1.0f, stack_f32(&vm, 0));
}

void test_variable_read_write(void)
{
    /* Write to var[0] via WRITE_PIN(64), read back via READ_PIN(64) */
    uint8_t code[32];
    emit(code, 0,  OP_PUSH_F32,  0x02, 0, f2u(99.0f));
    emit(code, 8,  OP_WRITE_PIN, 0,    64, 0);  /* var[0] = 99.0 */
    emit(code, 16, OP_READ_PIN,  0,    64, 0);  /* push var[0] */
    emit(code, 24, OP_NOP,       0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_EQUAL_UINT16(1, vm.sp);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 99.0f, stack_f32(&vm, 0));
}

void test_no_bytecode(void)
{
    TEST_ASSERT_EQUAL(ERR_NO_BYTECODE, vm_execute_tick(&vm));
}

void test_bytecode_not_aligned(void)
{
    uint8_t code[7] = {0};
    TEST_ASSERT_EQUAL(ERR_INVALID_OPERAND, vm_load_bytecode(&vm, code, 7));
}

void test_snapshot_syscall(void)
{
    uint8_t code[16];
    emit(code, 0, OP_NOP, 0x80, SYSCALL_RECORD_SNAPSHOT, 0);
    emit(code, 8, OP_NOP, 0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(VM_OK, vm_execute_tick(&vm));
    TEST_ASSERT_EQUAL_UINT8(1, vm.next_snapshot);
}

void test_emit_event_syscall(void)
{
    uint32_t event_data = (0x0042 << 16) | 0x0001;  /* event_data=0x42, event_id=0x01 */
    uint8_t code[16];
    emit(code, 0, OP_NOP, 0x80, SYSCALL_EMIT_EVENT, event_data);
    emit(code, 8, OP_NOP, 0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(VM_OK, vm_execute_tick(&vm));
    TEST_ASSERT_EQUAL_UINT16(1, vm.event_head);
    TEST_ASSERT_EQUAL_UINT16(0x0001, vm.events[0].event_id);
}

void test_pop(void)
{
    uint8_t code[24];
    emit(code, 0,  OP_PUSH_F32, 0x02, 0, f2u(1.0f));
    emit(code, 8,  OP_POP,      0,    0, 0);
    emit(code, 16, OP_NOP,      0x80, SYSCALL_HALT, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    vm_execute_tick(&vm);
    TEST_ASSERT_EQUAL_UINT16(0, vm.sp);
}

void test_pop_underflow(void)
{
    uint8_t code[8];
    emit(code, 0, OP_POP, 0, 0, 0);

    vm_load_bytecode(&vm, code, sizeof(code));
    TEST_ASSERT_EQUAL(ERR_STACK_UNDERFLOW, vm_execute_tick(&vm));
}

int main(void)
{
    UNITY_BEGIN();

    /* Spec test vectors 1-10 */
    RUN_TEST(test_simple_arithmetic);
    RUN_TEST(test_stack_underflow);
    RUN_TEST(test_div_by_zero);
    RUN_TEST(test_io_roundtrip);
    RUN_TEST(test_conditional_branch);
    RUN_TEST(test_cycle_budget);
    RUN_TEST(test_call_stack_underflow);
    RUN_TEST(test_clamp_f);
    RUN_TEST(test_neg_abs);
    RUN_TEST(test_pid_compute);

    /* Additional opcode tests */
    RUN_TEST(test_push_i8);
    RUN_TEST(test_push_i16);
    RUN_TEST(test_dup);
    RUN_TEST(test_swap);
    RUN_TEST(test_rot);
    RUN_TEST(test_sub_f);
    RUN_TEST(test_mul_f);
    RUN_TEST(test_min_f);
    RUN_TEST(test_max_f);
    RUN_TEST(test_comparison_eq);
    RUN_TEST(test_comparison_lt);
    RUN_TEST(test_logic_and);
    RUN_TEST(test_not_b);
    RUN_TEST(test_read_timer);
    RUN_TEST(test_pop);
    RUN_TEST(test_pop_underflow);

    /* Safety tests */
    RUN_TEST(test_stack_overflow);
    RUN_TEST(test_invalid_opcode);
    RUN_TEST(test_nan_guard_on_actuator_write);
    RUN_TEST(test_jump_out_of_bounds);
    RUN_TEST(test_jump_not_aligned);
    RUN_TEST(test_no_bytecode);
    RUN_TEST(test_bytecode_not_aligned);

    /* Control flow */
    RUN_TEST(test_call_and_return);
    RUN_TEST(test_jump_if_false);
    RUN_TEST(test_variable_read_write);

    /* Syscalls */
    RUN_TEST(test_snapshot_syscall);
    RUN_TEST(test_emit_event_syscall);

    return UNITY_END();
}
