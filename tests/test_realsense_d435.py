from context import modules
from unittest import TestCase, mock

from modules.realsense import rs_pipeline, depth_pipeline, color_pipeline, pose_pipeline

class TestRSPipeline(TestCase):
    def setUp(self):
        self.pipeline = rs_pipeline()
    
    def tearDown(self):
        pass

    """
    Can mocked pipe connection be made and close succesfully
    Test elegant exception handling during each event
    """
    
    @mock.patch('modules.realsense.rs_pipeline._exception_handle')
    @mock.patch('pyrealsense2.pipeline.stop')
    @mock.patch('pyrealsense2.pipeline.start')
    @mock.patch('modules.realsense.rs_pipeline.generate_config')
    @mock.patch('modules.realsense.rs_pipeline.post_connect_process')
    def test_start_stop_connection(self, mock_post_connect, mock_cfg, mock_start, 
                                   mock_stop, mock_exception):
        import pyrealsense2 as rs
        self.pipeline._pipe = rs.pipeline()

        # 1. Check a connection is attempted and closed
        with self.pipeline:
            pass
        mock_start.assert_called()
        mock_stop.assert_called()
        mock_cfg.assert_called()
        mock_post_connect.assert_called()

        # 2. Check exception are handled when using with 
        try:
            with self.pipeline:
                self.pipeline.not_a_function()
        except:
            pass
        mock_exception.assert_called()
        mock_exception.reset_mock()

        # 3. Check start timeout exception handling
        mock_start.side_effect = RuntimeError()
        with self.assertRaises(RuntimeError):
            self.pipeline.open_connection()
        mock_exception.assert_called()
   
    """
    Check get frame order of operation and exception handling
    """
    
    @mock.patch('modules.realsense.rs_pipeline._exception_handle')
    @mock.patch('modules.realsense.rs_pipeline.post_process')
    @mock.patch('modules.realsense.rs_pipeline.get_data')
    @mock.patch('modules.realsense.rs_pipeline.get_frame')
    @mock.patch('pyrealsense2.pipeline.wait_for_frames')
    @mock.patch('time.time', return_value=1)
    def test_wait_for_frame(self, mock_time, mock_wait, mock_get_frame,  
                            mock_get_data, mock_post, mock_exception):
        # Setup mock enviroment
        import pyrealsense2 as rs
        self.pipeline._pipe = rs.pipeline()

        mock_get_frame_return = 'MOCK_FRAME'
        mock_get_data_return = 'MOCK_DATA'
        mock_post_return = 'MOCK_POST'
        mock_wait_return = 'MOCK_WAIT'
        mock_time_return = 12

        mock_wait.return_value = mock_wait_return
        mock_get_frame.return_value = mock_get_frame_return
        mock_get_data.return_value = mock_get_data_return
        mock_post.return_value = mock_post_return
        mock_time.return_value = mock_time_return

        # Test full order of operations
        rtn_value = self.pipeline.wait_for_frame()
        
        mock_wait.assert_called()
        mock_get_frame.assert_called_with(mock_wait_return)
        mock_get_data.assert_called_with(mock_get_frame_return)
        mock_post.assert_called_with(mock_get_data_return)

        self.assertEqual(rtn_value[0], mock_time_return)
        self.assertEqual(rtn_value[1],  mock_post_return)

        # Test empty data frame exception handling
        mock_get_data.side_effect = RuntimeError()
        rtn_value = self.pipeline.wait_for_frame()
        mock_exception.assert_called()
        self.assertIsNone(rtn_value)

        # Test get frame timeout exception handling
        mock_exception.reset_mock()
        mock_wait.side_effect = RuntimeError()
        with self.assertRaises(RuntimeError):
            self.pipeline.wait_for_frame()

        mock_exception.assert_called()
    
class TestDepthPipeline(TestCase):
    def setUp(self):
        self.pipeline = depth_pipeline()
    
    def tearDown(self):
        pass

    """
    Test FOV getter function
    """
    def test_fov_return(self):
        self.pipeline._FOV = 9
        rtn = self.pipeline.get_fov()

        self.assertEqual(self.pipeline._FOV, rtn)

    """
    Test depth scale function
    """
    def test_scale_result(self):
        self.pipeline._scale = 10
        rtn = self.pipeline._scale_depth_frame(1)

        self.assertEqual(rtn, self.pipeline._scale)

    """
    Test depth frame deprojection application function
    """
    def test_deprojection_result(self):
        import numpy as np
        self.pipeline._x_deproject_matrix = np.asarray([2])
        self.pipeline._y_deproject_matrix = np.asarray([3])

        frame = np.asarray([1])

        rtn = self.pipeline._deproject_frame(frame)

        self.assertEqual(rtn[0][0], 1)
        self.assertEqual(rtn[0][1], 2)
        self.assertEqual(rtn[0][2], 3)

    """
    Test process depth frame calls required methods - Probably a stupid test
    """
    @mock.patch('modules.realsense.depth_pipeline._scale_depth_frame')
    @mock.patch('modules.realsense.depth_pipeline._limit_depth_range')
    def test_process_depth_frame(self, mock_limit, mock_scale):
        self.pipeline._process_depth_frame(1)

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

        self.pipeline._pipe = rs.pipeline()
        self.pipeline._get_intrinsics()

        self.assertEqual(self.pipeline._intrin, rs.intrinsics)
        self.assertEqual(self.pipeline._scale, mock_scale_value)
        self.assertEqual(self.pipeline._FOV, mocK_fov_value)


    """ 
    Check deprojection matrix is initialised correctly
    """
    @mock.patch('modules.realsense.depth_pipeline._get_intrinsics')    
    def test_deprojection_matrix(self, _):
        self.pipeline.depth_width = 640
        self.pipeline.depth_height = 480

        self.pipeline._intrin = mock.MagicMock()
        self.pipeline._intrin.ppx = 319.5
        self.pipeline._intrin.ppy = 239.5
        self.pipeline._intrin.fx = 2
        self.pipeline._intrin.fy = 2

        self.pipeline._initialise_deprojection_matrix()

        # Check it is initialised in the correct shape
        self.assertEqual(self.pipeline._x_deproject_matrix.shape, 
                        (self.pipeline.depth_height, self.pipeline.depth_width))
        self.assertEqual(self.pipeline._y_deproject_matrix.shape, 
                        (self.pipeline.depth_height, self.pipeline.depth_width))

        # Check maths (x - ppx)/fx & (y - ppy)/fy
        cell_x = self.pipeline._x_deproject_matrix[0][0]
        cell_y = self.pipeline._y_deproject_matrix[0][0]
        self.assertEqual(cell_x, -159.75)
        self.assertEqual(cell_y, -119.75)

        # Check maths (x - ppx)/fx & (y - ppy)/fy
        cell_x = self.pipeline._x_deproject_matrix[479][639]
        cell_y = self.pipeline._y_deproject_matrix[479][639]
        self.assertEqual(cell_x, 159.75)
        self.assertEqual(cell_y, 119.75)

    """
    Check depth frame data is filtered correctly to within specified range
    """
    def test_depth_range_limit(self):
        import numpy as np
        self.pipeline.min_range = 5
        self.pipeline.max_range = 10
        
        low_value = 4
        mid_value = 7
        high_value = 11

        test_array = np.asarray([low_value, mid_value, high_value], dtype=np.float32)
        rtn = self.pipeline._limit_depth_range(test_array)

        self.assertTrue(np.isnan(rtn[0]))
        self.assertEqual(rtn[1], test_array[1])
        self.assertTrue(np.isnan(rtn[2]))

class TestColorPipeline(TestCase):
    def setUp(self):
        self.pipeline = color_pipeline()
    
    def tearDown(self):
        pass
    
    @mock.patch('pyrealsense2.composite_frame.get_color_frame')
    def test_get_frame(self, mock_get_color):
        import pyrealsense2 as rs
        self.pipeline.get_frame(rs.composite_frame)
        mock_get_color.assert_called()

class TestPosPipeline(TestCase):
    def setUp(self):
        self.pipeline = pose_pipeline()
    
    def tearDown(self):
        pass
    """
    Check get frame order of operation and exception handling
    """
    @mock.patch('modules.realsense.pose_pipeline._convert_rotational_frame')
    @mock.patch('modules.realsense.pose_pipeline._convert_positional_frame')
    def test_post_process(self, mock_pos_transform, mock_rot_transform):
        import pyrealsense2 as rs

        mock_tranlation_return =[1,2,3]
        mock_quat_return = [0,0,0,1]
        mock_conf_return = 3

        data = mock.PropertyMock()
        type(data.translation).x = mock.PropertyMock(return_value=mock_tranlation_return[0])
        type(data.translation).y = mock.PropertyMock(return_value=mock_tranlation_return[1])
        type(data.translation).z = mock.PropertyMock(return_value=mock_tranlation_return[2])
        type(data.rotation).x = mock.PropertyMock(return_value=mock_quat_return[0])
        type(data.rotation).y = mock.PropertyMock(return_value=mock_quat_return[1])
        type(data.rotation).z = mock.PropertyMock(return_value=mock_quat_return[2])
        type(data.rotation).w = mock.PropertyMock(return_value=mock_quat_return[3])
        type(data).tracker_confidence = mock.PropertyMock(return_value=mock_conf_return)

        # Apply no transforms to the data
        mock_pos_transform.side_effect = (lambda x: x) 
        mock_rot_transform.side_effect = (lambda x: x) 

        # Test full order of operations
        rtn_value = self.pipeline.post_process(data)

        self.assertListEqual(rtn_value[0], mock_tranlation_return)
        self.assertListEqual(rtn_value[1], mock_quat_return)
        self.assertEqual(rtn_value[2], mock_conf_return)

        mock_pos_transform.assert_called()
        mock_rot_transform.assert_called()

    """
    Apply a set of know rotations to check transormation maths
    """
    def test_convert_coordinate_frame(self):
        import numpy as np
        # For not rotation no difference
        rtn_eul, rtn_pos = self.run_transform_tests(t265_eul=[0,0,0], t265_pos=[2,3,1], 
                                 north_offset=0, cam_tilt=0)
        np.testing.assert_almost_equal(rtn_pos, [-1,2,-3])
        np.testing.assert_almost_equal(rtn_eul, [0,0,0])

        # 90 degrees in cam Y give -90 in aero Z
        rtn_eul, rtn_pos = self.run_transform_tests(t265_eul=[0,90,0], t265_pos=[0,0,0], 
                                 north_offset=0, cam_tilt=0)
        np.testing.assert_almost_equal(rtn_eul, [0,0,-90])
        np.testing.assert_almost_equal(rtn_pos, [0,0,0])

        # 90 degrees in cam Y give -90 in aero Z with 45 degree tilt
        # 1 meter in z gives 1 meter in x
        rtn_eul, rtn_pos = self.run_transform_tests(t265_eul=[-45,90,0], t265_pos=[0,0,1], 
                                 north_offset=0, cam_tilt=45)
        np.testing.assert_almost_equal(rtn_pos, [-1,0,0])
        np.testing.assert_almost_equal(rtn_eul, [0,0,-90])

        # 90 degrees in cam Y give -90 in aero Z with 45 degree tilt
        rtn_eul, rtn_pos = self.run_transform_tests(t265_eul=[-60,0,90], t265_pos=[0,0,1], 
                                 north_offset=0, cam_tilt=60)
        np.testing.assert_almost_equal(rtn_pos, [-1,0,0])
        np.testing.assert_almost_equal(rtn_eul, [-90,0,0])

        # Above with north offset - Expect to see the north offset added to the output
        rtn_eul, rtn_pos = self.run_transform_tests(t265_eul=[-60,0,90], t265_pos=[0,0,1], 
                                 north_offset=90, cam_tilt=60)
        np.testing.assert_almost_equal(rtn_pos, [0,-1,0])
        np.testing.assert_almost_equal(rtn_eul, [-90,0,90])

    """
    Helper function for `test_convert_coordinate_frame` test
    """
    def run_transform_tests(self, t265_eul, t265_pos, north_offset, cam_tilt, ):
        from scipy.spatial.transform import Rotation as R
        self.pipeline.North_offset = north_offset
        self.pipeline.tilt_deg = cam_tilt

        self.pipeline._initialise_rotational_transforms()

        t265_quat = R.from_euler('xyz', t265_eul, degrees=True).as_quat()

        rtn_pos = self.pipeline._convert_positional_frame(t265_pos)
        rtn_quat = self.pipeline._convert_rotational_frame(t265_quat)

        rtn_eul = R.from_quat(rtn_quat).as_euler('xyz', degrees=True)

        return list(rtn_eul), list(rtn_pos)