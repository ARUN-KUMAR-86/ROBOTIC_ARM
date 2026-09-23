#!/usr/bin/env bash
# ==============================================================================
# TF Tree Validation Script for Auron Robot
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

source /opt/ros/jazzy/setup.bash
[ -f /home/arun/auron_robot_ws/install/setup.bash ] && source /home/arun/auron_robot_ws/install/setup.bash

echo -e "${BLUE}>>> Checking TF Tree connectivity...${NC}"

FRAMES=(
    "world"
    "base_link"
    "base_rotation_link"
    "shoulder_link"
    "upper_arm_link"
    "elbow_link"
    "forearm_link"
    "wrist_1_link"
    "wrist_2_link"
    "wrist_3_link"
    "tool0"
    "gripper_base"
    "camera_link"
)

echo -e "${BLUE}>>> Testing transforms relative to base_link:${NC}"
for f in "${FRAMES[@]}"; do
    if [ "$f" = "base_link" ]; then continue; fi
    if timeout 3 ros2 run tf2_ros tf2_echo base_link "$f" 2>&1 | grep -q "Translation:"; then
        echo -e " [✓] Transform base_link -> $f: ${GREEN}OK${NC}"
    else
        echo -e " [✗] Transform base_link -> $f: ${RED}FAILED / TIMEOUT${NC}"
    fi
done
