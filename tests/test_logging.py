from context import modules
from unittest import TestCase, mock

from modules.data_logger import logging_interface

class TestTemplate(TestCase):
    def setUp(self):
        self.logObj = logging_interface()
    
    def tearDown(self):
        pass

    def test_filter_valid_verbosity(self):
        self.logObj.verbosity = self.logObj.DEBUG

        self.assertTrue( self.logObj.filter_incoming(self.logObj.VERBOSE))

    def test_filter_invalid_verbosity(self):
        self.logObj.verbosity = self.logObj.NOTICE

        self.assertFalse( self.logObj.filter_incoming(self.logObj.VERBOSE))

    @mock.patch('modules.data_logger.logging_interface.queue_message')
    def test_valid_message_callback_queued(self, mock_fcn):
        self.logObj.verbosity = self.logObj.DEBUG
        self.logObj.message_callback('Data', self.logObj.VERBOSE)

        mock_fcn.assert_called()

    @mock.patch('modules.data_logger.logging_interface.queue_message')
    def test_invalid_message_callback_queued(self, mock_fcn):
        self.logObj.verbosity = self.logObj.NOTICE
        self.logObj.message_callback('Data', self.logObj.VERBOSE)

        mock_fcn.assert_not_called()

    # @mock.patch('time.time')
    @mock.patch('modules.data_logger.logging_interface.queue_message')
    def test_arguments_sent_to_queue_message(self, mock_fcn):
        data = 'Data'
        time = 2
    
        self.logObj.verbosity = self.logObj.DEBUG

        import time
        with mock.patch('time.time', return_value=time):
            self.logObj.message_callback(data, self.logObj.VERBOSE)

        mock_fcn.assert_called_with(time, data)

    @mock.patch('modules.data_logger.logging_interface.queue_message')
    def test_valid_message_event_set(self, mock_fcn):
        self.logObj.verbosity = self.logObj.DEBUG
        self.logObj.message_callback('Data', self.logObj.VERBOSE)

        self.assertTrue(self.logObj._log_queue_event.is_set())

    @mock.patch('modules.data_logger.logging_interface.queue_message')
    def test_invalid_message_event_set(self, mock_fcn):
        self.logObj.verbosity = self.logObj.NOTICE
        self.logObj.message_callback('Data', self.logObj.VERBOSE)

        self.assertFalse(self.logObj._log_queue_event.is_set())

    # test that data is put into log queue correctly
    # test that logger thread is created succesfully
    # test that logger waits for event
    # test that logger clears event
    # test that logger runs until loop closed
    # test that threaded loops closes on loop stop
    # test that save_to_file is called after message is recieved
    # config file based setup


    