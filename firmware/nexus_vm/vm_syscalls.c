/**
 * NEXUS Bytecode VM — Syscall Implementations
 *
 * Syscalls are encoded as NOP with FLAGS_SYSCALL set.
 * syscall_id is in operand1. Operand2 contains parameters.
 *
 * Spec: specs/firmware/reflex_bytecode_vm_spec.md §3
 * Build: claude-build/build-specification.md §1.2
 */

#include "vm.h"
#include <string.h>
#include <math.h>

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

vm_error_t vm_execute_syscall(vm_state_t *vm, const instruction_t *instr)
{
    uint16_t syscall_id = instr->operand1;

    switch (syscall_id) {

    case SYSCALL_HALT:
        /* Stop execution for this tick. Cycles: 1 */
        vm->halted = true;
        vm->cycle_count += 1;
        return VM_OK;

    case SYSCALL_PID_COMPUTE: {
        /* Pop setpoint + input, push PID output. Cycles: ~20 */
        if (vm->sp < 2) return ERR_STACK_UNDERFLOW;

        uint16_t pid_idx = instr->operand2 & 0xFFFF;
        if (pid_idx >= VM_PID_COUNT) return ERR_INVALID_PID;

        pid_state_t *pid = &vm->pid[pid_idx];

        float input    = u32_to_f32(vm->stack[--vm->sp]);
        float setpoint = u32_to_f32(vm->stack[--vm->sp]);

        float error = setpoint - input;

        /* Proportional */
        float p_term = pid->Kp * error;

        /* Integral with anti-windup clamping */
        pid->integral += error * vm->tick_period_sec;
        if (pid->integral > pid->integral_limit) {
            pid->integral = pid->integral_limit;
        } else if (pid->integral < -pid->integral_limit) {
            pid->integral = -pid->integral_limit;
        }
        float i_term = pid->Ki * pid->integral;

        /* Derivative */
        float d_term = pid->Kd * (error - pid->prev_error) / vm->tick_period_sec;
        pid->prev_error = error;

        /* Output with clamping */
        float output = p_term + i_term + d_term;
        if (output > pid->output_max) output = pid->output_max;
        if (output < pid->output_min) output = pid->output_min;

        /* NaN guard */
        if (isnan(output) || isinf(output)) {
            output = 0.0f;
        }

        if (vm->sp >= VM_STACK_SIZE) return ERR_STACK_OVERFLOW;
        vm->stack[vm->sp++] = f32_to_u32(output);

        vm->cycle_count += 20;
        return VM_OK;
    }

    case SYSCALL_RECORD_SNAPSHOT: {
        /* Save VM state to next snapshot slot. Cycles: ~10 */
        vm_snapshot_t *snap = &vm->snapshots[vm->next_snapshot];

        snap->tick_ms = vm->tick_count_ms;
        snap->cycle_count = vm->cycle_count;
        snap->current_state = vm->pc;

        /* Copy first 15 variables */
        for (int i = 0; i < 15 && i < VM_VAR_COUNT; i++) {
            snap->variables[i] = vm->vars[i];
        }

        /* Copy first 14 sensors */
        for (int i = 0; i < 14 && i < VM_SENSOR_COUNT; i++) {
            snap->sensors[i] = vm->sensors[i];
        }

        vm->next_snapshot = (vm->next_snapshot + 1) % VM_SNAPSHOT_COUNT;
        vm->cycle_count += 10;
        return VM_OK;
    }

    case SYSCALL_EMIT_EVENT: {
        /* Queue event to ring buffer. Cycles: 2 */
        uint16_t next_head = (vm->event_head + 1) % VM_EVENT_RING_SIZE;

        /* Silently drop on overflow (ring buffer semantics) */
        if (next_head != vm->event_tail) {
            vm->events[vm->event_head].tick_ms = vm->tick_count_ms;
            vm->events[vm->event_head].event_id = (uint16_t)(instr->operand2 & 0xFFFF);
            vm->events[vm->event_head].event_data = (uint16_t)((instr->operand2 >> 16) & 0xFFFF);
            vm->event_head = next_head;
        }

        vm->cycle_count += 2;
        return VM_OK;
    }

    default:
        return ERR_INVALID_SYSCALL;
    }
}
