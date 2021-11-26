from packet.p2t_packet import *


def get_packet_by_type(itype: int, reserved: int = 0) -> BasePacket:
    if itype == TYPE_ACK:
        req_type = reserved
        if req_type == TYPE_NOTIFY:
            return ACKNotifyPacket()
        if req_type == TYPE_REGISTER:
            return ACKRegisterPacket()
        if req_type == TYPE_REQUEST_PEERS:
            return ACKRequestPeer()

    if itype == TYPE_NOTIFY:
        return NotifyPacket()
    if itype == TYPE_REGISTER:
        return RegisterPacket()
    if itype == TYPE_REQUEST_PEERS:
        return RequestPeer()


def deserialize_packet(data: bytes) -> BasePacket:
    itype = data[0]
    rev = data[1] & MASK_REVERSED
    return get_packet_by_type(itype, rev).unpack(data)
