from __future__ import annotations

import threading
import time
from collections import namedtuple
from typing import Dict, Tuple, List

import controller
import packet.deserializer

import conn
import proxy
from packet.base_packet import BasePacket, FLAG_REASSEMBLE, MASK_REVERSED

from utils import bytes_utils, IPPort


class SocketManager:
    def __init__(self, pxy: proxy.Proxy, ctrl: controller.Controller):
        self.proxy = pxy
        self.controller = ctrl
        self.mapper: Dict[IPPort, conn.Conn] = dict()
        self.mtu = 1460
        # self.peers: List[ConnManager] = list()
        self.reassemblers: Dict[int, conn.ReAssembler] = dict()
        self.thread = threading.Thread(target=self.__run__)
        self.thread.start()

    def __run__(self):
        while True:
            data = None
            src_addr: IPPort = None
            try:
                (data, src_addr) = self.proxy.recvfrom(0.010)  # 10ms check
            except TimeoutError:
                pass
            if not data and not self.proxy.active:
                print("Socket Manager exited")
                return
            if data and src_addr:
                if src_addr not in self.mapper.keys():
                    peer = self.mapper[src_addr] = self.controller.accept_conn(src_addr)
                    if not peer:
                        print(f"[Socket] Reject Connection From {src_addr}")
                        continue
                self.mapper[src_addr].connectionStatus.feed_downlink(len(data))
                pkt = packet.deserializer.deserialize_packet(data)
                self.on_pkt_recv(src_addr, pkt)
            for con in self.mapper.values():
                con.check_timeout()

    def send_packet(self, pkt: BasePacket, dst_addr: IPPort):
        peer: conn.Conn = self.mapper[dst_addr]
        if pkt.reassemble.enabled:
            pkts = conn.Assembler(pkt, self.mtu).boxing()
            total_size = 0
            for pdata in pkts:
                self.proxy.sendto(pdata, dst_addr)
                total_size += len(pdata)
            peer.connectionStatus.feed_uplink(total_size)
        else:
            data = pkt.pack()
            self.proxy.sendto(data, dst_addr)
            peer.connectionStatus.feed_uplink(len(data))
            # non blocking

    def register(self, addr: IPPort, con: conn.Conn):
        if addr in self.mapper.keys():
            return
        con.socket = self
        self.mapper[addr] = con

    def unregister(self, addr: IPPort):
        if addr in self.mapper.keys():
            del self.mapper[addr]

    def on_pkt_recv(self, src_addr: IPPort, pkt: BasePacket):
        peer: conn.Conn = self.mapper[src_addr]
        fragment: bool = pkt.__data__[1] & FLAG_REASSEMBLE == FLAG_REASSEMBLE
        if fragment:
            identifier: int = bytes_utils.bytes_to_int(pkt.__data__[2:2 + 2])
            if identifier not in self.reassemblers.keys():
                ptype = pkt.__data__[0]
                rev = pkt.__data__[1] & MASK_REVERSED
                self.reassemblers[identifier] = conn.ReAssembler(ptype, rev)
            reass = self.reassemblers[identifier]
            if reass.assemble(pkt):
                fpkt = packet.deserialize_packet(reass.data)
                del self.reassemblers[identifier]
                peer.recv_packet(fpkt)
            return
        else:
            peer.recv_packet(pkt)

    def close(self):
        for remote_addr in self.mapper:
            self.mapper[remote_addr].close()
        self.mapper.clear()
        self.mapper.clear()
        self.proxy.close()
        self.thread.join()


if __name__ == '__main__':
    pass
