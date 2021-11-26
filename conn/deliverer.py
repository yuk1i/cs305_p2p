from __future__ import annotations

from typing import Dict, List, Tuple

import utils.bytes_utils
from conn.manager import ConnManager
from packet.base_packet import BasePacket, FLAG_REASSEMBLE
from utils import bytes_utils


class ReAssembler:
    """
    ReAssemble Packets into one packet object
    """

    def __init__(self, ptype: int):
        self.type: int = ptype
        """
        :param ptype: Packet Type
        """
        pass

    def assemble(self, packet: BasePacket) -> bool:
        """
        Reassemble a packet, return whether Reassembling is done
        :param packet:
        :return:
        """
        pass

    def final(self) -> BasePacket:
        """
        Get the final packet
        :return:
        """
        pass

    def done(self) -> bool:
        """
        Return whether reassemble is done
        :return:
        """
        pass


class Deliverer:
    def __init__(self):
        self.mapper: Dict[int, ConnManager] = dict()
        # self.peers: List[ConnManager] = list()
        self.reassemblers: Dict[int, ReAssembler] = dict()
        pass

    def register(self, addr: int, manager: ConnManager):
        if self.mapper[addr]:
            raise Exception("ConnManager exists for %s" % addr)
        self.mapper[addr] = manager

    def unregister(self, addr: int):
        if self.mapper[addr]:
            del self.mapper[addr]

    def deliver(self, src_addr: Tuple[str, int], packet: BasePacket):
        iaddr = bytes_utils.ipport_to_int(src_addr)
        peer = self.mapper[iaddr]
        fragment: bool = packet.__data__[1] & FLAG_REASSEMBLE == FLAG_REASSEMBLE
        if not peer:
            # TODO: Create new ConnManager
            peer = self.mapper[iaddr] = ConnManager(src_addr)
            peer.start()
        if fragment:
            identifier: int = bytes_utils.bytes_to_int(packet.__data__[2:2 + 2])
            reass = self.reassemblers[identifier]
            if not reass:
                ptype = packet.__data__[0]
                reass = self.reassemblers[identifier] = ReAssembler(ptype)
            if reass.assemble(packet):
                peer.deliver(reass.final())
                del self.reassemblers[identifier]
            return
        else:
            peer.deliver(packet)
