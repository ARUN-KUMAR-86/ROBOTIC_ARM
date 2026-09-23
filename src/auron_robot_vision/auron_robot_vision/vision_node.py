#!/usr/bin/env python3
"""
Computer Vision Node for Auron Robot.
Processes /camera/image_raw, detects target objects (red cube, blue cube, green cylinder),
projects 2D pixel coordinates to 3D camera coordinates using camera intrinsics,
broadcasts TF transforms, and publishes debug visualization image.
"""

import json
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import TransformStamped
from std_msgs.msg import String
from cv_bridge import CvBridge
from tf2_ros import TransformBroadcaster
import cv2

from auron_robot_vision.detectors import ColorBlobDetector, AIDetector

class AuronVisionNode(Node):
    def __init__(self):
        super().__init__('auron_vision_node')

        # Parameters
        self.declare_parameter('detector_type', 'color') # 'color' or 'ai'
        self.declare_parameter('min_contour_area', 300)
        self.declare_parameter('estimated_object_distance', 0.45) # meters (table height relative to camera)
        self.declare_parameter('enable_gui_display', False)

        detector_type = self.get_parameter('detector_type').value
        min_area = self.get_parameter('min_contour_area').value
        self.z_dist = self.get_parameter('estimated_object_distance').value
        self.show_gui = self.get_parameter('enable_gui_display').value

        if detector_type == 'ai':
            self.detector = AIDetector()
            self.get_logger().info("Using AI object detector interface")
        else:
            self.detector = ColorBlobDetector(min_area=min_area)
            self.get_logger().info("Using OpenCV Color Segmentation detector")

        self.bridge = CvBridge()
        self.camera_info = None

        # Subscriptions
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10
        )
        self.info_sub = self.create_subscription(
            CameraInfo, '/camera/camera_info', self.info_callback, 10
        )

        # Publishers
        self.vis_pub = self.create_publisher(Image, '/vision/detection_image', 10)
        self.detection_pub = self.create_publisher(String, '/vision/detections', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.get_logger().info("Auron Vision Node initialized and listening on /camera/image_raw")

    def info_callback(self, msg: CameraInfo):
        self.camera_info = msg

    def image_callback(self, msg: Image):
        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"cv_bridge conversion error: {e}")
            return

        # Run detection
        results = self.detector.detect(cv_img)

        # Visualization canvas
        vis_img = cv_img.copy()
        detections_data = []

        # Intrinsics
        fx = 500.0
        fy = 500.0
        cx0 = float(cv_img.shape[1] / 2.0)
        cy0 = float(cv_img.shape[0] / 2.0)
        if self.camera_info is not None and len(self.camera_info.k) >= 9:
            fx = self.camera_info.k[0] or fx
            fy = self.camera_info.k[4] or fy
            cx0 = self.camera_info.k[2] or cx0
            cy0 = self.camera_info.k[5] or cy0

        for det in results:
            x, y, w, h = det.bbox
            u, v = det.center_pixel

            # 3D ray projection in camera coordinate frame
            X_cam = (u - cx0) * self.z_dist / fx
            Y_cam = (v - cy0) * self.z_dist / fy
            Z_cam = self.z_dist

            detections_data.append({
                'class': det.class_name,
                'confidence': round(det.confidence, 3),
                'pixel_coords': [round(u, 1), round(v, 1)],
                'camera_coords_3d': [round(X_cam, 3), round(Y_cam, 3), round(Z_cam, 3)],
            })

            # Broadcast TF transform for detected object
            tf_msg = TransformStamped()
            tf_msg.header.stamp = self.get_clock().now().to_msg()
            tf_msg.header.frame_id = 'camera_optical_frame'
            tf_msg.child_frame_id = f"detected_{det.class_name}"
            tf_msg.transform.translation.x = float(X_cam)
            tf_msg.transform.translation.y = float(Y_cam)
            tf_msg.transform.translation.z = float(Z_cam)
            tf_msg.transform.rotation.w = 1.0
            self.tf_broadcaster.sendTransform(tf_msg)

            # Draw visual bounding box and crosshair
            color = (0, 255, 0)
            if 'red' in det.class_name:
                color = (0, 0, 255)
            elif 'blue' in det.class_name:
                color = (255, 100, 0)
            elif 'green' in det.class_name:
                color = (0, 255, 100)

            cv2.rectangle(vis_img, (x, y), (x + w, y + h), color, 2)
            cv2.circle(vis_img, (int(u), int(v)), 4, (0, 255, 255), -1)
            label = f"{det.class_name} ({det.confidence:.2f})"
            cv2.putText(vis_img, label, (x, max(20, y - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            coords_label = f"({X_cam:.2f}, {Y_cam:.2f}, {Z_cam:.2f})m"
            cv2.putText(vis_img, coords_label, (x, y + h + 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        # Publish detection telemetry JSON
        det_msg = String()
        det_msg.data = json.dumps({
            'timestamp': msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
            'count': len(results),
            'detections': detections_data
        })
        self.detection_pub.publish(det_msg)

        # Publish annotated image
        out_msg = self.bridge.cv2_to_imgmsg(vis_img, encoding='bgr8')
        out_msg.header = msg.header
        self.vis_pub.publish(out_msg)

        if self.show_gui:
            cv2.imshow("Auron Vision Feed", vis_img)
            cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = AuronVisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
