# Mapping
## Table of Contents
- [The Map](#the_map)
- [Pre-Processor](#preprocessor)

# <a name="the_map"></a>The Map

## Grid definition
Start points, voxels, etc

## Quering the map
3D linear interpolation

## Updating
A target update rate of 10Hz - this is a completly arbitary number

# <a name="preprocessor"></a>Pre-Processor
The preprocessor prepares data for addition into grid. The primary benefit of this is that the more computational intensive deprojection/discritasion methods can be parallelised for greater performance.

A base pre-processor class is provided that converts a point cloud into a discritised set of voxels. TODO: List of stages that make up this method
- A
- B
- C

## D435 Pre-processing
For the D435 realsense camera a child class handles the deprojection and filtering. The class produces a [MapPreProcessorIn](Publisher_List.md#MapPreProcessorIn) data object that is passed to the Map preprocessor. TODO: List of stages that make up this class:
- A
- B
- C

### Deprojection
Deprojection methods is descried in the [realsense](realsense.md) documentation.

### Downscaling
At full resolution the D435 contains too many data points to process - intractable