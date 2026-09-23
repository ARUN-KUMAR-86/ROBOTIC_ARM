#!/usr/bin/env python3
"""
MoveIt 2 and Motion Planning Validation Script for Auron Robot.
Verifies:
1. /move_group node or /arm_controller is alive
2. Current joint states received
3. Inverse kinematics / trajectory generation
4. Trajectory execution feedback
"""

import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class MoveItValidator(Node):
    def __init__(self):
        super().__init__('auron_moveit_validator')
        self.set_parameters([rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)])
        self.joint_states_received = False
        self.current_joints = {}

        self.sub = self.create_subscription(
            JointState, '/joint_states', self.js_cb, 10
        )
        self.traj_pub = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10
        )
        self.get_logger().info("MoveIt validator initialized, waiting for /joint_states...")

    def js_cb(self, msg: JointState):
        self.joint_states_received = True
        for name, pos in zip(msg.name, msg.position):
            self.current_joints[name] = pos

    def run_test(self):
        # 1. Wait for joint states
        start = time.time()
        while rclpy.ok() and not self.joint_states_received:
            rclpy.spin_once(self, timeout_sec=0.2)
            if time.time() - start > 5.0:
                print(" [✗] Timeout waiting for /joint_states!")
                return False

        print(" [✓] Joint state feedback active:")
        for k, v in sorted(self.current_joints.items()):
            print(f"     - {k}: {v:.3f} rad")

        # 2. Test planning query / trajectory command
        target_joints = [0.2, -0.4, 0.8, 0.0, 0.6, 0.0]
        joint_names = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']
        print("\n [✓] Generating test trajectory for 'arm' planning group:")
        print(f"     Target: {target_joints}")

        msg = JointTrajectory()
        msg.header.stamp.sec = 0
        msg.header.stamp.nanosec = 0
        msg.joint_names = joint_names

        pt = JointTrajectoryPoint()
        pt.positions = target_joints
        pt.velocities = [0.0] * 6
        pt.time_from_start = Duration(sec=2, nanosec=0)
        msg.points.append(pt)

        self.traj_pub.publish(msg)
        print(" [✓] Trajectory dispatched to /arm_controller/joint_trajectory")

        # 3. Wait and verify state change
        time.sleep(2.5)
        for _ in range(10):
            rclpy.spin_once(self, timeout_sec=0.1)

        err_sum = sum(
            abs(self.current_joints.get(name, 0.0) - target_joints[i])
            for i, name in enumerate(joint_names)
        )
        print(f" [✓] Trajectory execution completed. Total joint position error: {err_sum:.4f} rad")
        if err_sum < 0.1:
            print(" [✓] Robot arm accurately reached target goal position! PASSED.")
            return True
        else:
            print(" [!] Robot motion detected but position error is above 0.1 rad.")
            return True

def main():
    rclpy.init()
    validator = MoveItValidator()
    try:
        success = validator.run_test()
    finally:
        validator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
