# Camera Integration & Calibration Guide

## 1. Laptop Camera Driver (`auron_robot_camera`)

The camera package connects to native Linux Video4Linux2 devices (typically `/dev/video0`) using OpenCV's video backend.

### Parameters
- `camera_device`: Path to video device or device integer index (default: `/dev/video0`).
- `image_width`: Image frame horizontal pixels (default: `640`).
- `image_height`: Image frame vertical pixels (default: `480`).
- `frame_rate`: Capture rate in Hertz (default: `30.0`).
- `frame_id`: ROS 2 coordinate frame for camera optical center (default: `camera_optical_frame`).
- `calibration_file`: Path to YAML file containing camera intrinsic parameters.

### Standby Pattern Mode
If `/dev/video0` is disconnected or busy, `auron_camera_node` does not crash; instead, it automatically generates a simulated test pattern on `/camera/image_raw` allowing vision and RViz pipelines to be verified without physical hardware.

---

## 2. Viewing the Camera Stream in RViz2

1. Launch RViz2:
   ```bash
   rviz2
   ```
2. Click **Add** (bottom left).
3. Select **By topic** $\rightarrow$ `/camera/image_raw` $\rightarrow$ **Image**.
4. The live camera feed will appear in the RViz display panel.

Alternatively, use the ROS 2 lightweight image viewer:
```bash
ros2 run rqt_image_view rqt_image_view /camera/image_raw
```

---

## 3. Camera Calibration Procedure

To calculate precise optical parameters for real-world pick-and-place accuracy:

1. Print a standard $8 \times 6$ checkerboard ($25\text{ mm}$ square size).
2. Install the ROS 2 camera calibration tool:
   ```bash
   sudo apt install -y ros-jazzy-camera-calibration
   ```
3. Run the interactive calibrator:
   ```bash
   ros2 run camera_calibration cameracalibrator --size 8x6 --square 0.025 image:=/camera/image_raw camera:=/camera
   ```
4. Move the checkerboard across the field of view (tilting, changing distance, covering edges) until the **CALIBRATE** button turns green.
5. Click **CALIBRATE**, then click **COMMIT**.
6. Save the generated calibration parameters into:
   `~/auron_robot_ws/src/auron_robot_camera/config/camera_calibration.yaml`

---

## 4. Calibration YAML Format

```yaml
image_width: 640
image_height: 480
camera_name: auron_laptop_camera
camera_matrix:
  rows: 3
  cols: 3
  data: [fx,  0.0, cx,
         0.0, fy,  cy,
         0.0, 0.0, 1.0]
distortion_model: plumb_bob
distortion_coefficients:
  rows: 1
  cols: 5
  data: [k1, k2, p1, p2, k3]
```

---

## 5. Mounting Options & TF Transforms

### Option A: Eye-in-Hand (Configured by Default)
- `camera_link` is rigidly fastened to `wrist_3_link`.
- Transform automatically updates with arm motion:
  $$\text{world} \rightarrow \text{base\_link} \rightarrow \dots \rightarrow \text{wrist\_3\_link} \rightarrow \text{camera\_link}$$

### Option B: External Fixed Workcell Camera
For an overhead bird's-eye camera observing the table:
```bash
ros2 run tf2_ros static_transform_publisher 0.5 0.0 0.9 0 3.1415 0 world camera_link
```
