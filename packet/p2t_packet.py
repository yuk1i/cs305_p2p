from typing import List, Tuple

import utils.bytes_utils
from packet.base_packet import *
from utils.bytes_utils import ByteWriter, ByteReader


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


class ACKRequestPeer(ACKPacket):
    def __init__(self):
        super(ACKRequestPeer, self).__init__()
        self.reassemble = ReAssembleHeader()
        self.addresses: List[Tuple[str, int]] = list()

    def __pack_internal__(self, w: ByteWriter):
        for tp in self.addresses:
            w.write_bytes(int_to_bytes(utils.ipport_to_int(tp), 6))

    def __unpack_internal__(self, r: ByteReader):
        while r.remain() >= 6:
            b = r.read_bytes(6)
            self.addresses.append((utils.int_to_ipv4(bytes_to_int(b[0:4])), bytes_to_int(b[4:6])))


class Cancel(BasePacket):
    def __init__(self):
        super(Cancel, self).__init__(TYPE_CANCEL)
        self.uuid: int = 0
        self.torrent_hash: bytes = b''

    def __pack_internal__(self, w: ByteWriter):
        w.write_long(self.uuid)
        w.write_bytes(self.torrent_hash)

    def __unpack_internal__(self, r: ByteReader):
        self.uuid = r.read_long()
        self.torrent_hash = r.read_bytes(32)


class ACKCancel(ACKPacket):
    def __init__(self):
        super(ACKCancel, self).__init__()

    def __pack_internal__(self, w: ByteWriter):
        pass

    def __unpack_internal__(self, r: ByteReader):
        pass


class Close(BasePacket):
    def __init__(self):
        super(Close, self).__init__(TYPE_CLOSE)
        self.uuid: int = 0

    def __pack_internal__(self, w: ByteWriter):
        w.write_long(self.uuid)

    def __unpack_internal__(self, r: ByteReader):
        self.uuid = r.read_long()


class ACKClose(ACKPacket):
    def __init__(self):
        super(ACKClose, self).__init__()

    def __pack_internal__(self, w: ByteWriter):
        pass

    def __unpack_internal__(self, r: ByteReader):
        pass


