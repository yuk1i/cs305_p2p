from __future__ import annotations

import copy
import math
from typing import Any, List, Tuple

import packet
import utils.bytes_utils
from packet.p2t_packet import *
from utils import bytes_utils


def get_entry_size(itype, rev) -> int:
    """
    How many bytes does a partition need
    :return:
    """
    if itype == TYPE_ACK and rev == TYPE_REQUEST_PEERS:
        return 6
    else:
        return 1


class ReAssembler:
    """
    ReAssemble Packets into one packet object
    """

    def __init__(self, itype: int, rev: int):
        self.type: int = itype
        self.rev = rev & MASK_REVERSED
        self.entry_size = get_entry_size(self.type, self.rev)
        self.final_pkt = None
        self.done = False
        self.intervals: List[List[int]] = list()
        """
        :param ptype: Packet Type
        """
        pass

    def assemble(self, pkt: BasePacket) -> bool:
        """
        Reassemble a packet, return whether Reassembling is done
        :param packet:
        :return:
        """
        if self.entry_size <= 0:
            self.final_pkt = pkt
            self.done = True
            return True
        start = bytes_to_int(pkt.__data__[4:8])
        length = bytes_to_int(pkt.__data__[8:12])
        total_length = bytes_to_int(pkt.__data__[12:16])
        # print("assembling packets: start:{} length:{}, total:{}".format(start, length, total_length))
        if not self.final_pkt:
            self.final_pkt = packet.deserializer.get_packet_by_type(self.type, self.rev)
            self.final_pkt.__data__ = bytearray(total_length + 4 + 12)
            self.final_pkt.__data__[0:16] = pkt.__data__[0:16]
        self.final_pkt.__data__[start + 16:16 + start + length] = pkt.__data__[16:]
        self.intervals.append([start, start + length])
        self.merge()
        self.done = self.intervals[0][0] == 0 and self.intervals[0][1] == total_length
        # print(bytes_utils.bytes_to_hexstr(self.final_pkt.__data__))
        return self.done

    def final(self) -> BasePacket:
        """
        Get the final packet
        :return:
        """
        return self.final_pkt

    def merge(self):
        if len(self.intervals) == 0 or len(self.intervals) == 1:
            return True
        self.intervals.sort(key=lambda x: x[0])
        result = [self.intervals[0]]
        for interval in self.intervals[1:]:
            if interval[0] <= result[-1][1]:
                result[-1][1] = max(result[-1][1], interval[1])
            else:
                result.append(interval)
        self.intervals = result


class Assembler:
    def __init__(self, itype, rev, raw_data: List[Any] | bytes, mtu: int = 1460):
        self.type = itype
        self.rev = rev
        self.raw_data = raw_data
        self.mtu = mtu

    def boxing(self, request: BasePacket = None) -> List[BasePacket]:
        # if self.type == TYPE_ACK and self.rev == TYPE_REQUEST_PEERS:
        entry_size = get_entry_size(self.type, self.rev)

        raw = copy.deepcopy(self.raw_data)
        ret: List[BasePacket] = list()
        max_p = math.floor(self.mtu / entry_size)
        cnt: int = 0
        total_bytes: int = len(self.raw_data) * entry_size
        while len(raw) > 0:
            packed_data = raw[:max_p]
            raw = raw[max_p:]
            pkt = ACKRequestPeer()
            pkt.set_request(request)
            pkt.reassemble.total_length = total_bytes
            pkt.reassemble.start = cnt * entry_size
            pkt.reassemble.length = len(packed_data) * entry_size
            self.pack_once(packed_data, pkt)
            ret.append(pkt)
            cnt += len(packed_data)
        return ret

    def pack_once(self, packed_data: List[Any] | bytes, pkt: BasePacket):
        if self.type == TYPE_ACK and self.rev == TYPE_REQUEST_PEERS:
            pkt: ACKRequestPeer
            packed_data: List[Tuple[str, int]]
            pkt.addresses.extend(packed_data)
        else:
            pkt.data = packed_data
