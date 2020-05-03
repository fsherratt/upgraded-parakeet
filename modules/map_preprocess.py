"""
This module contains all classes related to preprocessing of point data to
be added to the occupancy map
"""
import numpy as np
from .async_message import AsyncMessageCallback
from scipy.spatial.transform import Rotation as R

class MapPreprocess:
    """
    This class takes a localised point cloud and prepares it to
    be added to the global occupancy map
    """
    def __init__(self):
        self.xRange = [-10, 10]
        self.yRange = [-10, 10]
        self.zRange = [-2, 5]

        self.xDivisions = 50
        self.yDivisions = 50
        self.zDivisions = 10

        self.xBins = np.linspace(self.xRange[0], self.xRange[1], self.xDivisions)
        self.yBins = np.linspace(self.yRange[0], self.yRange[1], self.yDivisions)
        self.zBins = np.linspace(self.zRange[0], self.zRange[1], self.zDivisions)
        # Map grid delimitations

    def process_local_point_cloud(self, point_cloud, pose):
        """
        Process batches of local point clouds
        """
        point_cloud = self._local_to_global(point_cloud, pose)

        map_points, point_count = self._discretise_point_cloud(point_cloud)

        map_points, point_count = self._batch_filter(map_points, point_count)

        self.publish_data_set(map_points, point_count)

    def publish_data_set(self, points, count):
        """
        Passes data to Rabbit MQ
        """

    def _local_to_global(self, local_points, pose):
        """
        Convert local points to a global coordinate system
        """
        rot = R.from_quat(pose[2])

        global_points = rot.apply(local_points)
        global_points = np.add(global_points, pose[1])

        return global_points

    def _discretise_point_cloud(self, points):
        """
        Take continous point cloud and discritise to map grid
        """
        xSort = np.digitize(points[:, 0], self.xBins) -1
        ySort = np.digitize(points[:, 1], self.yBins) -1
        zSort = np.digitize(points[:, 2], self.zBins) -1

        points = np.column_stack((xSort, ySort, zSort))

        points, count = self._compress_point_cloud(points)
        return points, count

    def _compress_point_cloud(self, points):
        """
        Take a discritised point cloud and compress to cummalative
        counts of unique points
        """
        points, count = np.unique(points, axis=0, return_counts=True)
        return (points, count)

    def _batch_filter(self, points, count):
        """
        Final filtering stage before adding to the map
        """
        return points, count

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
        coord = self._deproject_frame(depth_frame, depth_data[2])

        self.process_local_point_cloud(coord, pose_data)

    def _pre_process(self, depth_frame, intrin):
        """
        Any pre-processing before deprojection
        """
        depth_frame = self._scale_depth_frame(depth_frame, intrin[0])
        depth_frame = self._limit_depth_range(depth_frame)
        return depth_frame

    def _scale_depth_frame(self, depth_frame, scale):
        """
        Convert depth pixels into meter units
        """
        return depth_frame * scale

    def _limit_depth_range(self, depth_frame):
        """
        Limit the maximum/minimum range of the depth camera
        """
        depth_frame[np.logical_or(depth_frame < self.depth_min_range,
                                  depth_frame > self.depth_max_range)] = np.nan
        return depth_frame

    def _deproject_frame(self, depth_frame, intrin):
        """
        Deproject depth image to local cartesian coordinate system
        """
        frame_shape = depth_frame.shape
        x_deproject, y_deproject = self._initialise_deprojection_matrix(frame_shape, intrin)

        z_coord = depth_frame
        x_coord = np.multiply(depth_frame, x_deproject)
        y_coord = np.multiply(depth_frame, y_deproject)

        z_coord = np.reshape(z_coord, (-1))
        x_coord = np.reshape(x_coord, (-1))
        y_coord = np.reshape(y_coord, (-1))

        coord = np.column_stack((z_coord, x_coord, y_coord)) # Output as FRD coordinates
        return coord[~np.isnan(z_coord), :]

    def _initialise_deprojection_matrix(self, matrix_shape, intrin):
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
