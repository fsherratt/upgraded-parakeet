#!/bin/python3
import rospy
import sys
import os
import pyrealsense2 as rs2
from cv_bridge import CvBridge, CvBridgeError
#Handle pointcloud class
from sensor_msgs.msg import PointCloud2, PointField
#Import method to convert point cloud to xyz points
from sensor_msgs import point_cloud2
import numpy as np

class PointCloudListener:
    def __init__( self, point_cloud_topic ):
        self.bridge = CvBridge();
        self.sub = rospy.Subscriber( point_cloud_topic, PointCloud2, self.pointCloudCallback);
        self.pointCloud = None;

    def pointCloudCallback( self, data ):
        print( data.header.seq );
        print( '--START_CORDS--' );
        # Create generator for iteration over point cloud.
        # gen = point_cloud2.read_points( data );
        gen = point_cloud2.read_points( data, skip_nans=True, field_names = ("x", "y", "z" ) );
        for p in gen:
            print( "x : %f, y: %f, z: %f" %(p[0], p[1], p[2]))
        print( '--END_CORDS--' );

def main():
    point_topic = '/camera/depth/color/points';
    print('')
    print('testing point cloud.py')
    print('----------------------')
    print('This is here to test how the subscriber works')

    listener = PointCloudListener( point_topic )
    rospy.spin()

if __name__ == '__main__':
    node_name = os.path.basename( sys.argv[ 0 ] ).split('.')[0];
    rospy.init_node( node_name );
    main();
