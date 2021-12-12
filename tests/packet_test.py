import pprint
import random
import unittest
from random import shuffle

import conn
from conn import ReAssembler
from packet.deserializer import deserialize_packet
from packet.p2t_packet import *
from packet.p2p_packet import *
from utils.bytes_utils import *
from packet.base_packet import *
from utils.test_utils import assert_attr_equal, print_packet
from utils.hash_utils import __get_hasher__
from torrent_local_state import *


class MyTestCase(unittest.TestCase):
    def test_bytes_util(self):
        self.assertEqual(int_to_bytes(0x1000, 2), b'\x10\x00')
        self.assertEqual(int_to_bytes(0x11, 1), b'\x11')
        self.assertEqual(int_to_bytes(0x1000FFFF, 4), b'\x10\x00\xFF\xFF')
        self.assertEqual(bytes_to_int(b'\x10'), 0x10)
        self.assertEqual(bytes_to_int(b'\x11\xFF'), 0x11FF)
        self.assertEqual(bytes_to_int(b'\xFF\xFF\xFF\xFF'), 0xFFFFFFFF)
        self.assertEqual(bytes_to_int(b'\x12\x11'), 0x1211)
        hasher = __get_hasher__()
        hasher.update(random_long())
        hasher.update(random_long())
        hasher.update(random_long())
        b = hasher.digest()
        bstr = hasher.hexdigest()
        self.assertEqual(hexstr_to_bytes(bstr), b)
        self.assertEqual(bytes_to_hexstr(b), bstr)

    def test_notify(self):
        n = NotifyPacket()
        n.identifier = bytes_to_int(random_short())
        n.ipv4_address = bytes_to_int(random_int())
        n.udp_port = bytes_to_int(random_short())
        binary = n.pack()
        nn = deserialize_packet(binary)
        assert_attr_equal(self, n, nn)

        ack = ACKNotifyPacket()
        ack.set_request(nn)
        back = ack.pack()
        uack: ACKNotifyPacket = deserialize_packet(back)
        self.assertEqual(uack.identifier, n.identifier)
        self.assertEqual(ack.identifier, n.identifier)
        print("Request Data: " + bytes_to_hexstr(binary))
        print("Response Data: " + bytes_to_hexstr(back))
        assert_attr_equal(self, ack, uack)

    def test_requestPeers(self):
        req = RequestPeerPacket()
        req.identifier = bytes_to_int(random_short())
        req.torrent_hash = random_bytes(32)
        breq = req.pack()
        rreq = deserialize_packet(breq)
        assert_attr_equal(self, req, rreq)

    def test_reassemble_header(self):
        pass

    def test_assembler_boxing(self):
        req = RequestPeerPacket()
        req.identifier = bytes_to_int(random_short())
        req.torrent_hash = random_bytes(32)
        ack = ACKRequestPeerPacket()
        ack.set_request(req)
        ack.status = STATUS_OK
        lst: List[IPPort] = list()
        for i in range(1, 205):
            lst.append((int_to_ipv4(bytes_to_int(random_int())), bytes_to_int(random_short())))
        ack.addresses = lst
        ass = conn.Assembler(ack, mtu=100)
        bs = ass.boxing()
        total_data = ""
        shuffle(bs)
        ra = ReAssembler(bs[0][0], bs[0][1] & MASK_REVERSED)
        print(total_data)
        print()
        print()
        for assed_ack in bs:
            pkt = deserialize_packet(assed_ack)
            result = ra.assemble(pkt)
            if assed_ack == bs[len(bs) - 1]:
                self.assertTrue(result)
            else:
                self.assertFalse(result)
        fpkt = deserialize_packet(ra.data)
        fpkt: ACKRequestPeerPacket
        self.assertEqual(fpkt.addresses, lst)

    def test_sid_packing(self):
        ids = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 16, 20, 21, 22, 30, 999, 11, 23}
        lst = TorrentLocalState.pack_seq_ids(ids)
        print(lst)
        lst_noflag = lst.copy()
        for i in range(0, len(lst_noflag)):
            lst_noflag[i] = lst_noflag[i] & (SID_FLAG_RANGE - 1)
        print(lst_noflag)
        unpacked_ids = TorrentLocalState.unpack_seq_ids(lst)
        self.assertEqual(ids, unpacked_ids)

    def test_random_sid_packing(self):
        for _ in range(0, 1000):
            mmax = 100
            ids = set()
            for i in range(0, 90):
                ii = random.randrange(1, mmax)
                ids.add(ii)
            lst = TorrentLocalState.pack_seq_ids(ids)
            unpacked = TorrentLocalState.unpack_seq_ids(lst)
            self.assertEqual(ids, unpacked)


if __name__ == '__main__':
    unittest.main()
