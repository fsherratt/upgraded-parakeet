import numpy as np

class depth_post_process():
        """
    Initialise conversion matrix for converting the depth frame to a de-projected 3D 
    coordinate system
    """
    def _initialise_deprojection_matrix(self):
        self._get_intrinsics()
        
        x_deproject_row = (np.arange( self.depth_width ) - self._intrin.ppx) / self._intrin.fx
        y_deproject_col = (np.arange( self.depth_height ) - self._intrin.ppy) / self._intrin.fy

        self._x_deproject_matrix = np.tile( x_deproject_row, (self.depth_height, 1) )
        self._y_deproject_matrix = np.tile( y_deproject_col, (self.depth_width, 1) ).transpose()

    """
    Perform data pre-processing to depth frame
    """
    def _process_depth_frame(self, frame:np.array):
        frame = self._scale_depth_frame(frame)
        frame = self._limit_depth_range(frame)
        return frame

    """
    Scale the depth output to meteres
    """
    def _scale_depth_frame(self, frame:np.array):
        return frame * self._scale

    """
    Limit the maximum/minimum range of the depth camera
    """
    def _limit_depth_range(self, frame:np.array):
        frame[ np.logical_or(frame < self.min_range, frame > self.max_range) ] = np.nan
        return frame

    """
    Converts from depth frame to 3D local FED coordiate system
    """
    def _deproject_frame(self, frame:np.array) -> list:       
        Z = frame
        X = np.multiply( frame, self._x_deproject_matrix )
        Y = np.multiply( frame, self._y_deproject_matrix )

        Z = np.reshape(Z, (-1))
        X = np.reshape(X, (-1))
        Y = np.reshape(Y, (-1))

        return np.column_stack( (Z,X,Y) ) # Output as FRD coordinates

class test_depth_post_process():
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