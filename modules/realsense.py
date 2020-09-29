"""
Realsense stream connection modules - abstracts the pyrealsense API
"""
import time

import cv2
import numpy as np
import pyrealsense2 as rs
from scipy.spatial.transform import Rotation as R

from modules.utils import load_config, cli_parser

from modules.__context import definitions
from definitions import data_types


class RealsensePipeline:
    """
    Parent class for all realsense stream classes
    """

    def __init__(self, config_file=None, debug=False):
        """
        Declare all the constants, tunable variables are public
        """
        # private
        self._pipe = None
        self._object_name = "Untitled"

        self.debug = debug
        self.conf = load_config.from_file(config_file)

    def __enter__(self):
        """
        with enter method opens realsense connection
        """
        self.open_connection()

    def __exit__(self, exception_type, exception_value, traceback):
        """
        with exit method closes the realsense connection
        """
        if traceback:
            print(traceback.tb_frame)
            self._exception_handle(
                "rs_pipeline: __exit__: `{}`".format(exception_value)
            )

        self.close_connection()

    def open_connection(self):
        """
        Open Connection to realsense camera
        """
        self._pipe = rs.pipeline()
        cfg = self._generate_config()

        try:
            self._pipe.start(cfg)
        except RuntimeError as raised_exception:
            self._exception_handle(
                "rs_pipeline:{}: failed to connect to camera".format(self._object_name)
            )
            raise raised_exception

        self._post_connect_process()

        print("rs_pipeline:{}: Connection Open".format(self._object_name))

    def close_connection(self):
        """
        Close connection to Realsense camera
        """
        if self._pipe is None:
            return

        try:
            self._pipe.stop()
        except RuntimeError:
            pass
        finally:
            self._pipe = None

        print("rs_pipeline:{}: Connection Closed".format(self._object_name))

    def wait_for_frame(self) -> tuple:
        """
        Retrieve a data from the pipeline
        """
        try:
            frames = self._pipe.wait_for_frames()
        except RuntimeError as raised_exception:
            self._exception_handle(
                "rs_pipeline:{}:wait_for_frame: Timeout waiting for data frame".format(
                    self._object_name
                )
            )
            raise raised_exception

        frame = self._get_frame(frames)

        try:
            data = self._get_data(frame)
        except RuntimeError:
            self._exception_handle(
                "rs_pipeline:{}:wait_for_frame: Frame contained no data".format(
                    self._object_name
                )
            )
            return None

        # Post Process
        data = self._post_process(data)

        if self.debug:
            self._debug_output(data)

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

    def _debug_output(self, data):
        raise NotImplementedError


class DepthPipeline(RealsensePipeline):
    """
    D435 depth stream realsense class
    """

    def __init__(self, config_file="conf/realsense.yaml", debug=False):
        super().__init__(config_file, debug)

        # private
        self._object_name = self.conf.realsense.depth.object_name

        self._intrin = None
        self._fov = (0, 0)

    def wait_for_frame(self) -> data_types.Depth:
        return super().wait_for_frame()

    def _generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(
            rs.stream.depth,
            self.conf.realsense.depth.width,
            self.conf.realsense.depth.height,
            rs.format.z16,
            self.conf.realsense.depth.framerate,
        )
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
        sensor = profile.get_device().first_depth_sensor()

        time.sleep(1)
        sensor.set_option(
            rs.option.visual_preset, self.conf.realsense.depth.visual_preset
        )

        intrin = (
            profile.get_stream(rs.stream.depth)
            .as_video_stream_profile()
            .get_intrinsics()
        )

        scale = sensor.get_depth_scale()

        self._intrin = data_types.Intrinsics(
            scale, intrin.ppx, intrin.ppy, intrin.fx, intrin.fy
        )

        self._fov = rs.rs2_fov(intrin)

    def _debug_output(self, data: data_types.Depth):
        depth = data.depth * data.intrin.scale
        depth = cv2.applyColorMap(
            cv2.convertScaleAbs(depth, alpha=75), cv2.COLORMAP_JET
        )

        cv2.imshow("realsense_depth", depth)
        cv2.waitKey(1)


class ColorPipeline(RealsensePipeline):
    """
    D435 RGB color stream realsense class
    """

    def __init__(self, config_file="conf/realsense.yaml", debug=False):
        super().__init__(config_file, debug)

        # private
        self._object_name = self.conf.realsense.color.object_name

    def wait_for_frame(self) -> data_types.Color:
        return super().wait_for_frame()

    def _generate_config(self) -> rs.config:
        cfg = rs.config()
        cfg.enable_stream(
            rs.stream.color,
            self.conf.realsense.color.width,
            self.conf.realsense.color.height,
            rs.format.bgr8,
            self.conf.realsense.color.framerate,
        )
        return cfg

    def _get_frame(self, frames: rs.composite_frame):
        return frames.get_color_frame()

    def _post_process(self, data):
        image = np.asarray(data, dtype=np.uint8)

        return data_types.Color(time.time(), image)

    def _debug_output(self, data: data_types.Color):
        cv2.imshow("realsense_color", data.image)
        cv2.waitKey(1)


class PosePipeline(RealsensePipeline):
    """
    T265 pose stream realsense class
    """

    def __init__(self, config_file="conf/realsense.yaml", debug=False):
        super().__init__(config_file, debug)

        # Private
        self._object_name = self.conf.realsense.pose.object_name

        self._north_offset_deg = 0
        self._tilt_deg = 0

        self.h_aeroref_t265ref = None
        self.h_t265body_aerobody = None

        self.set_tilt_offset(self.conf.realsense.pose.tilt_deg)

    def wait_for_frame(self) -> data_types.Pose:
        return super().wait_for_frame()

    def set_north_offset(self, offset):
        self._north_offset_deg = offset
        self._initialise_rotational_transforms()

    def set_tilt_offset(self, offset):
        self._tilt_deg = offset
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
        pos = [data.translation.x, data.translation.y, data.translation.z]

        quat = [data.rotation.x, data.rotation.y, data.rotation.z, data.rotation.w]

        quat = self._convert_rotational_frame(quat)
        pos = self._convert_positional_frame(pos)

        return data_types.Pose(time.time(), pos, quat, data.tracker_confidence)

    def _initialise_rotational_transforms(self):
        """
        Initialise rotational transforms between tilted T265 and NED aero body and ref frames
        """
        h_aeroNEDref_aeroref = R.from_euler("z", self._north_offset_deg, degrees=True)
        h_aeroref_t265ref = R.from_matrix([[0, 0, -1], [1, 0, 0], [0, -1, 0]])
        h_t265tilt_t265body = R.from_euler("x", self._tilt_deg, degrees=True)

        self.h_aeroref_t265ref = h_aeroNEDref_aeroref * h_aeroref_t265ref
        self.h_t265body_aerobody = h_t265tilt_t265body * h_aeroref_t265ref.inv()

    def _convert_rotational_frame(self, quat) -> list:
        """
        Convert T265 rotational frame to aero NED frame
        """
        rot = self.h_aeroref_t265ref * R.from_quat(quat) * self.h_t265body_aerobody

        return rot.as_quat()

    def _convert_positional_frame(self, pos) -> list:
        """
        Convert T265 translation frame to aero NED translation
        """
        return self.h_aeroref_t265ref.apply(pos)

    def _debug_output(self, data: data_types.Pose):
        print(
            "Pos:{}\tQuat:{}\tConf:{}".format(
                data.translation, data.quaternion, data.conf
            )
        )


if __name__ == "__main__":
    cli_args = cli_parser.parse_cli_input()

    # CLI arguments are optional, a keyword argument dictionary is the
    # simplest way to achieve optional arguments without overriding defaults
    object_arguments = {}

    if cli_args.config is not None:
        object_arguments["config_file"] = cli_args.config
    else:
        object_arguments["config_file"] = "conf/realsense.yaml"

    if cli_args.debug is not None:
        object_arguments["debug"] = cli_args.debug

    realsense = None
    # Setup realsense object
    if cli_args.process == "rs_depth":
        realsense = DepthPipeline(**object_arguments)
    elif cli_args.process == "rs_color":
        realsense = ColorPipeline(**object_arguments)
    elif cli_args.process == "rs_pose":
        realsense = PosePipeline(**object_arguments)
    else:
        raise Warning("Incorrect realsense module specified")

    # Open connection and stream data
    try:
        realsense.open_connection()

        while True:
            data = realsense.wait_for_frame()
            # TODO: add in data streaming

    except KeyboardInterrupt:
        pass

    # Clean up and close
    finally:
        realsense.close_connection()
