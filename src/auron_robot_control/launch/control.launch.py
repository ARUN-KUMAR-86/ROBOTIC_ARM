#!/usr/bin/env python3
"""Launch ros2_control controller spawners for Auron Robot."""

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Spawner for joint_state_broadcaster
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
        output='screen',
    )

    # Spawner for arm_controller (JointTrajectoryController)
    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'arm_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
        output='screen',
    )

    # Spawner for gripper_controller
    gripper_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'gripper_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
        output='screen',
    )

    return LaunchDescription([
        joint_state_broadcaster_spawner,
        arm_controller_spawner,
        gripper_controller_spawner,
    ])
