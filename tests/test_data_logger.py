from context import modules
from unittest import TestCase, mock

from modules.data_logger import LoggingInterface, FileLogger

class TestDataLogger(TestCase):
    def setUp(self):
        self.logObj = LoggingInterface()
    
    def tearDown(self):
        self.logObj.stop_logging_loop()

    @mock.patch('modules.data_logger.LoggingInterface._queue_message')
    def test_valid_message_callback_queued(self, mock_fcn):
        self.logObj.message_callback('Data')

        mock_fcn.assert_called()

    @mock.patch('modules.data_logger.LoggingInterface._queue_message')
    def test_arguments_sent_to_queue_message(self, mock_fcn):
        data = 'Data'
        time = 2
    
        with mock.patch('time.time', return_value=time):
            self.logObj.message_callback(data)

        mock_fcn.assert_called_with(time, data)

    @mock.patch('modules.data_logger.LoggingInterface._queue_message')
    def test_valid_message_event_set(self, mock_fcn):
        self.logObj.message_callback('Data')

        self.assertTrue(self.logObj._log_queue_event.is_set())

    @mock.patch('queue.Queue.put')
    def test_logging_queue_put(self, mock_fcn):
        data = 'Data'
        time = 2
    
        with mock.patch('time.time', return_value=time):
            self.logObj.message_callback(data)

        mock_fcn.assert_called_with((time, data))

    def test_thread_created(self):
        self.logObj.start_logging_loop()

        self.assertTrue(self.logObj._log_thread.is_alive())

    def test_thread_closed(self):
        self.logObj.start_logging_loop()
        self.logObj.stop_logging_loop()

        self.logObj._log_thread.join(timeout=2)

        self.assertFalse(self.logObj._log_thread.is_alive())
    
    @mock.patch('modules.data_logger.LoggingInterface._get_message', return_value=None)
    def test_loop_waits_for_message(self, mock_get):
        self.logObj.start_logging_loop()

        self.logObj._set_message_event()

        import time
        time.sleep(0.1)

        mock_get.assert_called()

    @mock.patch('modules.data_logger.LoggingInterface._clear_message_event')
    def test_event_cleared_on_empty_queue(self, mock_clear):

        self.logObj.start_logging_loop()
        self.logObj._set_message_event()

        import time
        time.sleep(0.1)

        mock_clear.assert_called()

    @mock.patch('modules.data_logger.LoggingInterface.save_to_file')
    def test_loop_stays_open_after_message(self, mock_save):
        self.logObj.start_logging_loop()
        self.logObj.message_callback('data')
        
        import time
        time.sleep(0.1)

        self.assertTrue(self.logObj._log_thread.is_alive())

    @mock.patch('modules.data_logger.LoggingInterface._get_message', return_value=None)
    @mock.patch('modules.data_logger.LoggingInterface.save_to_file')
    def test_empty_message_not_passed_to_save(self, mock_save, mock_get):
        self.logObj.start_logging_loop()
        
        self.logObj.message_callback('data')
        import time
        time.sleep(0.1)

        mock_save.assert_not_called()
    
    @mock.patch('modules.data_logger.LoggingInterface.save_to_file')
    def test_message_passed_to_save(self, mock_save):
        self.logObj.start_logging_loop()
        self.logObj.message_callback('data')

        import time
        time.sleep(0.1)

        mock_save.assert_called()

class FileLog(TestCase):
    def setUp(self):
        self.logObj = FileLogger()
    
    def tearDown(self):
        self.logObj.stop_logging_loop()