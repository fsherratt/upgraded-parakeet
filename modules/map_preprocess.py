"""
This module contains all classes related to preprocessing of point data to
be added to the occupancy map
"""

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

    def _local_to_global(self, local_points):
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

    def _batch_filter(self):
        """
        Final filtering stage before adding to the map
        """

class DepthMapAdapter(MapPreprocess):
    """
    Prepare D435 depth data for feeding into the occupancy map
    """
    def __init__(self):
        super().__init__()

    def depth_callback(self, data):
        """
        Recieve incoming depth data
        """

    def pose_callback(self, data):
        """
        Recieve incoming pose data
        """

    def adapter_pipeline(self):
        """
        Run incoming data through all processing steps
        """

    def _pre_process(self, data):
        """
        Any pre-processing before deprojection
        """

    def _scale_depth(self, data):
        """
        Convert depth pixels into meter units
        """

    def _range_limit(self, data):
        """
        Limit depth camera to specified range
        """

    def _deproject(self, data):
        """
        Deproject depth image to cartesian coordinate system
        """

if __name__ == "__main__":
    pass
