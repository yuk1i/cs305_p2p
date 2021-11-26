from __future__ import annotations

import threading
from collections import namedtuple
from typing import Dict, Tuple

import controller
import packet.deserializer

import conn
import proxy
from packet.base_packet import BasePacket, FLAG_REASSEMBLE, MASK_REVERSED

from utils import bytes_utils

IPPortBase = namedtuple("IPPortBase", ["ip", "port"])


class IPPort(IPPortBase):
    def __new__(cls, ip, port):
        obj = IPPortBase.__new__(cls, ip, port)
        return obj


class SocketManager:
    def __init__(self, pxy: proxy.Proxy, ctrl: controller.Controller):
        self.proxy = pxy
        self.controller = ctrl
        self.mapper: Dict[IPPort, conn.Conn] = dict()
        # self.peers: List[ConnManager] = list()
        self.reassemblers: Dict[int, conn.ReAssembler] = dict()
        self.thread = threading.Thread(target=self.__run__)
        self.thread.start()

    def __run__(self):
        while True:
            (data, src_addr) = self.proxy.recvfrom()
            if data is None and not self.proxy.active:
                print("Socket Manager exited")
                return
            pkt = packet.deserializer.deserialize_packet(data)
            self.on_pkt_recv(src_addr, pkt)

    def send_packet(self, pkt: BasePacket, dst_addr: IPPort):
        data = pkt.pack()
        self.proxy.sendto(data, dst_addr)

    def register(self, addr: IPPort, con: conn.Conn):
        if addr in self.mapper.keys():
            raise Exception("ConnManager exists for %s" % addr)
        con.socket = self
        self.mapper[addr] = con

    def unregister(self, addr: IPPort):
        if addr in self.mapper.keys():
            self.mapper[addr].close()
            del self.mapper[addr]

    def on_pkt_recv(self, src_addr: Tuple[str, int], pkt: BasePacket):
        iaddr = IPPort(src_addr[0], src_addr[1])
        if iaddr not in self.mapper.keys():
            # TODO: Create new Conn
            peer = self.mapper[iaddr] = self.controller.accept_conn(src_addr)
            if not peer:
                print("[Socket] Reject Connection From %s:%s" % src_addr)
                return
        peer: conn.Conn = self.mapper[iaddr]
        fragment: bool = pkt.__data__[1] & FLAG_REASSEMBLE == FLAG_REASSEMBLE
        if fragment:
            identifier: int = bytes_utils.bytes_to_int(pkt.__data__[2:2 + 2])
            reass = self.reassemblers[identifier]
            if not reass:
                ptype = pkt.__data__[0]
                rev = pkt.__data__[1] & MASK_REVERSED
                reass = self.reassemblers[identifier] = conn.ReAssembler(ptype, rev)
            if reass.assemble(pkt):
                fpkt = packet.deserialize_packet(reass.data)
                del self.reassemblers[identifier]
                peer.recv_packet(fpkt)
            return
        else:
            peer.recv_packet(pkt)

    def close(self):
        self.proxy.close()
        self.thread.join()
        for con in self.mapper.values():
            con.close()


if __name__ == '__main__':
    pass
