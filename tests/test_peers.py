from __future__ import annotations

import threading
import time
import unittest
from controller import TrackerController, PeerController, Controller, TrackerStatus, TorrentStatus
from proxy import Proxy
from torrent import Torrent


class MyTestCase(unittest.TestCase):
    def test_torrent_file(self):
        tracker = TrackerController(Proxy(0, 0, 10086))
        tracker_addr = ('127.0.0.1', 10086)
        p1_addr = ("127.0.0.1", 20086)
        p1 = PeerController(Proxy(0, 0, 20086), p1_addr, tracker_addr)
        p1.notify_tracker()

        p2_addr = ('127.0.0.1', 30086)
        p2 = PeerController(Proxy(0, 0, 30086), p2_addr, tracker_addr)
        p2.notify_tracker()

        full_tt = Torrent.generate_torrent("test_torrent", "A Test Torrent")
        tt_hash = full_tt.torrent_hash
        dummy_tt = Torrent.create_dummy_torrent(tt_hash)

        p1.register_torrent(full_tt)
        p2.register_torrent(dummy_tt)

        p1.retrieve_peer_list(tt_hash)
        self.assertIn(p2_addr, p1.active_torrents[tt_hash].peer_list)

        p2.retrieve_peer_list(tt_hash)
        p2.start_download(tt_hash, "excluded/test_download/", "excluded/test_torrent.torrent")

        p2.active_torrents[tt_hash].wait_downloaded()

        p1.close_from_tracker()
        p1.close()
        p2.close_from_tracker()
        p2.close()
        tracker.close()



if __name__ == '__main__':
    unittest.main()
