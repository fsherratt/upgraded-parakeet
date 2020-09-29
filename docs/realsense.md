# Realsense Pipeline

## Table of Contents
- [Using the pipeline](#pipeline)
- [D435 Maths](#d435)
- [T265 Maths](#t265)

# <a name="pipeline"></a>Using the Pipeline
The realsense pipeline module _[modules/realsense.py]()_ connects the realsense cameras to rabbit mq. Individual streams can be enable and disabled indepentendly

## Starting Up
**TODO:**
To begin streaming realsense data to rabbit mq you can use the command below.
```bash
> Some startup command sequence
```

This takes the following arguments
- -R [depth/color/pose]
- -C config_file [optional]
- Any additional OmegaConf overide methods. Read more about this her [Config](Config.md)

## Published Data
A description of the data structures produced by each realsense publisher is available here, [Publisher List](Publisher_List.md)

## Adding More
For additional functionality a wrapper class can be constructed around to the realsense class. An example of how to interface with a rs_pipeline child class is presented below below.

```python
from modules.realsense import depth_pipeline

depth_obj = depth_pipeline()

with depth_obj:
    while True:
        depth_frame = depth_obj.wait_for_frame()

        if depth_frame is None:
            continue

        # Do something with depth data
```

# <a name="d435"></a>Realsense D435

> [The D435] uses stereo vision to calculate depth. The D435 is a USB-powered depth camera and consists of a pair of depth sensors, RGB sensor, and infrared projector. It is ideal for makers and developers to add depth perception capability to their prototype.

__Source [Intel® RealSense™ Depth Camera D435](https://store.intelrealsense.com/buy-intel-realsense-depth-camera-d435.html)_


## Visual Presets
Various visual presets exsist for the depth camera. These change the onboard paramaters for different situations. More details can be found here, [D400 Series Visual Presets](https://github.com/IntelRealSense/librealsense/wiki/D400-Series-Visual-Presets).
| Value | Preset |
| --- | --- |
| 0 | Custom |
| 1 | Default |
| 2 | Hand |
| 3 | High Accuracy |
| 4 | High Density |
| 5 | Medium Density |

## Depth calcuation
Intel provide a detailed description of how stereo depth is calculated here,
[Depth from Stereo](https://github.com/IntelRealSense/librealsense/blob/28c404a419ebab98d2ee93615776e8cefb46a340/doc/depth-from-stereo.md).

## Camera Coordinate System
The D435 camera uses the following coordinate system. The X-axis points to the right, the positive Y-axis points down, and the positive Z-axis points forward. To convert to a FRD coordinate system a mapping of `[X, Y, Z] = [Z, X, -Y]` is used

![D435 coordinate system](images/D435_CS_axis.png)

_Source: [How-to: Getting IMU data from D435i and T265](https://www.intelrealsense.com/how-to-getting-imu-data-from-d435i-and-t265/)_

## Deprojection
Projection is the process of mapping a 3D object to a 2D plane. The inverse is deprojection, the process of converting a depth image into a 3D point cloud. It uses the intrinsics of the camera to achieve this.

#### Camera Intrinsics
The camera intrinsics are,
* **_Fx_** - Focal length in x
* **_Fy_** - Focal length in y
* **_Ppx_** - Principal point in x, usually called the optical center **_cx_**
* **_Ppy_** - Principal point in y, usually called the optical center **_cy_**

All have units of pixels  

This is often presented as a camera projection matrix **_k_**:  
_[ &nbsp;Fx, &nbsp;Skew, &nbsp;Cx ]  
[ &nbsp;0, &nbsp;&nbsp;&nbsp;Fy, &nbsp;&nbsp;&nbsp;Cy ]  
[ &nbsp;0, &nbsp;&nbsp;&nbsp;0,  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;1 ]_

Skew is not given by the realsense camera so is taken as zero

#### Deprojection Equations
Using the deprojection equations the equivalent 3D coordinates for each depth_point `z` can be obtained. `i` and `j` are the depth pixel coordinates. 

`X = z * (i - Ppx) / fx`  
`Y = z * (j - Ppy) / fy`  
`Z = z`

_Source: [Camera Intrinsics](https://berkeleyautomation.github.io/perception/api/camera_intrinsics.html), [Projection in RealSense SDK 2.0](https://github.com/IntelRealSense/librealsense/wiki/Projection-in-RealSense-SDK-2.0), [Original equations](
https://github.com/IntelRealSense/librealsense/blob/7148f9ae1d78b5d44bee4fc578bf0b8fb9a220c5/wrappers/python/examples/box_dimensioner_multicam/helper_functions.py#L121), 
[Potentially better method](
https://github.com/BerkeleyAutomation/perception/blob/c7f8429600775c450d5d2ea6a2a10f1d4c508184/perception/camera_intrinsics.py#L335)_

# <a name="t265"></a>Realsense T265
Inside out 6 DOF tracking camera. Uses a combination of SLAM using stereo grayscale cameras and IMU data to provide high frequency 6 DOF data.

## Camera Coordinate Frame
The T265 uses the defacto VR framework standard coordinate system instead of the SDK standard. The positive X direction is towards right imager, the positive Y direction is upwards toward the top of the device, with the zero reference aligned to gravity, and the positive Z direction is inwards toward the back of the device.

![T265 coordinate system](images/T265_CS_axis.png)

_Source: [How-to: Getting IMU data from D435i and T265](https://www.intelrealsense.com/how-to-getting-imu-data-from-d435i-and-t265/)_

## Conversion to Aircraft Reference Coordinate System
For the aircraft to understand the 6DOF data from the camera it must be in the same refence coordinate system. The aircraft uses the NED (North, East, Down) coordinate system whereas the T265 uses A VR standard system described above. The T265 may be mounted at a tilted angle _**&alpha;**_. Where _**&alpha;**_ is between 0 and 90 degrees. so this must also be taken into account.

### Coordinate Frame Definition
1. The aircraft NED reference frame `{0}` is aligned to North, East and Gravity
1. The aircraft reference frame `{1}` is specified as FRD (Front Right Down (Gravity)) .
1. The camera reference frame `{2}` is as described above
1. The camera body frame `{3}` is given by the output produced from the T265
1. The untilted camera body frame `{4}` is after the tilt angle _**&alpha;**_ has been accounted for
1. The aircraft body frame `{5}` is rigidly attached to the aircraft orientation in the FRD configuration.

The rotational frame that the aircraft requires is the _**R<sup>0</sup><sub>5</sub>**_ frame using the above definitions. Note all reference frames origins are coincident to each other and the same for all body frames.

### Rotational Transforms
The transforms between frames can be described using homogeneous rotational transforms described below:

* The transform between `{0}` and `{1}` is the rotation, around Z, between Front and North. The body frames of FRD and NED are the same. 
* A static rotational transform between frames `{1}` and `{2}`, _**R<sup>1</sup><sub>2</sub>**_,  can be trivially calcualted. 
* The same for frames `{4}` and `{5}`. The relationship between these two homogeneous transforms is _**R<sup>1</sup><sub>2</sub><sup>T</sup> = R<sup>4</sup><sub>5</sub>**_.
* _**R<sup>3</sup><sub>4</sub>**_ is a rotation in x by alpha. The DCM matrix of which is  
_[ 1, &nbsp;&nbsp;&nbsp;&nbsp;0, &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;0 &nbsp;&nbsp;&nbsp;&nbsp;]  
[ 0, cos &alpha;, -sin &alpha; ]  
[ 0, sin &alpha;,  &nbsp;cos &alpha; ]_

Therefore  
 _**R<sup>0</sup><sub>5</sub> = R<sup>0</sup><sub>1</sub><sup>1</sup><sub>2</sub>R<sup>2</sup><sub>3</sub>R<sup>3</sup><sub>4</sub>R<sup>4</sup><sub>5</sub>**_

### Translation Transforms
We only need to worry about the change in reference frame for translation. To rotate the vector_**V**_ the equation _**V<sub>new</sub> = R*V**_ is used. For our purposes _**R = R<sup>0</sup><sub>2</sub>**_