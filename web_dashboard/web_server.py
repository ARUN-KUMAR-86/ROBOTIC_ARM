#!/usr/bin/env python3
"""
High-Performance Web & MJPEG Video Streaming Server for Auron Robot Dashboard.
Serves:
  - Web UI at http://localhost:8080
  - Live Robot Camera MJPEG Stream at http://localhost:8080/stream/camera
  - Live AI Computer Vision Stream at http://localhost:8080/stream/vision
  - Camera Snapshot download at http://localhost:8080/api/camera_snapshot
  - Live Target Detection API at http://localhost:8080/api/detections
  - Health & Bridge Diagnostics at http://localhost:8080/api/health
"""

import http.server
import json
import os
import socket
import sys
import threading
import time
import cv2
import numpy as np

PORT = 8080
WEB_DIR = os.path.dirname(os.path.abspath(__file__))

# Global frame buffers and locks
frame_lock = threading.Lock()
latest_camera_jpeg = None
latest_vision_jpeg = None
latest_camera_timestamp = 0
latest_vision_timestamp = 0
latest_detections_data = {"timestamp": 0, "count": 0, "detections": []}

def make_placeholder_frame(title="AURON OPTICAL SENSOR", subtitle="Awaiting live stream on /camera/image_raw..."):
    """Generate a crisp cyberpunk standby frame with crosshairs and diagnostic grid."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Dark blue-navy background
    img[:] = (24, 18, 14)

    # Grid overlay
    for x in range(0, 640, 40):
        cv2.line(img, (x, 0), (x, 480), (38, 30, 24), 1)
    for y in range(0, 480, 40):
        cv2.line(img, (0, y), (640, y), (38, 30, 24), 1)

    # Glowing reticle
    center = (320, 240)
    cv2.circle(img, center, 75, (255, 229, 0), 2)     # Cyan
    cv2.circle(img, center, 78, (255, 140, 0), 1)     # Outer accent
    cv2.circle(img, center, 6, (255, 229, 0), -1)

    # Reticle ticks
    cv2.line(img, (230, 240), (280, 240), (255, 229, 0), 2)
    cv2.line(img, (360, 240), (410, 240), (255, 229, 0), 2)
    cv2.line(img, (320, 150), (320, 200), (255, 229, 0), 2)
    cv2.line(img, (320, 280), (320, 330), (255, 229, 0), 2)

    # Corner brackets
    def corner(x, y, dx, dy):
        cv2.line(img, (x, y), (x + dx, y), (0, 229, 255), 2)
        cv2.line(img, (x, y), (x, y + dy), (0, 229, 255), 2)
    corner(40, 40, 30, 30)
    corner(600, 40, -30, 30)
    corner(40, 440, 30, -30)
    corner(600, 440, -30, -30)

    # Branding & Status Text
    cv2.putText(img, "AURON ROBOTICS // OPTICAL PIPELINE", (50, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 229, 255), 2, cv2.LINE_AA)
    cv2.putText(img, title, (320 - len(title)*9, 370),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, subtitle, (320 - len(subtitle)*5, 405),
                cv2.FONT_HERSHEY_SIMPLEX, 0.50, (180, 180, 180), 1, cv2.LINE_AA)

    # Timestamp badge
    t_str = time.strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(img, f"STANDBY - {t_str}", (50, 435),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 140, 160), 1, cv2.LINE_AA)

    _, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return buf.tobytes()

DEFAULT_PLACEHOLDER = make_placeholder_frame()

def start_ros2_subscriber():
    """Background ROS 2 node to capture camera and vision frames."""
    try:
        import rclpy
        from rclpy.node import Node
        from sensor_msgs.msg import Image as RosImage
        from std_msgs.msg import String as RosString
        from cv_bridge import CvBridge

        if not rclpy.ok():
            rclpy.init(args=None)

        node = Node('auron_web_streamer')
        bridge = CvBridge()

        def camera_callback(msg):
            global latest_camera_jpeg, latest_camera_timestamp
            try:
                cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                ret, buf = cv2.imencode('.jpg', cv_img, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    with frame_lock:
                        latest_camera_jpeg = buf.tobytes()
                        latest_camera_timestamp = time.time()
            except Exception as e:
                pass

        def vision_callback(msg):
            global latest_vision_jpeg, latest_vision_timestamp
            try:
                cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                ret, buf = cv2.imencode('.jpg', cv_img, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    with frame_lock:
                        latest_vision_jpeg = buf.tobytes()
                        latest_vision_timestamp = time.time()
            except Exception as e:
                pass

        def detections_callback(msg):
            global latest_detections_data
            try:
                data = json.loads(msg.data)
                with frame_lock:
                    latest_detections_data = data
            except Exception:
                pass

        node.create_subscription(RosImage, '/camera/image_raw', camera_callback, 10)
        node.create_subscription(RosImage, '/vision/detection_image', vision_callback, 10)
        node.create_subscription(RosString, '/vision/detections', detections_callback, 10)

        print("[Streamer] ROS 2 frame listeners active on /camera/image_raw & /vision/detection_image")
        rclpy.spin(node)
    except Exception as e:
        print(f"[Streamer] ROS 2 streaming listener encountered note: {e}")


class StreamHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        # 0. Favicon
        if self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        # 1. API Health Check
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Check rosbridge port
            rosbridge_up = False
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.3)
                s.connect(('127.0.0.1', 9090))
                s.close()
                rosbridge_up = True
            except Exception:
                rosbridge_up = False

            with frame_lock:
                cam_age = time.time() - latest_camera_timestamp if latest_camera_timestamp else 999.0
                vis_age = time.time() - latest_vision_timestamp if latest_vision_timestamp else 999.0

            data = {
                'status': 'online',
                'dashboard_port': PORT,
                'rosbridge_connected': rosbridge_up,
                'rosbridge_url': 'ws://localhost:9090',
                'camera_active': cam_age < 3.0,
                'vision_active': vis_age < 3.0,
                'camera_latency_sec': round(cam_age, 2) if cam_age < 999 else None,
                'message': 'Auron Web Controller & Video Streamer Active'
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        # 2. API Live Detections
        if self.path == '/api/detections':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with frame_lock:
                data = latest_detections_data
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        # 3. API Camera Snapshot (Download image)
        if self.path == '/api/camera_snapshot':
            with frame_lock:
                frame = latest_camera_jpeg or DEFAULT_PLACEHOLDER
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Disposition', 'attachment; filename="auron_camera_snapshot.jpg"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(frame)
            return

        # 4. Live MJPEG Camera Stream
        if self.path.startswith('/stream/camera') or self.path.startswith('/stream/vision'):
            is_vision = '/stream/vision' in self.path
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            try:
                while True:
                    with frame_lock:
                        if is_vision:
                            frame = latest_vision_jpeg or latest_camera_jpeg or DEFAULT_PLACEHOLDER
                        else:
                            frame = latest_camera_jpeg or DEFAULT_PLACEHOLDER

                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
                    time.sleep(0.033)  # ~30 FPS
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        # Standard file serving
        super().do_GET()

    def end_headers(self):
        # Prevent caching for dynamic development
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()


def run_server():
    os.chdir(WEB_DIR)

    # Start background ROS 2 frame listener
    ros_thread = threading.Thread(target=start_ros2_subscriber, daemon=True)
    ros_thread.start()

    http.server.ThreadingHTTPServer.allow_reuse_address = True
    try:
        with http.server.ThreadingHTTPServer(("", PORT), StreamHandler) as httpd:
            print("=" * 65)
            print("  AURON ROBOTICS - DASHBOARD & LIVE STREAM SERVER")
            print("=" * 65)
            print(f"  Web Dashboard:  http://localhost:{PORT}")
            print(f"  Live Camera:    http://localhost:{PORT}/stream/camera")
            print(f"  Vision Stream:  http://localhost:{PORT}/stream/vision")
            print(f"  ROS 2 Bridge:   ws://localhost:9090")
            print("=" * 65)
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"[WARN] Port {PORT} in use. Terminate prior instance first.")
        else:
            raise e


if __name__ == '__main__':
    run_server()
