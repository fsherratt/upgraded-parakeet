from context import modules
from unittest import TestCase, mock

from modules import startup


class TestStartup(TestCase):
    def setUp(self):
        self.proc_name = "test"
        self.start_obj = startup.Startup(self.proc_name)

    def test_thread_creation(self):
        pass

    def test_thread_closure(self):
        pass

    def test_one(self):
        pass
