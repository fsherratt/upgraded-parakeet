from context import modules
from unittest import TestCase, mock

from modules.map_preprocess import MapPreprocess, DepthMapAdapter

class TestMapPreprocess(TestCase):
    def setUp(self):
        self.map_pre = MapPreprocess()

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
        import numpy as np
        mock_init_deproject.return_value = (2, 3)

        frame = np.asarray([1])

        rtn = self.map_pre._deproject_frame(frame, None)

        self.assertEqual(rtn[0][0], 1)
        self.assertEqual(rtn[0][1], 2)
        self.assertEqual(rtn[0][2], 3)

    @mock.patch('modules.map_preprocess.DepthMapAdapter._scale_depth_frame')
    @mock.patch('modules.map_preprocess.DepthMapAdapter._limit_depth_range')
    def test_process_depth_frame(self, mock_limit, mock_scale):
        """
        Test process depth frame calls required methods - Probably a stupid test
        """
        self.map_pre._pre_process(1, [0,1])

        mock_limit.assert_called()
        mock_scale.assert_called()

    def test_deprojection_matrix(self):
        """ 
        Check deprojection matrix is initialised correctly
        """
        frame_shape = (480, 640)

        # Scale, PPx, PPy, Fx, Fy
        intrin = [0, 319.5, 239.5, 2, 2]

        matricies = self.map_pre._initialise_deprojection_matrix(frame_shape, intrin)
        x_deproject_matrix, y_deproject_matrix = matricies

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
        import numpy as np
        self.map_pre.depth_min_range = 5
        self.map_pre.depth_max_range = 10
        
        low_value = 4
        mid_value = 7
        high_value = 11

        test_array = np.asarray([low_value, mid_value, high_value], dtype=np.float32)
        rtn = self.map_pre._limit_depth_range(test_array)

        self.assertTrue(np.isnan(rtn[0]))
        self.assertEqual(rtn[1], test_array[1])
        self.assertTrue(np.isnan(rtn[2]))
