#!/usr/bin/env python3
"""
Launch file for Auron Robotics Web Dashboard & ROS 2 WebSocket Bridge.
Usage:
  ros2 launch auron_robot_bringup web_control.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, LogInfo
from launch_ros.actions import Node


def generate_launch_description():
    pkg_bringup = get_package_share_directory('auron_robot_bringup')
    dashboard_dir = '/home/arun/auron_robot_ws/web_dashboard'

    # 1. Rosbridge WebSocket Server Node
    rosbridge_node = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        output='screen',
        parameters=[{
            'port': 9090,
            'address': '0.0.0.0',
            'retry_startup_delay': 2.0,
        }]
    )

    # 2. Python Web Server for Dashboard UI (port 8080)
    web_server_cmd = ExecuteProcess(
        cmd=['python3', os.path.join(dashboard_dir, 'web_server.py')],
        output='screen',
    )

    return LaunchDescription([
        LogInfo(msg="Launching Auron Web Control Dashboard on http://localhost:8080 and ws://localhost:9090"),
        rosbridge_node,
        web_server_cmd,
    ])
