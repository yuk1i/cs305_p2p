import unittest

from packet.deserializer import deserialize_packet
from packet.p2t_packet import *
from utils.bytes_utils import *
from packet.base_packet import *
from utils.test_utils import assert_attr_equal
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
        n.uuid = bytes_to_int(random_long())
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


if __name__ == '__main__':
    unittest.main()
