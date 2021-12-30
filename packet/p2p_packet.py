from typing import List, Tuple, Set

import utils.bytes_utils
import torrent
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
        self.start_at = 0
        self.length = 0
        self.total_length = 0
        self.data: bytes = b''

    def __pack_internal__(self, w: ByteWriter):
        w.write_int(self.status)
        w.write_int(self.start_at)
        w.write_int(self.length)
        w.write_int(self.total_length)
        w.write_bytes(self.data)

    def __unpack_internal__(self, r: ByteReader):
        self.status = r.read_int()
        self.start_at = r.read_int()
        self.length = r.read_int()
        self.total_length = r.read_int()
        self.data = r.read_bytes(r.remain())


class UpdateChunkInfo(BasePacket):
    def __init__(self):
        super(UpdateChunkInfo, self).__init__(TYPE_UPDATE_CHUNK_INFO)
        self.reassemble = ReAssembleHeader()
        self.torrent_hash: bytes = b''
        self.packed_seq_ids: List[int] = list()

    def __pack_internal__(self, w: ByteWriter):
        w.write_bytes(self.torrent_hash)
        for seq in self.packed_seq_ids:
            w.write_int(seq)

    def __unpack_internal__(self, r: ByteReader):
        self.torrent_hash = r.read_bytes(32)
        while r.remain() >= 4:
            self.packed_seq_ids.append(r.read_int())


class ACKUpdateChunkInfo(ACKPacket):
    def __init__(self):
        super(ACKUpdateChunkInfo, self).__init__()
        self.reassemble = ReAssembleHeader()
        self.status: int = STATUS_NOT_SET
        self.packed_seq_ids: List[int] = list()

    def __pack_internal__(self, w: ByteWriter):
        w.write_int(self.status)
        for seq in self.packed_seq_ids:
            w.write_int(seq)

    def __unpack_internal__(self, r: ByteReader):
        self.status = r.read_int()
        while r.remain() >= 4:
            self.packed_seq_ids.append(r.read_int())


class RequestChunk(BasePacket):
    def __init__(self):
        super(RequestChunk, self).__init__(TYPE_REQUEST_CHUNK)
        self.torrent_hash: bytes = b''
        self.chunk_seq_id: int = 0
        self.start_byte: int = 0
        self.expected_end_byte: int = 0xFFFFFFFF

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
        self.reassemble = ReAssembleHeader()
        self.status: int = STATUS_NOT_SET
        self.chunk_seq_id: int = 0
        self.data: bytes = b''

    def __pack_internal__(self, w: ByteWriter):
        w.write_int(self.status)
        w.write_int(self.chunk_seq_id)
        w.write_bytes(self.data)

    def __unpack_internal__(self, r: ByteReader):
        self.status = r.read_int()
        self.chunk_seq_id = r.read_int()
        self.data = r.read_bytes(r.remain())

class SetChokeStatus(BasePacket):
    def __init__(self):
        super(SetChokeStatus, self).__init__(TYPE_SET_CHOKE_STATUS)
        self.torrent_hash: bytes = b''
        self.choke_status: bool = False

    def __pack_internal__(self, w: ByteWriter):
        w.write_bytes(self.torrent_hash)
        w.write_int(1 if self.choke_status else 0)

    def __unpack_internal__(self, r: ByteReader):
        self.torrent_hash = r.read_bytes(32)
        self.choke_status = True if r.read_int() == 1 else False