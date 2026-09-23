# Comprehensive Troubleshooting Guide

## 1. Missing Dependencies
If system dependencies are missing, run the automated checker:
```bash
bash ~/auron_robot_ws/scripts/check_installation.sh
```
To install all required packages on Ubuntu 24.04 / ROS 2 Jazzy:
```bash
sudo apt update && sudo apt install -y \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-moveit \
  ros-jazzy-moveit-servo \
  ros-jazzy-joint-state-publisher-gui
```

---

## 2. Gazebo Issues

### Symptom: `Failed to load system plugin [gz_ros2_control-system] : Could not find shared library`
- **Root Cause**: `ros-jazzy-gz-ros2-control` package is not installed.
- **Solution**: Run `sudo apt install -y ros-jazzy-gz-ros2-control`.

### Symptom: Robot meshes appear white or black in Gazebo
- **Root Cause**: Gazebo cannot locate the mesh package path.
- **Solution**: Set the resource path before launching:
  ```bash
  export GZ_SIM_RESOURCE_PATH=~/auron_robot_ws/src:$GZ_SIM_RESOURCE_PATH
  ```
  *(Note: This is automatically handled inside `gazebo.launch.py`)*.

---

## 3. Controller & ros2_control Issues

### Symptom: Controllers are in `inactive` or `unconfigured` state
- **Root Cause**: `gz_ros2_control` plugin was not loaded or Gazebo physics paused.
- **Inspection**:
  ```bash
  ros2 control list_controllers
  ```
- **Manual Activation**:
  ```bash
  ros2 control set_controller_state arm_controller active
  ros2 control set_controller_state joint_state_broadcaster active
  ```

---

## 4. MoveIt Issues

### Symptom: `move_group` crashes with missing kinematic solver
- **Root Cause**: `ros-jazzy-moveit-kinematics` is missing.
- **Solution**: Run `sudo apt install -y ros-jazzy-moveit-kinematics`.

### Symptom: Trajectory execution fails with "Goal tolerance violated"
- **Root Cause**: High damping or tight tolerances in `controllers.yaml`.
- **Solution**: Tolerances in `controllers.yaml` are set to generous values (`0.15 rad` trajectory, `0.05 rad` goal). If needed, relax `stopped_velocity_tolerance` to `0.05`.

---

## 5. Camera & Video Device Issues

### Symptom: `Could not open camera /dev/video0`
- **Root Cause**: Permission denied or webcam is in use by another application (e.g. browser, Zoom).
- **Check User Group**:
  ```bash
  sudo usermod -aG video $USER
  ```
- **Check Device Busy**:
  ```bash
  fuser -v /dev/video0
  ```
- **Alternative Device**:
  If external USB webcam is `/dev/video1` or `/dev/video2`, specify on launch:
  ```bash
  ros2 launch auron_robot_camera camera.launch.py camera_device:=/dev/video1
  ```
