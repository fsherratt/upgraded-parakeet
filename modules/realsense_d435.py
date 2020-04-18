import pyrealsense2 as rs
import traceback
import sys
import time

import numpy as np

class rs_d435:
    min_range = 0.1
    max_range = 10

    def __init__(self):
        self.depth_width = 640
        self.depth_height = 480
        self.rgb_width = 640
        self.rgb_height = 480

        self.framerate = 30

        self.intrin = None
        self.scale = 1

        self._FOV = (0, 0)

        self.xDeprojectMatrix = None
        self.yDeprojectMatrix = None

    def __enter__(self):
        self.openConnection()

    def __exit__(self, exception_type, exception_value, traceback):
        if traceback:
            print(traceback.tb_frame)

        self.closeConnection()
    
    # --------------------------------------------------------------------------
    # openConnection
    # return void
    # --------------------------------------------------------------------------
    def openConnection(self):
        self.pipe = rs.pipeline()

        self.cfg = rs.config()
        self.cfg.enable_stream( rs.stream.depth, 
                                self.depth_width, self.depth_height,
                                rs.format.z16, 
                                self.framerate )
        self.cfg.enable_stream(rs.stream.color, 
                                self.rgb_width, self.rgb_height, 
                                rs.format.bgr8, 
                                self.framerate)

        self.profile = self.pipe.start( self.cfg  )

        self.initialise_deprojection_matrix()

        print('rs_d435:D435 Connection Open')
    
    # --------------------------------------------------------------------------
    # closeConnection
    # return void
    # --------------------------------------------------------------------------
    def closeConnection(self):
        self.pipe.stop()
        
        print('rs_t265:D435 Connection Closed')

    # --------------------------------------------------------------------------
    # getIntrinsics
    # get camera intrinsics
    # return void
    # --------------------------------------------------------------------------
    def getIntrinsics( self ):
        profile = self.pipe.get_active_profile()

        self.intrin = profile.get_stream( rs.stream.depth ) \
                        .as_video_stream_profile() \
                        .get_intrinsics()

        self.scale = profile.get_device() \
                        .first_depth_sensor() \
                        .get_depth_scale()
                        
        self.scale *= 1000 # Convert from mm to m

        self.FOV = rs.rs2_fov( self.intrin )
        self.FOV = np.deg2rad( self.FOV )

    # --------------------------------------------------------------------------
    # initialise_deprojection_matrix
    # Conversion matrix from detpth to
    # return void
    # --------------------------------------------------------------------------
    def initialise_deprojection_matrix( self ):
        self.getIntrinsics()
        
        # Create deproject row/column vector
        self.xDeprojectRow = (np.arange( self.depth_width ) - self.intrin.ppx) / self.intrin.fx
        self.yDeprojectCol = (np.arange( self.depth_height ) - self.intrin.ppy) / self.intrin.fy

        # Tile across full matrix height/width
        self.xDeprojectMatrix = np.tile( self.xDeprojectRow, (self.depth_height, 1) )
        self.yDeprojectMatrix = np.tile( self.yDeprojectCol, (self.depth_width, 1) ).transpose()

    # --------------------------------------------------------------------------
    # getFrame
    # Retrieve a depth frame with scale metres from camera
    # return np.float32[width, height]
    # --------------------------------------------------------------------------
    def getFrame(self):
        frames = self.pipe.wait_for_frames()

        # Get depth data
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        try:
            depth_points = depth_frame.get_data()
            color_image = color_frame.get_data()
        except AttributeError:
            return None

        depth_points = np.asarray(depth_points, dtype=np.float32)
        color_image = np.asanyarray(color_image, dtype=np.uint8)

        depth_points = self.deproject_frame(depth_points)

        return (time.time(), depth_points, color_image)

    # --------------------------------------------------------------------------
    # deproject_frame
    # Conversion depth frame to 3D local coordiate system in meters
    # return [[x,y,z]] coordinates of depth pixels
    # --------------------------------------------------------------------------
    def deproject_frame( self, frame ):
        frame = frame * self.scale
        Z = frame
        X = np.multiply( frame, self.xDeprojectMatrix )
        Y = np.multiply( frame, self.yDeprojectMatrix )

        return [X, Y, Z]

if __name__ == "__main__":
    import cv2

    d435Obj = rs_d435()

    with d435Obj:
        while True:
            frame = d435Obj.getFrame()

            depth = frame[1][2]
            depth = cv2.applyColorMap(cv2.convertScaleAbs(depth, alpha=0.03), cv2.COLORMAP_JET)

            cv2.imshow('depth_frame', depth)
            cv2.imshow('color_frame', frame[2])
            cv2.waitKey(1)