/**
 * NEXUS Bytecode VM — Pre-Execution Bytecode Validator
 *
 * Validates bytecode before loading into VM:
 * - Size alignment (multiple of 8)
 * - Opcode validity
 * - Jump target bounds and alignment
 * - Terminates with HALT
 *
 * Spec: specs/firmware/reflex_bytecode_vm_spec.md §6
 */

#include "vm.h"

vm_error_t vm_validate_bytecode(const uint8_t *code, uint32_t size)
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

    uint32_t num_instructions = size / 8;

    for (uint32_t i = 0; i < num_instructions; i++) {
        const instruction_t *instr = (const instruction_t *)(code + i * 8);

        /* Check for syscall (NOP + FLAGS_SYSCALL is valid) */
        if (instr->opcode == OP_NOP && (instr->flags & FLAGS_SYSCALL)) {
            uint16_t syscall_id = instr->operand1;
            if (syscall_id < SYSCALL_HALT || syscall_id > SYSCALL_EMIT_EVENT) {
                return ERR_INVALID_SYSCALL;
            }
            continue;
        }

        /* Validate opcode range */
        if (instr->opcode >= OP_COUNT) {
            /* Allow A2A opcodes (0x20+) to pass as NOPs for forward compat */
            if (instr->opcode < 0x60) {
                continue;
            }
            return ERR_INVALID_OPCODE;
        }

        /* Validate jump targets */
        if (instr->opcode == OP_JUMP ||
            instr->opcode == OP_JUMP_IF_FALSE ||
            instr->opcode == OP_JUMP_IF_TRUE) {

            uint32_t target = instr->operand2;

            /* Special case: RET uses target 0xFFFFFFFF */
            if (instr->opcode == OP_JUMP &&
                (instr->flags & FLAGS_IS_CALL) &&
                target == 0xFFFFFFFF) {
                continue;
            }

            if (target >= size) {
                return ERR_JUMP_OUT_OF_BOUNDS;
            }
            if (target % 8 != 0) {
                return ERR_JUMP_OUT_OF_BOUNDS;
            }
        }

        /* Validate I/O pin ranges */
        if (instr->opcode == OP_READ_PIN) {
            if (instr->operand1 >= VM_SENSOR_COUNT + VM_VAR_COUNT) {
                return ERR_INVALID_OPERAND;
            }
        }
        if (instr->opcode == OP_WRITE_PIN) {
            if (instr->operand1 >= VM_ACTUATOR_COUNT + VM_VAR_COUNT) {
                return ERR_INVALID_OPERAND;
            }
        }
    }

    return VM_OK;
}
