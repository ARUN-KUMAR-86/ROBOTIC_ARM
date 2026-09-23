#!/usr/bin/env python3
"""Launch keyboard teleoperation node for Auron robot."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_teleop = get_package_share_directory('auron_robot_teleop')
    config_file = os.path.join(pkg_teleop, 'config', 'teleop.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true'
    )

    teleop_node = Node(
        package='auron_robot_teleop',
        executable='teleop_keyboard',
        name='auron_teleop_keyboard',
        output='screen',
        emulate_tty=True,
        parameters=[config_file, {'use_sim_time': use_sim_time}]
    )

    return LaunchDescription([
        declare_use_sim_time,
        teleop_node
    ])
