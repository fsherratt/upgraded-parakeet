import pyrealsense2 as rs
import traceback
import sys
import scipy

import numpy as np
from scipy import signal

class unexpectedDisconnect( Exception):
    # Camera unexpectably disconnected
    pass

class rs_d435:
    min_range = 0.1
    max_range = 10

    def __init__(self, width=640, height=480, framerate=30):
        self.width = width
        self.height = height

        self.framerate = framerate

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
        self.cfg.enable_stream( rs.stream.depth, self.width, self.height, \
                                rs.format.z16, self.framerate )
        self.cfg.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, self.framerate)

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

        self.intrin = profile.get_stream( rs.stream.depth ).as_video_stream_profile().get_intrinsics()
        self.scale = profile.get_device().first_depth_sensor().get_depth_scale()

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
        self.xDeprojectRow = (np.arange( self.width ) - self.intrin.ppx) / self.intrin.fx
        self.yDeprojectCol = (np.arange( self.height ) - self.intrin.ppy) / self.intrin.fy

        # Tile across full matrix height/width
        self.xDeprojectMatrix = np.tile( self.xDeprojectRow, (self.height, 1) )
        self.yDeprojectMatrix = np.tile( self.yDeprojectCol, (self.width, 1) ).transpose()

        # self.xDeprojectMatrix = self.shrink(self.xDeprojectMatrix)
        # self.yDeprojectMatrix = self.shrink(self.yDeprojectMatrix)

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
        if not depth_frame:
            return None

        depth_points = np.asarray( depth_frame.get_data(), dtype=np.float32 )
        color_image = np.asanyarray(color_frame.get_data(), dtype=np.uint8)

        # depth_points = self.shrink(depth_points)
        return depth_points, color_image

    # --------------------------------------------------------------------------
    # shrink
    # Shrink X, Y and Z by a factor so processing is faster
    # --------------------------------------------------------------------------
    def shrink(self, frame, factor=4):
        frame = signal.decimate(frame, factor, n=None, ftype='iir', axis=1, zero_phase=True)
        frame = signal.decimate(frame, factor, n=None, ftype='iir', axis=0, zero_phase=True)

        return frame


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

        Z = np.reshape(Z, (-1))
        X = np.reshape(X, (-1))
        Y = np.reshape(Y, (-1))

        # Conversion into aero-reference frame
        points = np.column_stack( (Z,X,Y) )

        inRange = np.where( (points[:,0] > self.min_range) & (points[:,0] < self.max_range) )
        points = points[inRange]

        return points

if __name__ == "__main__":
    import cv2

    d435Obj = rs_d435( framerate = 30 )

    with d435Obj:
        while True:
            frame = d435Obj.getFrame()
            threeDFrame = d435Obj.deproject_frame(frame)

            cv2.imshow('frameX', threeDFrame[0,:,:])
            cv2.imshow('frameY', threeDFrame[1,:,:])
            cv2.imshow('frameZ', threeDFrame[2,:,:])
            cv2.waitKey(1)