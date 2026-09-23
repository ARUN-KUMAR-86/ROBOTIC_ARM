#!/usr/bin/env python3
"""
Interactive Keyboard Teleoperation Node for Auron 6-DOF Industrial Robot.
Integrates directly with:
- MoveIt Servo (/servo_node/delta_joint_cmds)
- ros2_control (/arm_controller/joint_trajectory)
- Gripper controller (/gripper_controller/joint_trajectory)

Controls:
  A / D : Joint 1 (Base Pan)
  S / W : Joint 2 (Shoulder)
  F / R : Joint 3 (Elbow)
  G / T : Joint 4 (Wrist Roll)
  H / Y : Joint 5 (Wrist Pitch)
  J / U : Joint 6 (Tool Roll)
  O     : Open Gripper
  P     : Close Gripper
  SPACE : Emergency Stop
  0     : Home Reset
  Q     : Quit Teleoperation
"""

import math
import os
import select
import sys
import termios
import time
import tty

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.msg import JointJog
from builtin_interfaces.msg import Duration
from moveit_msgs.srv import ServoCommandType
from std_srvs.srv import SetBool

HELP_BANNER = """
============================================================
           AURON ROBOTICS - 6-DOF ARM TELEOPERATION         
============================================================
 Joint Controls:
   J1 (Base Pan):      [A] Decrease (-)   |  [D] Increase (+)
   J2 (Shoulder):      [S] Decrease (-)   |  [W] Increase (+)
   J3 (Elbow):         [F] Decrease (-)   |  [R] Increase (+)
   J4 (Wrist Roll):    [G] Decrease (-)   |  [T] Increase (+)
   J5 (Wrist Pitch):   [H] Decrease (-)   |  [Y] Increase (+)
   J6 (Tool Roll):     [J] Decrease (-)   |  [U] Increase (+)

 Gripper:
   [O] Open Gripper    |  [P] Close Gripper

 Safety & System:
   [SPACE] EMERGENCY STOP (Halt all motion immediately)
   [0]     RESET (Smoothly return arm to home 0.0 position)
   [Q]     QUIT teleoperation
============================================================
"""

class TeleopKeyboardNode(Node):
    def __init__(self):
        super().__init__('auron_teleop_keyboard')

        # Declare parameters
        self.declare_parameter('step_size_deg', 2.5)
        self.declare_parameter('gripper_step', 0.005)
        self.declare_parameter('trajectory_duration', 0.20)
        self.declare_parameter('joint_names', [
            'joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6'
        ])
        self.declare_parameter('gripper_joint_names', [
            'left_finger_joint', 'right_finger_joint'
        ])

        # Joint limits in radians
        self.joint_limits = {
            'joint_1': (-3.14159, 3.14159),
            'joint_2': (-2.0944, 2.0944),
            'joint_3': (-2.61799, 2.61799),
            'joint_4': (-3.14159, 3.14159),
            'joint_5': (-2.0944, 2.0944),
            'joint_6': (-6.28318, 6.28318),
        }
        self.gripper_limits = (0.0, 0.035)

        self.joint_names = self.get_parameter('joint_names').value
        self.gripper_joint_names = self.get_parameter('gripper_joint_names').value
        self.step_size = math.radians(self.get_parameter('step_size_deg').value)
        self.gripper_step = self.get_parameter('gripper_step').value
        self.traj_duration = self.get_parameter('trajectory_duration').value

        # Positions tracking
        self.target_positions = [0.0] * 6
        self.target_gripper = 0.035  # Start open
        self.current_positions = [0.0] * 6
        self.has_joint_feedback = False
        self.is_estop = False
        self.mode_str = "TELEOP"

        # Publishers
        self.arm_traj_pub = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10
        )
        self.servo_jog_pub = self.create_publisher(
            JointJog, '/servo_node/delta_joint_cmds', 10
        )
        self.gripper_traj_pub = self.create_publisher(
            JointTrajectory, '/gripper_controller/joint_trajectory', 10
        )

        # MoveIt Servo Service Clients
        self.switch_cmd_client = self.create_client(
            ServoCommandType, '/servo_node/switch_command_type'
        )
        self.pause_servo_client = self.create_client(
            SetBool, '/servo_node/pause_servo'
        )
        self.servo_initialized = False

        # Subscriber for live joint states
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.joint_state_sub = self.create_subscription(
            JointState, '/joint_states', self.joint_state_callback, qos
        )

        self.last_display_time = 0.0

    def init_servo(self):
        """Enable joint jog mode on MoveIt Servo if servo_node is active."""
        if self.servo_initialized:
            return
        if self.switch_cmd_client.service_is_ready():
            req = ServoCommandType.Request()
            req.command_type = 0  # 0 = JOINT_JOG
            self.switch_cmd_client.call_async(req)
            self.servo_initialized = True
            self.get_logger().info("Connected to MoveIt Servo (JOINT_JOG mode active)")

    def joint_state_callback(self, msg: JointState):
        name_to_pos = dict(zip(msg.name, msg.position))
        updated = False
        for i, name in enumerate(self.joint_names):
            if name in name_to_pos:
                val = name_to_pos[name]
                if not math.isnan(val) and not math.isinf(val):
                    self.current_positions[i] = val
                    updated = True

        if updated and not self.has_joint_feedback:
            # Sync target positions to initial joint state on first read
            self.target_positions = list(self.current_positions)
            self.has_joint_feedback = True

    def send_servo_jog(self, joint_idx, velocity):
        """Send JointJog command to MoveIt Servo pipeline."""
        self.init_servo()
        jog_msg = JointJog()
        jog_msg.header.stamp = self.get_clock().now().to_msg()
        jog_msg.header.frame_id = 'base_link'
        jog_msg.joint_names = [self.joint_names[joint_idx]]
        jog_msg.velocities = [float(velocity)]
        jog_msg.duration = 0.2
        self.servo_jog_pub.publish(jog_msg)

    def send_arm_command(self, duration_sec=None):
        """Send trajectory command directly to ros2_control arm_controller."""
        if self.is_estop:
            return

        if duration_sec is None:
            duration_sec = self.traj_duration

        msg = JointTrajectory()
        # Using zero timestamp for immediate controller execution
        msg.header.stamp.sec = 0
        msg.header.stamp.nanosec = 0
        msg.joint_names = self.joint_names

        point = JointTrajectoryPoint()
        point.positions = list(self.target_positions)
        point.velocities = [0.0] * 6
        sec = int(duration_sec)
        nanosec = int((duration_sec - sec) * 1e9)
        point.time_from_start = Duration(sec=sec, nanosec=nanosec)

        msg.points.append(point)
        self.arm_traj_pub.publish(msg)

    def send_gripper_command(self):
        """Send trajectory command directly to gripper_controller."""
        if self.is_estop:
            return

        msg = JointTrajectory()
        msg.header.stamp.sec = 0
        msg.header.stamp.nanosec = 0
        msg.joint_names = self.gripper_joint_names

        point = JointTrajectoryPoint()
        point.positions = [float(self.target_gripper), float(self.target_gripper)]
        point.velocities = [0.0, 0.0]
        point.time_from_start = Duration(sec=0, nanosec=500000000)

        msg.points.append(point)
        self.gripper_traj_pub.publish(msg)

    def emergency_stop(self):
        self.is_estop = True
        self.mode_str = "EMERGENCY STOP (ACTIVE)"
        self.target_positions = list(self.current_positions)

        # Halt trajectory
        msg = JointTrajectory()
        msg.header.stamp.sec = 0
        msg.header.stamp.nanosec = 0
        msg.joint_names = self.joint_names
        point = JointTrajectoryPoint()
        point.positions = list(self.current_positions)
        point.velocities = [0.0] * 6
        point.time_from_start = Duration(sec=0, nanosec=10000000)
        msg.points.append(point)
        self.arm_traj_pub.publish(msg)

        # Pause servo if available
        if self.pause_servo_client.service_is_ready():
            req = SetBool.Request()
            req.data = True
            self.pause_servo_client.call_async(req)

    def clear_estop(self):
        if self.is_estop:
            self.is_estop = False
            self.mode_str = "TELEOP"
            if self.pause_servo_client.service_is_ready():
                req = SetBool.Request()
                req.data = False
                self.pause_servo_client.call_async(req)

    def reset_home(self):
        self.clear_estop()
        self.mode_str = "HOMING..."
        self.target_positions = [0.0] * 6
        self.target_gripper = 0.035
        self.send_arm_command(duration_sec=2.0)
        self.send_gripper_command()
        self.mode_str = "TELEOP"

    def apply_joint_delta(self, joint_idx, delta):
        self.clear_estop()
        j_name = self.joint_names[joint_idx]
        limit_min, limit_max = self.joint_limits[j_name]
        new_val = self.target_positions[joint_idx] + delta
        new_val = max(limit_min, min(limit_max, new_val))
        self.target_positions[joint_idx] = new_val

        # Route via MoveIt Servo joint jog and arm_controller trajectory
        sign = 1.0 if delta > 0 else -1.0
        self.send_servo_jog(joint_idx, sign * 0.4)
        self.send_arm_command()

    def set_gripper(self, target_pos):
        self.clear_estop()
        self.target_gripper = max(self.gripper_limits[0], min(self.gripper_limits[1], target_pos))
        self.send_gripper_command()

    def print_dashboard(self):
        j_deg = [math.degrees(p) for p in self.target_positions]
        grip_str = "OPEN" if self.target_gripper > 0.02 else "CLOSED"

        sys.stdout.write("\r\033[K")
        sys.stdout.write(
            f"[{self.mode_str}] "
            f"J1:{j_deg[0]:+6.1f}° | J2:{j_deg[1]:+6.1f}° | J3:{j_deg[2]:+6.1f}° | "
            f"J4:{j_deg[3]:+6.1f}° | J5:{j_deg[4]:+6.1f}° | J6:{j_deg[5]:+6.1f}° | "
            f"Gripper: {grip_str}"
        )
        sys.stdout.flush()


def open_input_device():
    """Find and open an interactive TTY device even when run from ros2 launch."""
    if sys.stdin.isatty():
        return sys.stdin.fileno(), False
    try:
        fd = os.open('/dev/tty', os.O_RDWR)
        return fd, True
    except Exception:
        pass
    try:
        return sys.stdin.fileno(), False
    except Exception:
        return None, False


def get_key(fd, settings, is_tty=True, timeout=0.05):
    """Read a single key non-blockingly from specified file descriptor."""
    if fd is None:
        return ''
    try:
        if is_tty and settings is not None:
            tty.setraw(fd)
        rlist, _, _ = select.select([fd], [], [], timeout)
        if rlist:
            key = os.read(fd, 1).decode('latin1')
            if key == '\x1b':
                rlist_sub, _, _ = select.select([fd], [], [], 0.01)
                if rlist_sub:
                    seq = os.read(fd, 2).decode('latin1')
                    key = '\x1b' + seq
        else:
            key = ''
    except Exception:
        key = ''
    finally:
        if is_tty and settings is not None:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, settings)
            except Exception:
                pass
    return key


def main(args=None):
    rclpy.init(args=args)
    node = TeleopKeyboardNode()

    fd, opened_tty = open_input_device()
    orig_settings = None
    is_tty = False
    if fd is not None:
        try:
            orig_settings = termios.tcgetattr(fd)
            is_tty = True
        except Exception:
            orig_settings = None
            is_tty = False

    print(HELP_BANNER)
    node.get_logger().info("Teleoperation node ready. Listening for keyboard inputs.")

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.01)

            if fd is not None:
                key = get_key(fd, orig_settings, is_tty=is_tty, timeout=0.04)
            else:
                time.sleep(0.05)
                key = ''

            if not key:
                now = time.time()
                if now - node.last_display_time > 0.1:
                    node.print_dashboard()
                    node.last_display_time = now
                continue

            k = key.lower()

            # J1: Base Pan
            if k == 'a':
                node.apply_joint_delta(0, -node.step_size)
            elif k == 'd':
                node.apply_joint_delta(0, node.step_size)

            # J2: Shoulder
            elif k == 's':
                node.apply_joint_delta(1, -node.step_size)
            elif k == 'w':
                node.apply_joint_delta(1, node.step_size)

            # J3: Elbow
            elif k == 'f':
                node.apply_joint_delta(2, -node.step_size)
            elif k == 'r':
                node.apply_joint_delta(2, node.step_size)

            # J4: Wrist Roll
            elif k == 'g':
                node.apply_joint_delta(3, -node.step_size)
            elif k == 't':
                node.apply_joint_delta(3, node.step_size)

            # J5: Wrist Pitch
            elif k == 'h':
                node.apply_joint_delta(4, -node.step_size)
            elif k == 'y':
                node.apply_joint_delta(4, node.step_size)

            # J6: Tool Roll
            elif k == 'j':
                node.apply_joint_delta(5, -node.step_size)
            elif k == 'u':
                node.apply_joint_delta(5, node.step_size)

            # Gripper Open / Close
            elif k == 'o':
                node.set_gripper(0.035)
            elif k == 'p':
                node.set_gripper(0.0)

            # Emergency stop
            elif key == ' ':
                node.emergency_stop()

            # Reset Home
            elif key == '0':
                node.reset_home()

            # Quit
            elif k == 'q' or key == '\x03':  # Ctrl-C or 'q'
                print("\nExiting teleoperation node...")
                break

            node.print_dashboard()

    except Exception as e:
        print(f"\nTeleoperation encountered exception: {e}")
    finally:
        if fd is not None and orig_settings is not None:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, orig_settings)
            except Exception:
                pass
            if opened_tty:
                os.close(fd)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
