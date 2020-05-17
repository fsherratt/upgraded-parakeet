from unittest import TestCase, mock

import numpy as np
from scipy.spatial.transform import Rotation as R

from context import modules
from modules import data_types
from modules.map_preprocess import DepthMapAdapter, MapPreprocess


class TestMapPreprocess(TestCase):
    def setUp(self):
        self.map_pre = MapPreprocess()

    def test_local_to_global(self):
        test_local_point = [1, 0, 0]
        test_translation = [1, 0, 0]
        test_rotation = R.from_euler('zyx', [90, 0, 0], degrees=True).as_quat()

        test_pose = data_types.Pose(timestamp=1,
                                    translation=[0, 0, 0],
                                    quaternion=[0, 0, 0, 1],
                                    conf=3)

        # Test translation no rotation
        test_pose.translation[:] = [1, 0, 0]
        rtn = self.map_pre._local_to_global(test_local_point, test_pose)
        np.testing.assert_almost_equal(rtn, [2, 0, 0])

        # Test roatation no translation
        test_pose.translation[:] = [0, 0, 0]
        test_pose.quaternion[:] = test_rotation
        rtn = self.map_pre._local_to_global(test_local_point, test_pose)
        np.testing.assert_almost_equal(rtn, [0, 1, 0])

        # Test both
        test_pose.translation[:] = test_translation
        rtn = self.map_pre._local_to_global(test_local_point, test_pose)
        np.testing.assert_almost_equal(rtn, [1, 1, 0])

    def test_discritise_point_cloud(self):
        map_shape = self.map_pre.map_definition
        test_coord = np.asarray([[map_shape.x_min, map_shape.y_min, map_shape.z_min],
                                 [map_shape.x_max, map_shape.y_max, map_shape.z_max]])

        return_coord = np.asarray([[0, 0, 0],
                                   [map_shape.x_divisions - 1,
                                    map_shape.y_divisions - 1,
                                    map_shape.z_divisions - 1]])

        self.map_pre.conf.depth_preprocess.enable_compression = False
        rtn, count = self.map_pre._discretise_point_cloud(test_coord)

        np.testing.assert_equal(return_coord, rtn)
        np.testing.assert_equal(count, [1, 1])
        self.assertEqual(rtn.shape, (2, 3)) # Should be a shape of Nx3

        self.map_pre.conf.depth_preprocess.enable_compression = True
        rtn, count = self.map_pre._discretise_point_cloud(test_coord)

        np.testing.assert_equal(return_coord, rtn)
        np.testing.assert_equal(count, [1, 1])
        self.assertEqual(rtn.shape, (2, 3)) # Should be a shape of Nx3

    def test_compress_point_cloud(self):
        test_set = np.asarray([[0, 0, 0], [0, 0, 0], [1, 0, 0]])
        test_result = np.asarray([[0, 0, 0], [1, 0, 0]])
        test_count = [2, 1]

        rtn_set, rtn_cnt = self.map_pre._compress_point_cloud(test_set)

        np.testing.assert_equal(test_result, rtn_set)
        np.testing.assert_equal(test_count, rtn_cnt)


class TestDepthAdapter(TestCase):
    def setUp(self):
        self.map_pre = DepthMapAdapter()

    def test_scale_result(self):
        """
        Test depth scale function
        """
        scale = 10
        rtn = self.map_pre._scale_depth_frame(1, scale)

        self.assertEqual(rtn, scale)

    @mock.patch('modules.map_preprocess.DepthMapAdapter._initialise_deprojection_matrix')
    def test_deprojection_result(self, mock_init_deproject):
        """
        Test depth frame deprojection application function
        """
        mock_init_deproject.return_value = (2, 3)

        frame = np.asarray([1])

        rtn = self.map_pre._deproject_frame(frame, None)

        self.assertEqual(rtn[0][0], 1)
        self.assertEqual(rtn[0][1], 2)
        self.assertEqual(rtn[0][2], 3)

    @mock.patch('modules.map_preprocess.DepthMapAdapter._scale_depth_frame')
    @mock.patch('modules.map_preprocess.DepthMapAdapter._limit_depth_range')
    @mock.patch('modules.map_preprocess.DepthMapAdapter._downscale_data')
    def test_process_depth_frame(self, mock_downscale, mock_limit, mock_scale):
        """
        Test process depth frame calls required methods - Probably a stupid test
        """
        mock_downscale.side_effect = lambda x: x

        intrin = data_types.Intrinsics(scale=0, ppx=0, ppy=0, fx=0, fy=0)
        self.map_pre._pre_process(1, intrin)

        mock_limit.assert_called()
        mock_scale.assert_called()

    def test_deprojection_matrix(self):
        """
        Check deprojection matrix is initialised correctly
        """
        frame_shape = (480, 640)
        self.map_pre.conf.depth_preprocess.downscale_block_size = [1, 1]

        # Scale, PPx, PPy, Fx, Fy
        intrin = data_types.Intrinsics(scale=0, ppx=319.5, ppy=239.5, fx=2, fy=2)

        matrices = self.map_pre._initialise_deprojection_matrix(frame_shape, intrin)
        x_deproject_matrix, y_deproject_matrix = matrices

        # Check it is initialised in the correct shape
        self.assertEqual(x_deproject_matrix.shape, frame_shape)
        self.assertEqual(y_deproject_matrix.shape, frame_shape)

        # Check maths (x - ppx)/fx & (y - ppy)/fy
        cell_x = x_deproject_matrix[0][0]
        cell_y = y_deproject_matrix[0][0]
        self.assertEqual(cell_x, -159.75)
        self.assertEqual(cell_y, -119.75)

        # Check maths (x - ppx)/fx & (y - ppy)/fy
        cell_x = x_deproject_matrix[479][639]
        cell_y = y_deproject_matrix[479][639]
        self.assertEqual(cell_x, 159.75)
        self.assertEqual(cell_y, 119.75)

    def test_depth_range_limit(self):
        """
        Check depth frame data is filtered correctly to within specified range
        """
        self.map_pre.conf.depth_preprocess.min_range = 5
        self.map_pre.conf.depth_preprocess.max_range = 10

        low_value = 4
        mid_value = 7
        high_value = 11

        test_array = np.asarray([low_value, mid_value, high_value], dtype=np.float32)
        rtn = self.map_pre._limit_depth_range(test_array)

        self.assertTrue(np.isnan(rtn[0]))
        self.assertEqual(rtn[1], test_array[1])
        self.assertTrue(np.isnan(rtn[2]))

    def test_downscale_data(self):
        test_block_size = (2, 2)
        test_data_frame = np.asarray([[0, 1], [0, 1]])

        self.map_pre.conf.depth_preprocess.downscale_block_size = test_block_size

        self.map_pre.conf.depth_preprocess.downscale_method = 'mean'
        rtn_data = self.map_pre._downscale_data(test_data_frame)
        self.assertEqual(rtn_data, 0.5)

        self.map_pre.conf.depth_preprocess.downscale_method = 'min_pool'
        rtn_data = self.map_pre._downscale_data(test_data_frame)
        self.assertEqual(rtn_data, 0)

        self.map_pre.conf.depth_preprocess.downscale_method = 'max_pool'
        rtn_data = self.map_pre._downscale_data(test_data_frame)
        self.assertEqual(rtn_data, 1)
