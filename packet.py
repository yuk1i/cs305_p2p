from __future__ import annotations
from utils.bytes_utils import int_to_bytes, bytes_to_int

TYPE_NOTIFY = 0x05
TYPE_REGISTER = 0x10
TYPE_REQUEST_PEERS = 0x11
TYPE_CANCEL = 0x12
TYPE_CLOSE = 0x13
TYPE_REQUEST_FOR_TORRENT = 0x30
TYPE_CHUNK_FOR_TORRENT = 0x31
TYPE_REQUEST_FOR_CHUNK = 0x32
TYPE_ACK = 0x20


def deserialize_packet(data: bytes) -> BasePacket:
    ptype = data[0]
    if ptype == TYPE_NOTIFY:
        return NotifyPacket().unpack(data)
    elif ptype == TYPE_REGISTER:
        return RegisterPacket().unpack(data)
    # elif ptype == TYPE_REQUEST_PEERS:


class BasePacket:
    def __init__(self, itype: int):
        self.type: int = itype
        self.reversed: int = 0
        self.identifier: int = 0

    def unpack_header(self, data: bytes) -> BasePacket:
        # self.type = data[0]
        self.reversed = data[1]
        self.identifier = bytes_to_int(data[2:2 + 2])
        return self

    def pack(self) -> bytes:
        pass

    def unpack(self, data: bytes) -> BasePacket:
        pass


class NotifyPacket(BasePacket):
    def __init__(self):
        super(NotifyPacket, self).__init__(TYPE_NOTIFY)
        self.uuid: int = 0
        self.ipv4_address: int = 0
        self.udp_port: int = 0

    def pack(self) -> bytes:
        b = bytearray(17)
        b[0] = self.type
        b[1] = self.reversed
        b[2:2 + 2] = int_to_bytes(self.identifier, 2)
        b[4:4 + 8] = int_to_bytes(self.uuid, 8)
        b[12:12 + 4] = int_to_bytes(self.ipv4_address, 4)
        b[16:16 + 2] = int_to_bytes(self.udp_port, 2)
        return b

    def unpack(self, data: bytes) -> BasePacket:
        self.unpack_header(data[0:0 + 4])
        self.uuid = bytes_to_int(data[4:4 + 8])
        self.ipv4_address = bytes_to_int(data[12:12 + 4])
        self.udp_port = bytes_to_int(data[16:16 + 2])
        return self


class RegisterPacket(BasePacket):
    def __init__(self):
        super(RegisterPacket, self).__init__(TYPE_REGISTER)

    def pack(self) -> bytes:
        pass

    def unpack(self, data: bytes) -> BasePacket:
        pass
