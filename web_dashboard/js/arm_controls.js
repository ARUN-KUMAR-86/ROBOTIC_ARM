/**
 * Auron 6-DOF Robotic Arm Controls
 * Handles joint sliders, incremental jogging, degree/radian conversions,
 * preset motion sequences, and trajectory dispatch.
 */

const ArmControls = {
  stepSizeDeg: 5.0,
  targetJointsRad: [0, 0, 0, 0, 0, 0],
  jointLimits: [
    { min: -3.14159, max: 3.14159, name: 'Joint 1', desc: 'Base Rotation (Pan)' },
    { min: -2.0944,  max: 2.0944,  name: 'Joint 2', desc: 'Shoulder Pitch' },
    { min: -2.61799, max: 2.61799, name: 'Joint 3', desc: 'Elbow Pitch' },
    { min: -3.14159, max: 3.14159, name: 'Joint 4', desc: 'Wrist Roll' },
    { min: -2.0944,  max: 2.0944,  name: 'Joint 5', desc: 'Wrist Pitch' },
    { min: -6.28318, max: 6.28318, name: 'Joint 6', desc: 'Tool Flange Roll' },
  ],

  // Debounce dispatch timer
  sendTimer: null,

  init() {
    this.bindJointInputs();
    this.bindPresets();
    this.bindSafetyButtons();
    this.bindSpeedControl();
    this.bindStepSelectors();
    this.updateUI(this.targetJointsRad);
  },

  bindJointInputs() {
    for (let i = 1; i <= 6; i++) {
      const idx = i - 1;
      const slider = document.getElementById(`joint-${i}-slider`);
      const minusBtn = document.getElementById(`joint-${i}-minus`);
      const plusBtn = document.getElementById(`joint-${i}-plus`);
      const zeroBtn = document.getElementById(`joint-${i}-zero`);

      if (slider) {
        slider.addEventListener('input', (e) => {
          const deg = parseFloat(e.target.value);
          const rad = (deg * Math.PI) / 180.0;
          this.setJointRad(idx, rad);
        });
      }

      if (minusBtn) {
        minusBtn.addEventListener('click', () => {
          this.jogJointDeg(idx, -this.stepSizeDeg);
        });
      }

      if (plusBtn) {
        plusBtn.addEventListener('click', () => {
          this.jogJointDeg(idx, this.stepSizeDeg);
        });
      }

      if (zeroBtn) {
        zeroBtn.addEventListener('click', () => {
          this.setJointRad(idx, 0.0);
        });
      }
    }
  },

  bindStepSelectors() {
    const stepBtns = document.querySelectorAll('.step-btn');
    stepBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        stepBtns.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        this.stepSizeDeg = parseFloat(btn.dataset.step) || 5.0;
      });
    });
  },

  bindSpeedControl() {
    const speedSlider = document.getElementById('speed-slider');
    const speedLabel = document.getElementById('speed-value-label');
    if (speedSlider) {
      speedSlider.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        RosBridge.trajectoryDuration = val;
        if (speedLabel) {
          speedLabel.textContent = `${val.toFixed(1)}s`;
        }
      });
    }
  },

  bindPresets() {
    const presets = {
      'preset-home': [0, 0, 0, 0, 0, 0],
      'preset-ready': [0, -0.4, 0.8, 0, -0.4, 0],
      'preset-pick': [0.35, 0.45, 0.65, 0, -1.1, 0.35],
      'preset-place': [-0.75, 0.40, 0.70, 0, -1.1, -0.75],
      'preset-inspect': [0.85, -0.25, 1.05, 1.57, -0.8, 0],
      'preset-high': [0, -1.2, 0.2, 0, 1.0, 0],
    };

    Object.keys(presets).forEach((id) => {
      const btn = document.getElementById(id);
      if (btn) {
        btn.addEventListener('click', () => {
          this.goToPose(presets[id], 1.2);
          showToast(`Executing preset: ${btn.textContent.trim()}`, 'info');
        });
      }
    });

    const waveBtn = document.getElementById('preset-wave');
    if (waveBtn) {
      waveBtn.addEventListener('click', () => this.runWaveDemo());
    }
  },

  bindSafetyButtons() {
    const estopBtn = document.getElementById('btn-estop');
    const resetBtn = document.getElementById('btn-reset-home');

    if (estopBtn) {
      estopBtn.addEventListener('click', () => {
        if (RosBridge.isEstop) {
          RosBridge.clearEstop();
          estopBtn.classList.remove('active');
          estopBtn.innerHTML = `<span>⚠️</span> E-STOP`;
          showToast("Emergency stop CLEARED. Robot ready.", "success");
        } else {
          RosBridge.emergencyStop();
          estopBtn.classList.add('active');
          estopBtn.innerHTML = `<span>🛑</span> STOPPED (RESUME)`;
          showToast("EMERGENCY STOP ACTIVATED! Arm halted.", "error");
        }
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        RosBridge.clearEstop();
        if (estopBtn) {
          estopBtn.classList.remove('active');
          estopBtn.innerHTML = `<span>⚠️</span> E-STOP`;
        }
        this.goToPose([0, 0, 0, 0, 0, 0], 1.5);
        RosBridge.sendGripperTrajectory(0.035, 1.0);
        showToast("Homing sequence initiated...", "info");
      });
    }
  },

  setJointRad(idx, rad) {
    if (RosBridge.isEstop) return;
    const limit = this.jointLimits[idx];
    const clamped = Math.max(limit.min, Math.min(limit.max, rad));
    this.targetJointsRad[idx] = clamped;

    this.updateUI(this.targetJointsRad);
    if (typeof Robot3DView !== 'undefined' && Robot3DView.updateJoints) {
      Robot3DView.updateJoints(this.targetJointsRad);
    }

    this.scheduleTrajectorySend();
  },

  jogJointDeg(idx, deltaDeg) {
    const currentDeg = (this.targetJointsRad[idx] * 180.0) / Math.PI;
    const newDeg = currentDeg + deltaDeg;
    this.setJointRad(idx, (newDeg * Math.PI) / 180.0);
  },

  goToPose(jointsRad, durationSec = 1.0) {
    if (RosBridge.isEstop) return;
    for (let i = 0; i < 6; i++) {
      const limit = this.jointLimits[i];
      this.targetJointsRad[i] = Math.max(limit.min, Math.min(limit.max, jointsRad[i]));
    }
    this.updateUI(this.targetJointsRad);
    if (typeof Robot3DView !== 'undefined' && Robot3DView.updateJoints) {
      Robot3DView.updateJoints(this.targetJointsRad);
    }
    RosBridge.sendArmTrajectory(this.targetJointsRad, durationSec);
  },

  scheduleTrajectorySend() {
    clearTimeout(this.sendTimer);
    this.sendTimer = setTimeout(() => {
      RosBridge.sendArmTrajectory(this.targetJointsRad);
    }, 40); // 25Hz throttle
  },

  runWaveDemo() {
    showToast("Starting Wave Gesture demo...", "info");
    const poses = [
      { pose: [0, -0.6, 0.9, 0, 0, 0], duration: 0.8 },
      { pose: [0, -0.6, 0.9, 0, 0, 0.6], duration: 0.4 },
      { pose: [0, -0.6, 0.9, 0, 0, -0.6], duration: 0.4 },
      { pose: [0, -0.6, 0.9, 0, 0, 0.6], duration: 0.4 },
      { pose: [0, -0.6, 0.9, 0, 0, 0], duration: 0.5 },
      { pose: [0, 0, 0, 0, 0, 0], duration: 1.0 }
    ];

    let delay = 0;
    poses.forEach((step) => {
      setTimeout(() => {
        if (!RosBridge.isEstop) {
          this.goToPose(step.pose, step.duration);
        }
      }, delay);
      delay += step.duration * 1000;
    });
  },

  updateUI(positionsRad) {
    for (let i = 1; i <= 6; i++) {
      const idx = i - 1;
      const rad = positionsRad[idx] || 0.0;
      const deg = (rad * 180.0) / Math.PI;

      const slider = document.getElementById(`joint-${i}-slider`);
      const degText = document.getElementById(`joint-${i}-deg`);
      const radText = document.getElementById(`joint-${i}-rad`);

      if (slider && document.activeElement !== slider) {
        slider.value = deg.toFixed(1);
      }
      if (degText) {
        degText.textContent = `${deg >= 0 ? '+' : ''}${deg.toFixed(1)}°`;
      }
      if (radText) {
        radText.textContent = `${rad >= 0 ? '+' : ''}${rad.toFixed(2)} rad`;
      }
    }
  }
};
