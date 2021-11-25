from __future__ import annotations
import random


def bytes_to_int(data: bytes) -> int:
    return int.from_bytes(data, byteorder='big', signed=False)


def int_to_bytes(value: int, length: int) -> bytes:
    return int.to_bytes(value, length, byteorder="big", signed=False)


def hexstr_to_bytes(hex: str) -> bytes:
    return bytes.fromhex(hex)


def bytes_to_hexstr(b: bytes) -> str:
    return b.hex()


def random_byte() -> bytes:
    return random.randbytes(1)


def random_short() -> bytes:
    return random.randbytes(2)


def random_int() -> bytes:
    return random.randbytes(4)


def random_long() -> bytes:
    return random.randbytes(8)


class ByteWriter:
    def __init__(self, data: bytearray):
        self.data = data

    def len(self):
        return len(self.data)

    def write_byte(self, value: int) -> ByteWriter:
        self.data.extend(int_to_bytes(value, 1))
        return self

    def write_short(self, value: int) -> ByteWriter:
        self.data.extend(int_to_bytes(value, 2))
        return self

    def write_int(self, value: int) -> ByteWriter:
        self.data.extend(int_to_bytes(value, 4))
        return self

    def write_long(self, value: int) -> ByteWriter:
        self.data.extend(int_to_bytes(value, 8))
        return self

    def write_bytes(self, data: bytes) -> ByteWriter:
        self.data.extend(data)
        return self


class ByteReader:
    def __init__(self, data: bytes):
        self.data = data
        self.cursor = 0

    def skip(self, _len: int):
        self.cursor += _len

    def read_byte(self) -> int:
        ret = bytes_to_int(self.data[self.cursor:self.cursor + 1])
        self.cursor += 1
        return ret

    def read_short(self) -> int:
        ret = bytes_to_int(self.data[self.cursor:self.cursor + 2])
        self.cursor += 2
        return ret

    def read_int(self) -> int:
        ret = bytes_to_int(self.data[self.cursor:self.cursor + 4])
        self.cursor += 4
        return ret

    def read_long(self) -> int:
        ret = bytes_to_int(self.data[self.cursor:self.cursor + 8])
        self.cursor += 8
        return ret

    def read_bytes(self, _len: int) -> bytes:
        ret = self.data[self.cursor:self.cursor + _len]
        self.cursor += _len
        return ret

    def remain(self) -> int:
        return len(self.data) - self.cursor
