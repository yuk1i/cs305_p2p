from typing import Tuple

import conn
import proxy


class Controller:
    def __init__(self, pxy: proxy.Proxy):
        self.proxy: proxy.Proxy = pxy
        self.local_addr: Tuple[str, int] = ("", 0)
        self.socket: conn.SocketManager = conn.SocketManager(self.proxy, self)

    def set_local_addr(self, addr: Tuple[str, int]):
        self.local_addr = addr

    def accept_conn(self, src_addr: Tuple[str, int]) -> conn.Conn:
        print("[Controller] : new Conn from %s" % src_addr)
        return None

    def create_conn(self, target_addr: Tuple[str, int]) -> conn.Conn:
        pass
