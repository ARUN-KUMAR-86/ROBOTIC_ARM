#!/usr/bin/env python3
"""Launch computer vision node for Auron robot."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    detector_type = LaunchConfiguration('detector_type')
    enable_gui = LaunchConfiguration('enable_gui')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_detector = DeclareLaunchArgument(
        'detector_type',
        default_value='color',
        description='Detector implementation: color or ai'
    )

    declare_gui = DeclareLaunchArgument(
        'enable_gui',
        default_value='false',
        description='Display standalone OpenCV window'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true'
    )

    vision_node = Node(
        package='auron_robot_vision',
        executable='vision_node',
        name='auron_vision_node',
        output='screen',
        parameters=[{
            'detector_type': detector_type,
            'min_contour_area': 300,
            'estimated_object_distance': 0.45,
            'enable_gui_display': enable_gui,
            'use_sim_time': use_sim_time,
        }]
    )

    return LaunchDescription([
        declare_detector,
        declare_gui,
        declare_use_sim_time,
        vision_node,
    ])
