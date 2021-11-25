from packet.base_packet import *
from packet.p2t_packet import *


def deserialize_packet(data: bytes) -> BasePacket:
    ptype = data[0]
    if ptype == TYPE_ACK:
        req_type = data[1] & MASK_REVERSED
        if req_type == TYPE_NOTIFY:
            return ACKNotifyPacket().unpack(data)
        if req_type == TYPE_REGISTER:
            return ACKRegisterPacket().unpack(data)
        if req_type == TYPE_REQUEST_PEERS:
            return ACKRequestPeer().unpack(data)

    if ptype == TYPE_NOTIFY:
        return NotifyPacket().unpack(data)
    if ptype == TYPE_REGISTER:
        return RegisterPacket().unpack(data)
    if ptype == TYPE_REQUEST_PEERS:
        return RequestPeer().unpack(data)
