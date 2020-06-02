import subprocess
from unittest import TestCase, mock

import start  # pylint: disable=import-error
from modules import data_types  # pylint: disable=import-error


class TestProcessManagement(TestCase):
    def setUp(self):
        self.test_process_list = [subprocess.Popen(args=["echo", "'test'"])]

    @mock.patch("subprocess.Popen")
    def test_launch_process(self, mock_popen):
        mock_popen.side_effect = lambda args, stderr, start_new_session: args

        start.launch_list = {"test_tag": ["a", "b", "c"]}

        test_launch_item = data_types.StartupItem(
            module="test_tag",
            config_file="config_file",
            process_tag="test_tag",
            debug=True,
        )

        rtn = start.launch_process(test_launch_item)

        self.assertListEqual(rtn[0:2], ["python3", "-m"])

        mock_popen.assert_called()

    @mock.patch("start.launch_process")
    def test_launch_processes(self, mock_launch):
        mock_launch.return_value = subprocess.Popen(args=["echo", "'test'"])

        test_process_list = [
            data_types.StartupItem(
                module="test_tag", config_file="", process_tag="", debug=True
            ),
            data_types.StartupItem(
                module="test_tag_2", config_file="", process_tag="", debug=True
            ),
        ]

        rtn = start.launch_processes(test_process_list)

        self.assertIsInstance(rtn[0], subprocess.Popen)
        self.assertEqual(len(rtn), 2)

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
