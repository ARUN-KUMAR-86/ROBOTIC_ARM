#!/usr/bin/env bash
# ==============================================================================
# Auron Robot - Simulation & Process Cleanup Utility
# ==============================================================================

echo "Stopping any running Auron Robot and Gazebo processes..."

# Kill Gazebo Sim and Ruby processes
killall -9 gz-sim-server gz ruby 2>/dev/null || true

# Kill ROS bridges and nodes
pkill -9 -f "parameter_bridge" 2>/dev/null || true
pkill -9 -f "rosbridge_websocket" 2>/dev/null || true
pkill -9 -f "web_server.py" 2>/dev/null || true
pkill -9 -f "rviz2" 2>/dev/null || true
pkill -9 -f "move_group" 2>/dev/null || true
pkill -9 -f "servo_node" 2>/dev/null || true
pkill -9 -f "robot_state_publisher" 2>/dev/null || true
pkill -9 -f "auron_camera_node" 2>/dev/null || true
pkill -9 -f "auron_vision_node" 2>/dev/null || true

echo "Cleanup complete. All simulation processes have been stopped."
