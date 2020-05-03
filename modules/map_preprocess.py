"""
This module contains all classes related to preprocessing of point data to
be added to the occupancy map
"""
import numpy as np
from .async_message import AsyncMessageCallback

class MapPreprocess:
    """
    This class takes a localised point cloud and prepares it to
    be added to the global occupancy map
    """
    def __init__(self):
        pass

    def process_local_point_cloud(self, point_cloud, pose):
        """
        Process batches of local point clouds
        """

    def publish_data_set(self):
        """
        Passes data to Rabbit MQ
        """

    def _local_to_global(self, local_points, pose):
        """
        Convert local points to a global coordinate system
        """

    def _discretise_point_cloud(self):
        """
        Take continous point cloud and discritise to map grid
        """

    def _compress_point_cloud(self):
        """
        Take a discritised point cloud and compress to cummalative
        counts of unique points
        """

    def _batch_filter(self, point_cloud):
        """
        Final filtering stage before adding to the map
        """

class DepthMapAdapter(MapPreprocess):
    """
    Prepare D435 depth data for feeding into the occupancy map
    """
    def __init__(self):
        super().__init__()

        self.depth_min_range = 0.1
        self.depth_max_range = 10

        self.depth_message_queue = AsyncMessageCallback(queue_size=1)

        self._pose_data = None

    def depth_callback(self, data):
        """
        Recieve incoming depth data
        """
        if self._pose_data is None:
            return

        self.depth_message_queue.queue_message((data, self._pose_data))

    def pose_callback(self, data):
        """
        Recieve incoming pose data
        """
        self._pose_data = data

    def adapter_pipeline(self):
        """
        Run incoming data through all processing steps
        """
        msg = self.depth_message_queue.wait_for_message()

        if msg is None:
            return

        depth_data, pose_data = msg[1]

        depth_frame = self._pre_process(depth_data[1], depth_data[2])
        coord = self._deproject(depth_frame, depth_data[2])

        self.process_local_point_cloud(coord, pose_data[1])

    def _pre_process(self, depth_frame, intrin):
        """
        Any pre-processing before deprojection
        """
        depth_frame = self._scale_depth(depth_frame, intrin)
        depth_frame = self._range_limit(depth_frame)
        return depth_frame

    def _scale_depth(self, depth_frame, intrin):
        """
        Convert depth pixels into meter units
        """
        return depth_frame * intrin[0]

    def _range_limit(self, depth_frame):
        """
        Limit the maximum/minimum range of the depth camera
        """
        depth_frame[np.logical_or(depth_frame < self.depth_min_range,
                                  depth_frame > self.depth_max_range)] = np.nan
        return depth_frame

    def _deproject(self, depth_frame, intrin):
        """
        Deproject depth image to local cartesian coordinate system
        """
        frame_shape = depth_frame.shape
        x_deproject, y_deproject = self._init_deprojection_matrix(frame_shape, intrin)

        z_coord = depth_frame
        x_coord = np.multiply(depth_frame, x_deproject)
        y_coord = np.multiply(depth_frame, y_deproject)

        z_coord = np.reshape(z_coord, (-1))
        x_coord = np.reshape(x_coord, (-1))
        y_coord = np.reshape(y_coord, (-1))

        coord = np.column_stack((z_coord, x_coord, y_coord)) # Output as FRD coordinates
        return coord[~np.isnan(z_coord), :]

    def _init_deprojection_matrix(self, matrix_shape, intrin):
        """
        Initialise conversion matrix for converting the depth frame to a de-projected 3D
        coordinate system
        """
        matrix_height, matrix_width = matrix_shape

        x_deproject_row = (np.arange(matrix_width) - intrin[1]) / intrin[3]
        y_deproject_col = (np.arange(matrix_height) - intrin[2]) / intrin[4]

        x_deproject_matrix = np.tile(x_deproject_row, (matrix_height, 1))
        y_deproject_matrix = np.tile(y_deproject_col, (matrix_width, 1)).transpose()

        return x_deproject_matrix, y_deproject_matrix

if __name__ == "__main__":
    pass
