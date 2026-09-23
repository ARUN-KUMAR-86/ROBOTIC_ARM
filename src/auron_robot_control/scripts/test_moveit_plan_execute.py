#!/usr/bin/env python3
"""Test script to verify MoveIt 2 planning and execution to Gazebo arm_controller."""
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint
from sensor_msgs.msg import JointState


class MoveItTester(Node):
    def __init__(self):
        super().__init__('moveit_plan_execute_tester')
        self.set_parameters([rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)])
        self.client = ActionClient(self, MoveGroup, '/move_action')
        self.joint_state_sub = self.create_subscription(JointState, '/joint_states', self.js_cb, 10)
        self.latest_js = {}

    def js_cb(self, msg):
        self.latest_js = dict(zip(msg.name, msg.position))

    def run_test(self):
        self.get_logger().info("Waiting for MoveGroup action server (/move_action)...")
        if not self.client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error("MoveGroup action server not available!")
            return False

        self.get_logger().info("Connected to MoveGroup! Building target pose goal...")
        goal = MoveGroup.Goal()
        goal.planning_options.plan_only = False
        goal.request.group_name = 'arm'
        goal.request.num_planning_attempts = 5
        goal.request.allowed_planning_time = 5.0

        # Target: Nominal test position
        target_joints = {
            'joint_1': 0.35,
            'joint_2': -0.40,
            'joint_3': 0.90,
            'joint_4': 0.15,
            'joint_5': 0.60,
            'joint_6': -0.20,
        }

        constraints = Constraints()
        for j_name, pos in target_joints.items():
            jc = JointConstraint()
            jc.joint_name = j_name
            jc.position = pos
            jc.tolerance_above = 0.05
            jc.tolerance_below = 0.05
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)

        goal.request.goal_constraints.append(constraints)

        self.get_logger().info("Sending Plan & Execute request to MoveGroup...")
        send_goal_future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_goal_future)
        goal_handle = send_goal_future.result()

        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected by MoveGroup!")
            return False

        self.get_logger().info("Goal accepted! Waiting for execution trajectory to reach Gazebo...")
        get_result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, get_result_future)
        result = get_result_future.result().result

        self.get_logger().info(f"MoveGroup result error_code: {result.error_code.val}")

        # Settle and read live feedback from Gazebo /joint_states
        time.sleep(1.0)
        for _ in range(10):
            rclpy.spin_once(self, timeout_sec=0.1)

        success = True
        self.get_logger().info("--- Physical Joint Verification (Gazebo /joint_states) ---")
        for j, val in target_joints.items():
            cur = self.latest_js.get(j, 0.0)
            diff = abs(cur - val)
            self.get_logger().info(f"  {j}: target={val:+6.2f} rad | actual={cur:+6.2f} rad | diff={diff:.4f}")
            if diff > 0.08:
                success = False

        if result.error_code.val == 1 and success:
            self.get_logger().info("[SUCCESS] MoveIt 2 Plan -> Execute -> Gazebo trajectory execution VERIFIED!")
            return True
        else:
            self.get_logger().warn("[FAILED] MoveIt execution did not achieve target tolerances.")
            return False


def main(args=None):
    rclpy.init(args=args)
    tester = MoveItTester()
    res = tester.run_test()
    tester.destroy_node()
    rclpy.shutdown()
    exit(0 if res else 1)


if __name__ == '__main__':
    main()
