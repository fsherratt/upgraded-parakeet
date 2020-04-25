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

        # Private
        self._pipe = None
        
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

        self.close_connection()

    """
    Open a connected to the T265 camera
    """
    def open_connection(self):
        cfg = rs.config()
        cfg.enable_stream(rs.stream.pose)

        self._pipe = rs.pipeline()

        # TODO: Add in timeout exception handling
        self._pipe.start(cfg)
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
        # TODO: add in timeout exception handling
        frames = self._pipe.wait_for_frames()

        pose = frames.get_pose_frame()

        try:
            data = pose.get_pose_data()
        except AttributeError:
            # TODO: error about no data in frame
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
    TODO: Add comments and test
    TODO: Add method to convert to NED coordinates
    """
    def _initialise_rotational_transforms(self):
        self.H_aeroRef_T265Ref = [[0,0,-1],[1,0,0],[0,-1,0]]
        self.H_aeroRef_T265Ref = R.from_matrix(self.H_aeroRef_T265Ref)

        self.H_T265body_aeroBody = R.from_euler('x', self.tilt_deg, degrees=True) * self.H_aeroRef_T265Ref.inv()

    """
    TODO: Add comments and test
    TODO: Add method to convert to NED coordinates
    """
    def _convert_rotational_frame(self, quat) -> list:
        rot = self.H_aeroRef_T265Ref * R.from_quat(quat)  * self.H_T265body_aeroBody

        return rot.as_quat()

    """
    TODO: Add comments and test
    TODO: Add method to convert to NED coordinates
    """
    def _convert_positional_frame(self, pos) -> list:
        return self.H_aeroRef_T265Ref.apply(np.asarray(pos))

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
