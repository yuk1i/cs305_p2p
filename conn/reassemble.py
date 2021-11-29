from __future__ import annotations

import copy
import math
from typing import Any, List, Tuple

import packet
import utils.bytes_utils
from packet.p2t_packet import *
from utils import bytes_utils


class ReAssembler:
    """
    ReAssemble Packets into one packet object
    """

    def __init__(self, itype: int, rev: int):
        self.type: int = itype
        self.rev = rev & MASK_REVERSED
        self.data = None
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
        start = bytes_to_int(pkt.__data__[4:8])
        length = bytes_to_int(pkt.__data__[8:12])
        total_length = bytes_to_int(pkt.__data__[12:16])
        # print("assembling packets: start:{} length:{}, total:{}".format(start, length, total_length))
        if not self.data:
            self.data = bytearray(total_length + 16)
            self.data[0:16] = pkt.__data__[0:16]
        self.data[start + 16:16 + start + length] = pkt.__data__[16:]
        self.intervals.append([start, start + length])
        self.merge()
        self.done = self.intervals[0][0] == 0 and self.intervals[0][1] == total_length
        # print(bytes_utils.bytes_to_hexstr(self.final_pkt.__data__))
        return self.done

    def final(self) -> bytes:
        """
        Get the bytes
        :return:
        """
        return self.data

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
    def __init__(self, pkt: BasePacket, mtu: int = 1460):
        self.raw_data = bytearray()
        w = ByteWriter(self.raw_data)
        pkt.__pack_internal__(w)
        pkt.pack_header()
        self.header: bytes = pkt.__data__[0:4]
        self.mtu = mtu

    def boxing(self) -> List[bytes]:
        # if self.type == TYPE_ACK and self.rev == TYPE_REQUEST_PEERS:

        raw = copy.deepcopy(self.raw_data)
        ret: List[bytes] = list()
        max_p = self.mtu
        cnt: int = 0
        total_bytes: int = len(self.raw_data)
        while len(raw) > 0:
            packed_data = raw[:max_p]
            raw = raw[max_p:]
            ba = bytearray()
            w = ByteWriter(ba)
            w.write_bytes(self.header)
            total_length = total_bytes
            start = cnt
            length = len(packed_data)
            w.write_int(start)
            w.write_int(length)
            w.write_int(total_length)
            w.write_bytes(packed_data)
            ret.append(ba)
            cnt += len(packed_data)
        return ret
