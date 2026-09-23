# Auron 6-DOF Industrial Robotic Arm Simulation

An industrial-grade 6-DOF articulated robotic arm simulation platform built for **Ubuntu 24.04 LTS**, **ROS 2 Jazzy Jalisco**, **Gazebo Harmonic (gz-sim 8.11)**, and **MoveIt 2**.

Visual design synthesized from reference specifications: **blue and white industrial finish, circular gear housings, cyan turbine faceplates, articulated 2-finger gripper, and compact 6-axis kinematics**.

---

## ⚡ Quick Start

```bash
# 1. Source ROS 2 Jazzy
source /opt/ros/jazzy/setup.bash

# 2. Build the workspace
cd ~/auron_robot_ws
colcon build --symlink-install
source install/setup.bash

# 3. Launch the complete simulation
ros2 launch auron_robot_bringup auron_robot.launch.py
# Or using the simulation alias:
# ros2 launch auron_robot_bringup simulation.launch.py
```

To control the arm using keyboard teleoperation:
```bash
# In a separate terminal:
source /opt/ros/jazzy/setup.bash
source ~/auron_robot_ws/install/setup.bash
ros2 run auron_robot_teleop teleop_keyboard
```

To launch the **Modern Web Control Dashboard & Dexterous Hand UI**:
```bash
bash ~/auron_robot_ws/launch_web_dashboard.sh
# Or navigate to: http://localhost:8080
```

---

## 📦 Workspace Architecture

```text
auron_robot_ws/
├── web_dashboard/                   # Web Control Dashboard & Dexterous Hand 3D UI
├── src/
│   ├── auron_robot_description/     # Kinematics, Xacro, binary STL meshes, materials, RViz
│   ├── auron_robot_bringup/         # Master launch, industrial world SDF, ros_gz_bridge, web_control
│   ├── auron_robot_control/         # ros2_control configuration, controllers, pick & place demo
│   ├── auron_robot_moveit_config/   # MoveIt 2 SRDF, OMPL, kinematics, joint limits, Servo
│   ├── auron_robot_teleop/          # Real-time keyboard teleoperation with ANSI dashboard
│   ├── auron_robot_camera/          # Linux /dev/video0 camera driver & calibration
│   └── auron_robot_vision/          # OpenCV detection & 3D ray projection (YOLO ready)
├── scripts/                         # Automated validation & test scripts
├── docs/                            # In-depth architectural documentation
└── README.md
```

---

## 🛠️ System Requirements & Installation

### Platform
- **OS**: Ubuntu 24.04 LTS (Noble Numbat)
- **ROS Distro**: ROS 2 Jazzy Jalisco
- **Simulator**: Gazebo Harmonic (`gz sim 8.11+`)
- **Python**: Python 3.12 with OpenCV and NumPy

### Dependency Verification
Run the built-in system verification script:
```bash
bash ~/auron_robot_ws/scripts/check_installation.sh
```

To install all required ROS 2 Jazzy packages:
```bash
sudo apt update && sudo apt install -y \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-moveit \
  ros-jazzy-moveit-servo \
  ros-jazzy-joint-state-publisher-gui
```

---

## 🚀 Launch Options & Commands

### 1. Master Simulation Launch
```bash
ros2 launch auron_robot_bringup simulation.launch.py
```
**Optional Launch Arguments:**
- `use_gazebo:=true|false` (default: `true`)
- `use_moveit:=true|false` (default: `true`)
- `use_rviz:=true|false` (default: `true`)
- `use_camera:=true|false` (default: `true`)
- `use_teleop:=true|false` (default: `false`)
- `camera_device:=/dev/video0` (default: `/dev/video0`)

### 2. Standalone Robot Visualization (RViz2)
Inspect the robot model and TF frames without starting Gazebo:
```bash
ros2 launch auron_robot_description description.launch.py
```

### 3. Standalone Gazebo Harmonic Environment
Launch Gazebo Harmonic with the industrial workcell, stand, table, and colored demo objects:
```bash
ros2 launch auron_robot_bringup gazebo.launch.py
```

### 4. Standalone MoveIt 2
Launch MoveIt motion planning with the interactive RViz MotionPlanning display:
```bash
ros2 launch auron_robot_moveit_config moveit.launch.py
```

### 5. Laptop Webcam Node
Start the camera driver capturing from `/dev/video0`:
```bash
ros2 launch auron_robot_camera camera.launch.py
```

### 6. Computer Vision Detection Node
Start OpenCV detection tracking red cube, blue cube, and green cylinder:
```bash
ros2 launch auron_robot_vision vision.launch.py
```

### 7. Automated Pick-and-Place Demonstration
Execute the 10-step pick, lift, transfer, place, and retreat cycle:
```bash
ros2 run auron_robot_control pick_place_demo.py
```

---

## 🎮 Teleoperation Controls

Launch the interactive keyboard node:
```bash
ros2 run auron_robot_teleop teleop_keyboard
```

| Key | Function | Key | Function |
| :---: | :--- | :---: | :--- |
| **A / D** | Joint 1 (Base Pan) - / + | **O** | Open Gripper (35 mm) |
| **S / W** | Joint 2 (Shoulder) - / + | **P** | Close Gripper (0 mm) |
| **F / R** | Joint 3 (Elbow) - / + | **SPACE** | **EMERGENCY STOP** (Halt motion) |
| **G / T** | Joint 4 (Wrist Roll) - / + | **0** | **RESET HOME** (Return to 0 rad) |
| **H / Y** | Joint 5 (Wrist Pitch) - / + | **Q** | Exit Teleoperation |
| **J / U** | Joint 6 (Tool Roll) - / + | | |

---

## 🔍 Validation & Health Checks

Run any of the pre-configured diagnostic scripts:

| Script | Purpose |
| :--- | :--- |
| `bash scripts/check_installation.sh` | Verifies OS, ROS, Gazebo, and package dependencies |
| `bash scripts/build.sh` | Compiles workspace packages with Release flags |
| `bash scripts/check_topics.sh` | Confirms active status of all essential topics |
| `bash scripts/check_controllers.sh` | Inspects `controller_manager` and controller lifecycle |
| `bash scripts/check_tf.sh` | Tests full TF2 transform tree from `world` to `tool0` |
| `bash scripts/test_moveit.sh` | Validates MoveIt motion plan generation and execution |

---

## 📚 In-Depth Documentation

Detailed guides are located in the `docs/` folder:
- [docs/architecture.md](docs/architecture.md): Overall design, data flow diagrams, topic mapping.
- [docs/robot_description.md](docs/robot_description.md): Kinematic specifications, masses, inertias, collision geometries.
- [docs/gazebo.md](docs/gazebo.md): Gazebo Harmonic plugins, DART physics solver, SDF world layout.
- [docs/ros2_control.md](docs/ros2_control.md): Controller configurations, lifecycle states, hardware interfaces.
- [docs/moveit.md](docs/moveit.md): MoveIt 2 setup, SRDF self-collision matrix, OMPL planners, MoveIt Servo.
- [docs/teleoperation.md](docs/teleoperation.md): Teleoperation safety bounds, smoothing, USB gamepad architecture.
- [docs/web_control.md](docs/web_control.md): Web control dashboard, Three.js 3D visualizer, and modern bionic hand upgrade.
- [docs/camera.md](docs/camera.md): Linux webcam integration, RViz streaming, checkerboard calibration guide.
- [docs/vision.md](docs/vision.md): OpenCV segmentation, 3D ray projection, YOLO integration.
- [docs/troubleshooting.md](docs/troubleshooting.md): Diagnosis and remedies for simulation and controller edge cases.
- [docs/future_development.md](docs/future_development.md): Roadmap for deep learning, depth sensors, and physical arm hardware.
