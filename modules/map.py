import numpy as np
from scipy.interpolate import RegularGridInterpolator as RGI
from scipy import io

from modules import load_config, async_message

class Map:
    def __init__(self, config_file='conf/map.yaml'):
        self.conf = load_config.from_file(config_file)
        self.interp_func = None

        self.bins = self.initialise_bins(self.conf)
        self.grid = self.initialise_grid(self.conf)

        self._initialise_interp_func()

        self.new_map_data = async_message.AsyncMessageCallback()

    @staticmethod
    def initialise_bins(map_conf):
        """
        Initialise grid divisions
        """
        x_bins = np.linspace(map_conf.map.size.x_min,
                             map_conf.map.size.x_max,
                             map_conf.map.resolution.x_divisions)
        y_bins = np.linspace(map_conf.map.size.y_min,
                             map_conf.map.size.y_max,
                             map_conf.map.resolution.y_divisions)
        z_bins = np.linspace(map_conf.map.size.z_min,
                             map_conf.map.size.z_max,
                             map_conf.map.resolution.z_divisions)

        return (x_bins, y_bins, z_bins)

    @staticmethod
    def initialise_grid(map_conf):
        """
        Setup grid system
        """
        grid = np.zeros((map_conf.map.resolution.x_divisions,
                         map_conf.map.resolution.y_divisions,
                         map_conf.map.resolution.z_divisions),
                        dtype=np.int16)

        return grid

    def add_map_data_callback(self, data):
        """
        Callback for incoming map data to add to grid
        """
        self.new_map_data.queue_message(data)

    def save_to_matlab(self, filename):
        """
        Save the grid to a matlab object
        """
        io.savemat(filename, mdict=dict(map=self.grid), do_compression=False)

    def _initialise_interp_func(self):
        """
        """
        self.interp_func = RGI(self.bins, self.grid,
                               method='linear',
                               bounds_error=False,
                               fill_value=np.nan)

    def _update_map(self):
        """
        Adds count at (N,3) coordiante points array to grid
        """
        new_data = self.new_map_data.wait_for_message()

        np.add.at(self.grid, new_data.voxels, new_data.count)

        self.interp_func.values = self.grid

    def _query_map(self, query_points):
        """
        Returns occupancy value for each cooridnate provided
        """
        return self.interp_func(query_points)
