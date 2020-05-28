# Publisher Data Packets

## Table of Contents
- [Realsense](#realsense)
- [Map](#map)
- [Launch](#launch)

## <a name="realsense"></a>Realsense

### <a name="Intrinsics"></a>Intrinsics
- scale (float32)
- ppx (float32)
- ppy (float32)
- fx (float32)
- fy (float32)

### <a name="Depth"></a>Depth Data
- timestamp (float32)
- data [x, y] (uint16/y16)
- intrin: **[Intrinsics](#Intrinsics)**

### <a name="Color"></a>Color Data
- timestamp (float32)
- data [x, y, 3] (uint8/bgr8)

### <a name="Pose"></a>Pose
- timestamp (float32)
- translation_x (float32)
- translation_y (float32)
- translation_z (float32)
- quat_x (float32)
- quat_y (float32)
- quat_z (float32)
- quat_w (float32)
- conf (uint8)

## <a name="map"></a>Map

### <a name="MapPreProcessorOut"></a>MapPreProcessorOut
- timestamp (float32)
- voxels: (float32)
- count: (uint16)

## <a name="map"></a>Launch
### <a name="procHeart"></a>ProcessHeartbeat
    timestamp: float
    process_name: str
    process_alive: bool
    thread_count: int


### <a name="startItem"></a>StartupItem
    module: str
    config_file: str
    process_name: str
    debug: bool
