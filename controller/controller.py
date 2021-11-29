from __future__ import annotations

from typing import Tuple

import conn
import proxy
from utils import IPPort


class Controller:
    def __init__(self, pxy: proxy.Proxy):
        self.proxy: proxy.Proxy = pxy
        self.local_addr: IPPort = ("", 0)
        self.socket: conn.SocketManager = conn.SocketManager(self.proxy, self)

    def set_local_addr(self, addr: IPPort):
        self.local_addr = addr

    def accept_conn(self, src_addr: IPPort) -> conn.Conn:
        print("[Controller] : new Conn from %s:%s" % src_addr)
        return None

    def close(self):
        pass
