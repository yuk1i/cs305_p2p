from packet.base_packet import *
from utils.bytes_utils import ByteWriter, ByteReader


class NotifyPacket(BasePacket):
    def __init__(self):
        super(NotifyPacket, self).__init__(TYPE_NOTIFY)
        self.uuid: int = 0
        self.ipv4_address: int = 0
        self.udp_port: int = 0

    def __pack_internal__(self, w: ByteWriter):
        w.write_long(self.uuid)
        w.write_int(self.ipv4_address)
        w.write_short(self.udp_port)

    def __unpack_internal__(self, r: ByteReader):
        self.uuid = r.read_long()
        self.ipv4_address = r.read_int()
        self.udp_port = r.read_short()


class ACKNotifyPacket(ACKPacket):
    def __init__(self, request: BasePacket):
        super(ACKNotifyPacket, self).__init__(request)
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
    def __init__(self, request: BasePacket):
        super(ACKRegisterPacket, self).__init__(request)

    def __pack_internal__(self, w: ByteWriter):
        pass

    def __unpack_internal__(self, r: ByteReader):
        pass
