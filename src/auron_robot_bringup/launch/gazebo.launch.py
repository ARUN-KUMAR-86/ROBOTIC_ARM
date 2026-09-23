#!/usr/bin/env python3
"""Launch Gazebo Harmonic with Auron industrial robot and bridge."""

import os
import signal
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
    SetEnvironmentVariable,
)
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


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
    pkg_description = get_package_share_directory('auron_robot_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world_path = os.path.join(pkg_bringup, 'worlds', 'industrial_world.sdf')
    xacro_file = os.path.join(pkg_description, 'urdf', 'auron_robot.urdf.xacro')
    bridge_config = os.path.join(pkg_bringup, 'config', 'gz_bridge.yaml')

    # Robot description
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    # Ensure Gazebo can find meshes
    # GZ_SIM_RESOURCE_PATH needs to include parent directory of auron_robot_description
    ws_src_dir = os.path.abspath(os.path.join(pkg_description, '..'))
    
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[ws_src_dir, ':', os.environ.get('GZ_SIM_RESOURCE_PATH', '')]
    )

    # Launch Gazebo Sim
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': f'-r -v 3 {world_path}',
            'on_exit_shutdown': 'true',
        }.items(),
    )

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )

    # Spawn Robot Entity in Gazebo Sim
    # Placed on stand at z=0.30m
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name', 'auron_robot',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.30'
        ]
    )

    # ROS-GZ Parameter Bridge
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config
        }],
        output='screen'
    )

    shutdown_handler = RegisterEventHandler(
        event_handler=OnShutdown(
            on_shutdown=lambda event, context: _cleanup_zombie_gazebo()
        )
    )

    return LaunchDescription([
        shutdown_handler,
        set_gz_resource_path,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        gz_bridge,
    ])
