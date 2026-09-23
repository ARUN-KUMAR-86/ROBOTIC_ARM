/**
 * Modern Robotic Hand & Gripper Controller Module
 * Handles master grip stroke (0 - 35mm), individual bionic finger articulation,
 * and intelligent gesture presets (Fist, Pinch, Point, Peace, Thumbs Up).
 */

const HandControls = {
  currentStrokeMeters: 0.035, // default open 35mm
  maxStrokeMeters: 0.035,

  // Individual finger curl factors (0.0 open, 1.0 curled)
  fingerCurls: {
    thumb: 0.0,
    index: 0.0,
    middle: 0.0,
    ring: 0.0,
    pinky: 0.0,
  },

  sendTimer: null,

  init() {
    this.bindMasterGrip();
    this.bindHandPresets();
    this.bindGestureButtons();
    this.bindIndividualFingers();
    this.updateUI(this.currentStrokeMeters);
  },

  bindMasterGrip() {
    const gripSlider = document.getElementById('hand-grip-slider');
    const gripMinus = document.getElementById('hand-grip-minus');
    const gripPlus = document.getElementById('hand-grip-plus');

    if (gripSlider) {
      gripSlider.addEventListener('input', (e) => {
        const mm = parseFloat(e.target.value);
        this.setGripStroke(mm / 1000.0);
      });
    }

    if (gripMinus) {
      gripMinus.addEventListener('click', () => {
        // Decrease span (close hand)
        this.setGripStroke(this.currentStrokeMeters - 0.005);
      });
    }

    if (gripPlus) {
      gripPlus.addEventListener('click', () => {
        // Increase span (open hand)
        this.setGripStroke(this.currentStrokeMeters + 0.005);
      });
    }
  },

  bindHandPresets() {
    const presets = [
      { id: 'hand-btn-open', val: 0.035, label: 'Full Open (35 mm)' },
      { id: 'hand-btn-close', val: 0.000, label: 'Full Close (0 mm)' },
      { id: 'hand-btn-pinch', val: 0.012, label: 'Pinch Grasp (12 mm)' },
      { id: 'hand-btn-can', val: 0.024, label: 'Cylinder Grasp (24 mm)' },
    ];

    presets.forEach((p) => {
      const btn = document.getElementById(p.id);
      if (btn) {
        btn.addEventListener('click', () => {
          this.setGripStroke(p.val);
          showToast(`Hand: ${p.label}`, 'info');
        });
      }
    });
  },

  bindGestureButtons() {
    const gestures = ['open', 'fist', 'pinch', 'point', 'peace', 'thumbsup'];
    gestures.forEach((g) => {
      const btn = document.getElementById(`gesture-${g}`);
      if (btn) {
        btn.addEventListener('click', () => {
          document.querySelectorAll('.gesture-btn').forEach((b) => b.classList.remove('active'));
          btn.classList.add('active');
          this.applyGesture(g);
          showToast(`Hand Gesture: ${g.toUpperCase()}`, 'info');
        });
      }
    });
  },

  bindIndividualFingers() {
    const fingers = ['thumb', 'index', 'middle', 'ring', 'pinky'];
    fingers.forEach((f) => {
      const slider = document.getElementById(`finger-${f}-slider`);
      const valLabel = document.getElementById(`finger-${f}-val`);

      if (slider) {
        slider.addEventListener('input', (e) => {
          const curl = parseFloat(e.target.value) / 100.0;
          this.fingerCurls[f] = curl;
          if (valLabel) valLabel.textContent = `${e.target.value}%`;

          // Update individual finger in 3D visualizer
          if (typeof Robot3DView !== 'undefined' && Robot3DView.fingerNodes) {
            const nodeObj = Robot3DView.fingerNodes.find(
              (n) => n.name.toLowerCase() === f
            );
            if (nodeObj) {
              nodeObj.baseNode.rotation.x = curl * 0.75;
              nodeObj.pipNode.rotation.x = curl * 0.95;
              nodeObj.dipNode.rotation.x = curl * 0.85;
            }
          }

          // Calculate average curl to send to ROS 2 gripper stroke
          const avgCurl =
            (this.fingerCurls.thumb +
              this.fingerCurls.index +
              this.fingerCurls.middle +
              this.fingerCurls.ring +
              this.fingerCurls.pinky) /
            5.0;
          const stroke = (1.0 - avgCurl) * this.maxStrokeMeters;
          this.scheduleGripperSend(stroke);
        });
      }
    });
  },

  setGripStroke(strokeMeters) {
    this.currentStrokeMeters = Math.max(0.0, Math.min(this.maxStrokeMeters, strokeMeters));
    this.updateUI(this.currentStrokeMeters);

    // Sync individual finger sliders
    const curlFactor = 1.0 - this.currentStrokeMeters / this.maxStrokeMeters;
    const fingers = ['thumb', 'index', 'middle', 'ring', 'pinky'];
    fingers.forEach((f) => {
      this.fingerCurls[f] = curlFactor;
      const slider = document.getElementById(`finger-${f}-slider`);
      const valLabel = document.getElementById(`finger-${f}-val`);
      if (slider) slider.value = Math.round(curlFactor * 100);
      if (valLabel) valLabel.textContent = `${Math.round(curlFactor * 100)}%`;
    });

    if (typeof Robot3DView !== 'undefined' && Robot3DView.updateHandGrip) {
      Robot3DView.updateHandGrip(this.currentStrokeMeters);
    }

    this.scheduleGripperSend(this.currentStrokeMeters);
  },

  applyGesture(gestureName) {
    if (typeof Robot3DView !== 'undefined' && Robot3DView.applyGesture) {
      Robot3DView.applyGesture(gestureName);
    }

    // Map gesture to equivalent gripper stroke
    let targetStroke = 0.035;
    if (gestureName === 'fist') targetStroke = 0.002;
    else if (gestureName === 'pinch') targetStroke = 0.012;
    else if (gestureName === 'point') targetStroke = 0.020;
    else if (gestureName === 'peace') targetStroke = 0.025;
    else if (gestureName === 'thumbsup') targetStroke = 0.018;
    else targetStroke = 0.035;

    this.currentStrokeMeters = targetStroke;
    this.updateUI(targetStroke);
    this.scheduleGripperSend(targetStroke);
  },

  scheduleGripperSend(strokeMeters) {
    clearTimeout(this.sendTimer);
    this.sendTimer = setTimeout(() => {
      RosBridge.sendGripperTrajectory(strokeMeters);
    }, 50);
  },

  updateUI(strokeMeters) {
    const mm = strokeMeters * 1000.0;
    const gripSlider = document.getElementById('hand-grip-slider');
    const gripValText = document.getElementById('hand-grip-mm');
    const gripPctText = document.getElementById('hand-grip-pct');

    if (gripSlider && document.activeElement !== gripSlider) {
      gripSlider.value = mm.toFixed(1);
    }
    if (gripValText) {
      gripValText.innerHTML = `${mm.toFixed(1)} <span>mm</span>`;
    }
    if (gripPctText) {
      const pct = Math.round((strokeMeters / this.maxStrokeMeters) * 100);
      gripPctText.textContent = `${pct}% OPEN`;
    }
  }
};
