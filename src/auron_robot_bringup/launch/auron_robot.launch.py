#!/usr/bin/env python3
"""
Master Launch File for Auron Robotics 6-DOF Robotic Arm.
Starts the complete integrated system:
 1. Gazebo Harmonic
 2. Industrial world
 3. Robot description
 4. robot_state_publisher
 5. Gazebo robot spawn
 6. gz_ros2_control
 7. joint_state_broadcaster
 8. arm_controller
 9. gripper_controller
10. MoveIt 2 (move_group)
11. MoveIt Servo (servo_node)
12. RViz2 (with MoveIt plugin and TF)
13. Keyboard teleoperation
14. Laptop camera (if /dev/video0 is available)
15. Vision node (color detection and TF2 broadcasting)
16. TF tree
17. Required Gazebo/ROS bridges

Usage:
  ros2 launch auron_robot_bringup auron_robot.launch.py
"""

import os
import signal
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnShutdown
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _cleanup_zombie_gazebo():
    """Kill any orphaned gz sim server or parameter_bridge processes to avoid clock conflicts."""
    my_pid = os.getpid()
    for pid_str in os.listdir('/proc'):
        if not pid_str.isdigit():
            continue
        pid = int(pid_str)
        if pid == my_pid:
            continue
        try:
            exe = os.readlink(f'/proc/{pid}/exe')
            if 'ruby' in exe or 'parameter_bridge' in exe:
                with open(f'/proc/{pid}/cmdline', 'rb') as f:
                    cmd = f.read().decode('utf-8', errors='ignore')
                    if 'gz' in cmd or 'sim' in cmd or 'parameter_bridge' in cmd:
                        os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, FileNotFoundError):
            pass


def generate_launch_description():
    # Clean any stale Gazebo instances from previous interrupted runs
    _cleanup_zombie_gazebo()
    pkg_bringup = get_package_share_directory('auron_robot_bringup')
    pkg_control = get_package_share_directory('auron_robot_control')
    pkg_moveit = get_package_share_directory('auron_robot_moveit_config')
    pkg_camera = get_package_share_directory('auron_robot_camera')
    pkg_vision = get_package_share_directory('auron_robot_vision')
    pkg_teleop = get_package_share_directory('auron_robot_teleop')

    # Launch configuration options
    use_gazebo = LaunchConfiguration('use_gazebo')
    use_moveit = LaunchConfiguration('use_moveit')
    use_rviz = LaunchConfiguration('use_rviz')
    use_servo = LaunchConfiguration('use_servo')
    use_teleop = LaunchConfiguration('use_teleop')
    use_camera = LaunchConfiguration('use_camera')
    use_vision = LaunchConfiguration('use_vision')
    camera_device = LaunchConfiguration('camera_device')
    use_web = LaunchConfiguration('use_web')

    declare_use_gazebo = DeclareLaunchArgument(
        'use_gazebo', default_value='true',
        description='Launch Gazebo Harmonic simulation'
    )
    declare_use_moveit = DeclareLaunchArgument(
        'use_moveit', default_value='true',
        description='Launch MoveIt 2 motion planning system'
    )
    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Launch RViz2 visualization'
    )
    declare_use_servo = DeclareLaunchArgument(
        'use_servo', default_value='true',
        description='Launch MoveIt Servo node'
    )
    declare_use_teleop = DeclareLaunchArgument(
        'use_teleop', default_value='true',
        description='Launch keyboard teleoperation node'
    )
    declare_use_camera = DeclareLaunchArgument(
        'use_camera', default_value='false',
        description='Launch laptop camera if available (set false when Gazebo camera is active)'
    )
    declare_use_vision = DeclareLaunchArgument(
        'use_vision', default_value='true',
        description='Launch vision detection node if camera available'
    )
    declare_camera_device = DeclareLaunchArgument(
        'camera_device', default_value='/dev/video0',
        description='Path to video device'
    )
    declare_use_web = DeclareLaunchArgument(
        'use_web', default_value='true',
        description='Launch Web Control Dashboard and rosbridge WebSocket'
    )

    # 1. Gazebo Harmonic Simulation (SDF World, Spawner, Bridges, Robot State Publisher)
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'gazebo.launch.py')
        ),
        condition=IfCondition(use_gazebo),
    )

    # 2. ros2_control Controller Spawners (Delayed to allow Gazebo model creation)
    # Spawns: joint_state_broadcaster, arm_controller, gripper_controller
    control_launch = TimerAction(
        period=4.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_control, 'launch', 'control.launch.py')
                ),
                condition=IfCondition(use_gazebo),
            )
        ]
    )

    # 3. MoveIt 2 System (move_group, RViz2, MoveIt Servo)
    # Delayed to allow ros2_control controllers to reach ACTIVE state
    moveit_launch = TimerAction(
        period=8.5,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_moveit, 'launch', 'moveit.launch.py')
                ),
                launch_arguments={
                    'use_rviz': use_rviz,
                    'use_sim_time': use_gazebo,
                    'use_servo': use_servo,
                }.items(),
                condition=IfCondition(use_moveit),
            )
        ]
    )

    # 4. Camera & Vision Pipeline
    camera_launch = TimerAction(
        period=2.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_camera, 'launch', 'camera.launch.py')
                ),
                launch_arguments={
                    'camera_device': camera_device,
                    'use_sim_time': use_gazebo,
                }.items(),
                condition=IfCondition(use_camera),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_vision, 'launch', 'vision.launch.py')
                ),
                launch_arguments={
                    'use_sim_time': use_gazebo,
                }.items(),
                condition=IfCondition(use_vision),
            ),
        ]
    )

    # 5. Keyboard Teleoperation (Integrated in the master launch terminal)
    teleop_launch = TimerAction(
        period=9.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_teleop, 'launch', 'teleop.launch.py')
                ),
                launch_arguments={
                    'use_sim_time': use_gazebo,
                }.items(),
                condition=IfCondition(use_teleop),
            )
        ]
    )

    # 6. Web Dashboard & ROS 2 WebSocket Bridge
    web_launch = TimerAction(
        period=3.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_bringup, 'launch', 'web_control.launch.py')
                ),
                condition=IfCondition(use_web),
            )
        ]
    )

    shutdown_handler = RegisterEventHandler(
        event_handler=OnShutdown(
            on_shutdown=lambda event, context: _cleanup_zombie_gazebo()
        )
    )

    return LaunchDescription([
        shutdown_handler,
        declare_use_gazebo,
        declare_use_moveit,
        declare_use_rviz,
        declare_use_servo,
        declare_use_teleop,
        declare_use_camera,
        declare_use_vision,
        declare_camera_device,
        declare_use_web,
        gazebo_launch,
        control_launch,
        moveit_launch,
        camera_launch,
        teleop_launch,
        web_launch,
    ])
