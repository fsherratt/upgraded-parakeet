# Publisher Data Packets

## Realsense

### Depth Data
- timestamp (float32)
- data [x, y] (uint16/y16)
- scale (float32)
- ppx (float32)
- ppy (float32)
- fx (float32)
- fy (float32)

### Color Data
- timestamp (float32)
- data [x, y, 3] (uint8/bgr8)

### Pose
- timestamp (float32)
- translation_x (float32)
- translation_y (float32)
- translation_z (float32)
- quat_x (float32)
- quat_y (float32)
- quat_z (float32)
- quat_w (float32)
- conf (uint8)
