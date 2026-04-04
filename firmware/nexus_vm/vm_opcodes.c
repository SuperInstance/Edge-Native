/**
 * NEXUS Bytecode VM — Opcode Implementations
 *
 * All 32 opcodes per spec §2.4. Stack effects, error conditions,
 * and cycle costs match the build specification exactly.
 *
 * Spec: specs/firmware/reflex_bytecode_vm_spec.md
 * Build: claude-build/build-specification.md §1.2
 */

#include "vm.h"
#include <string.h>
#include <math.h>

/* ── Helper macros ────────────────────────────────────────────────────── */

static inline float u32_to_f32(uint32_t u)
{
    float f;
    memcpy(&f, &u, sizeof(f));
    return f;
}

static inline uint32_t f32_to_u32(float f)
{
    uint32_t u;
    memcpy(&u, &f, sizeof(u));
    return u;
}

#define CHECK_STACK_MIN(vm, n) \
    do { if ((vm)->sp < (n)) return ERR_STACK_UNDERFLOW; } while (0)

#define CHECK_STACK_SPACE(vm) \
    do { if ((vm)->sp >= VM_STACK_SIZE) return ERR_STACK_OVERFLOW; } while (0)

#define POP_U32(vm) ((vm)->stack[--(vm)->sp])
#define PUSH_U32(vm, v) ((vm)->stack[(vm)->sp++] = (v))

#define POP_F32(vm) u32_to_f32(POP_U32(vm))
#define PUSH_F32(vm, v) PUSH_U32(vm, f32_to_u32(v))

/* ── Opcode dispatch ──────────────────────────────────────────────────── */

vm_error_t vm_execute_opcode(vm_state_t *vm, const instruction_t *instr)
{
    switch (instr->opcode) {

    /* ── Stack Operations (0x00-0x07) ─────────────────────────────── */

    case OP_NOP:
        vm->pc += 8;
        return VM_OK;

    case OP_PUSH_I8: {
        CHECK_STACK_SPACE(vm);
        int8_t val = (int8_t)(instr->operand1 & 0xFF);
        PUSH_U32(vm, f32_to_u32((float)val));
        vm->pc += 8;
        return VM_OK;
    }

    case OP_PUSH_I16: {
        CHECK_STACK_SPACE(vm);
        int16_t val = (int16_t)instr->operand1;
        PUSH_U32(vm, f32_to_u32((float)val));
        vm->pc += 8;
        return VM_OK;
    }

    case OP_PUSH_F32: {
        CHECK_STACK_SPACE(vm);
        PUSH_U32(vm, instr->operand2);
        vm->pc += 8;
        return VM_OK;
    }

    case OP_POP:
        CHECK_STACK_MIN(vm, 1);
        vm->sp--;
        vm->pc += 8;
        return VM_OK;

    case OP_DUP:
        CHECK_STACK_MIN(vm, 1);
        CHECK_STACK_SPACE(vm);
        vm->stack[vm->sp] = vm->stack[vm->sp - 1];
        vm->sp++;
        vm->pc += 8;
        return VM_OK;

    case OP_SWAP: {
        CHECK_STACK_MIN(vm, 2);
        uint32_t tmp = vm->stack[vm->sp - 1];
        vm->stack[vm->sp - 1] = vm->stack[vm->sp - 2];
        vm->stack[vm->sp - 2] = tmp;
        vm->pc += 8;
        return VM_OK;
    }

    case OP_ROT: {
        /* [..., C, B, A] -> [..., B, A, C]  (spec §2.4) */
        CHECK_STACK_MIN(vm, 3);
        uint32_t a = vm->stack[vm->sp - 1];
        uint32_t b = vm->stack[vm->sp - 2];
        uint32_t c = vm->stack[vm->sp - 3];
        vm->stack[vm->sp - 1] = c;
        vm->stack[vm->sp - 2] = a;
        vm->stack[vm->sp - 3] = b;
        vm->pc += 8;
        return VM_OK;
    }

    /* ── Arithmetic (0x08-0x10) ───────────────────────────────────── */

    case OP_ADD_F: {
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        PUSH_F32(vm, a + b);
        vm->pc += 8;
        return VM_OK;
    }

    case OP_SUB_F: {
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        PUSH_F32(vm, a - b);
        vm->pc += 8;
        return VM_OK;
    }

    case OP_MUL_F: {
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        PUSH_F32(vm, a * b);
        vm->pc += 8;
        return VM_OK;
    }

    case OP_DIV_F: {
        /* Division by zero returns 0.0, NOT IEEE Inf (spec requirement) */
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        PUSH_F32(vm, (b == 0.0f) ? 0.0f : (a / b));
        vm->pc += 8;
        return VM_OK;
    }

    case OP_NEG_F: {
        /* Flip sign bit directly (spec: XOR with 0x80000000) */
        CHECK_STACK_MIN(vm, 1);
        vm->stack[vm->sp - 1] ^= 0x80000000u;
        vm->pc += 8;
        return VM_OK;
    }

    case OP_ABS_F: {
        /* Clear sign bit directly (spec: AND with 0x7FFFFFFF) */
        CHECK_STACK_MIN(vm, 1);
        vm->stack[vm->sp - 1] &= 0x7FFFFFFFu;
        vm->pc += 8;
        return VM_OK;
    }

    case OP_MIN_F: {
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        /* NaN-safe: if either is NaN, return the other */
        if (isnan(a)) { PUSH_F32(vm, b); }
        else if (isnan(b)) { PUSH_F32(vm, a); }
        else { PUSH_F32(vm, (a < b) ? a : b); }
        vm->pc += 8;
        return VM_OK;
    }

    case OP_MAX_F: {
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        /* NaN-safe: if either is NaN, return the other */
        if (isnan(a)) { PUSH_F32(vm, b); }
        else if (isnan(b)) { PUSH_F32(vm, a); }
        else { PUSH_F32(vm, (a > b) ? a : b); }
        vm->pc += 8;
        return VM_OK;
    }

    case OP_CLAMP_F: {
        /* Clamp TOS to [lo, hi] encoded in operand2 halves */
        CHECK_STACK_MIN(vm, 1);
        int16_t lo_i16 = (int16_t)(instr->operand2 & 0xFFFF);
        int16_t hi_i16 = (int16_t)((instr->operand2 >> 16) & 0xFFFF);
        float lo = (float)lo_i16;
        float hi = (float)hi_i16;
        float val = u32_to_f32(vm->stack[vm->sp - 1]);
        if (isnan(val)) val = 0.0f;
        if (val < lo) val = lo;
        if (val > hi) val = hi;
        vm->stack[vm->sp - 1] = f32_to_u32(val);
        vm->pc += 8;
        return VM_OK;
    }

    /* ── Comparison (0x11-0x15) ───────────────────────────────────── */

    case OP_EQ_F: {
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        PUSH_U32(vm, (a == b) ? 1 : 0);
        vm->pc += 8;
        return VM_OK;
    }

    case OP_LT_F: {
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        PUSH_U32(vm, (a < b) ? 1 : 0);
        vm->pc += 8;
        return VM_OK;
    }

    case OP_GT_F: {
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        PUSH_U32(vm, (a > b) ? 1 : 0);
        vm->pc += 8;
        return VM_OK;
    }

    case OP_LTE_F: {
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        PUSH_U32(vm, (a <= b) ? 1 : 0);
        vm->pc += 8;
        return VM_OK;
    }

    case OP_GTE_F: {
        CHECK_STACK_MIN(vm, 2);
        float b = POP_F32(vm);
        float a = POP_F32(vm);
        PUSH_U32(vm, (a >= b) ? 1 : 0);
        vm->pc += 8;
        return VM_OK;
    }

    /* ── Logic (0x16-0x19) ────────────────────────────────────────── */

    case OP_AND_B:
        CHECK_STACK_MIN(vm, 2);
        vm->stack[vm->sp - 2] &= vm->stack[vm->sp - 1];
        vm->sp--;
        vm->pc += 8;
        return VM_OK;

    case OP_OR_B:
        CHECK_STACK_MIN(vm, 2);
        vm->stack[vm->sp - 2] |= vm->stack[vm->sp - 1];
        vm->sp--;
        vm->pc += 8;
        return VM_OK;

    case OP_XOR_B:
        CHECK_STACK_MIN(vm, 2);
        vm->stack[vm->sp - 2] ^= vm->stack[vm->sp - 1];
        vm->sp--;
        vm->pc += 8;
        return VM_OK;

    case OP_NOT_B:
        CHECK_STACK_MIN(vm, 1);
        vm->stack[vm->sp - 1] = ~vm->stack[vm->sp - 1];
        vm->pc += 8;
        return VM_OK;

    /* ── I/O (0x1A-0x1C) ─────────────────────────────────────────── */

    case OP_READ_PIN: {
        CHECK_STACK_SPACE(vm);
        uint16_t pin = instr->operand1;
        if (pin < VM_SENSOR_COUNT) {
            PUSH_U32(vm, vm->sensors[pin]);
        } else if (pin < VM_SENSOR_COUNT + VM_VAR_COUNT) {
            PUSH_U32(vm, vm->vars[pin - VM_SENSOR_COUNT]);
        } else {
            return ERR_INVALID_OPERAND;
        }
        vm->pc += 8;
        return VM_OK;
    }

    case OP_WRITE_PIN: {
        CHECK_STACK_MIN(vm, 1);
        uint16_t pin = instr->operand1;
        uint32_t val = POP_U32(vm);

        /* NaN guard on actuator writes */
        if (pin < VM_ACTUATOR_COUNT) {
            float fval = u32_to_f32(val);
            if (isnan(fval) || isinf(fval)) {
                return ERR_NAN_DETECTED;
            }
            vm->actuators[pin] = val;
        } else if (pin < VM_ACTUATOR_COUNT + VM_VAR_COUNT) {
            vm->vars[pin - VM_ACTUATOR_COUNT] = val;
        } else {
            return ERR_INVALID_OPERAND;
        }
        vm->pc += 8;
        return VM_OK;
    }

    case OP_READ_TIMER_MS:
        CHECK_STACK_SPACE(vm);
        PUSH_U32(vm, vm->tick_count_ms);
        vm->pc += 8;
        return VM_OK;

    /* ── Control Flow (0x1D-0x1F) ─────────────────────────────────── */

    case OP_JUMP: {
        uint32_t target = instr->operand2;

        /* CALL: flags bit 3 set */
        if (instr->flags & FLAGS_IS_CALL) {
            /* RET: target == 0xFFFFFFFF */
            if (target == 0xFFFFFFFF) {
                if (vm->csp == 0) {
                    return ERR_CALL_STACK_UNDERFLOW;
                }
                vm->csp--;
                vm->pc = vm->call_stack[vm->csp].return_addr;
                return VM_OK;
            }

            /* CALL to target */
            if (vm->csp >= VM_CALL_STACK_SIZE) {
                return ERR_CALL_STACK_OVERFLOW;
            }
            vm->call_stack[vm->csp].return_addr = vm->pc + 8;
            vm->call_stack[vm->csp].frame_pointer = vm->sp;
            vm->csp++;
        }

        /* Validate jump target */
        if (target >= vm->bytecode_size || (target % 8) != 0) {
            return ERR_JUMP_OUT_OF_BOUNDS;
        }
        vm->pc = target;
        return VM_OK;
    }

    case OP_JUMP_IF_FALSE: {
        CHECK_STACK_MIN(vm, 1);
        uint32_t cond = POP_U32(vm);
        if (cond == 0) {
            uint32_t target = instr->operand2;
            if (target >= vm->bytecode_size || (target % 8) != 0) {
                return ERR_JUMP_OUT_OF_BOUNDS;
            }
            vm->pc = target;
        } else {
            vm->pc += 8;
        }
        return VM_OK;
    }

    case OP_JUMP_IF_TRUE: {
        CHECK_STACK_MIN(vm, 1);
        uint32_t cond = POP_U32(vm);
        if (cond != 0) {
            uint32_t target = instr->operand2;
            if (target >= vm->bytecode_size || (target % 8) != 0) {
                return ERR_JUMP_OUT_OF_BOUNDS;
            }
            vm->pc = target;
        } else {
            vm->pc += 8;
        }
        return VM_OK;
    }

    default:
        return ERR_INVALID_OPCODE;
    }
}
