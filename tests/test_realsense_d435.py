from context import modules
from unittest import TestCase, mock

from modules import realsense_d435

class TestTemplate(TestCase):
    def setUp(self):
        self.d435 = realsense_d435.rs_d435()
    
    def tearDown(self):
        pass

    def test_import_success(self):
        self.assertTrue(True)

    @mock.patch('pyrealsense2.pipeline.stop')
    @mock.patch('pyrealsense2.pipeline.start')
    @mock.patch('modules.realsense_d435.rs_d435._initialise_deprojection_matrix')
    def test_open_connection(self, _, mock_start, mock_stop):
        import pyrealsense2 as rs
        self.d435._pipe = rs.pipeline()

        with self.d435:
            pass
        mock_start.assert_called()
        mock_stop.assert_called()       

    @mock.patch('modules.realsense_d435.rs_d435._get_intrinsics')    
    def test_deprojection_matrix_shape(self, _):
        self.d435._intrin = mock.MagicMock()
        self.d435._intrin.ppx = 1
        self.d435._intrin.ppy =1
        self.d435._intrin.fx = 1
        self.d435._intrin.fy = 1

        self.d435._initialise_deprojection_matrix()

        self.assertEqual(self.d435._x_deproject_matrix.shape, (self.d435.depth_height, self.d435.depth_width))
        self.assertEqual(self.d435._y_deproject_matrix.shape, (self.d435.depth_height, self.d435.depth_width))       

    def test_depth_range_limit(self):
        import numpy as np
        low_value = self.d435.min_range - 1
        mid_value = self.d435.min_range + (self.d435.max_range - self.d435.min_range) / 2
        high_value = self.d435.max_range + 1

        test_array = np.asarray([low_value, mid_value, high_value], dtype=np.float32)
        rtn = self.d435._limit_depth_range(test_array)

        self.assertTrue(np.isnan(rtn[0]))
        self.assertEqual(rtn[1], test_array[1])
        self.assertTrue(np.isnan(rtn[2]))

    '''
    This is a stupid test...
    '''
    @mock.patch('pyrealsense2.pipeline.wait_for_frames')
    @mock.patch('modules.realsense_d435.rs_d435._process_depth_frame')
    def test_get_frames(self, mock_process, mock_wait):
        import pyrealsense2 as rs
        import numpy as np
        self.d435._pipe = rs.pipeline()

        mock_depth_data = 1
        mock_color_data = 1

        depth_mock = mock.MagicMock()
        depth_mock.get_data = mock.MagicMock(return_value=mock_depth_data)

        color_mock = mock.MagicMock()
        color_mock.get_data = mock.MagicMock(return_value=mock_color_data)

        frames_mock = mock.MagicMock()
        frames_mock.get_depth_frame = mock.MagicMock(return_value=depth_mock)
        frames_mock.get_color_frame = mock.MagicMock(return_value=color_mock)

        mock_wait.return_value = frames_mock
        mock_process.return_value = np.asarray(mock_depth_data, dtype=np.float32)

        rtn_value = self.d435.get_frame()

        mock_process.assert_called()
        self.assertEqual(rtn_value[1],  mock_depth_data)
        self.assertEqual(rtn_value[2], mock_color_data)

    def test_fov_return(self):
        self.d435._FOV = 9
        rtn = self.d435.get_fov()

        self.assertEqual(self.d435._FOV, rtn)

    def test_scale_result(self):
        self.d435._scale = 10
        rtn = self.d435._scale_depth_frame(1)

        self.assertEqual(rtn, self.d435._scale)

    def test_deprojection_result(self):
        import numpy as np
        self.d435._x_deproject_matrix = np.asarray([2])
        self.d435._y_deproject_matrix = np.asarray([3])

        frame = np.asarray([1])

        rtn = self.d435._deproject_frame(frame)

        self.assertEqual(rtn[0], 1)
        self.assertEqual(rtn[1], 2)
        self.assertEqual(rtn[2], 3)

    @mock.patch('modules.realsense_d435.rs_d435._scale_depth_frame')
    @mock.patch('modules.realsense_d435.rs_d435._limit_depth_range')
    @mock.patch('modules.realsense_d435.rs_d435._deproject_frame')
    def test_process_depth_frame(self, mock_deproject, mock_limit, mock_scale):
        self.d435._process_depth_frame(1)

        mock_deproject.assert_called()
        mock_limit.assert_called()
        mock_scale.assert_called()
