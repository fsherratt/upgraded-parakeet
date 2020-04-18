from context import modules
import unittest

from modules import realsense_t265

class TestTemplate(unittest.TestCase):
    def setUp(self):
        self.rs = realsense_t265.rs_t265()
    
    def tearDown(self):
        pass

    def test_import_success(self):
        self.assertTrue(True)
