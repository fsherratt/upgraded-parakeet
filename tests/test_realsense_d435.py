from context import modules
from unittest import TestCase, mock

from modules import realsense_d435

class TestTemplate(TestCase):
    def setUp(self):
        self.d435 = realsense_d435.rs_d435()
    
    def tearDown(self):
        pass
    
    """
    Does the module import and initialise succesfully
    """
    def test_import_success(self):
        self.assertTrue(True)
    
    """
    Can mocked pipe connection be made and close succesfully
    Test elegant exception handling during each event
    """
    @mock.patch('modules.realsense_d435.rs_d435._exception_handle')
    @mock.patch('pyrealsense2.pipeline.stop')
    @mock.patch('pyrealsense2.pipeline.start')
    @mock.patch('modules.realsense_d435.rs_d435._initialise_deprojection_matrix')
    def test_start_stop_connection(self, _, mock_start, mock_stop, mock_exception):
        import pyrealsense2 as rs
        self.d435._pipe = rs.pipeline()

        # 1. Check a connection is attempted and closed
        with self.d435:
            pass
        mock_start.assert_called()
        mock_stop.assert_called()

        # 2. Check exception are handled when using with 
        try:
            with self.d435:
                self.d435.not_a_function()
        except:
            pass
        mock_exception.assert_called()
        mock_exception.reset_mock()

        # 3. Check start timeout exception handling
        mock_start.side_effect = TimeoutError()
        with self.assertRaises(TimeoutError):
            self.d435.open_connection()
        mock_exception.assert_called()
    
    """ 
    Check deprojection matrix is initialised correctly
    """
    @mock.patch('modules.realsense_d435.rs_d435._get_intrinsics')    
    def test_deprojection_matrix(self, _):
        self.d435.depth_width = 640
        self.d435.depth_height = 480

        self.d435._intrin = mock.MagicMock()
        self.d435._intrin.ppx = 319.5
        self.d435._intrin.ppy = 239.5
        self.d435._intrin.fx = 2
        self.d435._intrin.fy = 2

        self.d435._initialise_deprojection_matrix()

        # Check it is initialised in the correct shape
        self.assertEqual(self.d435._x_deproject_matrix.shape, 
                        (self.d435.depth_height, self.d435.depth_width))
        self.assertEqual(self.d435._y_deproject_matrix.shape, 
                        (self.d435.depth_height, self.d435.depth_width))

        # Check maths (x - ppx)/fx & (y - ppy)/fy
        cell_x = self.d435._x_deproject_matrix[0][0]
        cell_y = self.d435._y_deproject_matrix[0][0]
        self.assertEqual(cell_x, -159.75)
        self.assertEqual(cell_y, -119.75)

        # Check maths (x - ppx)/fx & (y - ppy)/fy
        cell_x = self.d435._x_deproject_matrix[479][639]
        cell_y = self.d435._y_deproject_matrix[479][639]
        self.assertEqual(cell_x, 159.75)
        self.assertEqual(cell_y, 119.75)

    """
    Check depth frame data is filtered correctly to within specified range
    """
    def test_depth_range_limit(self):
        import numpy as np
        self.d435.min_range = 5
        self.d435.max_range = 10
        
        low_value = 4
        mid_value = 7
        high_value = 11

        test_array = np.asarray([low_value, mid_value, high_value], dtype=np.float32)
        rtn = self.d435._limit_depth_range(test_array)

        self.assertTrue(np.isnan(rtn[0]))
        self.assertEqual(rtn[1], test_array[1])
        self.assertTrue(np.isnan(rtn[2]))

    """
    Check get frame order of operation and exception handling
    """
    @mock.patch('time.time')
    @mock.patch('modules.realsense_d435.rs_d435._exception_handle')
    @mock.patch('pyrealsense2.pipeline.wait_for_frames')
    @mock.patch('pyrealsense2.composite_frame.get_depth_frame')
    @mock.patch('pyrealsense2.composite_frame.get_color_frame')
    @mock.patch('pyrealsense2.depth_frame.get_data')
    @mock.patch('pyrealsense2.video_frame.get_data')
    @mock.patch('modules.realsense_d435.rs_d435._process_depth_frame')
    @mock.patch('modules.realsense_d435.rs_d435._deproject_frame')
    def test_get_frames(self, mock_deproject, mock_process, mock_color_data,
                        mock_depth_data, mock_get_color, mock_get_depth, mock_wait, 
                        mock_exception, mock_time):
        # Setup mock enviroment
        import pyrealsense2 as rs
        import numpy as np

        mock_time.return_value = 12

        mock_wait.return_value = rs.composite_frame
        mock_get_depth.return_value = rs.depth_frame
        mock_get_color.return_value = rs.video_frame
        mock_color_data.return_value = 2
        mock_depth_data.return_value = 1
        # Apply no transforms to the data
        mock_process.side_effect = (lambda x: x)
        mock_deproject.side_effect = (lambda x: 3)  
        
        self.d435._pipe = rs.pipeline()

        # Test full order of operations
        rtn_value = self.d435.get_frame()
        
        mock_process.assert_called()
        mock_deproject.assert_called()

        self.assertEqual(rtn_value[0], 12)
        self.assertEqual(rtn_value[1],  3)
        self.assertEqual(rtn_value[2],  1)
        self.assertEqual(rtn_value[3], 2)

        # Test empty data frame exception handling
        mock_color_data.side_effect = AttributeError()
        rtn_value = self.d435.get_frame()
        
        mock_exception.assert_called()
        self.assertIsNone(rtn_value)

        # Test get frame timeout exception handling
        mock_exception.reset_mock()
        mock_wait.side_effect = TimeoutError()
        with self.assertRaises(TimeoutError):
            self.d435.get_frame()

        mock_exception.assert_called()
    
    """
    Test FOV getter function
    """
    def test_fov_return(self):
        self.d435._FOV = 9
        rtn = self.d435.get_fov()

        self.assertEqual(self.d435._FOV, rtn)

    """
    Test depth scale function
    """
    def test_scale_result(self):
        self.d435._scale = 10
        rtn = self.d435._scale_depth_frame(1)

        self.assertEqual(rtn, self.d435._scale)

    """
    Test depth frame deprojection application function
    """
    def test_deprojection_result(self):
        import numpy as np
        self.d435._x_deproject_matrix = np.asarray([2])
        self.d435._y_deproject_matrix = np.asarray([3])

        frame = np.asarray([1])

        rtn = self.d435._deproject_frame(frame)

        self.assertEqual(rtn[0][0], 1)
        self.assertEqual(rtn[0][1], 2)
        self.assertEqual(rtn[0][2], 3)

    """
    Test process depth frame calls required methods - Probably a stupid test
    """
    @mock.patch('modules.realsense_d435.rs_d435._scale_depth_frame')
    @mock.patch('modules.realsense_d435.rs_d435._limit_depth_range')
    def test_process_depth_frame(self, mock_limit, mock_scale):
        self.d435._process_depth_frame(1)

        mock_limit.assert_called()
        mock_scale.assert_called()

    """
    Test get intrinsics order of operations
    """
    @mock.patch('pyrealsense2.pipeline.get_active_profile')
    @mock.patch('pyrealsense2.pipeline_profile.get_stream')
    @mock.patch('pyrealsense2.stream_profile.as_video_stream_profile')
    @mock.patch('pyrealsense2.video_stream_profile.get_intrinsics')
    @mock.patch('pyrealsense2.pipeline_profile.get_device')
    @mock.patch('pyrealsense2.device.first_depth_sensor')
    @mock.patch('pyrealsense2.depth_sensor.get_depth_scale')
    @mock.patch('pyrealsense2.rs2_fov')
    def test_get_intrinsics(self, mock_fov, mock_depth_scale, mock_first_sensor, 
                            mock_get_device, mock_get_intrinsics,  
                            mock_video_stream_profile, mock_get_stream, mock_get_profile):
        import pyrealsense2 as rs

        mock_scale_value = 0.001
        mocK_fov_value = [0,0]

        mock_get_profile.return_value = rs.pipeline_profile

        mock_get_stream.return_value = rs.stream_profile
        mock_video_stream_profile.return_value = rs.video_stream_profile
        mock_get_intrinsics.return_value = rs.intrinsics

        mock_get_device.return_value = rs.device
        mock_first_sensor.return_value = rs.depth_sensor
        mock_depth_scale.return_value = mock_scale_value

        mock_fov.return_value = mocK_fov_value

        self.d435._pipe = rs.pipeline()
        self.d435._get_intrinsics()

        self.assertEqual(self.d435._intrin, rs.intrinsics)
        self.assertEqual(self.d435._scale, mock_scale_value)
        self.assertEqual(self.d435._FOV, mocK_fov_value)
