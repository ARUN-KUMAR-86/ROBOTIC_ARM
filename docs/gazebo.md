# Gazebo Harmonic Simulation Environment

## 1. Gazebo Harmonic vs Gazebo Classic

This project uses **Gazebo Harmonic (gz-sim 8.x)**, the official long-term support release for ROS 2 Jazzy Jalisco. Gazebo Classic (`gazebo-11`) is deprecated and not used.

Key distinctions in Gazebo Harmonic:
- Command line utility is `gz sim`, not `gazebo` or `gzserver`.
- System plugins are modular C++ shared objects loaded dynamically (e.g. `gz-sim-physics-system`, `gz_ros2_control-system`).
- Message serialization utilizes Google Protocol Buffers (`gz.msgs`) bridged to ROS 2 messages via `ros_gz_bridge`.

---

## 2. World Model (`industrial_world.sdf`)

The simulation environment provides a realistic manufacturing workcell:
- **Floor**: High-friction $20 \times 20\text{ m}$ textured surface.
- **Lighting**: Dual-source setup consisting of a primary directional sun with realistic shadows and a secondary fill light to illuminate joint recesses and turbines.
- **Robot Mounting Stand**: Heavy cylindrical pedestal at $(0, 0, 0.15)$ providing a stable foundation at $z = 0.30\text{ m}$.
- **Worktable**: Industrial metal worktable placed at $(0.50, 0, 0.15)$ directly in front of the robot arm.
- **Target Manipulation Objects**:
  - `red_cube`: $35\text{ mm}$ cube placed at $(0.45, -0.15, 0.32)$, mass $40\text{ g}$.
  - `blue_cube`: $35\text{ mm}$ cube placed at $(0.50, 0.00, 0.32)$, mass $40\text{ g}$.
  - `green_cylinder`: $36\text{ mm}$ diameter $\times 45\text{ mm}$ length placed at $(0.45, 0.15, 0.325)$, mass $40\text{ g}$.
  Each object includes high contact friction ($\mu = 100$) allowing robust physical gripping by the two-finger gripper.

---

## 3. Physics Configuration

- **Solver**: DART (Dynamic Animation and Robotics Toolkit) physics engine.
- **Max Step Size**: $0.001\text{ s}$ ($1\text{ ms}$, $1000\text{ Hz}$).
- **Real-Time Factor Target**: $1.0$.

---

## 4. Gazebo ROS Bridge (`gz_bridge.yaml`)

The `ros_gz_bridge` translates native Gazebo topics to ROS 2:
```yaml
- ros_topic_name: "/clock"
  gz_topic_name: "/clock"
  ros_type_name: "rosgraph_msgs/msg/Clock"
  gz_type_name: "gz.msgs.Clock"
  direction: GZ_TO_ROS

- ros_topic_name: "/camera/image_raw"
  gz_topic_name: "/camera/image_raw"
  ros_type_name: "sensor_msgs/msg/Image"
  gz_type_name: "gz.msgs.Image"
  direction: GZ_TO_ROS
```
