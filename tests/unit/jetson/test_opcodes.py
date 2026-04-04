"""
Unit tests for shared.bytecode.opcodes module.

Verifies opcode constants, instruction encoding/decoding, and helper functions.
"""

from __future__ import annotations

import struct

from shared.bytecode.opcodes import (
    FLAGS_IS_FLOAT,
    FLAGS_SYSCALL,
    Instruction,
    Opcode,
    SyscallID,
    make_halt,
    make_push_f32,
    make_read_pin,
    make_simple,
    make_write_pin,
)


class TestOpcodeValues:
    """Verify opcode enum values match spec §2.4."""

    def test_stack_opcodes(self) -> None:
        assert Opcode.NOP == 0x00
        assert Opcode.PUSH_I8 == 0x01
        assert Opcode.PUSH_I16 == 0x02
        assert Opcode.PUSH_F32 == 0x03
        assert Opcode.POP == 0x04
        assert Opcode.DUP == 0x05
        assert Opcode.SWAP == 0x06
        assert Opcode.ROT == 0x07

    def test_arithmetic_opcodes(self) -> None:
        assert Opcode.ADD_F == 0x08
        assert Opcode.DIV_F == 0x0B
        assert Opcode.CLAMP_F == 0x10

    def test_comparison_opcodes(self) -> None:
        assert Opcode.EQ_F == 0x11
        assert Opcode.GTE_F == 0x15

    def test_control_opcodes(self) -> None:
        assert Opcode.JUMP == 0x1D
        assert Opcode.JUMP_IF_TRUE == 0x1F

    def test_opcode_count(self) -> None:
        assert len(Opcode) == 32


class TestInstruction:
    """Verify 8-byte instruction encoding/decoding."""

    def test_instruction_size(self) -> None:
        instr = Instruction(0x03, 0x02, 0x0000, 0x40400000)
        data = instr.to_bytes()
        assert len(data) == 8

    def test_roundtrip(self) -> None:
        original = Instruction(0x03, 0x02, 0x1234, 0xDEADBEEF)
        data = original.to_bytes()
        decoded = Instruction.from_bytes(data)
        assert decoded == original

    def test_push_f32_encoding(self) -> None:
        instr = make_push_f32(3.14)
        data = instr.to_bytes()
        assert data[0] == Opcode.PUSH_F32
        assert data[1] == FLAGS_IS_FLOAT
        # operand2 should be IEEE 754 encoding of 3.14
        raw_f32 = struct.pack("<f", 3.14)
        assert data[4:8] == raw_f32

    def test_halt_encoding(self) -> None:
        instr = make_halt()
        assert instr.opcode == Opcode.NOP
        assert instr.flags == FLAGS_SYSCALL
        assert instr.operand1 == SyscallID.HALT

    def test_read_pin(self) -> None:
        instr = make_read_pin(42)
        assert instr.opcode == Opcode.READ_PIN
        assert instr.operand1 == 42

    def test_write_pin(self) -> None:
        instr = make_write_pin(7)
        assert instr.opcode == Opcode.WRITE_PIN
        assert instr.operand1 == 7

    def test_simple_add(self) -> None:
        instr = make_simple(Opcode.ADD_F)
        assert instr.opcode == Opcode.ADD_F
        assert instr.flags == 0


class TestBytecodeAssembly:
    """Test assembling multi-instruction bytecode programs."""

    def test_simple_arithmetic(self) -> None:
        """PUSH 3.0, PUSH 4.0, ADD_F, HALT -> stack[0] = 7.0"""
        program = b"".join([
            make_push_f32(3.0).to_bytes(),
            make_push_f32(4.0).to_bytes(),
            make_simple(Opcode.ADD_F).to_bytes(),
            make_halt().to_bytes(),
        ])
        assert len(program) == 32  # 4 instructions x 8 bytes
        assert program[0] == Opcode.PUSH_F32
        assert program[16] == Opcode.ADD_F

    def test_program_alignment(self) -> None:
        """All programs must be multiples of 8 bytes."""
        for n in range(1, 10):
            instrs = [make_simple(Opcode.NOP) for _ in range(n)]
            program = b"".join(i.to_bytes() for i in instrs)
            assert len(program) % 8 == 0
