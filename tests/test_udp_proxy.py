from context import modules
import unittest
import mock

from modules.udp_proxy import udp_proxy
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 5005

class TestTemplate( TestCase ):
    def setUp(self):
        self.udp_proxy = udp_proxy( DEFAULT_IP, DEFAULT_PORT )
    
    def tearDown(self):
        pass

    def test_bind(self):
        self.udp_proxy._bind_to_port()
