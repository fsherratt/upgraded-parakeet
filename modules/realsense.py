import time
import numpy as np
import pyrealsense2 as rs
from scipy.spatial.transform import Rotation as R

from modules import data_types

class RealsensePipeline:

    def __init__(self):
        """
        Declare all the constants, tunable variables are public
        """
        # private
        self._pipe = None
        self._object_name = 'Untitled'

    def __enter__(self):
        """
        with enter method opens D435 connection
        """
        self.open_connection()

    def __exit__(self, exception_type, exception_value, traceback):
        """
        with exit method closes the D435 connection
        """
        if traceback:
            print(traceback.tb_frame)
            self._exception_handle("rs_d435: __exit__: `{}`".format(exception_value))

        self.close_connection()

    def open_connection(self):
        """
        Open Connection to D435 camera
        """
        self._pipe = rs.pipeline()
        cfg = self._generate_config()

        try:
            self._pipe.start(cfg)
        except RuntimeError as raised_exception:
            self._exception_handle("rs_pipeline:{}: failed to connect to camera"
                                   .format(self._object_name))
            raise raised_exception

        self._post_connect_process()

        print('rs_pipeline:{}: Connection Open'.format(self._object_name))

    def close_connection(self):
        """
        Close connection to D435 camera
        """
        if self._pipe is None:
            return

        self._pipe.stop()
        self._pipe = None

        print('rs_pipeline:{}: Connection Closed'.format(self._object_name))

    def wait_for_frame(self) -> tuple:
        """
        Retrieve a data from the pipeline
        """
        try:
            frames = self._pipe.wait_for_frames()
        except RuntimeError as raised_exception:
            self._exception_handle("rs_pipeline:{}:wait_for_frame: Timeout waiting for data frame"
                                   .format(self._object_name))
            raise raised_exception

        frame = self._get_frame(frames)

        try:
            data = self._get_data(frame)
        except RuntimeError:
            self._exception_handle("rs_pipeline:{}:wait_for_frame: Frame contained no data"
                                   .format(self._object_name))
            return None

        # Post Process
        data = self._post_process(data)

        # End
        return data

    def _generate_config(self) -> rs.config:
        """
        OVERLOADED FUNCTION: Generate the pipeline config
        """
        raise NotImplementedError

    def _post_connect_process(self):
        """
        OVERLOADED FUNCTION: Process run after a succesful connection
        """
        return

    def _get_frame(self, frames):
        """
        OVERLOADED FUNCTION: Extract frame from rs.composite_frame
        """
        raise NotImplementedError

    def _get_data(self, frame):
        """
        OVERLOADED FUNCTION: Extract data from frame
        """
        return frame.get_data()

    def _post_process(self, data):
        """
        OVERLOADED FUNCTION: Process run on extractred frame data
        """
        return data

    def _exception_handle(self, err):
        """
        Function to collate interal class exceptions
        TODO: Log error - requires rabbit MQ stuff
        """
        print(err)

class DepthPipeline(RealsensePipeline):
    def __init__(self):
        super().__init__()

        # public
        self.depth_width = 640
        self.depth_height = 480

        self.framerate = 30

        # private
        self._object_name = 'Depth'

        self._intrin = None
        self._fov = (0, 0)

    def wait_for_frame(self) -> data_types.Depth:
        return super().wait_for_frame()

    def _generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(rs.stream.depth,
                          self.depth_width,
                          self.depth_height,
                          rs.format.z16,
                          self.framerate)
        return cfg

    def _post_connect_process(self):
        self._get_intrinsics()

    def _get_frame(self, frames):
        return frames.get_depth_frame()

    def _post_process(self, data):
        depth = np.asarray(data, dtype=np.uint16)
        return data_types.Depth(time.time(), depth, self._intrin)

    def get_fov(self) -> tuple:
        """
        Returns the FOV of the connected camera
        """
        return self._fov

    def _get_intrinsics(self):
        """
        Get camera intrinsics
        """
        profile = self._pipe.get_active_profile()

        intrin = profile.get_stream(rs.stream.depth) \
                        .as_video_stream_profile() \
                        .get_intrinsics()

        scale = profile.get_device() \
                        .first_depth_sensor() \
                        .get_depth_scale()

        self._intrin = data_types.Intrinsics(scale, intrin.ppx, intrin.ppy, intrin.fx, intrin.fy)

        self._fov = rs.rs2_fov(intrin)

class ColorPipeline(RealsensePipeline):
    def __init__(self):
        super().__init__()

        # public
        self.rgb_width = 640
        self.rgb_height = 480

        self.framerate = 30

        # private
        self._object_name = 'Color'

    def wait_for_frame(self) -> data_types.Color:
        return super().wait_for_frame()

    def _generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(rs.stream.color,
                          self.rgb_width,
                          self.rgb_height,
                          rs.format.bgr8,
                          self.framerate)
        return cfg

    def _get_frame(self, frames: rs.composite_frame):
        return frames.get_color_frame()

    def _post_process(self, data):
        image = np.asarray(data, dtype=np.uint8)

        return data_types.Color(time.time(), image)

class PosePipeline(RealsensePipeline):
    def __init__(self):
        super().__init__()

        # Public
        self.tilt_deg = 0
        self.north_offset = 0

        # Private
        self._object_name = 'Pose'

        self.h_aeroRef_T265Ref = None
        self.h_T265body_aeroBody = None

        self._initialise_rotational_transforms()

    def wait_for_frame(self) -> data_types.Pose:
        return super().wait_for_frame()

    def _generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(rs.stream.pose)
        return cfg

    def _get_frame(self, frames):
        return frames.get_pose_frame()

    def _get_data(self, frame):
        return frame.get_pose_data()

    def _post_process(self, data):
        pos = [data.translation.x,
               data.translation.y,
               data.translation.z]

        quat = [data.rotation.x,
                data.rotation.y,
                data.rotation.z,
                data.rotation.w]

        quat = self._convert_rotational_frame(quat)
        pos = self._convert_positional_frame(pos)

        return data_types.Pose(time.time(), pos, quat, data.tracker_confidence)

    def _initialise_rotational_transforms(self):
        """
        Initialise rotational transforms between tilted T265 and NED aero body and ref frames
        """
        h_aeroNEDRef_aeroRef = R.from_euler('z', self.north_offset, degrees=True)
        h_aeroRef_T265Ref = R.from_matrix([[0, 0, -1], [1, 0, 0], [0, -1, 0]])
        h_T265Tilt_T265Body = R.from_euler('x', self.tilt_deg, degrees=True)

        self.h_aeroRef_T265Ref = h_aeroNEDRef_aeroRef * h_aeroRef_T265Ref
        self.h_T265body_aeroBody = h_T265Tilt_T265Body * h_aeroRef_T265Ref.inv()

    def _convert_rotational_frame(self, quat) -> list:
        """
        Convert T265 rotational frame to aero NED frame
        """
        rot = self.h_aeroRef_T265Ref * R.from_quat(quat)  * self.h_T265body_aeroBody

        return rot.as_quat()

    def _convert_positional_frame(self, pos) -> list:
        """
        Convert T264 translation frame to aero NED translation
        """
        return self.h_aeroRef_T265Ref.apply(pos)

if __name__ == "__main__": #pragma: no cover
    import signal
    import threading

    def depth_loop():
        import cv2
        global RUNNING

        depth_obj = DepthPipeline()
        with depth_obj:
            while RUNNING:
                depth_frame = depth_obj.wait_for_frame()

                if depth_frame is None:
                    continue

                depth_frame = depth_frame.depth * depth_frame.intrin.scale
                depth_frame = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame, alpha=50),
                                                cv2.COLORMAP_JET)
                cv2.imshow('depth_frame', depth_frame)
                cv2.waitKey(1)

    def color_loop():
        import cv2
        global RUNNING

        color_obj = ColorPipeline()
        with color_obj:
            while RUNNING:
                color_frame = color_obj.wait_for_frame()

                if color_frame is None:
                    continue

                cv2.imshow('color_frame', color_frame.image)
                cv2.waitKey(1)

    def pose_loop():
        global RUNNING
        pose_obj = PosePipeline()
        with pose_obj:
            while RUNNING:
                pose_frame = pose_obj.wait_for_frame()

                if pose_frame is None:
                    continue

                print(pose_frame.translation)
                time.sleep(0.1)

    def stop_running(sig, frame):
        global RUNNING
        RUNNING = False

    global RUNNING
    RUNNING = True

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
