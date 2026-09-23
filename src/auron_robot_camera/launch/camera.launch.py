#!/usr/bin/env python3
"""Launch Auron camera node."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_camera = get_package_share_directory('auron_robot_camera')
    default_calib = os.path.join(pkg_camera, 'config', 'camera_calibration.yaml')

    camera_device = LaunchConfiguration('camera_device')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_camera_device = DeclareLaunchArgument(
        'camera_device',
        default_value='/dev/video0',
        description='V4L2 camera device path or index'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true'
    )

    camera_node = Node(
        package='auron_robot_camera',
        executable='camera_node',
        name='auron_camera_node',
        output='screen',
        parameters=[{
            'camera_device': camera_device,
            'image_width': 640,
            'image_height': 480,
            'frame_rate': 30.0,
            'frame_id': 'camera_optical_frame',
            'calibration_file': default_calib,
            'use_sim_time': use_sim_time,
        }]
    )

    return LaunchDescription([
        declare_camera_device,
        declare_use_sim_time,
        camera_node,
    ])
