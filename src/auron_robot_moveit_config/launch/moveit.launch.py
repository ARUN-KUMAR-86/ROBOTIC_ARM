#!/usr/bin/env python3
"""Launch MoveIt 2 move_group and RViz2 for Auron industrial robot."""

import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    abs_file_path = os.path.join(pkg_path, file_path)
    try:
        with open(abs_file_path, 'r') as file:
            return file.read()
    except EnvironmentError:
        return None

def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    abs_file_path = os.path.join(pkg_path, file_path)
    try:
        with open(abs_file_path, 'r') as file:
            return yaml.safe_load(file)
    except EnvironmentError:
        return None

def generate_launch_description():
    pkg_description = get_package_share_directory('auron_robot_description')
    pkg_moveit = get_package_share_directory('auron_robot_moveit_config')

    use_rviz = LaunchConfiguration('use_rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_servo = LaunchConfiguration('use_servo')

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Whether to start MoveIt RViz'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    declare_use_servo = DeclareLaunchArgument(
        'use_servo',
        default_value='true',
        description='Whether to start MoveIt Servo node'
    )

    # Robot description
    xacro_file = os.path.join(pkg_description, 'urdf', 'auron_robot.urdf.xacro')
    robot_description_content = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)
    robot_description = {'robot_description': robot_description_content}

    # Robot semantic description (SRDF)
    robot_description_semantic_content = load_file('auron_robot_moveit_config', 'config/auron_robot.srdf')
    robot_description_semantic = {'robot_description_semantic': robot_description_semantic_content}

    # Kinematics
    kinematics_yaml = load_yaml('auron_robot_moveit_config', 'config/kinematics.yaml')
    robot_description_kinematics = {'robot_description_kinematics': kinematics_yaml}

    # Joint limits
    joint_limits_yaml = load_yaml('auron_robot_moveit_config', 'config/joint_limits.yaml')
    robot_description_planning = {'robot_description_planning': joint_limits_yaml}

    # Planning pipeline (OMPL)
    ompl_planning_pipeline_config = {
        'planning_pipelines': ['ompl'],
        'default_planning_pipeline': 'ompl',
        'planning_plugin': 'ompl_interface/OMPLPlanner',
        'ompl': {
            'planning_plugin': 'ompl_interface/OMPLPlanner',
            'planning_plugins': ['ompl_interface/OMPLPlanner'],
            'request_adapters': [
                'default_planning_request_adapters/ResolveConstraintFrames',
                'default_planning_request_adapters/ValidateWorkspaceBounds',
                'default_planning_request_adapters/CheckStartStateBounds',
                'default_planning_request_adapters/CheckStartStateCollision',
            ],
            'response_adapters': [
                'default_planning_response_adapters/AddTimeOptimalParameterization',
                'default_planning_response_adapters/ValidateSolution',
                'default_planning_response_adapters/DisplayMotionPath',
            ],
            'start_state_max_bounds_error': 0.1,
        }
    }
    ompl_yaml = load_yaml('auron_robot_moveit_config', 'config/ompl_planning.yaml')
    if ompl_yaml:
        ompl_planning_pipeline_config['ompl'].update(ompl_yaml)

    # MoveIt controller manager configuration
    controllers_yaml = load_yaml('auron_robot_moveit_config', 'config/moveit_controllers.yaml')
    moveit_controllers = {
        'moveit_simple_controller_manager': controllers_yaml['moveit_simple_controller_manager'],
        'moveit_controller_manager': 'moveit_simple_controller_manager/MoveItSimpleControllerManager',
    }

    # Trajectory execution parameters
    trajectory_execution = {
        'moveit_manage_controllers': True,
        'trajectory_execution.allowed_execution_duration_scaling': 1.2,
        'trajectory_execution.allowed_goal_duration_margin': 0.5,
        'trajectory_execution.allowed_start_tolerance': 0.01,
    }

    # Planning Scene Monitor
    planning_scene_monitor_parameters = {
        'publish_planning_scene': True,
        'publish_geometry_updates': True,
        'publish_state_updates': True,
        'publish_transforms_updates': True,
    }

    # Move Group Node
    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            robot_description_planning,
            ompl_planning_pipeline_config,
            trajectory_execution,
            moveit_controllers,
            planning_scene_monitor_parameters,
            {'use_sim_time': use_sim_time},
        ],
    )

    # MoveIt RViz
    rviz_config_file = os.path.join(pkg_moveit, 'rviz', 'moveit.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            robot_description_planning,
            {'use_sim_time': use_sim_time},
        ],
        condition=IfCondition(use_rviz),
    )

    # MoveIt Servo Node
    servo_yaml = load_yaml('auron_robot_moveit_config', 'config/moveit_servo.yaml')
    servo_params = {'moveit_servo': servo_yaml}
    acceleration_filter_update_period = {'update_period': 0.02}
    planning_group_name = {'planning_group_name': 'arm'}

    servo_node = Node(
        package='moveit_servo',
        executable='servo_node',
        name='servo_node',
        output='screen',
        parameters=[
            servo_params,
            acceleration_filter_update_period,
            planning_group_name,
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            robot_description_planning,
            {'use_sim_time': use_sim_time},
        ],
        condition=IfCondition(use_servo),
    )

    return LaunchDescription([
        declare_use_rviz,
        declare_use_sim_time,
        declare_use_servo,
        move_group_node,
        rviz_node,
        servo_node,
    ])
