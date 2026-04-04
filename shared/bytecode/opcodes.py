"""
NEXUS Shared — Opcode Definitions (Python)

Canonical opcode constants shared between Jetson tools and tests.
Must be kept in sync with opcodes.h.

Spec: specs/firmware/reflex_bytecode_vm_spec.md §2.4
"""

from __future__ import annotations

import struct
from enum import IntEnum
from typing import NamedTuple


class Opcode(IntEnum):
    """All 32 core opcodes."""

    # Stack (0x00-0x07)
    NOP = 0x00
    PUSH_I8 = 0x01
    PUSH_I16 = 0x02
    PUSH_F32 = 0x03
    POP = 0x04
    DUP = 0x05
    SWAP = 0x06
    ROT = 0x07

    # Arithmetic (0x08-0x10)
    ADD_F = 0x08
    SUB_F = 0x09
    MUL_F = 0x0A
    DIV_F = 0x0B
    NEG_F = 0x0C
    ABS_F = 0x0D
    MIN_F = 0x0E
    MAX_F = 0x0F
    CLAMP_F = 0x10

    # Comparison (0x11-0x15)
    EQ_F = 0x11
    LT_F = 0x12
    GT_F = 0x13
    LTE_F = 0x14
    GTE_F = 0x15

    # Logic (0x16-0x19)
    AND_B = 0x16
    OR_B = 0x17
    XOR_B = 0x18
    NOT_B = 0x19

    # I/O (0x1A-0x1C)
    READ_PIN = 0x1A
    WRITE_PIN = 0x1B
    READ_TIMER_MS = 0x1C

    # Control (0x1D-0x1F)
    JUMP = 0x1D
    JUMP_IF_FALSE = 0x1E
    JUMP_IF_TRUE = 0x1F


class SyscallID(IntEnum):
    """Syscall IDs (NOP + FLAGS_SYSCALL)."""

    HALT = 0x01
    PID_COMPUTE = 0x02
    RECORD_SNAPSHOT = 0x03
    EMIT_EVENT = 0x04


# Flags byte bit definitions
FLAGS_HAS_IMMEDIATE = 1 << 0
FLAGS_IS_FLOAT = 1 << 1
FLAGS_EXTENDED_CLAMP = 1 << 2
FLAGS_IS_CALL = 1 << 3
FLAGS_SYSCALL = 1 << 7


class Instruction(NamedTuple):
    """8-byte fixed instruction."""

    opcode: int
    flags: int
    operand1: int
    operand2: int

    def to_bytes(self) -> bytes:
        """Encode to 8-byte little-endian binary."""
        return struct.pack("<BBHI", self.opcode, self.flags, self.operand1, self.operand2)

    @classmethod
    def from_bytes(cls, data: bytes) -> Instruction:
        """Decode from 8-byte little-endian binary."""
        opcode, flags, operand1, operand2 = struct.unpack("<BBHI", data[:8])
        return cls(opcode, flags, operand1, operand2)


def make_push_f32(value: float) -> Instruction:
    """Create a PUSH_F32 instruction."""
    raw = struct.pack("<f", value)
    operand2 = struct.unpack("<I", raw)[0]
    return Instruction(Opcode.PUSH_F32, FLAGS_IS_FLOAT, 0, operand2)


def make_halt() -> Instruction:
    """Create a HALT syscall instruction."""
    return Instruction(Opcode.NOP, FLAGS_SYSCALL, SyscallID.HALT, 0)


def make_read_pin(pin: int) -> Instruction:
    """Create a READ_PIN instruction."""
    return Instruction(Opcode.READ_PIN, 0, pin, 0)


def make_write_pin(pin: int) -> Instruction:
    """Create a WRITE_PIN instruction."""
    return Instruction(Opcode.WRITE_PIN, 0, pin, 0)


def make_simple(opcode: Opcode) -> Instruction:
    """Create a simple instruction with no operands."""
    return Instruction(opcode, 0, 0, 0)
