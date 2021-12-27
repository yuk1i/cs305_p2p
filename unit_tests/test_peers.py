from __future__ import annotations

import os
import pathlib
import shutil
import threading
import time
import unittest

import controller
import utils.bytes_utils
from controller import TrackerController, PeerController, Controller, TrackerStatus, TorrentStatus
from Proxy import Proxy
from torrent import Torrent


def new_peer(port, tracker_addr, upload=0, download=0):
    p2_addr = ('127.0.0.1', port)
    p = PeerController(Proxy(upload, download, port), p2_addr, tracker_addr)
    p.socket.mtu = 65500
    p.notify_tracker()
    return p


class MyTestCase(unittest.TestCase):
    def test_chunk_info(self):
        if os.path.exists("excluded/dummy"):
            shutil.rmtree("excluded/dummy")
        if os.path.exists("excluded/dummy.bt"):
            os.remove("excluded/dummy.bt")
        tracker = TrackerController(Proxy(0, 0, 10086))
        tracker_addr = ('127.0.0.1', 10086)
        p1_addr = ("127.0.0.1", 20086)
        p1 = PeerController(Proxy(0, 0, 20086), p1_addr, tracker_addr)
        p1.socket.mtu = 65500
        p1.notify_tracker()

        p2_addr = ('127.0.0.1', 30086)
        p2 = PeerController(Proxy(0, 0, 30086), p2_addr, tracker_addr)
        p2.socket.mtu = 65500
        p2.notify_tracker()

        full_tt = Torrent.generate_torrent("test_torrent", "A Test Torrent for download", 204800)
        # 8403382 bytes in total
        tt_hash = full_tt.torrent_hash
        dummy_tt = Torrent.create_dummy_torrent(tt_hash)

        p1.register_torrent(full_tt, 'excluded/full.bt', "test_torrent")

        p2.register_torrent(dummy_tt, 'excluded/dummy.bt', "excluded/dummy")

        tstart = utils.bytes_utils.current_time_ms()
        p2.start_download(tt_hash)

        p2.active_torrents[tt_hash].wait_downloaded()
        tend = utils.bytes_utils.current_time_ms()
        print("Download use time %s" % (tend - tstart))

        self.assertTrue(p2.active_torrents[tt_hash].dir_controller.check_all_hash())

        p1.close_from_tracker()
        p1.close()
        p2.close_from_tracker()
        p2.close()
        tracker.close()
        self.assertEqual(True, True)

    def test_speed(self):
        if os.path.exists("excluded/dummy"):
            shutil.rmtree("excluded/dummy")
        if os.path.exists("excluded/dummy.bt"):
            os.remove("excluded/dummy.bt")
        if os.path.exists("excluded/dummy3"):
            shutil.rmtree("excluded/dummy3")
        if os.path.exists("excluded/dummy3.bt"):
            os.remove("excluded/dummy3.bt")
        if os.path.exists("excluded/dummy4"):
            shutil.rmtree("excluded/dummy4")
        if os.path.exists("excluded/dummy4.bt"):
            os.remove("excluded/dummy4.bt")
        tracker = TrackerController(Proxy(0, 0, 10086))
        tracker_addr = ('127.0.0.1', 10086)

        p1 = new_peer(20086, tracker_addr, upload=409600 * 4)
        # approximate 5s for full uploading
        p2 = new_peer(30086, tracker_addr)
        p3 = new_peer(40086, tracker_addr)
        p4 = new_peer(15616, tracker_addr)

        full_tt = Torrent.generate_torrent("test_torrent", "A Test Torrent for download", 204800)
        # 8403382 bytes in total
        tt_hash = full_tt.torrent_hash
        dummy_tt = Torrent.create_dummy_torrent(tt_hash)
        dummy_tt3 = Torrent.create_dummy_torrent(tt_hash)
        dummy_tt4 = Torrent.create_dummy_torrent(tt_hash)

        p1.register_torrent(full_tt, 'excluded/full.bt', "test_torrent")
        p1.active_torrents[tt_hash].upload_mode = controller.MODE_DONT_REPEAT

        p2.register_torrent(dummy_tt, 'excluded/dummy.bt', "excluded/dummy")
        p3.register_torrent(dummy_tt3, 'excluded/dummy3.bt', "excluded/dummy3")
        p4.register_torrent(dummy_tt4, 'excluded/dummy4.bt', "excluded/dummy4")

        tstart = utils.bytes_utils.current_time_ms()
        p2.start_download(tt_hash)
        p3.start_download(tt_hash)
        p4.start_download(tt_hash)
        p2.active_torrents[tt_hash].wait_downloaded()
        p3.active_torrents[tt_hash].wait_downloaded()
        p4.active_torrents[tt_hash].wait_downloaded()
        tend = utils.bytes_utils.current_time_ms()
        print("Download use time %s" % (tend - tstart))

        p1.close_from_tracker()
        p1.close()
        p2.close_from_tracker()
        p2.close()
        p3.close_from_tracker()
        p3.close()
        p4.close_from_tracker()
        p4.close()
        tracker.close()


if __name__ == '__main__':
    unittest.main()
