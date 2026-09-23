#!/usr/bin/env bash
# ==============================================================================
# Build Script for Auron Robot Workspace
# ==============================================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

WS_DIR="/home/arun/auron_robot_ws"
echo -e "${BLUE}>>> Building Auron Robot Workspace in ${WS_DIR} ...${NC}"

# Source ROS 2 Jazzy underlay
source /opt/ros/jazzy/setup.bash

cd "$WS_DIR"

# Generate fresh meshes if needed
if [ ! -f "src/auron_robot_description/meshes/base/base_pedestal.stl" ]; then
    echo "Generating procedural STL meshes..."
    python3 src/auron_robot_description/meshes/generate_meshes.py
fi

# Build workspace packages
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

echo -e "${GREEN}>>> Build completed successfully!${NC}"
echo -e "${BLUE}>>> To source the workspace in your current terminal run:${NC}"
echo -e "${GREEN}source ${WS_DIR}/install/setup.bash${NC}"
