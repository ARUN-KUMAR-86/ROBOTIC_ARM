#!/usr/bin/env python3
"""
Camera Publisher Node for Auron Robot.
Captures frames from Linux V4L2 device (e.g. /dev/video0) using OpenCV
and publishes sensor_msgs/Image and sensor_msgs/CameraInfo to ROS 2 topics.
"""

import os
import cv2
import yaml
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge

class AuronCameraNode(Node):
    def __init__(self):
        super().__init__('auron_camera_node')

        # Declare parameters
        self.declare_parameter('camera_device', '/dev/video0')
        self.declare_parameter('image_width', 640)
        self.declare_parameter('image_height', 480)
        self.declare_parameter('frame_rate', 30.0)
        self.declare_parameter('frame_id', 'camera_optical_frame')
        self.declare_parameter('calibration_file', '')

        self.device_str = self.get_parameter('camera_device').value
        self.width = self.get_parameter('image_width').value
        self.height = self.get_parameter('image_height').value
        self.fps = self.get_parameter('frame_rate').value
        self.frame_id = self.get_parameter('frame_id').value
        calib_file = self.get_parameter('calibration_file').value

        self.bridge = CvBridge()
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)

        # Parse device id (if numeric or path)
        if self.device_str.startswith('/dev/video'):
            try:
                self.device_index = int(self.device_str.replace('/dev/video', ''))
            except ValueError:
                self.device_index = self.device_str
        else:
            try:
                self.device_index = int(self.device_str)
            except ValueError:
                self.device_index = self.device_str

        # Check if device exists before opening
        device_exists = True
        if str(self.device_str).startswith('/dev/'):
            device_exists = os.path.exists(self.device_str)

        self.cap = None
        self.camera_available = False

        if not device_exists:
            print("Camera: NOT AVAILABLE")
            self.get_logger().warn("Camera: NOT AVAILABLE")
        else:
            self.get_logger().info(f"Connecting to camera device: {self.device_str} (index: {self.device_index})")
            try:
                self.cap = cv2.VideoCapture(self.device_index)
                if not self.cap.isOpened():
                    print("Camera: NOT AVAILABLE")
                    self.get_logger().warn(f"Could not open camera {self.device_str}! Camera: NOT AVAILABLE")
                    self.camera_available = False
                else:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                    self.camera_available = True
                    self.get_logger().info(f"Camera opened successfully: {self.width}x{self.height} @ {self.fps} FPS")
            except Exception as e:
                print("Camera: NOT AVAILABLE")
                self.get_logger().warn(f"Camera error ({e}): Camera: NOT AVAILABLE")
                self.camera_available = False

        # Load calibration if provided
        self.camera_info_msg = self.build_camera_info(calib_file)

        # Timer loop
        timer_period = 1.0 / max(1.0, self.fps)
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def build_camera_info(self, calib_file):
        info = CameraInfo()
        info.header.frame_id = self.frame_id
        info.width = self.width
        info.height = self.height

        if calib_file and os.path.exists(calib_file):
            try:
                with open(calib_file, 'r') as f:
                    data = yaml.safe_load(f)
                    info.k = data.get('camera_matrix', {}).get('data', [500.0, 0, 320.0, 0, 500.0, 240.0, 0, 0, 1.0])
                    info.d = data.get('distortion_coefficients', {}).get('data', [0.0, 0.0, 0.0, 0.0, 0.0])
                    info.r = data.get('rectification_matrix', {}).get('data', [1.0, 0, 0, 0, 1.0, 0, 0, 0, 1.0])
                    info.p = data.get('projection_matrix', {}).get('data', [500.0, 0, 320.0, 0, 0, 500.0, 240.0, 0, 0, 0, 1.0, 0])
                    info.distortion_model = data.get('distortion_model', 'plumb_bob')
                    self.get_logger().info(f"Loaded calibration from {calib_file}")
                    return info
            except Exception as e:
                self.get_logger().warn(f"Failed to parse calibration file: {e}")

        # Default pinhole model
        fx = fy = float(self.width)
        cx = self.width / 2.0
        cy = self.height / 2.0
        info.distortion_model = 'plumb_bob'
        info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        info.k = [fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0]
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.p = [fx, 0.0, cx, 0.0, 0.0, fy, cy, 0.0, 0.0, 0.0, 1.0, 0.0]
        return info

    def timer_callback(self):
        stamp = self.get_clock().now().to_msg()

        if not self.camera_available:
            self.get_logger().warn("Camera: NOT AVAILABLE", throttle_duration_sec=10.0)
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.get_logger().warn("Frame read failed from device", throttle_duration_sec=5.0)
            return

        # Publish real image
        img_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        img_msg.header.stamp = stamp
        img_msg.header.frame_id = self.frame_id
        self.image_pub.publish(img_msg)

        # Publish camera info
        self.camera_info_msg.header.stamp = stamp
        self.info_pub.publish(self.camera_info_msg)

    def destroy_node(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = AuronCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
