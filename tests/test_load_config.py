from context import modules
from unittest import TestCase

from typing import NamedTuple
from modules.load_config import from_file, conf_to_named_tuple


class TestLoadConfig(TestCase):
    def setUp(self):
        self.test_filename = "conf/test.yaml"
        self.test_invalid_filename = "conf/not_a_file.yaml"

        self.test_value = 10

    def tearDown(self):
        pass

    def test_load_file(self):
        conf = from_file(self.test_filename)
        self.assertIsNotNone(conf)

    def test_cli_input(self):
        import sys

        sys.argv = [__name__, "test={}".format(self.test_value)]  # Mock CLI inpuut
        conf = from_file()

        self.assertEqual(conf.test, self.test_value)

    def test_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            from_file(self.test_invalid_filename)

    def test_source_merge(self):
        import sys

        sys.argv = [__name__, "test={}".format(self.test_value)]  # Mock CLI inpuut

        conf = from_file(self.test_filename)

        self.assertEqual(conf.test, self.test_value)


class TestNamedTuple(NamedTuple):
    var_1: str


class TestConfToNameTuple(TestCase):
    def test(self):
        TestConfig = {"var_1": "test"}
        rtn = conf_to_named_tuple(TestNamedTuple, TestConfig)

        self.assertEqual(rtn.var_1, TestConfig["var_1"])
