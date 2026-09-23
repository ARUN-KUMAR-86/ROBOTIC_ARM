#!/usr/bin/env bash
# ==============================================================================
# Simulation Runner for Auron Robot
# ==============================================================================
set -e

WS_DIR="/home/arun/auron_robot_ws"

source /opt/ros/jazzy/setup.bash
if [ -f "${WS_DIR}/install/setup.bash" ]; then
    source "${WS_DIR}/install/setup.bash"
else
    echo "Workspace install/setup.bash not found. Running build.sh first..."
    bash "${WS_DIR}/scripts/build.sh"
    source "${WS_DIR}/install/setup.bash"
fi

echo "============================================================"
echo " Starting Auron 6-DOF Industrial Robot Simulation"
echo " Options:"
echo "   --no-gazebo   Disable Gazebo, start RViz + State Publisher"
echo "   --no-moveit   Disable MoveIt move_group"
echo "   --teleop      Enable keyboard teleoperation in launch"
echo "============================================================"

cleanup() {
    echo "Cleaning up simulation processes..."
    # Terminate any leftover Gazebo or bridge processes
    killall -9 gz-sim-server gz 2>/dev/null || true
    pkill -9 -f "parameter_bridge" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Clean any existing stale simulator instances before launching
cleanup

# Pass all incoming flags to the master launch file
ros2 launch auron_robot_bringup simulation.launch.py "$@"
