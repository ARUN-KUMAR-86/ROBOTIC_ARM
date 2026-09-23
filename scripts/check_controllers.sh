#!/usr/bin/env bash
# ==============================================================================
# Controller Validation Script for Auron Robot ros2_control
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

source /opt/ros/jazzy/setup.bash
[ -f /home/arun/auron_robot_ws/install/setup.bash ] && source /home/arun/auron_robot_ws/install/setup.bash

echo -e "${BLUE}>>> Checking ros2_control Controller Manager and Spawners...${NC}"

FOUND_CM=0
for i in 1 2 3 4 5; do
    if ros2 service list 2>/dev/null | grep -q "/controller_manager/list_controllers"; then
        FOUND_CM=1
        break
    fi
    sleep 1
done

if [ "$FOUND_CM" -eq 0 ]; then
    echo -e "${RED}[✗] /controller_manager service is not reachable! Is Gazebo Sim or ros2_control running?${NC}"
    exit 1
fi

if command -v ros2 >/dev/null && ros2 control -h >/dev/null 2>&1; then
    CONTROLLERS_OUTPUT=$(ros2 control list_controllers 2>/dev/null)
else
    CONTROLLERS_OUTPUT=$(ros2 service call /controller_manager/list_controllers controller_manager_msgs/srv/ListControllers {} 2>/dev/null)
fi
echo "$CONTROLLERS_OUTPUT"

echo -e "${BLUE}>>> Verifying Controller Lifecycle States:${NC}"

verify_active() {
    local name="$1"
    if echo "$CONTROLLERS_OUTPUT" | grep -E "($name.*state='active'|^$name\s+\[.*active\]|^$name.*active)"; then
        echo -e " [✓] $name: ${GREEN}ACTIVE [OK]${NC}"
    else
        echo -e " [✗] $name: ${RED}NOT ACTIVE or NOT FOUND!${NC}"
    fi
}

verify_active "joint_state_broadcaster"
verify_active "arm_controller"
verify_active "gripper_controller"
