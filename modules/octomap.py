from time import sleep

import rospy
from sensor_msgs.msg import Image, CameraInfo, PointCloud2
from nav_msgs.msg import Odometry
from dynamic_reconfigure.msg import Config

import dynamic_reconfigure.client

import cv2
from cv_bridge import CvBridge


def callback(data):
    bridge = CvBridge()
    image = bridge.imgmsg_to_cv2(data)
    image = image * 0.001

    # image = cv2.resize(image, (640, 360), interpolation=cv2.INTER_AREA)

    depth = cv2.applyColorMap(cv2.convertScaleAbs(image, alpha=120), cv2.COLORMAP_JET)

    cv2.imshow("depth image", depth)
    cv2.waitKey(3)


if __name__ == "__main__":
    rospy.init_node("pointcloud_listener", anonymous=True)

    # Get camera info
    # "/d400/depth/camera_info", CameraInfo
    #     [fx  0 cx]
    # K = [ 0 fy cy]
    #     [ 0  0  1]

    # Subscribe to D435 cloud and T265 pose
    # "/d400/depth/color/points", PointCloud2
    # "/t265/odom/sample", Odometry

    # Apply transform to points to convert from Local to Global FRD ref frame

    # Publish as new point cloud

    # Setup
    stereo_client = dynamic_reconfigure.client.Client("/d400/stereo_module", timeout=5)
    stereo_client.update_configuration(
        {"visual_preset": 3, "enable_auto_exposure": True}
    )  # Visual_preset = 3 (High accuracy)

    # stereo_client.update_configuration({"hdr_enabled": True,})

    decimation_client = dynamic_reconfigure.client.Client("/d400/decimation", timeout=5)
    decimation_client.update_configuration({"filter_magnitude": 8})

    sub = rospy.Subscriber("/d400/depth/image_rect_raw", Image, callback, queue_size=1)

    rospy.spin()
    sub.unregister()
