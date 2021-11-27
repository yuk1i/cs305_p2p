from __future__ import annotations

import threading
import time
import unittest
from controller import TrackerController, PeerController, Controller, TrackerStatus
from proxy import Proxy


class TrackerTest(unittest.TestCase):
    def test_tracker(self):
        tracker = TrackerController(Proxy(0, 0, 10086))
        tracker_addr = ('127.0.0.1', 10086)
        peer_addr = ("127.0.0.1", 20086)
        peer = PeerController(Proxy(0, 0, 20086), peer_addr, tracker_addr)

        # Test Notify
        peer.notify_tracker()
        while peer.tracker_status != TrackerStatus.NOTIFIED:
            time.sleep(0.05)
        time.sleep(1)
        self.assertEqual((peer.tracker_uuid, peer_addr), tracker.peers[0])
        tracker.close()
        peer.close()

        for thread in threading.enumerate():
            print(thread.name)


if __name__ == '__main__':
    unittest.main()
