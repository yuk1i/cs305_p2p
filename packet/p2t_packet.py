from typing import List

from packet.base_packet import *
from utils.bytes_utils import ByteWriter, ByteReader

STATUS_NOT_SET = 0x00
STATUS_OK = 0x01
STATUS_NO_AUTH = 0xF0


class NotifyPacket(BasePacket):
    def __init__(self):
        super(NotifyPacket, self).__init__(TYPE_NOTIFY)
        self.ipv4_address: int = 0
        self.udp_port: int = 0

    def __pack_internal__(self, w: ByteWriter):
        w.write_int(self.ipv4_address)
        w.write_short(self.udp_port)

    def __unpack_internal__(self, r: ByteReader):
        self.ipv4_address = r.read_int()
        self.udp_port = r.read_short()


class ACKNotifyPacket(ACKPacket):
    def __init__(self):
        super(ACKNotifyPacket, self).__init__()
        self.uuid: int = 0

    def __pack_internal__(self, w: ByteWriter):
        w.write_long(self.uuid)

    def __unpack_internal__(self, r: ByteReader):
        self.uuid = r.read_long()


class RegisterPacket(BasePacket):
    def __init__(self):
        super(RegisterPacket, self).__init__(TYPE_REGISTER)
        self.uuid: int = 0
        self.torrent_hash: bytes = b''

    def __pack_internal__(self, w: ByteWriter):
        w.write_long(self.uuid)
        w.write_bytes(self.torrent_hash)

    def __unpack_internal__(self, r: ByteReader):
        self.uuid = r.read_long()
        self.torrent_hash = r.read_bytes(32)


class ACKRegisterPacket(ACKPacket):
    def __init__(self):
        super(ACKRegisterPacket, self).__init__()
        self.status: int = STATUS_OK

    def __pack_internal__(self, w: ByteWriter):
        w.write_byte(self.status)

    def __unpack_internal__(self, r: ByteReader):
        self.status = r.read_byte()


class RequestPeer(BasePacket):
    def __init__(self):
        super(RequestPeer, self).__init__(TYPE_REQUEST_PEERS)
        self.torrent_hash: bytes = b''

    def __pack_internal__(self, w: ByteWriter):
        w.write_bytes(self.torrent_hash)

    def __unpack_internal__(self, r: ByteReader):
        self.torrent_hash = r.read_bytes(32)


class TupleAddressAndPort(Serializable):
    def __init__(self, ipv4: int = 0, port: int = 0):
        self.ipv4: int = ipv4
        self.port: int = port

    def __pack_internal__(self, w: ByteWriter):
        w.write_int(self.ipv4)
        w.write_short(self.port)

    def __unpack_internal__(self, r: ByteReader):
        self.ipv4 = r.read_int()
        self.port = r.read_int()


class ACKRequestPeer(ACKPacket):
    def __init__(self):
        super(ACKRequestPeer, self).__init__()
        self.reassemble = ReAssembleHeader()
        self.addresses: List[TupleAddressAndPort] = list()

    def __pack_internal__(self, w: ByteWriter):
        for tp in self.addresses:
            tp.__pack_internal__(w)

    def __unpack_internal__(self, r: ByteReader):
        while r.remain() >= 6:
            tp = TupleAddressAndPort()
            tp.__unpack_internal__(r)
            self.addresses.append(tp)
