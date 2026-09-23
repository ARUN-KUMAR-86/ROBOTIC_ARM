#!/usr/bin/env python3
"""
Master simulation launch file for Auron 6-DOF industrial robot.
Aliases to auron_robot.launch.py for backward compatibility.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg_bringup = get_package_share_directory('auron_robot_bringup')
    auron_robot_launch = os.path.join(pkg_bringup, 'launch', 'auron_robot.launch.py')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(auron_robot_launch)
        )
    ])
