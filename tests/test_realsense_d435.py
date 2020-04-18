from context import modules
import unittest

from modules import realsense_d435

class TestTemplate(unittest.TestCase):
    def setUp(self):
        self.rs = realsense_d435.rs_d435()
    
    def tearDown(self):
        pass

    def test_import_success(self):
        self.assertTrue(True)
