from context import modules
from unittest import TestCase, mock

from modules.data_logger import logging_interface

class TestTemplate(TestCase):
    def setUp(self):
        self.logObj = logging_interface()
        self.logObj.verbosity = self.logObj.NOTICE
    
    def tearDown(self):
        self.logObj.stop_logging_loop()

    def test_filter_valid_verbosity(self):
        self.assertTrue( self.logObj._filter_incoming(self.logObj.WARNING))

    def test_filter_invalid_verbosity(self):
        self.assertFalse( self.logObj._filter_incoming(self.logObj.VERBOSE))

    @mock.patch('modules.data_logger.logging_interface._queue_message')
    def test_valid_message_callback_queued(self, mock_fcn):
        self.logObj.message_callback('Data', self.logObj.WARNING)

        mock_fcn.assert_called()

    @mock.patch('modules.data_logger.logging_interface._queue_message')
    def test_invalid_message_callback_queued(self, mock_fcn):
        self.logObj.message_callback('Data', self.logObj.VERBOSE)

        mock_fcn.assert_not_called()

    @mock.patch('modules.data_logger.logging_interface._queue_message')
    def test_arguments_sent_to_queue_message(self, mock_fcn):
        data = 'Data'
        time = 2
    
        with mock.patch('time.time', return_value=time):
            self.logObj.message_callback(data, self.logObj.WARNING)

        mock_fcn.assert_called_with(time, data)

    @mock.patch('modules.data_logger.logging_interface._queue_message')
    def test_valid_message_event_set(self, mock_fcn):
        self.logObj.message_callback('Data', self.logObj.WARNING)

        self.assertTrue(self.logObj._log_queue_event.is_set())

    @mock.patch('modules.data_logger.logging_interface._queue_message')
    def test_invalid_message_event_set(self, mock_fcn):
        self.logObj.message_callback('Data', self.logObj.VERBOSE)

        self.assertFalse(self.logObj._log_queue_event.is_set())

    @mock.patch('queue.Queue.put')
    def test_logging_queue_put(self, mock_fcn):
        data = 'Data'
        time = 2
    
        with mock.patch('time.time', return_value=time):
            self.logObj.message_callback(data, self.logObj.WARNING)

        mock_fcn.assert_called_with((time, data))

    def test_thread_created(self):
        self.logObj.start_logging_loop()

        self.assertTrue(self.logObj._log_thread.is_alive())

    def test_thread_closed(self):
        self.logObj.start_logging_loop()
        self.logObj.stop_logging_loop()

        self.logObj._log_thread.join(timeout=2)

        self.assertFalse(self.logObj._log_thread.is_alive())
    
    @mock.patch('modules.data_logger.logging_interface._get_message', return_value=None)
    def test_loop_waits_for_message(self, mock_get):
        self.logObj.start_logging_loop()

        self.logObj._set_message_event()

        import time
        time.sleep(0.1)

        mock_get.assert_called()

    @mock.patch('modules.data_logger.logging_interface._clear_message_event')
    def test_event_cleared_on_empty_queue(self, mock_clear):

        self.logObj.start_logging_loop()
        self.logObj._set_message_event()

        import time
        time.sleep(0.1)

        mock_clear.assert_called()

    @mock.patch('modules.data_logger.logging_interface._get_message', return_value=None)
    @mock.patch('modules.data_logger.logging_interface.save_to_file')
    def test_empty_message_not_passed_to_save(self, mock_save, mock_get):
        self.logObj.start_logging_loop()
        
        self.logObj.message_callback('data', self.logObj.WARNING)
        import time
        time.sleep(0.1)

        mock_save.assert_not_called()
    
    @mock.patch('modules.data_logger.logging_interface.save_to_file')
    def test_message_passed_to_save(self, mock_save):
        self.logObj.start_logging_loop()
        self.logObj.message_callback('data', self.logObj.WARNING)

        import time
        time.sleep(0.1)

        mock_save.assert_called()

    