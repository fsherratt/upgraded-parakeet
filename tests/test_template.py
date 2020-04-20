from context import modules
import unittest

from modules import test

class TestTemplate(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def test_example_assert(self):
        self.assertEqual(test.testFunc(), 10)
