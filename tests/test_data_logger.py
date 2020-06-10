from context import modules
from unittest import TestCase, mock

from modules.data_logger import LoggingInterface, FileLogger

class TestDataLogger(TestCase):
    def setUp(self):
        self.logObj = LoggingInterface()

    def tearDown(self):
        self.logObj.stop_logging_loop()

    @mock.patch('modules.async_message.AsyncMessageCallback.queue_message')
    def test_logging_queue_put(self, mock_fcn):
        channel = None
        properties = None
        method = None
        data = 'Data'
        self.logObj.message_callback(channel, method, properties, data)
        mock_fcn.assert_called_with(data)

    def test_thread_created(self):
        self.logObj.start_logging_loop()

        self.assertTrue(self.logObj._log_thread.is_alive())

    def test_thread_closed(self):
        self.logObj.start_logging_loop()
        self.logObj.stop_logging_loop()

        self.logObj._log_thread.join(timeout=2)

        self.assertFalse(self.logObj._log_thread.is_alive())

    @mock.patch('modules.data_logger.LoggingInterface.save_to_file')
    def test_loop_stays_open_after_message(self, mock_save):
        self.logObj.start_logging_loop()
        self.logObj.message_callback(None, None, None, 'data')
        
        import time
        time.sleep(0.1)

        self.assertTrue(self.logObj._log_thread.is_alive())

    @mock.patch('modules.data_logger.LoggingInterface.save_to_file')
    def test_empty_message_not_passed_to_save(self, mock_save):
        self.logObj._wait_timeout = 0
        self.logObj.start_logging_loop()
        
        mock_save.assert_not_called()
        self.logObj.message_callback(None, None, None,'data')
        import time
        time.sleep(0.1)

        mock_save.assert_called()

class FileLog(TestCase):
    def setUp(self):
        self.logObj = FileLogger()
    
    def tearDown(self):
        self.logObj.stop_logging_loop()