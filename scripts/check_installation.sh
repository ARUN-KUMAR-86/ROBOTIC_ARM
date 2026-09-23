#!/usr/bin/env bash
# ==============================================================================
# Auron Robot System Installation & Dependency Checker
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}       AURON ROBOTICS - ENVIRONMENT DEPENDENCY CHECK        ${NC}"
echo -e "${BLUE}============================================================${NC}"

ERRORS=0
MISSING_PKGS=()

# 1. OS Check
OS_DISTRO=$(lsb_release -sc 2>/dev/null)
if [ "$OS_DISTRO" = "noble" ]; then
    echo -e " [✓] Operating System: Ubuntu 24.04 LTS (noble) ${GREEN}OK${NC}"
else
    echo -e " [!] Operating System: $OS_DISTRO ${YELLOW}(Target is Ubuntu 24.04 noble)${NC}"
fi

# 2. ROS 2 Distro Check
if [ "$ROS_DISTRO" = "jazzy" ]; then
    echo -e " [✓] ROS 2 Distribution: ROS 2 Jazzy Jalisco ${GREEN}OK${NC}"
else
    echo -e " [✗] ROS_DISTRO is '$ROS_DISTRO' (Expected: jazzy) ${RED}FAIL${NC}"
    ERRORS=$((ERRORS+1))
fi

# 3. Gazebo Harmonic Check
if command -v gz &> /dev/null; then
    GZ_VER=$(gz sim --version 2>&1 | head -n 1)
    echo -e " [✓] Gazebo Simulator: $GZ_VER ${GREEN}OK${NC}"
else
    echo -e " [✗] Gazebo Sim (gz) not found in PATH! ${RED}FAIL${NC}"
    ERRORS=$((ERRORS+1))
fi

# Pre-fetch package list to avoid broken pipe errors
INSTALLED_ROS_PKGS=$(ros2 pkg list 2>/dev/null)

# 4. ROS-GZ Integration Check
if echo "$INSTALLED_ROS_PKGS" | grep -qx "ros_gz_sim"; then
    echo -e " [✓] ros_gz_sim package: ${GREEN}OK${NC}"
else
    echo -e " [✗] ros_gz_sim missing! ${RED}FAIL${NC}"
    MISSING_PKGS+=("ros-jazzy-ros-gz")
fi

# 5. ros2_control & Controllers Check
if echo "$INSTALLED_ROS_PKGS" | grep -qx "controller_manager"; then
    echo -e " [✓] ros2_control (controller_manager): ${GREEN}OK${NC}"
else
    echo -e " [✗] controller_manager missing! ${RED}FAIL${NC}"
    MISSING_PKGS+=("ros-jazzy-controller-manager")
fi

if echo "$INSTALLED_ROS_PKGS" | grep -qx "joint_trajectory_controller"; then
    echo -e " [✓] ros2_controllers (joint_trajectory_controller): ${GREEN}OK${NC}"
else
    echo -e " [✗] joint_trajectory_controller missing! ${RED}FAIL${NC}"
    MISSING_PKGS+=("ros-jazzy-joint-trajectory-controller")
fi

# 6. gz_ros2_control Check
if dpkg -l | grep -q "ros-jazzy-gz-ros2-control"; then
    echo -e " [✓] gz_ros2_control: ${GREEN}OK${NC}"
else
    echo -e " [!] gz_ros2_control package is NOT installed in system ${YELLOW}WARNING${NC}"
    MISSING_PKGS+=("ros-jazzy-gz-ros2-control")
fi

# 7. MoveIt 2 Check
if dpkg -l | grep -q "ros-jazzy-moveit-ros-move-group"; then
    echo -e " [✓] MoveIt 2 (move_group): ${GREEN}OK${NC}"
else
    echo -e " [!] MoveIt 2 is NOT installed in system ${YELLOW}WARNING${NC}"
    MISSING_PKGS+=("ros-jazzy-moveit" "ros-jazzy-moveit-servo")
fi

# 8. RViz2 Check
if command -v rviz2 &> /dev/null; then
    echo -e " [✓] RViz2: ${GREEN}OK${NC}"
else
    echo -e " [✗] rviz2 missing! ${RED}FAIL${NC}"
    MISSING_PKGS+=("ros-jazzy-rviz2")
fi

# 9. Python & OpenCV Check
if python3 -c "import cv2, numpy, cv_bridge" &> /dev/null; then
    CV_VER=$(python3 -c "import cv2; print(cv2.__version__)")
    echo -e " [✓] Python OpenCV ($CV_VER) & cv_bridge: ${GREEN}OK${NC}"
else
    echo -e " [✗] Python OpenCV or cv_bridge missing! ${RED}FAIL${NC}"
    MISSING_PKGS+=("python3-opencv" "ros-jazzy-cv-bridge")
fi

# 10. Linux Video Camera Device
if [ -e "/dev/video0" ]; then
    echo -e " [✓] Camera device /dev/video0: ${GREEN}Detected${NC}"
else
    echo -e " [!] Camera device /dev/video0: ${YELLOW}Not currently attached (Fallback generator will be used)${NC}"
fi

echo -e "${BLUE}============================================================${NC}"

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo -e "${YELLOW}To install all missing or recommended packages, run:${NC}"
    echo -e "${GREEN}sudo apt update && sudo apt install -y ${MISSING_PKGS[*]}${NC}"
    echo -e "${BLUE}============================================================${NC}"
else
    echo -e "${GREEN}All core system dependencies are satisfied!${NC}"
fi
