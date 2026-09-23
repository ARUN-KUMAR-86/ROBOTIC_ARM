# Future Development Roadmap

## Phase 1: Real-Time MoveIt Servo Integration (Stage B)
- Integrate MoveIt Servo Cartesian joystick jogging.
- Connect USB gamepad buttons to TwistStamped commands published to `/servo_node/delta_twist_cmds`.
- Configure singularity avoidance threshold in `moveit_servo.yaml`.

## Phase 2: Deep Learning Object Detection (YOLOv8 / YOLOv11)
- Install Ultralytics:
  ```bash
  pip install ultralytics
  ```
- Download pre-trained weights or train custom weights for industrial parts (`nuts, bolts, electronic components`).
- Activate `AIDetector` in `auron_robot_vision/detectors.py`.

## Phase 3: 3D Depth Sensing & Point Cloud Reconstruction
- Mount Intel RealSense D435i or simulated RGB-D sensor in `gazebo.xacro`.
- Integrate Point Cloud Library (PCL) filtering with MoveIt OctoMap for dynamic obstacle avoidance.

## Phase 4: Closed-Loop Visual Servoing
- Implement Position-Based Visual Servoing (PBVS) where end-effector error is iteratively corrected using live visual feedback until gripper TCP aligns within $2\text{ mm}$ of object centroid.

## Phase 5: Hardware Deployment to Physical Arm
- Replace `gz_ros2_control/GazeboSimSystem` with custom hardware interface (`hardware_interface::SystemInterface`).
- Communicate with physical motor controllers via CAN bus (SocketCAN) or EtherCAT (SOEM).
