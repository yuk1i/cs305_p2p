from __future__ import annotations

import math
import random
import time
from typing import Tuple
import socket
import struct

import utils


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


def random_bytes(_len: int) -> bytes:
    return random.randbytes(_len)


def ipv4_to_int(addr4: str) -> int:
    """
    Give a ipv4 address in dot format, such as 1.1.1.1
    Convert it into uint32_t
    :param addr4:
    :return:
    """
    return struct.unpack("!I", socket.inet_aton(addr4))[0]


def int_to_ipv4(addri: int) -> str:
    return socket.inet_ntoa(struct.pack("!I", addri))


def ipport_to_int(src_addr: utils.ip_port.IPPort) -> int:
    i4 = ipv4_to_int(src_addr[0]) << 16
    i4 |= int(src_addr[1])
    return i4


def current_time_ms() -> int:
    return math.floor(time.time() * 1000)

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
