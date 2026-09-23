#!/usr/bin/env python3
"""Launch robot_state_publisher and RViz2 for Auron robot description."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_description = get_package_share_directory('auron_robot_description')
    
    xacro_file = os.path.join(pkg_description, 'urdf', 'auron_robot.urdf.xacro')
    rviz_config_file = os.path.join(pkg_description, 'rviz', 'auron_robot.rviz')

    use_rviz = LaunchConfiguration('use_rviz')
    use_jsp_gui = LaunchConfiguration('use_jsp_gui')

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Whether to start RViz2'
    )

    declare_use_jsp_gui = DeclareLaunchArgument(
        'use_jsp_gui',
        default_value='true',
        description='Whether to start joint_state_publisher_gui'
    )

    # Robot State Publisher
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description, 'use_sim_time': False}]
    )

    # Joint State Publisher GUI
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        condition=IfCondition(use_jsp_gui)
    )

    # RViz2 Node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        condition=IfCondition(use_rviz)
    )

    return LaunchDescription([
        declare_use_rviz,
        declare_use_jsp_gui,
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz_node,
    ])
