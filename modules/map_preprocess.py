"""
This module contains all classes related to preprocessing of point data to
be added to the occupancy map
"""
import numpy as np
from scipy.spatial.transform import Rotation as R

from modules import data_types, load_config
from modules.async_message import AsyncMessageCallback

class MapPreprocess:
    """
    This class takes a localised point cloud and prepares it to
    be added to the global occupancy map
    """
    def __init__(self, map_def: data_types.MapDefinition, config_file='conf/map.yaml'):
        self.conf = load_config.from_file(config_file)

        self._map_shape = map_def

        self._bins = None
        self._initialise_bin_delimitations()

        self.message_queue = AsyncMessageCallback(queue_size=1)
        self._pose_data = None

    def depth_callback(self, data: data_types.Depth):
        """
        Receive incoming depth data
        """
        if self._pose_data is None:
            return

        self.message_queue.queue_message((data, self._pose_data))

    def pose_callback(self, data: data_types.Pose):
        """
        Receive incoming pose data
        """
        self._pose_data = data

    def process_incoming_data(self):
        """
        Process batches of local point clouds
        """
        data_in = self.message_queue.wait_for_message()

        if data_in is None:
            return None
        
        data, pose = data_in[1]

        data = self._input_data_preprocess(data)
        points, count = self._point_data_to_map(data, pose)

        return data_types.MapPreProcessorOut(data_in[0], points, count)

    def _input_data_preprocess(self, data):
        """
        Taken the raw data and convert to a standardised (Nx3) matrix of local
        cartesian cooridantes. This function should be overriden by child class
        """
        raise NotImplementedError

    def _point_data_to_map(self, point_cloud, pose):
        """
        Take coordinate array and convert to a set of map voxel coordinates and
        a hit count for each voxel
        """
        map_points = self._local_to_global(point_cloud, pose)
        map_points, point_count = self._discretise_point_cloud(map_points)


        return (map_points, point_count)

    def _initialise_bin_delimitations(self):
        x_bins = np.linspace(self._map_shape.x_min,
                             self._map_shape.x_max,
                             self._map_shape.x_divisions)
        y_bins = np.linspace(self._map_shape.y_min,
                             self._map_shape.y_max,
                             self._map_shape.y_divisions)
        z_bins = np.linspace(self._map_shape.z_min,
                             self._map_shape.z_max,
                             self._map_shape.z_divisions)

        self._bins = (x_bins, y_bins, z_bins)

    def _local_to_global(self, local_points, pose):
        """
        Convert local points to a global coordinate system
        """
        rot = R.from_quat(pose.quaternion)

        global_points = rot.apply(local_points)
        global_points = np.add(global_points, pose.translation)

        return global_points

    def _discretise_point_cloud(self, points):
        """
        Take continous point cloud and discritise to map grid
        returns a Nx3 matrix of voxel coordinates and a vector 
        representing the number of hits in each voxel
        """
        x_sort = np.digitize(points[:, 0], self._bins[0]) - 1
        y_sort = np.digitize(points[:, 1], self._bins[1]) - 1
        z_sort = np.digitize(points[:, 2], self._bins[2]) - 1

        voxels = np.column_stack((x_sort, y_sort, z_sort))
        voxels[voxels < 0] = 0

        voxels = np.uint16(voxels)

        if self.conf.depth_preprocess.enable_compression:
            voxels, voxel_hits = self._compress_point_cloud(voxels)
        else:
            voxel_hits = np.ones(voxels.shape[0])

        return voxels, voxel_hits

    def _compress_point_cloud(self, points):
        """
        Take a discritised point cloud and compress to cumulative
        counts of unique points
        """
        points, count = np.unique(points, axis=0, return_counts=True)
    
        # Compress data
        points = np.uint16(points)
        count = np.uint16(count)
        
        return (points, count)

class DepthMapAdapter(MapPreprocess):
    """
    Prepare D435 depth data for feeding into the occupancy map
    """
    def _input_data_preprocess(self, data):
        depth_frame = self._pre_process(data.depth, data.intrin)
        coord = self._deproject_frame(depth_frame, data.intrin)

        return coord

    def _pre_process(self, depth_frame, intrin: data_types.Intrinsics):
        """
        Any pre-processing before de-projection
        """
        depth_frame = self._downscale_data(depth_frame)
        depth_frame = self._scale_depth_frame(depth_frame, intrin.scale)
        depth_frame = self._limit_depth_range(depth_frame)

        return depth_frame

    def _downscale_data(self, data_frame):
        """
        Downscale image to reduce noise and decrease computation time
        """
        block_size = tuple(self.conf.depth_preprocess.downscale_block_size)
        shape = data_frame.shape

        new_shape = (shape[0]//block_size[0], block_size[0], shape[1]//block_size[1], block_size[1])
        new_data_frame = np.reshape(data_frame, new_shape)

        downscale_method = self.conf.depth_preprocess.downscale_method

        if downscale_method == 'min_pool':
            new_data_frame = np.amin(new_data_frame, axis=(1, 3))

        elif downscale_method == 'max_pool':
            new_data_frame = np.amax(new_data_frame, axis=(1, 3))

        elif downscale_method == 'mean':
            new_data_frame = np.mean(new_data_frame, axis=(1, 3))

        else:
            raise RuntimeError('Downscaling method `{}` unknown'.format(downscale_method))

        return new_data_frame

    def _scale_depth_frame(self, depth_frame, scale):
        """
        Convert depth pixels into meter units
        """
        return depth_frame * scale

    def _limit_depth_range(self, depth_frame):
        """
        Limit the maximum/minimum range of the depth camera
        """
        depth_frame[np.logical_or(depth_frame < self.conf.depth_preprocess.min_range,
                                  depth_frame > self.conf.depth_preprocess.max_range)] = np.nan
        return depth_frame

    def _deproject_frame(self, depth_frame, intrin: data_types.Intrinsics):
        """
        De-project depth image to local cartesian coordinate system
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

    def _initialise_deprojection_matrix(self, matrix_shape, intrin: data_types.Intrinsics):
        """
        Initialise conversion matrix for converting the depth frame to a de-projected 3D
        coordinate system
        """
        matrix_height, matrix_width = matrix_shape
        block_height, block_width = tuple(self.conf.depth_preprocess.downscale_block_size)

        x_deproject_row = ((np.arange(matrix_width) * block_width) - intrin.ppx) / intrin.fx
        y_deproject_col = ((np.arange(matrix_height) * block_height) - intrin.ppy) / intrin.fy

        x_deproject_matrix = np.tile(x_deproject_row, (matrix_height, 1))
        y_deproject_matrix = np.tile(y_deproject_col, (matrix_width, 1)).transpose()

        return x_deproject_matrix, y_deproject_matrix

if __name__ == "__main__":
    pass
