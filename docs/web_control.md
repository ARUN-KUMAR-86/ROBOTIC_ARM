# Auron Web Dashboard & Modern Dexterous Hand Control

The **Auron Web Control Center** is a responsive, web-based teleoperation and monitoring interface for the Auron 6-DOF robotic arm and the newly designed **Modern Cybernetic Dexterous Hand**.

---

## 🌟 Modern Dexterous Hand Upgrade

The end-effector has been converted from a conventional 2-jaw industrial gripper to an ultra-modern, 5-finger articulated bionic hand:

| Subsystem | Specification |
| :--- | :--- |
| **End-Effector Architecture** | 5-Digit Multi-Phalanx Dexterous Robotic Hand |
| **Joint Articulation** | Metacarpophalangeal (MCP), Proximal Interphalangeal (PIP), Distal Interphalangeal (DIP) |
| **Actuator Drive** | High-torque coreless DC micro-actuators with Dyneema tendons |
| **Material Shell** | Pearl white polymer & aeronautical brushed titanium casing |
| **Visual Accents** | Illuminated cyan neon joint rings & dorsal circuit traces |
| **Grip Stroke** | 0.0 mm (Closed fist/pinch) to 35.0 mm (Full palm open) |
| **Grasp Payload** | 5.0 kg dynamic / 7.5 kg static |
| **Pre-Programmed Gestures** | Open Palm, Power Fist, Precision Pinch, Point, Peace, Thumbs Up |

Generated high-resolution conceptual design renders are located at:
- [`web_dashboard/assets/modern_robotic_hand.jpg`](file:///home/arun/auron_robot_ws/web_dashboard/assets/modern_robotic_hand.jpg) (Bionic Hand close-up)
- [`web_dashboard/assets/modern_arm_hand.jpg`](file:///home/arun/auron_robot_ws/web_dashboard/assets/modern_arm_hand.jpg) (Full 6-DOF arm integration)

---

## 🚀 Quick Launch

### Option 1: One-Click Shell Script
```bash
bash ~/auron_robot_ws/launch_web_dashboard.sh
```
*Starts `rosbridge_websocket` on port 9090, the Python web server on port 8080, and opens your browser.*

### Option 2: ROS 2 Launch File
```bash
source /opt/ros/jazzy/setup.bash
source ~/auron_robot_ws/install/setup.bash
ros2 launch auron_robot_bringup web_control.launch.py
```

### Option 3: Full Simulation with Web Enabled
```bash
ros2 launch auron_robot_bringup simulation.launch.py use_web:=true
```

---

## 🖥️ Web Dashboard Architecture

```text
auron_robot_ws/web_dashboard/
├── index.html                  # Cybernetic glassmorphism control UI
├── css/
│   └── dashboard.css           # Glowing cyan / dark-mode responsive stylesheet
├── js/
│   ├── libs/                   # Standalone offline libraries (roslibjs, Three.js, OrbitControls)
│   ├── ros_connection.js       # WebSocket link to ROS 2 & topic handlers
│   ├── robot_3d_view.js        # WebGL 3D kinematic arm & articulated hand visualizer
│   ├── arm_controls.js         # Joint sliders, degree/radian sync, step jogging, presets
│   ├── hand_controls.js        # Master grip stroke, gestures, and individual finger flex
│   └── app.js                  # Master application orchestrator & telemetry
├── assets/                     # Modern hand concept renders and graphics
└── web_server.py               # Lightweight server with /api/health check
```

---

## 📡 ROS 2 Interfaces & Topic Mapping

| Topic | Type | Direction | Description |
| :--- | :--- | :--- | :--- |
| `/arm_controller/joint_trajectory` | `trajectory_msgs/msg/JointTrajectory` | Publish | Sends 6-DOF joint target positions to ros2_control |
| `/gripper_controller/joint_trajectory` | `trajectory_msgs/msg/JointTrajectory` | Publish | Commands stroke for fingers / gripper |
| `/joint_states` | `sensor_msgs/msg/JointState` | Subscribe | Live real-time feedback of all joints and fingers |
| `/servo_node/delta_joint_cmds` | `control_msgs/msg/JointJog` | Publish | Real-time velocity jog for MoveIt Servo |
