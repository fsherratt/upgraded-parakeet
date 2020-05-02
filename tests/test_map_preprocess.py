from context import modules
from unittest import TestCase, mock

from modules.map_preprocess import MapPreprocess, DepthMapAdapter

class TestMapPreprocess(TestCase):
    def setUp(self):
        self.map_pre = MapPreprocess()

    def tearDown(self):
        pass

    def test_1(self):
        pass

class TestDepthAdapter(TestCase):
    def setUp(self):
        self.map_pre = DepthMapAdapter()

    def tearDown(self):
        pass

    def test_1(self):
        pass