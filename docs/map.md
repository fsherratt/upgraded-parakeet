# Mapping
## Table of Contents
- [The Map](#the_map)
- [Pre-Processor](#preprocessor)
    - [D435 Pre-processing](#d435_preprocessor)

# <a name="the_map"></a>The Map
The map is an occupancy map of all objects that have been detected by the onboard sensing.

## <a name="grid"></a>Grid definition
The grid resolution and size are defined by the _map.size_ and _map.resolution_ paramaters.

## <a name="map_query"></a>Quering the map
TODO

## <a name="update_map"></a>Updating
TODO

# <a name="preprocessor"></a>Pre-Processor
The preprocessor prepares data for addition into grid. The primary benefit of this is that the more computational intensive deprojection/discritasion methods can be parallelised for greater performance.

A base pre-processor class is provided that converts a point cloud into a discritised set of voxels. The list of stages involved in this class is presented below:
- Conversion from local to global coordinate frame
- Discritisation - Binning of the point cloud data to voxel coordinates 
- Compression - Identification and counting of unique cooridnate sets
- Filter - Filtering of compressed data (Removal of voxels with low counts)

## <a name="d435_preprocessor"></a>D435 Depth Pre-processing
For the D435 realsense camera a child class handles the deprojection and filtering. The class produces a [MapPreProcessorIn](Publisher_List.md#MapPreProcessorIn) data object that is passed to the Map preprocessor. A list of stages involved in this is given below:
- Image filtering - Filtering incoming image data data
- [Downscaling data](#d435_downscale) - Reduction in image size to reduce data to process and improve data quality
- Deprojection - Conversion from depth pixels to 3D coordinates - this is descried in detaile in the [realsense](realsense.md#deprojection) documentation.


### <a name="d435_downscale"></a>Downscaling
At full resolution the D435 contains too many data points to process.

The image is devived into the number of sample blocks of size specified by the _depth_preprocessor.downscale_block_size_ conf paramater. For each block a single value is returned to make the new downscaled image. The operation to achieve this is specified by the _depth_preprocessor.downscale_method_ paramater and can be any of the following:
- mean - Mean of values in sample block
- max_pool - Maximum value in sample block
- min_pool - Minimum value in sample block