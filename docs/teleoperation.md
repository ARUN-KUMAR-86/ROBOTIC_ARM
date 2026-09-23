# Teleoperation & Control Guide

## 1. Keyboard Teleoperation Layout

The `auron_robot_teleop` node provides keyboard control with live terminal feedback.

| Key | Action | Joint / Function | Movement Direction |
| :--- | :--- | :--- | :--- |
| **`A`** | Decrement | Joint 1 (Base Rotation) | Counter-clockwise (-) |
| **`D`** | Increment | Joint 1 (Base Rotation) | Clockwise (+) |
| **`S`** | Decrement | Joint 2 (Shoulder) | Forward / Down (-) |
| **`W`** | Increment | Joint 2 (Shoulder) | Backward / Up (+) |
| **`F`** | Decrement | Joint 3 (Elbow) | Flexion (-) |
| **`R`** | Increment | Joint 3 (Elbow) | Extension (+) |
| **`G`** | Decrement | Joint 4 (Wrist Roll) | Roll Left (-) |
| **`T`** | Increment | Joint 4 (Wrist Roll) | Roll Right (+) |
| **`H`** | Decrement | Joint 5 (Wrist Pitch) | Pitch Down (-) |
| **`Y`** | Increment | Joint 5 (Wrist Pitch) | Pitch Up (+) |
| **`J`** | Decrement | Joint 6 (Tool Roll) | Spin Left (-) |
| **`U`** | Increment | Joint 6 (Tool Roll) | Spin Right (+) |
| **`O`** | Command | Gripper | Open Fingers (35 mm stroke) |
| **`P`** | Command | Gripper | Close Fingers (0 mm stroke) |
| **`SPACE`** | Safety | Emergency Stop | Immediately halts all trajectory execution |
| **`0`** | Trajectory | Reset | Smoothly returns all joints to Home pose (0.0 rad) |
| **`Q`** | System | Exit | Gracefully restores terminal mode and shuts down |

---

## 2. Terminal Dashboard

While active, the node displays a persistent status line:
```text
[TELEOP] J1:  +0.0° | J2: -34.4° | J3: +68.8° | J4:  +0.0° | J5: +51.6° | J6:  +0.0° | Gripper: OPEN
```

When emergency stop is triggered:
```text
[EMERGENCY STOP (ACTIVE)] J1:  +0.0° | J2: -34.4° | ... | Gripper: OPEN
```

---

## 3. Safety Mechanisms

1. **Strict Joint Limiting**: Commands are clamped to the robot's physical boundaries before trajectory generation.
2. **Smooth Interpolation**: Steps default to $2.0^\circ$ increments with cubic/quintic spline time parametrization ($0.25\text{ s}$ per command) to prevent velocity spikes.
3. **Invalid Data Filtering**: Rejects any non-numeric, NaN, or infinite coordinates.
4. **Emergency Stop (E-Stop)**: When `SPACE` is pressed, an immediate zero-velocity point at current position is published, arresting motion in under $10\text{ ms}$.

---

## 4. USB Joystick / Gamepad Architecture

The system is prepared for standard USB gamepads (e.g. Sony DualShock, Xbox Controller) via the ROS 2 `joy` package:
- Axis 0 (Left Stick X) $\rightarrow$ J1 (Base)
- Axis 1 (Left Stick Y) $\rightarrow$ J2 (Shoulder)
- Axis 4 (Right Stick Y) $\rightarrow$ J3 (Elbow)
- D-Pad Up/Down $\rightarrow$ J5 (Pitch)
- Triggers $\rightarrow$ Gripper Open/Close
- Button A (Xbox) / X (PS) $\rightarrow$ Reset Home
- Button B (Xbox) / Circle (PS) $\rightarrow$ Emergency Stop
