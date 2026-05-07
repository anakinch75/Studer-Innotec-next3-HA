"""Unit tests for Modbus register decoding functions."""
import struct

import pytest

from custom_components.studer_next3.coordinator import _decode_float32, _decode_float64


def _to_regs_f32(value: float) -> list[int]:
    raw = struct.pack(">f", value)
    return list(struct.unpack(">HH", raw))


def _to_regs_f64(value: float) -> list[int]:
    raw = struct.pack(">d", value)
    return list(struct.unpack(">HHHH", raw))


@pytest.mark.parametrize("value", [0.0, 1.0, -1.0, 1000.0, -500.5, 3.14])
def test_decode_float32_roundtrip(value):
    assert _decode_float32(_to_regs_f32(value)) == pytest.approx(value, rel=1e-5)


@pytest.mark.parametrize("value", [0.0, 1.0, -1.0, 48_570_299.0, 29_118_343.0])
def test_decode_float64_roundtrip(value):
    assert _decode_float64(_to_regs_f64(value)) == pytest.approx(value, rel=1e-9)


def test_decode_float32_known_registers():
    # 1000.0 → 0x447A0000
    assert _decode_float32([0x447A, 0x0000]) == pytest.approx(1000.0)


def test_decode_float64_known_registers():
    # 1000.0 → 0x408F400000000000
    assert _decode_float64([0x408F, 0x4000, 0x0000, 0x0000]) == pytest.approx(1000.0)
