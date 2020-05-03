from context import modules
from unittest import TestCase, mock

from modules.async_message import AsyncMessageCallback 

class TestLoadConfig(TestCase):
    def setUp(self):
        self.message_obj = AsyncMessageCallback()
    
    @mock.patch('time.time')
    @mock.patch('queue.Queue.put_nowait')
    def test_queing_of_messages(self, mock_fcn, mock_time):
        message_test_data = 'Data'
        time_return = 2
        mock_time.return_value = time_return

        self.message_obj.queue_message(message_test_data)

        mock_fcn.assert_called_with((time_return, message_test_data))

        # Check event is set
        self.assertTrue(self.message_obj._new_message_event.is_set())

    def test_queue_size(self):
        self.message_obj._message_queue.maxsize = 1

        self.message_obj.queue_message('')
        self.message_obj._clear_message_event()

        # This message should be silently dropped
        self.message_obj.queue_message('')

        # Check event is not set
        self.assertFalse(self.message_obj._new_message_event.is_set())

        # Check queue only contains 1 item
        self.assertEqual(self.message_obj._message_queue.qsize(), 1)

    @mock.patch('time.time')
    def test_wait_for_message(self, mock_time):
        message_test_data = 'Test'

        time_return = 2
        mock_time.return_value = time_return

        self.message_obj._wait_timeout = 0

        # Test retrieve message
        self.message_obj.queue_message(message_test_data)
        data = self.message_obj.wait_for_message()

        self.assertEqual(data, (time_return, message_test_data))
    
        # Test retrieve no message - timeout = 0
        data = self.message_obj.wait_for_message()
        self.assertIsNone(data)

        # Check it clears the event when queue is empty
        self.assertFalse(self.message_obj._new_message_event.is_set())

    def test_unblock(self):
        self.message_obj.unblock_wait()
        self.assertTrue(self.message_obj._new_message_event.is_set())
