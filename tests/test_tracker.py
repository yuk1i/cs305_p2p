from __future__ import annotations

import threading
import time
import unittest
from controller import TrackerController, PeerController, Controller, TrackerStatus, TorrentStatus
from proxy import Proxy
from torrent import Torrent


class TrackerTest(unittest.TestCase):
    def test_tracker(self):
        tracker = TrackerController(Proxy(0, 0, 10086))
        tracker_addr = ('127.0.0.1', 10086)
        peer_addr = ("127.0.0.1", 20086)
        peer = PeerController(Proxy(0, 0, 20086), peer_addr, tracker_addr)

        # Test Notify
        peer.notify_tracker()
        # while peer.tracker_status != TrackerStatus.NOTIFIED:
        #     time.sleep(0.05)
        # time.sleep(1)
        self.assertEqual((peer.tracker_uuid, peer_addr), tracker.peers[0])

        # Test Register
        tt = Torrent.generate_torrent("test_torrent", "A Test Torrent")
        peer.register_torrent_from_object(tt, save_file_path='excluded/a1.bt')
        self.assertEqual(peer.active_torrents[tt.torrent_hash].torrent, tt)
        # wait response
        # while peer.active_torrents[tt.torrent_hash].status != TorrentStatus.TORRENT_STATUS_REGISTERED:
        #     time.sleep(0.05)
        self.assertIn(peer.local_addr, tracker.torrents[tt.torrent_hash])

        # Test retrieve peer list
        p2_addr = ('127.0.0.1', 30086)
        p2 = PeerController(Proxy(0, 0, 30086), p2_addr, tracker_addr)
        p2.notify_tracker()
        p2.register_torrent_from_object(tt, save_file_path='excluded/a2.bt')
        self.assertIn(p2.local_addr, tracker.torrents[tt.torrent_hash])

        p2.retrieve_peer_list(tt.torrent_hash)

        print(p2.active_torrents[tt.torrent_hash].peer_list)

        self.assertIn(peer_addr, p2.active_torrents[tt.torrent_hash].peer_list)

        p2.cancel(tt.torrent_hash)

        peer.retrieve_peer_list(tt.torrent_hash)

        self.assertNotIn(p2.local_addr, peer.active_torrents[tt.torrent_hash].peer_list)

        # Register p2 again
        p2.register_torrent_from_object(tt, save_file_path='excluded/a2.bt')
        peer.retrieve_peer_list(tt.torrent_hash)

        self.assertIn(p2.local_addr, peer.active_torrents[tt.torrent_hash].peer_list)

        torrent2 = Torrent.generate_torrent("test_torrent/qwq.txt", "test 2")
        p2.register_torrent_from_object(torrent2, save_file_path='excluded/b2.bt')

        self.assertIn(p2.local_addr, tracker.torrents[torrent2.torrent_hash])

        p2.close_from_tracker()

        self.assertNotIn(p2.local_addr, tracker.torrents[torrent2.torrent_hash])
        self.assertNotIn(p2.local_addr, tracker.torrents[tt.torrent_hash])

        peer.retrieve_peer_list(tt.torrent_hash)
        self.assertNotIn(p2.local_addr, peer.active_torrents[tt.torrent_hash].peer_list)
        peer.register_torrent_from_object(torrent2, save_file_path='excluded/b1.bt')
        peer.retrieve_peer_list(torrent2.torrent_hash)
        self.assertNotIn(p2.local_addr, peer.active_torrents[torrent2.torrent_hash].peer_list)

        peer.close()
        p2.close()
        tracker.close()

        for thread in threading.enumerate():
            print(thread.name)


if __name__ == '__main__':
    unittest.main()
