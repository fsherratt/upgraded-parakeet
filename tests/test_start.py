import subprocess
from unittest import TestCase, mock

import start
from context import modules


class TestProcessManagement(TestCase):
    def setUp(self):
        self.test_process_list = [subprocess.Popen(args=["echo", "'test'"])]

    def test_parse_startup_cli(self):
        pass

    def test_launch_process(self):
        pass

    def test_launch_processes(self):
        pass

    @mock.patch("subprocess.Popen.poll")
    def test_is_process_alive(self, mock_poll):
        # Process is running
        mock_poll.return_value = None
        rtn = start.process_is_alive(self.test_process_list)

        self.assertListEqual(rtn, self.test_process_list)

        # Process exited with code 1
        mock_poll.return_value = 1
        rtn = start.process_is_alive(self.test_process_list)

        self.assertListEqual(rtn, [])

    @mock.patch("select.select")
    def test_monitor_std_error(self, mock_select):
        mock_stream = mock.MagicMock(spec=mock.file_spec)
        mock_stream.read.return_value = b"Test"

        # Test timeout
        mock_select.return_value = ([], [], [])
        start.monitor_stderr([])

        mock_select.return_value = ([mock_stream], [], [])
        start.monitor_stderr([])

        mock_stream.read.assert_called_once()

    @mock.patch("subprocess.Popen.terminate")
    def test_kill_processes(self, mock_terminate):
        start.kill_processes(self.test_process_list)

        mock_terminate.assert_called()
