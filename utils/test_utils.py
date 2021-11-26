import unittest

from .bytes_utils import bytes_to_hexstr as hexstr, bytes_to_int as bint, hexstr_to_bytes
from packet.base_packet import FLAG_REASSEMBLE


def assert_attr_equal(self: unittest.TestCase, obj1: object, obj2: object):
    self.assertEqual(type(obj1), type(obj2))
    attrs = filter(lambda x: (not str(x).startswith("__")), vars(obj1))
    for att in attrs:
        self.assertEqual(obj1.__getattribute__(att), obj2.__getattribute__(att))


def print_packet(data: bytes) -> bytes:
    header = data[0:0 + 4]
    type = header[0]
    rev = header[1]
    ident = bint(header[2:4])
    data = data[4:]
    print("Header : Type:{}, \t\tRev:{}, \tIdent:{}".format(type, rev, ident))
    print("Flags  : RSMB:{}".format(header[1] & FLAG_REASSEMBLE == FLAG_REASSEMBLE))
    if header[1] & FLAG_REASSEMBLE == FLAG_REASSEMBLE:
        asm = data[0:12]
        data = data[12:]
        start = bint(asm[0:4])
        length = bint(asm[4:8])
        total_length = bint(asm[8:12])
        print("RSMB   : Start:{}  \tlength:{}  \ttotal:{}".format(start, length, total_length))
    return data


if __name__ == '__main__':
    hexs = "20917d2000000000000000c6000004aaf028a47e9787740ee0ac58370dfe7131785d31dc59fb49d484a0d8cbe9b66ba12ee969a3e2813c33082ca9da86d5e9c83d34fa883e7e344072b129bd8961e6805948534d849a6017aa0fad6dee3a0ae2cda64330fae264c6f60b7a70b772fc1d51b3f376520542778fb143429152194c463d8de415c7ed5c7f9a6318dcebc8844a951359ce4fff5c675009e7e089215d9de4531c73e60bd7d065d781e168498e1c6cc4bbe88c65bace0a219a32c6554924a6c0d9f73b064ffa4f63f9a9a9b905eb77738eff62"
    b = hexstr_to_bytes(hexs)
    print(hexstr(print_packet(b)))
    print(hexstr(b))
