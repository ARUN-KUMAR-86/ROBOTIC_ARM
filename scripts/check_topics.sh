#!/usr/bin/env bash
# ==============================================================================
# Topic Validation Script for Auron Robot System
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

source /opt/ros/jazzy/setup.bash
[ -f /home/arun/auron_robot_ws/install/setup.bash ] && source /home/arun/auron_robot_ws/install/setup.bash

echo -e "${BLUE}>>> Checking Active ROS 2 Topics...${NC}"

REQUIRED_TOPICS=(
    "/joint_states"
    "/tf"
    "/tf_static"
    "/robot_description"
    "/arm_controller/joint_trajectory"
    "/gripper_controller/joint_trajectory"
    "/camera/image_raw"
    "/camera/camera_info"
)

TOPICS=""
for i in 1 2 3 4 5; do
    TOPICS=$(ros2 topic list 2>/dev/null)
    COUNT=$(echo "$TOPICS" | wc -l)
    if [ "$COUNT" -ge 15 ]; then
        break
    fi
    sleep 1
done

ALL_PASSED=true

for t in "${REQUIRED_TOPICS[@]}"; do
    if echo "$TOPICS" | grep -qx "$t"; then
        echo -e " [✓] Topic $t: ${GREEN}ACTIVE${NC}"
    else
        echo -e " [✗] Topic $t: ${RED}NOT FOUND${NC}"
        ALL_PASSED=false
    fi
done

if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}>>> All essential topics are active and publishing!${NC}"
else
    echo -e "${RED}>>> Some required topics are missing. Ensure simulation.launch.py is running.${NC}"
fi
