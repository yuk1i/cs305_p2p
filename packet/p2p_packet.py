from typing import List, Tuple

import utils.bytes_utils
from packet.base_packet import *
from utils.bytes_utils import ByteWriter, ByteReader


class RequestForTorrent(BasePacket):
    def __init__(self):
        super(RequestForTorrent, self).__init__(TYPE_REQUEST_TORRENT)
        self.torrent_hash: bytes = b''
        self.since: int = 0
        self.expectedLength: int = 0xFFFFFFFF

    def __pack_internal__(self, w: ByteWriter):
        w.write_bytes(self.torrent_hash)
        w.write_int(self.since)
        w.write_int(self.expectedLength)

    def __unpack_internal__(self, r: ByteReader):
        self.torrent_hash = r.read_bytes(32)
        self.since = r.read_int()
        self.expectedLength = r.read_int()


class ACKRequestForTorrent(ACKPacket):
    def __init__(self):
        super(ACKRequestForTorrent, self).__init__()
        self.reassemble = ReAssembleHeader()
        self.status = STATUS_NOT_SET
        self.data: bytes = b''

    def __pack_internal__(self, w: ByteWriter):
        w.write_int(self.status)
        w.write_bytes(self.data)

    def __unpack_internal__(self, r: ByteReader):
        self.status = r.read_int()
        self.data = r.read_bytes(r.remain())


class UpdateChunkInfo(BasePacket):
    def __init__(self):
        super(UpdateChunkInfo, self).__init__(TYPE_UPDATE_CHUNK_INFO)
        self.reassemble = ReAssembleHeader()
        self.torrent_hash: bytes = b''
        self.seq_ids: List[int] = list()

    def __pack_internal__(self, w: ByteWriter):
        w.write_bytes(self.torrent_hash)
        for seq in self.seq_ids:
            w.write_int(seq)

    def __unpack_internal__(self, r: ByteReader):
        self.torrent_hash = r.read_bytes(32)
        while r.remain() >= 4:
            self.seq_ids.append(r.read_int())


class ACKRequestChunkInfo(ACKPacket):
    def __init__(self):
        super(ACKRequestChunkInfo, self).__init__()
        self.reassemble = ReAssembleHeader()
        self.status: int = STATUS_NOT_SET
        self.seq_ids: List[int] = list()

    def __pack_internal__(self, w: ByteWriter):
        w.write_int(self.status)
        for seq in self.seq_ids:
            w.write_int(seq)

    def __unpack_internal__(self, r: ByteReader):
        self.status = r.read_int()
        while r.remain() >= 4:
            self.seq_ids.append(r.read_int())


class RequestChunk(BasePacket):
    def __init__(self):
        super(RequestChunk, self).__init__(TYPE_REQUEST_CHUNK)
        self.torrent_hash: bytes = b''
        self.chunk_seq_id: int = 0
        self.start_byte: int = 0
        self.expected_end_byte: int = 0

    def __pack_internal__(self, w: ByteWriter):
        w.write_bytes(self.torrent_hash)
        w.write_int(self.chunk_seq_id)
        w.write_int(self.start_byte)
        w.write_int(self.expected_end_byte)

    def __unpack_internal__(self, r: ByteReader):
        self.torrent_hash = r.read_bytes(32)
        self.chunk_seq_id = r.read_int()
        self.start_byte = r.read_int()
        self.expected_end_byte = r.read_int()


class ACKRequestChunk(ACKPacket):
    def __init__(self):
        super(ACKRequestChunk, self).__init__()
        self.status: int = STATUS_NOT_SET
        self.data: bytes = b''

    def __pack_internal__(self, w: ByteWriter):
        w.write_int(self.status)
        w.write_bytes(self.data)

    def __unpack_internal__(self, r: ByteReader):
        self.status = r.read_int()
        self.data = r.read_bytes(r.remain())
