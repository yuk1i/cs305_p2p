import random


def bytes_to_int(data: bytes) -> int:
    return int.from_bytes(data, byteorder='big', signed=False)


def int_to_bytes(value: int, length: int) -> bytes:
    return int.to_bytes(value, length, byteorder="big", signed=False)


def random_byte() -> bytes:
    return random.randbytes(1)


def random_short() -> bytes:
    return random.randbytes(2)


def random_int() -> bytes:
    return random.randbytes(4)


def random_long() -> bytes:
    return random.randbytes(8)
