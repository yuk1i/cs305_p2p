from typing import List, Tuple

import utils.bytes_utils
from packet.base_packet import *
from utils import IPPort
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


class RequestPeerPacket(BasePacket):
    def __init__(self):
        super(RequestPeerPacket, self).__init__(TYPE_REQUEST_PEERS)
        self.torrent_hash: bytes = b''

    def __pack_internal__(self, w: ByteWriter):
        w.write_bytes(self.torrent_hash)

    def __unpack_internal__(self, r: ByteReader):
        self.torrent_hash = r.read_bytes(32)


class ACKRequestPeerPacket(ACKPacket):
    def __init__(self):
        super(ACKRequestPeerPacket, self).__init__()
        self.reassemble = ReAssembleHeader()
        self.status = STATUS_NOT_SET
        self.addresses: List[IPPort] = list()

    def __pack_internal__(self, w: ByteWriter):
        w.write_int(self.status)
        for tp in self.addresses:
            w.write_bytes(int_to_bytes(utils.ipport_to_int(tp), 6))

    def __unpack_internal__(self, r: ByteReader):
        self.status = r.read_int()
        while r.remain() >= 6:
            b = r.read_bytes(6)
            self.addresses.append((utils.int_to_ipv4(bytes_to_int(b[0:4])), bytes_to_int(b[4:6])))


class CancelPacket(BasePacket):
    def __init__(self):
        super(CancelPacket, self).__init__(TYPE_CANCEL)
        self.uuid: int = 0
        self.torrent_hash: bytes = b''

    def __pack_internal__(self, w: ByteWriter):
        w.write_long(self.uuid)
        w.write_bytes(self.torrent_hash)

    def __unpack_internal__(self, r: ByteReader):
        self.uuid = r.read_long()
        self.torrent_hash = r.read_bytes(32)


class ACKCancelPacket(ACKPacket):
    def __init__(self):
        super(ACKCancelPacket, self).__init__()

    def __pack_internal__(self, w: ByteWriter):
        pass

    def __unpack_internal__(self, r: ByteReader):
        pass


class ClosePacket(BasePacket):
    def __init__(self):
        super(ClosePacket, self).__init__(TYPE_CLOSE)
        self.uuid: int = 0

    def __pack_internal__(self, w: ByteWriter):
        w.write_long(self.uuid)

    def __unpack_internal__(self, r: ByteReader):
        self.uuid = r.read_long()


class ACKClosePacket(ACKPacket):
    def __init__(self):
        super(ACKClosePacket, self).__init__()

    def __pack_internal__(self, w: ByteWriter):
        pass

    def __unpack_internal__(self, r: ByteReader):
        pass


