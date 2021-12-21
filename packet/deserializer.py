from packet.p2t_packet import *
from packet.p2p_packet import *


def get_packet_by_type(itype: int, reserved: int = 0) -> BasePacket:
    if itype == TYPE_ACK:
        req_type = reserved
        if req_type == TYPE_NOTIFY:
            return ACKNotifyPacket()
        if req_type == TYPE_REGISTER:
            return ACKRegisterPacket()
        if req_type == TYPE_REQUEST_PEERS:
            return ACKRequestPeerPacket()
        if req_type == TYPE_CANCEL:
            return ACKCancelPacket()
        if req_type == TYPE_CLOSE:
            return ACKClosePacket()
        if req_type == TYPE_REQUEST_TORRENT:
            return ACKRequestForTorrent()
        if req_type == TYPE_REQUEST_CHUNK:
            return ACKRequestChunk()
        if req_type == TYPE_UPDATE_CHUNK_INFO:
            return ACKUpdateChunkInfo()

    if itype == TYPE_NOTIFY:
        return NotifyPacket()
    if itype == TYPE_REGISTER:
        return RegisterPacket()
    if itype == TYPE_REQUEST_PEERS:
        return RequestPeerPacket()
    if itype == TYPE_CANCEL:
        return CancelPacket()
    if itype == TYPE_CLOSE:
        return ClosePacket()
    if itype == TYPE_REQUEST_TORRENT:
        return RequestForTorrent()
    if itype == TYPE_REQUEST_CHUNK:
        return RequestChunk()
    if itype == TYPE_UPDATE_CHUNK_INFO:
        return UpdateChunkInfo()
    if itype == TYPE_SET_CHOKE_STATUS:
        return SetChokeStatus()


def deserialize_packet(data: bytes) -> BasePacket:
    itype = data[0]
    rev = data[1] & MASK_REVERSED
    return get_packet_by_type(itype, rev).unpack(data)
