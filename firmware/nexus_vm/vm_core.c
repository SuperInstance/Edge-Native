/**
 * NEXUS Bytecode VM — Core Fetch-Decode-Execute Loop
 *
 * Spec: specs/firmware/reflex_bytecode_vm_spec.md §5 (Execution Model)
 * All memory statically allocated. Zero heap.
 */

#include "vm.h"
#include <string.h>
#include <math.h>

/* Cycle costs per opcode (from spec §5) */
static const uint8_t opcode_cycles[OP_COUNT] = {
    [OP_NOP]           = 1,
    [OP_PUSH_I8]       = 1,
    [OP_PUSH_I16]      = 1,
    [OP_PUSH_F32]      = 1,
    [OP_POP]           = 1,
    [OP_DUP]           = 1,
    [OP_SWAP]          = 1,
    [OP_ROT]           = 2,
    [OP_ADD_F]         = 3,
    [OP_SUB_F]         = 3,
    [OP_MUL_F]         = 3,
    [OP_DIV_F]         = 4,
    [OP_NEG_F]         = 1,
    [OP_ABS_F]         = 1,
    [OP_MIN_F]         = 3,
    [OP_MAX_F]         = 3,
    [OP_CLAMP_F]       = 3,
    [OP_EQ_F]          = 3,
    [OP_LT_F]          = 3,
    [OP_GT_F]          = 3,
    [OP_LTE_F]         = 3,
    [OP_GTE_F]         = 3,
    [OP_AND_B]         = 1,
    [OP_OR_B]          = 1,
    [OP_XOR_B]         = 1,
    [OP_NOT_B]         = 1,
    [OP_READ_PIN]      = 2,
    [OP_WRITE_PIN]     = 2,
    [OP_READ_TIMER_MS] = 2,
    [OP_JUMP]          = 1,
    [OP_JUMP_IF_FALSE] = 2,
    [OP_JUMP_IF_TRUE]  = 2,
};

/* Forward declarations */
vm_error_t vm_execute_opcode(vm_state_t *vm, const instruction_t *instr);
vm_error_t vm_execute_syscall(vm_state_t *vm, const instruction_t *instr);

void vm_init(vm_state_t *vm)
{
    memset(vm, 0, sizeof(vm_state_t));
    vm->cycle_budget = VM_DEFAULT_CYCLE_BUDGET;
    vm->tick_period_sec = 0.001f;  /* 1ms tick */

    /* Initialize PID controllers to safe defaults */
    for (int i = 0; i < VM_PID_COUNT; i++) {
        vm->pid[i].output_min = -1.0f;
        vm->pid[i].output_max = 1.0f;
        vm->pid[i].integral_limit = 100.0f;
    }
}

void vm_reset_tick(vm_state_t *vm)
{
    vm->sp = 0;
    vm->pc = 0;
    vm->csp = 0;
    vm->cycle_count = 0;
    vm->halted = false;
    vm->last_error = VM_OK;
    vm->flags = 0;
    vm->tick_count_ms++;
}

vm_error_t vm_load_bytecode(vm_state_t *vm, const uint8_t *code, uint32_t size)
{
    if (code == NULL || size == 0) {
        return ERR_NO_BYTECODE;
    }
    if (size % 8 != 0) {
        return ERR_INVALID_OPERAND;
    }
    if (size > VM_MAX_BYTECODE_SIZE) {
        return ERR_INVALID_OPERAND;
    }

    vm->bytecode = code;
    vm->bytecode_size = size;
    return VM_OK;
}

vm_error_t vm_execute_tick(vm_state_t *vm)
{
    if (vm->bytecode == NULL || vm->bytecode_size == 0) {
        return ERR_NO_BYTECODE;
    }

    vm_reset_tick(vm);

    while (!vm->halted) {
        /* Bounds check PC */
        if (vm->pc >= vm->bytecode_size) {
            vm->halted = true;
            break;
        }

        /* Decode instruction */
        const instruction_t *instr = (const instruction_t *)(vm->bytecode + vm->pc);

        /* Check for syscall (NOP with FLAGS_SYSCALL) */
        if (instr->opcode == OP_NOP && (instr->flags & FLAGS_SYSCALL)) {
            vm_error_t err = vm_execute_syscall(vm, instr);
            if (err != VM_OK) {
                vm->last_error = err;
                vm->halted = true;
                return err;
            }
            vm->pc += 8;
            continue;
        }

        /* Validate opcode */
        if (instr->opcode >= OP_COUNT) {
            vm->last_error = ERR_INVALID_OPCODE;
            vm->halted = true;
            return ERR_INVALID_OPCODE;
        }

        /* Check cycle budget */
        uint32_t cost = opcode_cycles[instr->opcode];
        if (vm->cycle_count + cost > vm->cycle_budget) {
            vm->last_error = ERR_CYCLE_BUDGET_EXCEEDED;
            vm->halted = true;
            return ERR_CYCLE_BUDGET_EXCEEDED;
        }
        vm->cycle_count += cost;

        /* Execute */
        vm_error_t err = vm_execute_opcode(vm, instr);
        if (err != VM_OK) {
            vm->last_error = err;
            vm->halted = true;
            return err;
        }
    }

    return vm->last_error;
}

const char *vm_error_str(vm_error_t err)
{
    switch (err) {
    case VM_OK:                      return "OK";
    case ERR_STACK_UNDERFLOW:        return "STACK_UNDERFLOW";
    case ERR_STACK_OVERFLOW:         return "STACK_OVERFLOW";
    case ERR_INVALID_OPCODE:         return "INVALID_OPCODE";
    case ERR_INVALID_OPERAND:        return "INVALID_OPERAND";
    case ERR_JUMP_OUT_OF_BOUNDS:     return "JUMP_OUT_OF_BOUNDS";
    case ERR_CALL_STACK_OVERFLOW:    return "CALL_STACK_OVERFLOW";
    case ERR_CALL_STACK_UNDERFLOW:   return "CALL_STACK_UNDERFLOW";
    case ERR_CYCLE_BUDGET_EXCEEDED:  return "CYCLE_BUDGET_EXCEEDED";
    case ERR_INVALID_SYSCALL:        return "INVALID_SYSCALL";
    case ERR_INVALID_PID:            return "INVALID_PID";
    case ERR_DIVISION_BY_ZERO:       return "DIVISION_BY_ZERO";
    case ERR_NAN_DETECTED:           return "NAN_DETECTED";
    case ERR_NO_BYTECODE:            return "NO_BYTECODE";
    default:                         return "UNKNOWN_ERROR";
    }
}
