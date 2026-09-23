# Auron Robotics 6-DOF Industrial Robotic Arm Architecture

## 1. System Overview

The **Auron 6-DOF Industrial Robotic Arm** (`auron_robot_arm`) simulation system is engineered for Ubuntu 24.04 LTS running ROS 2 Jazzy Jalisco and Gazebo Harmonic (`gz sim 8.x`). It integrates low-level hardware abstraction via `ros2_control`, physics simulation via `gz_ros2_control`, kinematic motion planning with MoveIt 2, real-time keyboard/joystick teleoperation, and an extensible computer vision pipeline with native Linux webcam integration (`/dev/video0`).

```mermaid
graph TD
    User([User / Operator]) -->|Keyboard / Joystick| Teleop[auron_robot_teleop]
    User -->|Interactive Marker / Goal| MoveIt[MoveIt 2 move_group]
    CameraHW[/dev/video0 Camera] --> CameraNode[auron_robot_camera]
    CameraNode -->|/camera/image_raw| VisionNode[auron_robot_vision]
    VisionNode -->|Object 3D Pose| MoveIt
    
    Teleop -->|/arm_controller/joint_trajectory| CM[ros2_control Controller Manager]
    MoveIt -->|FollowJointTrajectory Action| CM
    
    CM --> JTC[arm_controller JointTrajectoryController]
    CM --> GTC[gripper_controller JointTrajectoryController]
    CM --> JSB[joint_state_broadcaster]
    
    JTC --> GZHW[gz_ros2_control / GazeboSimSystem]
    GTC --> GZHW
    GZHW <--> GZPhysics[(Gazebo Harmonic Physics)]
    
    JSB -->|/joint_states| RSP[robot_state_publisher]
    RSP -->|/tf, /tf_static| RViz[RViz2 Visualization]
    GZPhysics -->|/clock, /camera/image_raw| GZBridge[ros_gz_bridge]
    GZBridge --> RViz
```

---

## 2. Package Architecture

| Package | Build Type | Purpose | Key Artifacts |
| :--- | :--- | :--- | :--- |
| `auron_robot_description` | `ament_cmake` | Robot kinematics, visual/collision geometry, meshes, Xacro macros, materials | `auron_robot.urdf.xacro`, binary STLs, `auron_robot.rviz` |
| `auron_robot_bringup` | `ament_cmake` | Master launch files, simulation world, environment SDF, bridge config | `simulation.launch.py`, `industrial_world.sdf`, `gz_bridge.yaml` |
| `auron_robot_control` | `ament_cmake` | Controller configurations, spawner launch files, demo execution scripts | `controllers.yaml`, `control.launch.py`, `pick_place_demo.py` |
| `auron_robot_moveit_config` | `ament_cmake` | MoveIt 2 SRDF, OMPL planners, kinematics, joint limits, MoveIt Servo | `auron_robot.srdf`, `moveit.launch.py`, `moveit_servo.yaml` |
| `auron_robot_teleop` | `ament_python` | Safe interactive keyboard teleoperation with real-time ANSI dashboard | `teleop_keyboard.py`, `teleop.launch.py`, `teleop.yaml` |
| `auron_robot_camera` | `ament_python` | Linux webcam driver publishing standard ROS 2 image streams & camera info | `camera_node.py`, `camera.launch.py`, `camera_calibration.yaml` |
| `auron_robot_vision` | `ament_python` | OpenCV color detection & 3D ray projection framework ready for YOLO | `vision_node.py`, `detectors.py`, `vision.launch.py` |

---

## 3. Communication Graph & Topic Conventions

### Controller Topics
- `/arm_controller/joint_trajectory` (`trajectory_msgs/msg/JointTrajectory`): Accepts goal trajectory points for joints 1 through 6.
- `/arm_controller/follow_joint_trajectory` (`control_msgs/action/FollowJointTrajectory`): MoveIt trajectory execution action.
- `/gripper_controller/joint_trajectory` (`trajectory_msgs/msg/JointTrajectory`): Symmetrical finger stroke command.
- `/joint_states` (`sensor_msgs/msg/JointState`): Live feedback from `joint_state_broadcaster`.

### Coordinate Frames (TF2)
- `world`: Inertial world simulation reference frame.
- `base_link`: Center base frame of the flared pedestal stand.
- `base_rotation_link`: Rotating turret about vertical Z axis.
- `shoulder_link`: Horizontal pivot housing.
- `upper_arm_link`: Ascending cylindrical arm member.
- `elbow_link`: Second circular articulated housing.
- `forearm_link`: Forearm member leading to wrist.
- `wrist_1_link`: Forearm axial roll pivot.
- `wrist_2_link`: Wrist pitch pivot.
- `wrist_3_link`: Wrist tool roll pivot.
- `tool0`: Standard industrial tool mounting flange surface.
- `gripper_base`: Chassis of the two-finger gripper.
- `gripper_tcp`: Tool Center Point between finger tips.
- `camera_link` / `camera_optical_frame`: Eye-in-hand sensor coordinate frames.

### Perception Topics
- `/camera/image_raw` (`sensor_msgs/msg/Image`): Uncompressed BGR8 camera frames at 640x480 resolution.
- `/camera/camera_info` (`sensor_msgs/msg/CameraInfo`): Camera intrinsic calibration matrix ($K, D, R, P$).
- `/vision/detection_image` (`sensor_msgs/msg/Image`): Debug annotated image showing target bounding boxes and 3D estimates.
- `/vision/detections` (`std_msgs/msg/String`): JSON telemetry containing detected target classes, pixel centroids, and camera relative 3D coordinates.
