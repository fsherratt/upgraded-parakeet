from unittest import TestCase, mock

import numpy as np

from context import modules
from modules import data_types
from modules.mapping import Map


class TestMap(TestCase):
    def setUp(self):
        self.map = Map()

        self.test_map_shape = data_types.MapDefinition(x_min=-1, y_min=-1, z_min=-1,
                               x_max=1, y_max=1, z_max=1,
                               x_divisions=10, y_divisions=10, z_divisions=10)
                               
        self.map._setup_grid(self.test_map_shape)

    @mock.patch('modules.async_message.AsyncMessageCallback.wait_for_message')
    def test_map_update(self, mock_wait):
        """
        Test addition of voxel data to the map
        """
        mock_voxels = [(0, 0), (0, 0), (0, 1)]
        mock_count = [1, 2]
        mock_wait.return_value = (0, data_types.MapPreProcessorOut(0, np.asarray(mock_voxels).transpose(), mock_count))

        self.map._update_map()

        # Cell have correct value in
        np.testing.assert_equal(self.map._grid[mock_voxels], mock_count)
        # Sum of grid = sum of mock_count
        np.testing.assert_equal(self.map._grid.sum(), np.sum(mock_count))

    def test_map_query(self):
        """
        Test the map query function returns the correct values
        """
        self.map._initialise_interp_func(interp_method='linear')
        
        self.map.add_map_data_callback(data_types.MapPreProcessorOut(0, np.asarray([[0,0,0]]), 1))
        self.map._update_map()

        point = (self.test_map_shape.x_min, self.test_map_shape.y_min, self.test_map_shape.z_min)

        rtn_val = self.map._query_map(point)
        
        self.assertEqual(rtn_val, 1)

    def test_bin_initilisation(self):
        """
        Test that grid bins are initilised correctly
        """
        self.assertEqual(self.map._bins[0].min(), self.test_map_shape.x_min)
        self.assertEqual(self.map._bins[1].min(), self.test_map_shape.y_min)
        self.assertEqual(self.map._bins[2].min(), self.test_map_shape.z_min)
        self.assertEqual(self.map._bins[0].max(), self.test_map_shape.x_max)
        self.assertEqual(self.map._bins[1].max(), self.test_map_shape.y_max)
        self.assertEqual(self.map._bins[2].max(), self.test_map_shape.z_max)

    def test_grid_initilisation(self):
        """
        Test that the map grid is initilised correctly
        """
        grid_shape = (self.test_map_shape.x_divisions,
                      self.test_map_shape.y_divisions,
                      self.test_map_shape.z_divisions)

        self.assertEqual(self.map._grid.shape, grid_shape)
