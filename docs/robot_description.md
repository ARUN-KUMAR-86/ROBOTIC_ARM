# Auron Robot Description & Kinematic Specification

## 1. Visual Design & Reference Alignment

The Auron robot model was visually synthesized based on the reference design:
- **Flared Circular Pedestal Base**: Wide flared white base pedestal with lower cyan accent ring and metallic rim.
- **Circular Gear-Like Joint Housings**: Distinctive blue cylindrical actuator casings with radial bolt rings and cyan turbine/shutter disc faceplates on both Shoulder and Elbow joints.
- **Color Scheme**:
  - `auron_white`: RGB `(0.95, 0.95, 0.95)`
  - `auron_blue`: RGB `(0.00, 0.30, 0.80)`
  - `auron_cyan`: RGB `(0.00, 0.75, 1.00)`
  - `auron_dark_blue`: RGB `(0.02, 0.08, 0.18)`
  - `auron_metal_silver`: RGB `(0.82, 0.84, 0.86)`
- **Sleek Cylindrical Arm Links**: Smooth white tubes with cyan accent collars.
- **Industrial Articulated Gripper**: Rigid mounting base, pneumatic actuator housing, and dual parallel fingers with high-friction inner contact pads.

---

## 2. Kinematic Structure & Joint Limits

| Joint Name | Type | Parent Link | Child Link | Axis | Range (rad) | Range (deg) | Max Vel (rad/s) | Max Effort (Nm) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `joint_1` | Revolute | `base_link` | `base_rotation_link` | $[0, 0, 1]$ (Z) | $[-3.1416, 3.1416]$ | $[-180^\circ, +180^\circ]$ | 2.0 | 180.0 |
| `joint_2` | Revolute | `base_rotation_link` | `shoulder_link` | $[0, 1, 0]$ (Y) | $[-2.0944, 2.0944]$ | $[-120^\circ, +120^\circ]$ | 2.0 | 180.0 |
| `joint_3` | Revolute | `upper_arm_link` | `elbow_link` | $[0, 1, 0]$ (Y) | $[-2.6180, 2.6180]$ | $[-150^\circ, +150^\circ]$ | 2.5 | 120.0 |
| `joint_4` | Revolute | `forearm_link` | `wrist_1_link` | $[0, 0, 1]$ (Z) | $[-3.1416, 3.1416]$ | $[-180^\circ, +180^\circ]$ | 3.0 | 60.0 |
| `joint_5` | Revolute | `wrist_1_link` | `wrist_2_link` | $[0, 1, 0]$ (Y) | $[-2.0944, 2.0944]$ | $[-120^\circ, +120^\circ]$ | 3.0 | 40.0 |
| `joint_6` | Revolute | `wrist_2_link` | `wrist_3_link` | $[0, 0, 1]$ (Z) | $[-6.2832, 6.2832]$ | $[-360^\circ, +360^\circ]$ | 3.5 | 30.0 |
| `left_finger_joint` | Prismatic | `gripper_base` | `left_finger` | $[1, 0, 0]$ (X) | $[0.00, 0.035\text{ m}]$ | Stroke: 35 mm | 0.1 | 40.0 |
| `right_finger_joint` | Prismatic | `gripper_base` | `right_finger` | $[-1, 0, 0]$ (-X) | $[0.00, 0.035\text{ m}]$ | Stroke: 35 mm | 0.1 | 40.0 |

---

## 3. Mass & Inertial Properties

Mass distribution was balanced to ensure numerical stability under Gazebo Harmonic DART physics solver:
- `base_link`: 8.0 kg (Low center of mass prevents tipping)
- `base_rotation_link`: 4.5 kg
- `shoulder_link`: 5.5 kg
- `upper_arm_link`: 4.0 kg
- `elbow_link`: 3.2 kg
- `forearm_link`: 2.8 kg
- `wrist_1_link`: 1.2 kg
- `wrist_2_link`: 1.0 kg
- `wrist_3_link`: 0.6 kg
- `gripper_base`: 0.5 kg
- `left_finger` / `right_finger`: 0.08 kg each

Joint damping values ($d = 2.0 \text{ Nms/rad}$ on major axes, $d = 0.5$ on wrists) and Coulomb friction ($f = 1.0 \text{ Nm}$) are configured in `robot_constants.xacro` to eliminate oscillatory drift when holding position.

---

## 4. Collision Geometry Optimization

Visual geometry uses detailed multi-facet procedural STL meshes and compound visual elements for photorealism. In contrast, collision geometry consists of simplified analytic primitives (cylinders and bounding boxes):
- Prevents mesh collision intersection errors
- Accelerates real-time OMPL collision distance computations by an order of magnitude
- Protects against artificial self-collision deadlocks during path planning
