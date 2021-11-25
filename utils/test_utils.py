import unittest


def assert_attr_equal(self: unittest.TestCase, obj1: object, obj2: object):
    self.assertEqual(type(obj1), type(obj2))
    attrs = filter(lambda x: (not str(x).startswith("__")), vars(obj1))
    for att in attrs:
        self.assertEqual(obj1.__getattribute__(att), obj2.__getattribute__(att))
