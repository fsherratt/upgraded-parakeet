import traceback
import sys
import time
import pyrealsense2 as rs
from scipy.spatial.transform import Rotation as R

class rs_t265:
    """
    Initialise variables for T265 camera
    """
    def __init__(self):
        # Public
        self.tilt_deg = 0
        self.North_offset = 0

        # Private
        self._pipe = None
        self.H_aeroRef_T265Ref = None
        self.H_T265body_aeroBody = None
        
        self._initialise_rotational_transforms()

    """
    With __enter__ method opens a connected to the T265 camera
    """
    def __enter__(self):
        self.open_connection()

    """
    With __exit__ method closes the connection to the T265 camera
    """
    def __exit__(self, exception_type, exception_value, traceback):
        if traceback:
            print(traceback.tb_frame)
            self._exception_handle("rs_t265: __exit__: `{}`".format(exception_value))

        self.close_connection()

    """
    Open a connected to the T265 camera
    """
    def open_connection(self):
        cfg = rs.config()
        cfg.enable_stream(rs.stream.pose)

        self._pipe = rs.pipeline()

        try:
            self._pipe.start(cfg)
        except TimeoutError as e:
            self._exception_handle("rs_t265: getFrame: failed to connect to camera")
            raise e

        print('rs_t265:T265 Connection Open')

    """
    Close connected to the T265 camera
    """
    def close_connection(self):
        if self._pipe is None:
            return

        self._pipe.stop()
        self._pipe = None

        print('rs_t265:T265 Connection Closed')

    """
    Retrieve a data from the T265 camera
    """
    def get_frame(self) -> tuple:
        try:
            frames = self._pipe.wait_for_frames()
        except TimeoutError as e:
            self._exception_handle("rs_t265: getFrame: timeout waiting for data frame")
            raise e

        pose = frames.get_pose_frame()

        try:
            data = pose.get_pose_data()
        except AttributeError:
            self._exception_handle("rs_t265: getFrame: pose frame contains no data")
            return None

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

        return (time.time(), pos, quat, conf)

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

    """
    Function to collate interal class exceptions
    TODO: Log error - requires rabbit MQ stuff
    """
    def _exception_handle(self, err):
        print(err)

if __name__ == "__main__": #pragma: no cover
    t265Obj = rs_t265()

    with t265Obj:
        while True:
            data_frame = t265Obj.get_frame()

            print( ' Pos: {}\t Quat: {}\t Conf:{}'.format(
                    data_frame[1], 
                    data_frame[2], 
                    data_frame[3]) )

            time.sleep(0.5)
