from __future__ import annotations

from utils.bytes_utils import int_to_bytes, bytes_to_int, ByteWriter, ByteReader

TYPE_NOTIFY = 0x05
TYPE_REGISTER = 0x10
TYPE_REQUEST_PEERS = 0x11
TYPE_CANCEL = 0x12
TYPE_CLOSE = 0x13
TYPE_REQUEST_TORRENT = 0x30
TYPE_UPDATE_CHUNK_INFO = 0x31
TYPE_REQUEST_CHUNK = 0x32
TYPE_ACK = 0x20
TYPE_SET_CHOKE_STATUS = 0x41

FLAG_REASSEMBLE = 0x80
FLAG_SPEED_CONTROL = 0x40
MASK_RESERVED = 0x3F

STATUS_NOT_SET = 0x00
STATUS_OK = 0x01
STATUS_NOT_FOUND = 0x02
STATUS_NOT_READY = 0x03
STATUS_NOT_ENOUGH_UPLOAD = 0x04
STATUS_NO_AUTH = 0xF0


class ReAssembleHeader:
    def __init__(self, start: int = 0, length: int = 0, total_length: int = 0):
        self.enabled = True
        self.start = start
        self.length = length
        self.total_length = total_length


NO_REASSEMBLE = ReAssembleHeader()
NO_REASSEMBLE.enabled = False


class Serializable:
    def __pack_internal__(self, w: ByteWriter):
        pass

    def __unpack_internal__(self, r: ByteReader):
        pass


class BasePacket(Serializable):
    """
    Base Packet
    For Incoming Packet:
        set_data(raw_data) -> unpack(call unpack_header)
    For Outgoing Packet
        pack(call pack_header)
    """

    def __init__(self, itype: int):
        self.type: int = itype
        self.reserved: int = 0
        self.identifier: int = 0
        self.reassemble: ReAssembleHeader = NO_REASSEMBLE
        self.__reader__ = None
        self.__writer__ = None
        self.__data__ = None

    def get_header_length(self) -> int:
        if self.reassemble.enabled:
            return 16
        else:
            return 4

    def get_reader(self) -> ByteReader:
        if self.__reader__:
            return self.__reader__
        self.__reader__ = ByteReader(self.__data__)
        return self.__reader__

    def get_writer(self) -> ByteWriter:
        if self.__writer__:
            return self.__writer__
        self.__data__ = bytearray()
        self.__writer__ = ByteWriter(self.__data__)
        return self.__writer__

    def unpack_header(self) -> ByteReader:
        """
        unpack header from bytes
        :param reader: Byte Reader
        """
        # self.type = data[0]
        reader = self.get_reader()
        reader.skip(1)
        rev = reader.read_byte()  # The second byte
        self.reserved = rev & MASK_RESERVED
        self.identifier = reader.read_short()
        if rev & FLAG_REASSEMBLE == FLAG_REASSEMBLE:
            # ReAssemble Enabled
            self.reassemble = ReAssembleHeader(
                start=reader.read_int(),
                length=reader.read_int(),
                total_length=reader.read_int())
        return reader

    def pack_header(self) -> ByteWriter:
        """
        pack the header, containing Type, Reserved, and Identifier
        and Reassemble Header if needed
        """
        writer = self.get_writer()
        writer.write_byte(self.type)
        writer.write_byte(self.reserved & MASK_RESERVED)
        writer.write_short(self.identifier)
        if self.reassemble.enabled:
            writer.data[1] = writer.data[1] | FLAG_REASSEMBLE
            writer.write_int(self.reassemble.start)
            writer.write_int(self.reassemble.length)
            writer.write_int(self.reassemble.total_length)
        return writer

    def pack(self) -> bytes:
        w = self.pack_header()
        self.__pack_internal__(w)
        return w.data

    def unpack(self, data: bytes) -> BasePacket:
        if data:
            self.__data__ = data
        r = self.unpack_header()
        self.__unpack_internal__(r)
        return self

    def __pack_internal__(self, w: ByteWriter):
        pass

    def __unpack_internal__(self, r: ByteReader):
        pass


class ACKPacket(BasePacket):
    def __init__(self):
        super(ACKPacket, self).__init__(TYPE_ACK)

    def set_request(self, req: BasePacket):
        self.reserved = self.reserved | (req.type & MASK_RESERVED)
        self.identifier = req.identifier
