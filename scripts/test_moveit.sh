#!/usr/bin/env bash
# ==============================================================================
# MoveIt 2 Motion Planning Validation Runner
# ==============================================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

source /opt/ros/jazzy/setup.bash
[ -f /home/arun/auron_robot_ws/install/setup.bash ] && source /home/arun/auron_robot_ws/install/setup.bash

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}       AURON ROBOTICS - MOVEIT 2 MOTION PLANNING TEST       ${NC}"
echo -e "${BLUE}============================================================${NC}"

python3 /home/arun/auron_robot_ws/scripts/test_moveit.py
