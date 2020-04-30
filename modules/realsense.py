import sys
import time
import traceback
import numpy as np
import pyrealsense2 as rs
from scipy.spatial.transform import Rotation as R

class rs_pipeline:
    """
    Declare all the constants, tunable variables are public
    """
    def __init__(self):
        # private
        self._pipe = None
        self._object_name = 'Untitled'

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
        cfg = self._generate_config()
        
        try:
            self._pipe.start(cfg)
        except RuntimeError as e:
            self._exception_handle("rs_pipeline:{}: failed to connect to camera".format(self._object_name))
            raise e

        self._post_connect_process()

        print('rs_pipeline:{}: Connection Open'.format(self._object_name))
    
    """
    Close connection to D435 camera
    """
    def close_connection(self):
        if self._pipe is None:
            return

        self._pipe.stop()
        self._pipe = None

        print('rs_pipeline:{}: Connection Closed'.format(self._object_name))

    """
    Retrieve a data from the D435 camera
    """
    def wait_for_frame(self) -> tuple:
        try:
            frames = self._pipe.wait_for_frames()
        except RuntimeError as e:         
            self._exception_handle("rs_pipeline:{}:wait_for_frame: Timeout waiting for data frame".format(self._object_name))
            raise e
        
        frame = self._get_frame(frames)

        try:
            data = self._get_data(frame)
        except RuntimeError:
            self._exception_handle("rs_pipeline:{}:wait_for_frame: Frame contained no data".format(self._object_name))
            return None

        # Post Process
        data = self._post_process(data)

        # End
        return data

    """
    OVERLOADED FUNCTION: Generate the pipeline config
    """
    def _generate_config(self) -> rs.config:
        raise NotImplementedError
    
    """
    OVERLOADED FUNCTION: Process run after a succesful connection
    """
    def _post_connect_process(self):
        return

    """
    OVERLOADED FUNCTION: Extract frame from rs.composite_frame
    """
    def _get_frame(self, frames):
        raise NotImplementedError
    
    """
    OVERLOADED FUNCTION: Extract data from frame
    """
    def _get_data(self, frame):
        return frame.get_data()

    """
    OVERLOADED FUNCTION: Process run on extractred frame data
    """
    def _post_process(self, data):
        return data
    
    """
    Function to collate interal class exceptions
    TODO: Log error - requires rabbit MQ stuff
    """
    def _exception_handle(self, err):
        print(err)

class depth_pipeline(rs_pipeline):
    def __init__(self):
        super().__init__()

        # public
        self.depth_width = 640
        self.depth_height = 480

        self.framerate = 60

        # private
        self._object_name = 'Depth'

        self._intrin = None
        self._scale = 1

    def _generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(rs.stream.depth, 
                            self.depth_width, self.depth_height,
                            rs.format.z16, 
                            self.framerate )
        return cfg

    def _post_connect_process(self):
        self._get_intrinsics()

    def _get_frame(self, frames):
        return frames.get_depth_frame()

    def _post_process(self, data):
        timestamp = time.time()
        depth = np.asarray(data, dtype=np.uint16)
        intrin =  (self._scale, self._intrin.ppx, self._intrin.ppy, self._intrin.fx, self._intrin.fy)
        data = (timestamp, depth, intrin)

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

class color_pipeline(rs_pipeline):
    def __init__(self):
        super().__init__()

        # public
        self.rgb_width = 640
        self.rgb_height = 480

        self.framerate = 60

        # private
        self._object_name = 'Color'

    def _generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(rs.stream.color, 
                                self.rgb_width, self.rgb_height, 
                                rs.format.bgr8, 
                                self.framerate)
        return cfg

    def _get_frame(self, frames:rs.composite_frame):
        return frames.get_color_frame()

    def _post_process(self, data):
        timestamp = time.time()
        image = np.asarray(data, dtype=np.uint8)

        return (timestamp, image)

class pose_pipeline(rs_pipeline):
    def __init__(self):
        super().__init__()

        # Public
        self.tilt_deg = 0
        self.North_offset = 0

        # Private
        self._object_name = 'Pose'

        self.H_aeroRef_T265Ref = None
        self.H_T265body_aeroBody = None
        
        self._initialise_rotational_transforms()

    def _generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(rs.stream.pose)
        return cfg
        
    def _get_frame(self, frames):
        return frames.get_pose_frame()

    def _get_data(self, frame):
        return frame.get_pose_data()

    def _post_process(self, data):
        timestamp = time.time()

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

        return (timestamp, pos, quat, conf)

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

if __name__ == "__main__": #pragma: no cover
    import signal
    import threading

    def depth_loop():
        import cv2
        global Running

        depth_obj = depth_pipeline()
        with depth_obj:
            while Running:
                depth_frame = depth_obj.wait_for_frame()

                if depth_frame is None:
                    continue

                depth_frame = depth_frame[1] * depth_frame[2][0]
                depth_frame = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame, alpha=50), cv2.COLORMAP_JET)
                cv2.imshow('depth_frame', depth_frame)
                cv2.waitKey(1)

    def color_loop():
        import cv2
        global Running

        color_obj = color_pipeline()
        with color_obj:
            while Running:
                color_frame = color_obj.wait_for_frame()

                if color_frame is None:
                    continue

                cv2.imshow('color_frame', color_frame[1])
                cv2.waitKey(1)

    def pose_loop():
        global Running
        pose_obj = pose_pipeline()
        with pose_obj:
            while Running:
                pose_frame  = pose_obj.wait_for_frame()

                if pose_frame is None:
                    continue

                # print(pose_frame[1])
                time.sleep(0.1)

    def stop_running(sig, frame):
        global Running
        Running = False

    global Running
    Running = True

    signal.signal(signal.SIGINT, handler=stop_running)

    depth_thread = threading.Thread(target=depth_loop, name='Depth_Thread')
    depth_thread.start()

    color_thread = threading.Thread(target=color_loop, name='Color_Thread')
    color_thread.start()

    pose_thread = threading.Thread(target=pose_loop, name='Pose_Thread')
    pose_thread.start()

    signal.pause()
    time.sleep(0.5)
    print('Stopping')
