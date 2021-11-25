import unittest
from utils.bytes_utils import *
from packet.base_packet import *
from test_utils import assert_attr_equal


class MyTestCase(unittest.TestCase):
    def test_bytes_util(self):
        self.assertEqual(int_to_bytes(0x1000, 2), b'\x10\x00')
        self.assertEqual(int_to_bytes(0x11, 1), b'\x11')
        self.assertEqual(int_to_bytes(0x1000FFFF, 4), b'\x10\x00\xFF\xFF')
        self.assertEqual(bytes_to_int(b'\x10'), 0x10)
        self.assertEqual(bytes_to_int(b'\x11\xFF'), 0x11FF)
        self.assertEqual(bytes_to_int(b'\xFF\xFF\xFF\xFF'), 0xFFFFFFFF)
        self.assertEqual(bytes_to_int(b'\x12\x11'), 0x1211)

    def test_notify(self):
        n = NotifyPacket()
        n.identifier = bytes_to_int(random_short())
        n.uuid = bytes_to_int(random_long())
        n.ipv4_address = bytes_to_int(random_int())
        n.udp_port = bytes_to_int(random_short())
        binary = n.pack()
        nn = deserialize_packet(binary)
        assert_attr_equal(self, n, nn)


if __name__ == '__main__':
    unittest.main()
