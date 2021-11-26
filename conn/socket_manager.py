from __future__ import annotations

import threading
from typing import Dict, List, Tuple

import packet.deserializer
import proxy as proxy

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


class SocketManager:
    def __init__(self, proxy: proxy.Proxy):
        self.mapper: Dict[int, ConnManager] = dict()
        # self.peers: List[ConnManager] = list()
        self.reassemblers: Dict[int, ReAssembler] = dict()
        self.proxy = proxy
        self.thread = threading.Thread(target=self.__run__)
        self.thread.start()

    def __run__(self):
        while True:
            (data, src_addr) = self.proxy.recvfrom()
            pkt = packet.deserializer.deserialize_packet(data)
            self.deliver(src_addr, pkt)

    def send_packet(self, pkt: BasePacket, dst_addr: Tuple[str, int]):
        data = pkt.pack()
        self.proxy.sendto(data, dst_addr)

    def register(self, addr: int, manager: ConnManager):
        if self.mapper[addr]:
            raise Exception("ConnManager exists for %s" % addr)
        manager.socket = self
        self.mapper[addr] = manager

    def unregister(self, addr: int):
        if self.mapper[addr]:
            del self.mapper[addr]

    def deliver(self, src_addr: Tuple[str, int], pkt: BasePacket):
        iaddr = bytes_utils.ipport_to_int(src_addr)
        peer = self.mapper[iaddr]
        fragment: bool = pkt.__data__[1] & FLAG_REASSEMBLE == FLAG_REASSEMBLE
        if not peer:
            # TODO: Create new ConnManager
            peer = self.mapper[iaddr] = self.__new__peer(src_addr)
            peer.start()
        if fragment:
            identifier: int = bytes_utils.bytes_to_int(pkt.__data__[2:2 + 2])
            reass = self.reassemblers[identifier]
            if not reass:
                ptype = pkt.__data__[0]
                reass = self.reassemblers[identifier] = ReAssembler(ptype)
            if reass.assemble(pkt):
                peer.deliver(reass.final())
                del self.reassemblers[identifier]
            return
        else:
            peer.deliver(pkt)

    def __new__peer(self, src_addr: Tuple[str, int]) -> ConnManager:
        pass


if __name__ == '__main__':
    pass
