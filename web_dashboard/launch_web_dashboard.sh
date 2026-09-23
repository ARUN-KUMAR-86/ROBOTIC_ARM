#!/usr/bin/env bash
# ==============================================================================
# Auron Robotics Web Dashboard Launcher
# Starts rosbridge_websocket (port 9090), web server (port 8080), and opens UI
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="/home/arun/auron_robot_ws"

echo "============================================================"
echo "    AURON ROBOTICS: ARM & MODERN HAND WEB CONTROL"
echo "============================================================"

# 1. Source ROS 2 Jazzy
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
    echo "[INFO] Sourced ROS 2 Jazzy."
fi

# 2. Source Workspace if built
if [ -f "$WS_DIR/install/setup.bash" ]; then
    source "$WS_DIR/install/setup.bash"
    echo "[INFO] Sourced Auron Robot workspace."
fi

# 3. Check / Start rosbridge_websocket (ws://localhost:9090)
if ss -tuln | grep -q ":9090 "; then
    echo "[INFO] rosbridge_websocket is already running on port 9090."
else
    echo "[INFO] Launching rosbridge_websocket on port 9090..."
    setsid ros2 run rosbridge_server rosbridge_websocket > /tmp/rosbridge_web.log 2>&1 &
    sleep 2.0
fi

# 4. Check / Start Web Server (http://localhost:8080)
if ss -tuln | grep -q ":8080 "; then
    echo "[INFO] Web server is already running on port 8080."
else
    echo "[INFO] Starting web server on http://localhost:8080..."
    setsid python3 "$WS_DIR/web_dashboard/web_server.py" > /tmp/auron_web_server.log 2>&1 &
    sleep 1.0
fi

echo "============================================================"
echo "  Web Dashboard ready at: http://localhost:8080"
echo "  ROS 2 WebSocket:        ws://localhost:9090"
echo "============================================================"

# 5. Open browser if in desktop session
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:8080" 2>/dev/null || true
fi

echo "[INFO] Dashboard launched. To view, open http://localhost:8080"
