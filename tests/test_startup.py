from context import modules
from unittest import TestCase, mock

from modules import startup

from threading import Thread


class TestStartup(TestCase):
    def setUp(self):
        self.proc_name = "test"
        self.start_obj = startup.Startup(self.proc_name)

    @mock.patch("modules.startup.Startup.health_loop")
    @mock.patch("modules.startup.Startup.module_startup")
    @mock.patch("threading.Thread")
    @mock.patch("threading.Thread.start")
    def test_run(self, mock_thread_start, mock_thread, mock_startup, mock_health_loop):
        mock_thread.return_value = Thread(target=lambda x: x)

        self.start_obj.run()

        mock_startup.assert_called()
        mock_health_loop.assert_called()
        mock_thread_start.assert_called()

        self.assertTrue(mock_thread.call_args[1]["target"] == self.start_obj._main_loop)

    def test_close_callback(self):
        self.start_obj.stop_callback()

        self.assertFalse(self.start_obj.module_running)
        self.assertTrue(self.start_obj.health_loop_delay_event.is_set())

    @mock.patch("threading.Thread")
    def test_thread_creation(self, mock_thread):
        """
        Check that created threads are detected
        """
        mock_thread.name = mock.PropertyMock(return_value="test")

        self.start_obj.active_threads = []
        new_threads = [mock_thread]

        rtn = self.start_obj._log_thread_started(new_threads)
        self.assertListEqual(list(rtn), new_threads)

    @mock.patch("threading.Thread")
    def test_thread_closure(self, mock_thread):
        """
        Check that destroyed threads are detected
        """
        mock_thread.name = mock.PropertyMock(return_value="test")

        self.start_obj.active_threads = [mock_thread]
        new_threads = []

        rtn = self.start_obj._log_thread_closure(new_threads)
        self.assertListEqual(list(rtn), self.start_obj.active_threads)
