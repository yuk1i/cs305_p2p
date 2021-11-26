import pprint
import unittest
from random import shuffle

import conn
from conn import ReAssembler
from packet.deserializer import deserialize_packet
from packet.p2t_packet import *
from utils.bytes_utils import *
from packet.base_packet import *
from utils.test_utils import assert_attr_equal, print_packet
from utils.hash_utils import __get_hasher__


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
        req = RequestPeer()
        req.identifier = bytes_to_int(random_short())
        req.torrent_hash = random_bytes(32)
        breq = req.pack()
        rreq = deserialize_packet(breq)
        assert_attr_equal(self, req, rreq)

    def test_reassemble_header(self):
        pass

    def test_assembler_boxing(self):
        req = RequestPeer()
        req.identifier = bytes_to_int(random_short())
        req.torrent_hash = random_bytes(32)
        lst: List[Tuple[str, int]] = list()
        for i in range(1, 205):
            lst.append((int_to_ipv4(bytes_to_int(random_int())), bytes_to_int(random_short())))
        print(lst)
        ass = conn.Assembler(TYPE_ACK, TYPE_REQUEST_PEERS, lst, mtu=200)
        ret = ass.boxing(req)
        bs = list()
        total_data = ""
        for assed_ack in ret:
            bb = assed_ack.pack()
            bs.append(bb)
            data = print_packet(bb)
            print(bytes_to_hexstr(data))
            total_data += bytes_to_hexstr(data)
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
        fpkt: ACKRequestPeer
        self.assertEqual(fpkt.addresses, lst)


if __name__ == '__main__':
    unittest.main()
