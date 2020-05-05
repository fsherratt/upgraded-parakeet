from unittest import TestCase, mock
import pyrealsense2 as rs
import numpy as np
from scipy.spatial.transform import Rotation as R

from context import modules
from modules.realsense import RealsensePipeline, DepthPipeline, ColorPipeline, PosePipeline
from modules import data_types

class TestRSPipeline(TestCase):
    def setUp(self):
        self.pipeline = RealsensePipeline()

    def tearDown(self):
        pass

    @mock.patch('modules.realsense.RealsensePipeline._exception_handle')
    @mock.patch('pyrealsense2.pipeline.stop')
    @mock.patch('pyrealsense2.pipeline.start')
    @mock.patch('modules.realsense.RealsensePipeline._generate_config')
    @mock.patch('modules.realsense.RealsensePipeline._post_connect_process')
    def test_start_stop_connection(self, mock_post_connect, mock_cfg, mock_start,
                                   mock_stop, mock_exception):
        """
        Can mocked pipe connection be made and close succesfully
        Test elegant exception handling during each event
        """
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
        except AttributeError:
            pass

        mock_exception.assert_called()
        mock_exception.reset_mock()

        # 3. Check start timeout exception handling
        mock_start.side_effect = RuntimeError()
        with self.assertRaises(RuntimeError):
            self.pipeline.open_connection()
        mock_exception.assert_called()

    @mock.patch('modules.realsense.RealsensePipeline._exception_handle')
    @mock.patch('modules.realsense.RealsensePipeline._post_process')
    @mock.patch('modules.realsense.RealsensePipeline._get_data')
    @mock.patch('modules.realsense.RealsensePipeline._get_frame')
    @mock.patch('pyrealsense2.pipeline.wait_for_frames')
    def test_wait_for_frame(self, mock_wait, mock_get_frame,
                            mock_get_data, mock_post, mock_exception):
        """
        Check get frame order of operation and exception handling
        """
        # Setup mock enviroment
        self.pipeline._pipe = rs.pipeline()

        mock_get_frame_return = 'MOCK_FRAME'
        mock_get_data_return = 'MOCK_DATA'
        mock_post_return = 'MOCK_POST'
        mock_wait_return = 'MOCK_WAIT'

        mock_wait.return_value = mock_wait_return
        mock_get_frame.return_value = mock_get_frame_return
        mock_get_data.return_value = mock_get_data_return
        mock_post.return_value = mock_post_return

        # Test full order of operations
        rtn_value = self.pipeline.wait_for_frame()

        mock_wait.assert_called()
        mock_get_frame.assert_called_with(mock_wait_return)
        mock_get_data.assert_called_with(mock_get_frame_return)
        mock_post.assert_called_with(mock_get_data_return)

        self.assertEqual(rtn_value, mock_post_return)

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
        self.pipeline = DepthPipeline()

    def tearDown(self):
        pass

    @mock.patch('pyrealsense2.config.enable_stream')
    def test_stream_config(self, mock_config):
        """
        Test that a depth stream is requested
        """
        self.pipeline._generate_config()

        self.assertEqual(mock_config.call_args[0][0], rs.stream.depth)

    @mock.patch('time.time')
    def test_post_process(self, mock_time):
        """
        Check get frame order of operation and exception handling
        """
        mock_time_return = 12
        mock_intrin_return = data_types.Intrinsics(1, 2, 3, 4, 5)
        mock_data = 32

        mock_time.return_value = mock_time_return
        self.pipeline._intrin = mock_intrin_return
        mock_return = data_types.Depth(timestamp=mock_time_return,
                                       depth=mock_data,
                                       intrin=mock_intrin_return)

        # Test full order of operations
        rtn_value = self.pipeline._post_process(mock_data)
        self.assertEqual(rtn_value, mock_return)

    def test_fov_return(self):
        """
        Test FOV getter function
        """
        self.pipeline._fov = 9
        rtn = self.pipeline.get_fov()

        self.assertEqual(self.pipeline._fov, rtn)

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
        """
        Test get intrinsics order of operations
        """
        mock_scale_value = 0.001
        mock_fov_value = [0, 0]

        mock_intrin = data_types.Intrinsics(scale=mock_scale_value,
                                            ppx=0, ppy=0,
                                            fx=0, fy=0)

        mock_get_profile.return_value = rs.pipeline_profile

        mock_get_stream.return_value = rs.stream_profile
        mock_video_stream_profile.return_value = rs.video_stream_profile
        mock_get_intrinsics.return_value = mock_intrin

        mock_get_device.return_value = rs.device
        mock_first_sensor.return_value = rs.depth_sensor
        mock_depth_scale.return_value = mock_scale_value

        mock_fov.return_value = mock_fov_value

        self.pipeline._pipe = rs.pipeline()
        self.pipeline._get_intrinsics()

        self.assertEqual(self.pipeline._intrin, mock_intrin)
        self.assertEqual(self.pipeline._fov, mock_fov_value)

class TestColorPipeline(TestCase):
    def setUp(self):
        self.pipeline = ColorPipeline()

    def tearDown(self):
        pass

    @mock.patch('pyrealsense2.config.enable_stream')
    def test_stream_config(self, mock_config):
        """
        Test that a color stream is requested
        """
        self.pipeline._generate_config()

        self.assertEqual(mock_config.call_args[0][0], rs.stream.color)

    @mock.patch('pyrealsense2.composite_frame.get_color_frame')
    def test_get_frame(self, mock_get_color):
        """
        Test correct get frame is called
        """
        self.pipeline._get_frame(rs.composite_frame)
        mock_get_color.assert_called()

class TestPosPipeline(TestCase):
    def setUp(self):
        self.pipeline = PosePipeline()

    def tearDown(self):
        pass

    @mock.patch('pyrealsense2.config.enable_stream')
    def test_stream_config(self, mock_config):
        """
        Test that a pose stream is requested
        """
        self.pipeline._generate_config()

        self.assertEqual(mock_config.call_args[0][0], rs.stream.pose)

    @mock.patch('time.time')
    @mock.patch('modules.realsense.PosePipeline._convert_rotational_frame')
    @mock.patch('modules.realsense.PosePipeline._convert_positional_frame')
    def test_post_process(self, mock_pos_transform, mock_rot_transform, mock_time):
        """
        Check get frame order of operation and exception handling
        """
        mock_tranlation_return = [1, 2, 3]
        mock_quat_return = [0, 0, 0, 1]
        mock_conf_return = 3
        mock_time_return = 12

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

        mock_time.return_value = mock_time_return

        mock_pose_return = data_types.Pose(timestamp=mock_time_return,
                                           translation=mock_tranlation_return,
                                           quaternion=mock_quat_return,
                                           conf=mock_conf_return)

        # Test full order of operations
        rtn_value = self.pipeline._post_process(data)

        self.assertEqual(rtn_value, mock_pose_return)

        mock_pos_transform.assert_called()
        mock_rot_transform.assert_called()

    def test_convert_coordinate_frame(self):
        """
        Apply a set of know rotations to check transormation maths
        """
        # For not rotation no difference
        rtn_eul, rtn_pos = self.run_transform_tests(t265_eul=[0, 0, 0], t265_pos=[2, 3, 1],
                                                    north_offset=0, cam_tilt=0)
        np.testing.assert_almost_equal(rtn_pos, [-1, 2, -3])
        np.testing.assert_almost_equal(rtn_eul, [0, 0, 0])

        # 90 degrees in cam Y give -90 in aero Z
        rtn_eul, rtn_pos = self.run_transform_tests(t265_eul=[0, 90, 0], t265_pos=[0, 0, 0],
                                                    north_offset=0, cam_tilt=0)
        np.testing.assert_almost_equal(rtn_eul, [0, 0, -90])
        np.testing.assert_almost_equal(rtn_pos, [0, 0, 0])

        # 90 degrees in cam Y give -90 in aero Z with 45 degree tilt
        # 1 meter in z gives 1 meter in x
        rtn_eul, rtn_pos = self.run_transform_tests(t265_eul=[-45, 90, 0], t265_pos=[0, 0, 1],
                                                    north_offset=0, cam_tilt=45)
        np.testing.assert_almost_equal(rtn_pos, [-1, 0, 0])
        np.testing.assert_almost_equal(rtn_eul, [0, 0, -90])

        # 90 degrees in cam Y give -90 in aero Z with 45 degree tilt
        rtn_eul, rtn_pos = self.run_transform_tests(t265_eul=[-60, 0, 90], t265_pos=[0, 0, 1],
                                                    north_offset=0, cam_tilt=60)
        np.testing.assert_almost_equal(rtn_pos, [-1, 0, 0])
        np.testing.assert_almost_equal(rtn_eul, [-90, 0, 0])

        # Above with north offset - Expect to see the north offset added to the output
        rtn_eul, rtn_pos = self.run_transform_tests(t265_eul=[-60, 0, 90], t265_pos=[0, 0, 1],
                                                    north_offset=90, cam_tilt=60)
        np.testing.assert_almost_equal(rtn_pos, [0, -1, 0])
        np.testing.assert_almost_equal(rtn_eul, [-90, 0, 90])

    def run_transform_tests(self, t265_eul, t265_pos, north_offset, cam_tilt):
        """
        Helper function for `test_convert_coordinate_frame` test
        """
        self.pipeline.north_offset = north_offset
        self.pipeline.tilt_deg = cam_tilt

        self.pipeline._initialise_rotational_transforms()

        t265_quat = R.from_euler('xyz', t265_eul, degrees=True).as_quat()

        rtn_pos = self.pipeline._convert_positional_frame(t265_pos)
        rtn_quat = self.pipeline._convert_rotational_frame(t265_quat)

        rtn_eul = R.from_quat(rtn_quat).as_euler('xyz', degrees=True)

        return list(rtn_eul), list(rtn_pos)
