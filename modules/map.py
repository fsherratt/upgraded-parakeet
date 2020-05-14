import numpy as np
from scipy import interpolate
from scipy import io

from modules import load_config

class Map:
    def __init__(self, config_file='conf/map.yaml'):
        self.conf = load_config.from_file(config_file)

        self.x_bins = np.linspace(self.conf.map.size.x_min,
                                  self.conf.map.size.x_max,
                                  self.conf.map.resolution.x_divisions)
        self.y_bins = np.linspace(self.conf.map.size.y_min,
                                  self.conf.map.size.y_max,
                                  self.conf.map.resolution.y_divisions)
        self.z_bins = np.linspace(self.conf.map.size.z_min,
                                  self.conf.map.size.z_max,
                                  self.conf.map.resolution.z_divisions)

        self.grid = np.zeros((self.conf.map.resolution.x_divisions,
                              self.conf.map.resolution.y_divisions,
                              self.conf.map.resolution.z_divisions),
                             dtype=np.int16)

        bins = (self.x_bins, self.y_bins, self.z_bins)

        self.interp_func = interpolate.RegularGridInterpolator(bins, self.grid,
                                                               method='linear',
                                                               bounds_error=False,
                                                               fill_value=np.nan)

    def update_map(self, points, count):
        """
        Adds count at (N,3) coordiante points array to grid
        """
        np.add.at(self.grid, points, count)

        self.interp_func.values = self.grid

    def query_map(self, query_points):
        """
        Returns occupancy value for each cooridnate provided
        """
        return self.interp_func(query_points)

    def save_to_matlab(self, filename):
        """
        Save the grid to a matlab object
        """
        io.savemat(filename, mdict=dict(map=self.grid), do_compression=False)
