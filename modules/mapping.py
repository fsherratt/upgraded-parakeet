import numpy as np
from scipy.interpolate import RegularGridInterpolator as RGI

from modules import async_message, data_types, load_config


class Map:
    def __init__(self, map_def: data_types.MapDefinition, config_file='conf/map.yaml'):
        self._map_shape = map_def
        self.conf = load_config.from_file(config_file)

        self._bins = None
        self._grid = None
        self._interp_func = None

        self._setup_grid()
        self._initialise_interp_func(self.conf.map.interp_function)

        self.new_map_data = async_message.AsyncMessageCallback(queue_size=1)

    @staticmethod
    def initialise_bins(map_conf):
        """
        Initialise grid divisions
        """
        x_bins = np.linspace(map_conf.x_min,
                             map_conf.x_max,
                             map_conf.x_divisions)
        y_bins = np.linspace(map_conf.y_min,
                             map_conf.y_max,
                             map_conf.y_divisions)
        z_bins = np.linspace(map_conf.z_min,
                             map_conf.z_max,
                             map_conf.z_divisions)

        return (x_bins, y_bins, z_bins)

    @staticmethod
    def initialise_grid(map_conf):
        """
        Setup grid system
        """
        grid = np.zeros((map_conf.x_divisions,
                         map_conf.y_divisions,
                         map_conf.z_divisions),
                        dtype=np.int16)

        return grid

    def add_map_data_callback(self, data):
        """
        Callback for incoming map data to add to grid
        """
        self.new_map_data.queue_message(data)

    def _setup_grid(self):
        self._bins = self.initialise_bins(self._map_shape)
        self._grid = self.initialise_grid(self._map_shape)

    def _initialise_interp_func(self, interp_method='linear'):
        """
        Initialiser for interpolation function
        """
        self._interp_func = RGI(self._bins, self._grid,
                                method=interp_method,
                                bounds_error=False,
                                fill_value=np.nan)

    def _update_map(self):
        """
        Adds count at List of tuples with shape (3,N) coordinates points array to grid
        """
        data = self.new_map_data.wait_for_message()
        
        if data is None:
            return

        new_data = data[1]
        voxels = tuple(map(tuple, new_data.voxels.transpose()))

        np.add.at(self._grid, voxels, new_data.count)    

        self._interp_func.values = self._grid

    def _query_map(self, query_points):
        """
        Returns occupancy value for each cooridnate provided
        """
        return self._interp_func(query_points)
