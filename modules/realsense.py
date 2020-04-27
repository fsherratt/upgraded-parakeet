import pyrealsense2 as rs
import traceback
import sys
import time
import numpy as np
from scipy.spatial.transform import Rotation as R

class rs_pipeline:
    """
    Declare all the constants, tunable variables are public
    """
    def __init__(self):
        # private
        self._pipe = None

    """
    with enter method opens D435 connection
    """
    def __enter__(self):
        self.open_connection()

    """
    with exit method closes the D435 connection
    """
    def __exit__(self, exception_type, exception_value, traceback):
        if traceback:
            print(traceback.tb_frame)
            self._exception_handle("rs_d435: __exit__: `{}`".format(exception_value))

        self.close_connection()
    
    """
    Open Connection to D435 camera
    """
    def open_connection(self):
        self._pipe = rs.pipeline()
        cfg = self.generate_config()
        
        try:
            self._pipe.start(cfg)
        except RuntimeError as e:
            self._exception_handle("rs_d435: open_connection: failed to connect to camera")
            raise e

        self.post_connect_process()

        print('rs_pipeline:{} Connection Open'.format(__name__))
    
    """
    Close connection to D435 camera
    """
    def close_connection(self):
        if self._pipe is None:
            return

        self._pipe.stop()
        self._pipe = None

        print('rs_d435:D435 Connection Closed')

    """
    Retrieve a data from the D435 camera
    """
    def wait_for_frame(self) -> tuple:
        try:
            frames = self._pipe.wait_for_frames()
        except RuntimeError as e:         
            self._exception_handle("rs_d435: getFrame: timeout waiting for data frame")
            raise e
        
        frame = self.get_frame(frames)

        try:
            data = self.get_data(frame)
        except RuntimeError:
            self._exception_handle("rs_d435: getFrame: frame contained no data")
            return None

        # Post Process
        data = self.post_process(data)

        # End
        return (time.time(), data)

    """
    Function to collate interal class exceptions
    TODO: Log error - requires rabbit MQ stuff
    """
    def _exception_handle(self, err):
        print(err)

    # Functions to Overload
    def generate_config(self) -> rs.config:
        raise NotImplementedError
    
    def post_connect_process(self):
        return

    def get_frame(self, frames):
        raise NotImplementedError
    
    def get_data(self, frame):
        return frame.get_data()

    def post_process(self, data):
        return data

class depth_pipeline(rs_pipeline):
    """
    Declare all the constants, tunable variables are public
    """
    def __init__(self):
        super().__init__()

        # public
        self.depth_width = 640
        self.depth_height = 480

        self.framerate = 6

        self.min_range = 0.1
        self.max_range = 10

        # private
        self._intrin = None
        self._scale = 1

        self._FOV = None

        self._x_deproject_matrix = None
        self._y_deproject_matrix = None

    def generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(rs.stream.depth, 
                                self.depth_width, self.depth_height,
                                rs.format.z16, 
                                self.framerate )
        return cfg

    def post_connect_process(self):
        self._initialise_deprojection_matrix()

    def get_frame(self, frames):
        return frames.get_depth_frame()

    def post_process(self, data):
        data = np.asarray(data, dtype=np.float32)
        data = self._process_depth_frame(data)

        return data

    """
    Returns the FOV of the connected camera
    """
    def get_fov(self) -> tuple:
        return self._FOV

    """
    Get camera intrinsics
    """
    def _get_intrinsics(self):
        profile = self._pipe.get_active_profile()

        self._intrin = profile.get_stream( rs.stream.depth ) \
                        .as_video_stream_profile() \
                        .get_intrinsics()

        self._scale = profile.get_device() \
                        .first_depth_sensor() \
                        .get_depth_scale()
                        
        self._FOV = rs.rs2_fov(self._intrin)

    """
    Initialise conversion matrix for converting the depth frame to a de-projected 3D 
    coordinate system
    """
    def _initialise_deprojection_matrix(self):
        self._get_intrinsics()
        
        x_deproject_row = (np.arange( self.depth_width ) - self._intrin.ppx) / self._intrin.fx
        y_deproject_col = (np.arange( self.depth_height ) - self._intrin.ppy) / self._intrin.fy

        self._x_deproject_matrix = np.tile( x_deproject_row, (self.depth_height, 1) )
        self._y_deproject_matrix = np.tile( y_deproject_col, (self.depth_width, 1) ).transpose()

    """
    Perform data pre-processing to depth frame
    """
    def _process_depth_frame(self, frame:np.array):
        frame = self._scale_depth_frame(frame)
        frame = self._limit_depth_range(frame)
        return frame

    """
    Scale the depth output to meteres
    """
    def _scale_depth_frame(self, frame:np.array):
        return frame * self._scale

    """
    Limit the maximum/minimum range of the depth camera
    """
    def _limit_depth_range(self, frame:np.array):
        frame[ np.logical_or(frame < self.min_range, frame > self.max_range) ] = np.nan
        return frame

    """
    Converts from depth frame to 3D local FED coordiate system
    """
    def _deproject_frame(self, frame:np.array) -> list:       
        Z = frame
        X = np.multiply( frame, self._x_deproject_matrix )
        Y = np.multiply( frame, self._y_deproject_matrix )

        Z = np.reshape(Z, (-1))
        X = np.reshape(X, (-1))
        Y = np.reshape(Y, (-1))

        return np.column_stack( (Z,X,Y) ) # Output as FRD coordinates

class color_pipeline(rs_pipeline):
    """
    Declare all the constants, tunable variables are public
    """
    def __init__(self):
        super().__init__()

        # public
        self.rgb_width = 640
        self.rgb_height = 480

        self.framerate = 30

    def generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(rs.stream.color, 
                                self.rgb_width, self.rgb_height, 
                                rs.format.bgr8, 
                                self.framerate)
        return cfg

    def get_frame(self, frames:rs.composite_frame):
        return frames.get_color_frame()

    def post_process(self, data):
        return np.asarray(data, dtype=np.uint8)

class pose_pipeline(rs_pipeline):
    def __init__(self):
        super().__init__()

        # Public
        self.tilt_deg = 0
        self.North_offset = 0

        # Private
        self._pipe = None
        self.H_aeroRef_T265Ref = None
        self.H_T265body_aeroBody = None
        
        self._initialise_rotational_transforms()

    def generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(rs.stream.pose)
        return cfg
        
    def get_frame(self, frames):
        return frames.get_pose_frame()

    def get_data(self, frame):
        return frame.get_pose_data()

    def post_process(self, data):
        pos = [data.translation.x, 
                data.translation.y, 
                data.translation.z]

        quat = [data.rotation.x, 
                data.rotation.y, 
                data.rotation.z, 
                data.rotation.w]

        conf = data.tracker_confidence

        quat = self._convert_rotational_frame(quat)
        pos = self._convert_positional_frame(pos)

        return (pos, quat, conf)

    """
    Initialise rotational transforms between tilted T265 and NED aero body and ref frames
    """
    def _initialise_rotational_transforms(self):
        H_aeroNEDRef_aeroRef = R.from_euler('z', self.North_offset, degrees=True)
        H_aeroRef_T265Ref = R.from_matrix([[0,0,-1],[1,0,0],[0,-1,0]])
        H_T265Tilt_T265Body = R.from_euler('x', self.tilt_deg, degrees=True)
        
        self.H_aeroRef_T265Ref = H_aeroNEDRef_aeroRef * H_aeroRef_T265Ref
        self.H_T265body_aeroBody = H_T265Tilt_T265Body * H_aeroRef_T265Ref.inv()

    """
    Convert T265 rotational frame to aero NED frame
    """
    def _convert_rotational_frame(self, quat) -> list:
        rot = self.H_aeroRef_T265Ref * R.from_quat(quat)  * self.H_T265body_aeroBody

        return rot.as_quat()

    """
    Convert T264 translation frame to aero NED translation
    """
    def _convert_positional_frame(self, pos) -> list:
        return self.H_aeroRef_T265Ref.apply(pos)


def depth_loop():
    import cv2
    global Running

    depth_obj = depth_pipeline()
    with depth_obj:
        while Running:
            depth_frame = depth_obj.wait_for_frame()
            depth_frame = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame[1], alpha=50), cv2.COLORMAP_JET)
            cv2.imshow('depth_frame', depth_frame)
            cv2.waitKey(1)

def color_loop():
    import cv2
    global Running

    color_obj = color_pipeline()
    with color_obj:
        while Running:
            color_frame = color_obj.wait_for_frame()
            cv2.imshow('color_frame', color_frame[1])
            cv2.waitKey(1)

def pose_loop():
    global Running
    pose_obj = pose_pipeline()
    with pose_obj:
        while Running:
            pose_frame  = pose_obj.wait_for_frame()
            print(pose_frame[1])
            time.sleep(0.1)

import signal
import threading

def stop_running(sig, frame):
    global Running
    Running = False

if __name__ == "__main__": #pragma: no cover
    global Running
    Running = True

    signal.signal(signal.SIGINT, handler=stop_running)

    depth_thread = threading.Thread(target=depth_loop)
    depth_thread.start()

    color_thread = threading.Thread(target=color_loop)
    color_thread.start()

    pose_thread = threading.Thread(target=pose_loop)
    pose_thread.start()

    signal.pause()
    time.sleep(0.5)
    print('Stopping')