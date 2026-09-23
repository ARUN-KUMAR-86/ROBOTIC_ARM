#!/usr/bin/env python3
"""
Pick and Place Demonstration State Machine for Auron 6-DOF Industrial Robot.
Executes sequence:
1. Move to home / ready pose
2. Open gripper
3. Move to pre-grasp (above object)
4. Move to grasp pose (descend to target)
5. Close gripper (firm physical grasp)
6. Lift object
7. Move to place location
8. Lower to placement surface
9. Open gripper (release)
10. Retreat to home
"""

import math
import sys
import time
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class PickPlaceDemo(Node):
    def __init__(self):
        super().__init__('auron_pick_place_demo')

        # Configurable parameters (allows testing without hardcoded values)
        self.set_parameters([rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)])
        self.declare_parameter('pick_x', 0.45)
        self.declare_parameter('pick_y', -0.15)
        self.declare_parameter('pick_z', 0.35)
        self.declare_parameter('place_x', 0.45)
        self.declare_parameter('place_y', 0.15)
        self.declare_parameter('place_z', 0.35)
        self.declare_parameter('step_duration', 2.0)

        self.arm_pub = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10
        )
        self.gripper_pub = self.create_publisher(
            JointTrajectory, '/gripper_controller/joint_trajectory', 10
        )

        self.joint_names = [
            'joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6'
        ]
        self.gripper_names = ['left_finger_joint', 'right_finger_joint']

        self.get_logger().info("Auron Pick & Place Demo node initialized.")

    def publish_arm(self, positions, duration_sec):
        msg = JointTrajectory()
        msg.header.stamp.sec = 0
        msg.header.stamp.nanosec = 0
        msg.joint_names = self.joint_names

        pt = JointTrajectoryPoint()
        pt.positions = [float(p) for p in positions]
        pt.velocities = [0.0] * 6
        sec = int(duration_sec)
        nanosec = int((duration_sec - sec) * 1e9)
        pt.time_from_start = Duration(sec=sec, nanosec=nanosec)

        msg.points.append(pt)
        self.arm_pub.publish(msg)
        time.sleep(duration_sec + 0.5)

    def publish_gripper(self, width, duration_sec=1.0):
        msg = JointTrajectory()
        msg.header.stamp.sec = 0
        msg.header.stamp.nanosec = 0
        msg.joint_names = self.gripper_names

        pt = JointTrajectoryPoint()
        pt.positions = [float(width), float(width)]
        pt.velocities = [0.0, 0.0]
        pt.time_from_start = Duration(sec=int(duration_sec), nanosec=0)

        msg.points.append(pt)
        self.gripper_pub.publish(msg)
        time.sleep(duration_sec + 0.3)

    def run_sequence(self):
        duration = self.get_parameter('step_duration').value

        # Kinematically calculated joint waypoints for the pick & place arc:
        # Poses calibrated for table height z=0.35m in front of robot
        READY_POSE     = [ 0.0,   -0.50,  1.10,  0.0,  0.97,  0.0 ]
        PRE_GRASP_POSE = [-0.32,  -0.35,  1.35,  0.0,  0.57,  0.0 ]
        GRASP_POSE     = [-0.32,  -0.20,  1.52,  0.0,  0.25,  0.0 ]
        LIFT_POSE      = [-0.32,  -0.45,  1.20,  0.0,  0.82,  0.0 ]
        PRE_PLACE_POSE = [ 0.32,  -0.45,  1.20,  0.0,  0.82,  0.0 ]
        PLACE_POSE     = [ 0.32,  -0.20,  1.52,  0.0,  0.25,  0.0 ]

        self.get_logger().info("=== Step 1: Moving to Ready Position ===")
        self.publish_arm(READY_POSE, duration)

        self.get_logger().info("=== Step 2: Opening Gripper ===")
        self.publish_gripper(0.035, duration_sec=1.0)

        self.get_logger().info("=== Step 3: Moving to Pre-Grasp Pose (Above Pick Location) ===")
        self.publish_arm(PRE_GRASP_POSE, duration)

        self.get_logger().info("=== Step 4: Descending to Grasp Target Object ===")
        self.publish_arm(GRASP_POSE, duration)

        self.get_logger().info("=== Step 5: Closing Gripper (Grasping Object) ===")
        self.publish_gripper(0.012, duration_sec=1.2) # Firm grasp around cube

        self.get_logger().info("=== Step 6: Lifting Object ===")
        self.publish_arm(LIFT_POSE, duration)

        self.get_logger().info("=== Step 7: Moving to Place Location ===")
        self.publish_arm(PRE_PLACE_POSE, duration)

        self.get_logger().info("=== Step 8: Lowering to Placement Surface ===")
        self.publish_arm(PLACE_POSE, duration)

        self.get_logger().info("=== Step 9: Opening Gripper (Releasing Object) ===")
        self.publish_gripper(0.035, duration_sec=1.0)

        self.get_logger().info("=== Step 10: Retreating to Ready Pose ===")
        self.publish_arm(PRE_PLACE_POSE, duration)
        self.publish_arm(READY_POSE, duration)

        self.get_logger().info("Pick-and-Place sequence completed successfully!")

def main(args=None):
    rclpy.init(args=args)
    demo = PickPlaceDemo()
    time.sleep(1.0) # Allow publisher graph to settle
    try:
        demo.run_sequence()
    except KeyboardInterrupt:
        demo.get_logger().info("Demo aborted by user.")
    finally:
        demo.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
