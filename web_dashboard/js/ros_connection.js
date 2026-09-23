/**
 * ROS 2 Connection & Topic Communication Bridge
 * Communicates with rosbridge_websocket (ws://localhost:9090)
 * Handles:
 *  - /arm_controller/joint_trajectory (JointTrajectory)
 *  - /gripper_controller/joint_trajectory (JointTrajectory)
 *  - /joint_states (JointState)
 *  - Virtual Simulation Fallback when offline
 */

const RosBridge = {
  ros: null,
  connected: false,
  url: "ws://localhost:9090",
  reconnectTimer: null,

  // Topics
  armTrajTopic: null,
  gripperTrajTopic: null,
  jointStateTopic: null,

  // Joint definition matching auron_robot URDF
  jointNames: ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6'],
  gripperJointNames: ['left_finger_joint', 'right_finger_joint'],

  // State
  currentPositions: [0, 0, 0, 0, 0, 0],
  currentGripper: 0.035, // 35mm default open
  targetPositions: [0, 0, 0, 0, 0, 0],
  targetGripper: 0.035,
  isEstop: false,
  trajectoryDuration: 0.5, // seconds

  // Callbacks
  onJointStateUpdate: null,
  onConnectionStatusChange: null,

  init(url = "ws://localhost:9090") {
    this.url = url;
    this.connect();
  },

  connect() {
    if (typeof ROSLIB === 'undefined') {
      console.warn("ROSLIB is not loaded. Operating in Virtual Simulation mode.");
      this.updateStatus('offline', 'VIRTUAL MODE (ROSLIB MISSING)');
      return;
    }

    try {
      this.ros = new ROSLIB.Ros({
        url: this.url
      });

      this.ros.on('connection', () => {
        this.connected = true;
        console.log(`[ROS2] Connected to ${this.url}`);
        this.updateStatus('connected', 'ROS 2 CONNECTED');
        this.setupTopics();
      });

      this.ros.on('error', (error) => {
        console.warn('[ROS2] Connection error:', error);
        this.connected = false;
        this.updateStatus('disconnected', 'STANDALONE / SIMULATING');
      });

      this.ros.on('close', () => {
        console.log('[ROS2] Connection closed. Will retry in 4s...');
        this.connected = false;
        this.updateStatus('disconnected', 'STANDALONE / SIMULATING');
        if (!this.reconnectTimer) {
          this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
          }, 4000);
        }
      });
    } catch (err) {
      console.warn('[ROS2] Exception during connection setup:', err);
      this.connected = false;
      this.updateStatus('offline', 'STANDALONE / OFFLINE');
    }
  },

  setupTopics() {
    if (!this.ros || !this.connected) return;

    // Arm controller trajectory publisher
    this.armTrajTopic = new ROSLIB.Topic({
      ros: this.ros,
      name: '/arm_controller/joint_trajectory',
      messageType: 'trajectory_msgs/msg/JointTrajectory'
    });

    // Gripper controller trajectory publisher
    this.gripperTrajTopic = new ROSLIB.Topic({
      ros: this.ros,
      name: '/gripper_controller/joint_trajectory',
      messageType: 'trajectory_msgs/msg/JointTrajectory'
    });

    // Joint State subscriber
    this.jointStateTopic = new ROSLIB.Topic({
      ros: this.ros,
      name: '/joint_states',
      messageType: 'sensor_msgs/msg/JointState'
    });

    this.jointStateTopic.subscribe((msg) => {
      this.handleJointStateMsg(msg);
    });

    console.log('[ROS2] Topics configured & /joint_states subscribed.');
  },

  handleJointStateMsg(msg) {
    if (!msg || !msg.name || !msg.position) return;
    const nameMap = {};
    for (let i = 0; i < msg.name.length; i++) {
      nameMap[msg.name[i]] = msg.position[i];
    }

    let updatedArm = false;
    for (let i = 0; i < this.jointNames.length; i++) {
      const name = this.jointNames[i];
      if (name in nameMap && !isNaN(nameMap[name])) {
        this.currentPositions[i] = nameMap[name];
        updatedArm = true;
      }
    }

    if ('left_finger_joint' in nameMap && !isNaN(nameMap['left_finger_joint'])) {
      this.currentGripper = nameMap['left_finger_joint'];
    }

    if (this.onJointStateUpdate) {
      this.onJointStateUpdate(this.currentPositions, this.currentGripper);
    }
  },

  sendArmTrajectory(positions, durationSec = null) {
    if (this.isEstop) {
      console.warn("Cannot send arm command: EMERGENCY STOP is active.");
      return;
    }

    this.targetPositions = [...positions];
    const duration = durationSec || this.trajectoryDuration;
    const sec = Math.floor(duration);
    const nanosec = Math.floor((duration - sec) * 1e9);

    if (this.connected && this.armTrajTopic) {
      const msg = new ROSLIB.Message({
        header: {
          stamp: { sec: 0, nanosec: 0 },
          frame_id: 'base_link'
        },
        joint_names: this.jointNames,
        points: [
          {
            positions: positions,
            velocities: [0, 0, 0, 0, 0, 0],
            time_from_start: { sec: sec, nanosec: nanosec }
          }
        ]
      });
      this.armTrajTopic.publish(msg);
    } else {
      // Virtual mode simulation: smooth drift towards targets
      this.simulateVirtualMotion(duration);
    }
  },

  sendGripperTrajectory(positionMeters, durationSec = 0.4) {
    if (this.isEstop) return;

    this.targetGripper = Math.max(0.0, Math.min(0.035, positionMeters));
    const sec = Math.floor(durationSec);
    const nanosec = Math.floor((durationSec - sec) * 1e9);

    if (this.connected && this.gripperTrajTopic) {
      const msg = new ROSLIB.Message({
        header: {
          stamp: { sec: 0, nanosec: 0 },
          frame_id: 'tool0'
        },
        joint_names: this.gripperJointNames,
        points: [
          {
            positions: [this.targetGripper, this.targetGripper],
            velocities: [0, 0],
            time_from_start: { sec: sec, nanosec: nanosec }
          }
        ]
      });
      this.gripperTrajTopic.publish(msg);
    } else {
      this.currentGripper = this.targetGripper;
      if (this.onJointStateUpdate) {
        this.onJointStateUpdate(this.currentPositions, this.currentGripper);
      }
    }
  },

  emergencyStop() {
    this.isEstop = true;
    console.warn("[SAFETY] EMERGENCY STOP ACTIVATED!");

    // Command instantaneous stop to arm
    if (this.connected && this.armTrajTopic) {
      const msg = new ROSLIB.Message({
        header: { stamp: { sec: 0, nanosec: 0 } },
        joint_names: this.jointNames,
        points: [
          {
            positions: [...this.currentPositions],
            velocities: [0, 0, 0, 0, 0, 0],
            time_from_start: { sec: 0, nanosec: 20000000 }
          }
        ]
      });
      this.armTrajTopic.publish(msg);
    }
    this.targetPositions = [...this.currentPositions];
  },

  clearEstop() {
    this.isEstop = false;
    console.log("[SAFETY] E-Stop cleared.");
  },

  simulateVirtualMotion(durationSec) {
    const steps = 15;
    const intervalMs = (durationSec * 1000) / steps;
    let step = 0;
    const startPos = [...this.currentPositions];
    const targetPos = [...this.targetPositions];

    const timer = setInterval(() => {
      step++;
      const t = step / steps;
      // Smooth ease-in-out
      const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;

      for (let i = 0; i < 6; i++) {
        this.currentPositions[i] = startPos[i] + (targetPos[i] - startPos[i]) * ease;
      }

      if (this.onJointStateUpdate) {
        this.onJointStateUpdate(this.currentPositions, this.currentGripper);
      }

      if (step >= steps) {
        clearInterval(timer);
        this.currentPositions = [...targetPos];
        if (this.onJointStateUpdate) {
          this.onJointStateUpdate(this.currentPositions, this.currentGripper);
        }
      }
    }, intervalMs);
  },

  updateStatus(statusClass, label) {
    const badge = document.getElementById('connection-status-badge');
    const text = document.getElementById('connection-status-text');
    if (badge) {
      badge.className = `status-badge ${statusClass}`;
    }
    if (text) {
      text.textContent = label;
    }
    if (this.onConnectionStatusChange) {
      this.onConnectionStatusChange(this.connected, label);
    }
  }
};
