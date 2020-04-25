from context import modules
from unittest import TestCase, mock
import numpy as np
from modules import realsense_t265

class TestTemplate(TestCase):
    def setUp(self):
        self.t265 = realsense_t265.rs_t265()
    
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
    @mock.patch('modules.realsense_t265.rs_t265._exception_handle')
    @mock.patch('pyrealsense2.pipeline.stop')
    @mock.patch('pyrealsense2.pipeline.start')
    def test_start_stop_connection(self, mock_start, mock_stop, mock_exception):
        import pyrealsense2 as rs
        self.t265._pipe = rs.pipeline()

        # 1. Check a connection is attempted and closed
        with self.t265:
            pass
        mock_start.assert_called()
        mock_stop.assert_called()

        # 2. Check exception are handled when using with 
        try:
            with self.t265:
                self.t265.not_a_function()
        except:
            pass
        mock_exception.assert_called()
        mock_exception.reset_mock()

        # 3. Check start timeout exception handling
        mock_start.side_effect = TimeoutError()
        with self.assertRaises(TimeoutError):
            self.t265.open_connection()

        mock_exception.assert_called()

    """
    Check get frame order of operation and exception handling
    """
    @mock.patch('time.time')
    @mock.patch('modules.realsense_t265.rs_t265._exception_handle')
    @mock.patch('pyrealsense2.pipeline.wait_for_frames')
    @mock.patch('pyrealsense2.composite_frame.get_pose_frame')
    @mock.patch('pyrealsense2.pose_frame.get_pose_data')
    @mock.patch('modules.realsense_t265.rs_t265._convert_rotational_frame')
    @mock.patch('modules.realsense_t265.rs_t265._convert_positional_frame')
    def test_get_frames(self, mock_pos_transform, mock_rot_transform, 
                        mock_pose, mock_frame, mock_wait, mock_exception, mock_time):
        # Setup mock enviroment
        import pyrealsense2 as rs

        mock_time.return_value = 12

        mock_pose_data = mock.PropertyMock()
        type(mock_pose_data.translation).x = mock.PropertyMock(return_value=1)
        type(mock_pose_data.translation).y = mock.PropertyMock(return_value=2)
        type(mock_pose_data.translation).z = mock.PropertyMock(return_value=3)
        type(mock_pose_data.rotation).x = mock.PropertyMock(return_value=0)
        type(mock_pose_data.rotation).y = mock.PropertyMock(return_value=0)
        type(mock_pose_data.rotation).z = mock.PropertyMock(return_value=0)
        type(mock_pose_data.rotation).w = mock.PropertyMock(return_value=1)
        type(mock_pose_data).tracker_confidence = mock.PropertyMock(return_value=3)
        mock_pose.return_value = mock_pose_data

        # Apply no transforms to the data
        mock_pos_transform.side_effect = (lambda x: x) 
        mock_rot_transform.side_effect = (lambda x: x) 
        
        mock_wait.return_value = rs.composite_frame
        mock_frame.return_value = rs.pose_frame

        self.t265._pipe = rs.pipeline()

        # Test full order of operations
        rtn_value = self.t265.get_frame()

        self.assertEqual(rtn_value[0],  12)
        self.assertListEqual(rtn_value[1], [1,2,3])
        self.assertListEqual(rtn_value[2], [0,0,0,1])
        self.assertEqual(rtn_value[3], 3)

        mock_pos_transform.assert_called()
        mock_rot_transform.assert_called()
        
        # Test empty data frame exception handling
        mock_pose.side_effect = AttributeError()
        rtn_value = self.t265.get_frame()
        
        mock_exception.assert_called()
        self.assertIsNone(rtn_value)

        # Test get frame timeout exception handling
        mock_exception.reset_mock()
        mock_wait.side_effect = TimeoutError()
        with self.assertRaises(TimeoutError):
            self.t265.get_frame()
        mock_exception.assert_called()

    """
    Apply a set of know rotations to check transormation maths
    """
    def test_convert_coordinate_frame(self):
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
        self.t265.North_offset = north_offset
        self.t265.tilt_deg = cam_tilt

        self.t265._initialise_rotational_transforms()

        t265_quat = R.from_euler('xyz', t265_eul, degrees=True).as_quat()

        rtn_pos = self.t265._convert_positional_frame(t265_pos)
        rtn_quat = self.t265._convert_rotational_frame(t265_quat)

        rtn_eul = R.from_quat(rtn_quat).as_euler('xyz', degrees=True)

        return list(rtn_eul), list(rtn_pos)
