from __future__ import annotations

from typing import Tuple, Dict, List, Set

import conn
import proxy
import controller
from utils.bytes_utils import random_long, bytes_to_int


class PeerController(controller.Controller):
    def __init__(self, pxy: proxy.Proxy):
        super(PeerController, self).__init__(pxy)
        self.torrent_list = list()
