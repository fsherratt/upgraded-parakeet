import pyrealsense2 as rs
import traceback
import sys

import numpy as np
from scipy.spatial.transform import Rotation as R

class unexpectedDisconnect( Exception):
    # Camera unexpectably disconnected
    pass

class rs_t265:
    def __init__(self):
        
        # Setup variables
        self.pipe = None
        self.cfg = None

        # Adjust yaw to align north
        # self.rot_offset = [[0,0,-1],[1,0,0],[0,-1,0]] # Forward Facing, USB to right

        self.rot_offset = [0, 1/np.sqrt(2), -1/np.sqrt(2)], [1, 0, 0], [0, -1/np.sqrt(2), -1/np.sqrt(2)] # 45 degree

        self.ROffset = R.from_dcm(self.rot_offset)
        self.H_aeroRef_T265Ref = [ 0.,  0., -1.],        [ 1.,  0.,  0.],        [ 0., -1.,  0.]
        # self.ROffset = R.from_euler([])

        # self.H_aeroRef_T265Ref = [[0,0,-1],[1,0,0],[0,-1,0]] # Forward Facing, USB to right
        # self.H_T265body_aeroBody = [[0,1,0],[1,0,0],[0,0,-1]]
        # self.H_aeroRef_T265Ref = R.from_dcm(self.H_aeroRef_T265Ref)
        # self.H_T265body_aeroBody = R.from_dcm(self.H_T265body_aeroBody)

    def __enter__(self):
        self.openConnection()

    def __exit__(self, exception_type, exception_value, traceback):
        if traceback:
            print(traceback.tb_frame)

        self.closeConnection()

    def openConnection(self):
        # Declare RealSense pipeline, encapsulating the actual device and sensors
        self.pipe = rs.pipeline()

        # Build config object and request pose data
        self.cfg = rs.config()
        self.cfg.enable_stream(rs.stream.pose)
        # How set frame rate, how select data

        # Start streaming with requested config
        self.pipe.start(self.cfg)

        print('rs_t265:T265 Connection Open')

    def closeConnection(self):
        self.pipe.stop()

        print('rs_t265:T265 Connection Closed')

    def getFrame(self):
        # Wait for new frame
        try:
            frames = self.pipe.wait_for_frames()
        except RuntimeError as e:
            traceback.print_exc(file=sys.stdout)
            raise unexpectedDisconnect( e )

        # Fetch data
        pose = frames.get_pose_frame()

        if pose:
            data = pose.get_pose_data()

            pos = np.asarray([data.translation.x, data.translation.y, data.translation.z],dtype=np.float)
            quat = [data.rotation.x, data.rotation.y, data.rotation.z, data.rotation.w]
            conf = data.tracker_confidence

            # Calculate Euler angles from Quat - Quat is WXYZ
            rot = R.from_quat( quat )

            # Convert from camera body to aero body and reference frame to aero ref
            rot = R.from_euler('y', [45], degrees=True) * self.ROffset * rot * self.ROffset.inv()
            # rot = self.H_aeroRef_T265Ref * rot * self.H_T265body_aeroBody

            # Apply pixhawk rotational offset
            # pos = self.ROffset.apply(pos)
            pos = [-pos[2], pos[0], -pos[1]]

            return pos, rot, conf

        return None

    def calcNorthOffset( self, t265Yaw, pixYaw ):
        # Implement some form of gradient descent method to correct for yaw offset
        pass

if __name__ == "__main__":
    import time
    
    t265Obj = rs_t265()

    with t265Obj:
        while True:
            pos, r, conf = t265Obj.getFrame()
            eul = r.as_euler('xyz', degrees=True)

            # print(i, pos, conf)

            print( 'Pos: {}\t Eul: {}\t Conf:{}'.format(pos, eul, conf) )

            time.sleep(0.5)