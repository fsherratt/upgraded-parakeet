import traceback
import sys
import time

import pyrealsense2 as rs

class rs_t265:
    """
    Initialise variables for T265 camera
    """
    def __init__(self):
        # Private
        self._pipe = None

    """
    with __enter__ method opens a connected to the T265 camera
    """
    def __enter__(self):
        self.open_connection()

    """
    with __exit__ method closes the connection to the T265 camera
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

        quat = self._convert_coordinate_frame(quat)

        return (time.time(), pos, quat, conf)

    """
    TODO: Add method to convert to FED coordinates
    """
    def _convert_coordinate_frame(self, quat) -> list:
        return quat

if __name__ == "__main__":   
    t265Obj = rs_t265()

    with t265Obj:
        while True:
            data_frame = t265Obj.get_frame()

            print( ' Pos: {}\t Quat: {}\t Conf:{}'.format(
                    data_frame[1], 
                    data_frame[2], 
                    data_frame[3]) )

            time.sleep(0.5)