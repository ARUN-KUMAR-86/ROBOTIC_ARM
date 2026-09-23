/**
 * Main Application Orchestrator
 * Connects modules, handles tab transitions, viewport controls, camera streaming,
 * high-resolution image lightbox, and real-time telemetry tables.
 */

// Toast notification helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '⚠️';
  toast.innerHTML = `<span>${icon}</span> <div>${message}</div>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

document.addEventListener('DOMContentLoaded', () => {
  console.log("[Auron Web Dashboard] Initializing system...");

  // 1. Initialize 3D Viewport
  Robot3DView.init('canvas-container');

  // 2. Initialize Controllers
  ArmControls.init();
  HandControls.init();

  // 3. Connect ROS 2 Bridge
  RosBridge.init("ws://" + window.location.hostname + ":9090");

  // Handle incoming live joint feedback from ROS 2
  RosBridge.onJointStateUpdate = (positions, gripperStroke) => {
    Robot3DView.updateJoints(positions);
    Robot3DView.updateHandGrip(gripperStroke);
    updateTelemetryTable(positions, gripperStroke);
  };

  // 4. Setup Tabs
  setupTabs();

  // 5. Setup 3D Viewport Toolbar & Camera Presets
  setupViewportTools();

  // 6. Setup Live Optical & AI Vision Stream Controls
  initCameraStreaming();

  // 7. Setup Picture-in-Picture Floating Camera
  initPiPCamera();

  // 8. Setup Interactive High-Resolution Image Lightbox
  initImageLightbox();

  // Initial toast welcome
  setTimeout(() => {
    showToast("Auron Robotic Arm & Vision Dashboard Online.", "info");
  }, 500);
});

function setupTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      tabBtns.forEach((b) => b.classList.remove('active'));
      tabContents.forEach((c) => c.classList.remove('active'));

      btn.classList.add('active');
      const targetContent = document.getElementById(tabId);
      if (targetContent) targetContent.classList.add('active');

      if (tabId === 'tab-showcase') {
        Robot3DView.setCameraView('hand');
      }
    });
  });
}

function setupViewportTools() {
  const camBtns = document.querySelectorAll('.cam-btn');
  camBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      camBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const view = btn.dataset.view;
      Robot3DView.setCameraView(view);
    });
  });

  const toolGridBtn = document.getElementById('tool-toggle-grid');
  if (toolGridBtn) {
    toolGridBtn.addEventListener('click', () => {
      const active = Robot3DView.toggleGrid();
      toolGridBtn.classList.toggle('active', active);
    });
  }

  const toolWireBtn = document.getElementById('tool-toggle-wireframe');
  if (toolWireBtn) {
    toolWireBtn.addEventListener('click', () => {
      const active = Robot3DView.toggleWireframe();
      toolWireBtn.classList.toggle('active', active);
    });
  }

  const toolResetCam = document.getElementById('tool-reset-cam');
  if (toolResetCam) {
    toolResetCam.addEventListener('click', () => {
      Robot3DView.setCameraView('iso');
      camBtns.forEach((b) => b.classList.remove('active'));
      const isoBtn = document.querySelector('[data-view="iso"]');
      if (isoBtn) isoBtn.classList.add('active');
    });
  }
}

// -------------------------------------------------------------
// LIVE CAMERA & AI VISION STREAM CONTROLLER
// -------------------------------------------------------------
function initCameraStreaming() {
  const mainStreamImg = document.getElementById('main-camera-stream');
  const topicBadge = document.getElementById('camera-topic-badge');
  const btnRaw = document.getElementById('stream-btn-camera');
  const btnVision = document.getElementById('stream-btn-vision');
  const btnSnapshot = document.getElementById('btn-camera-snapshot');
  const btnFullscreen = document.getElementById('btn-camera-fullscreen');
  const feedCard = document.getElementById('camera-feed-card');

  if (btnRaw && btnVision && mainStreamImg) {
    btnRaw.addEventListener('click', () => {
      btnRaw.classList.add('active');
      btnVision.classList.remove('active');
      mainStreamImg.src = '/stream/camera?t=' + Date.now();
      if (topicBadge) topicBadge.textContent = '/camera/image_raw';
      showToast("Switched to Raw Eye-in-Hand Optical Stream", "info");
    });

    btnVision.addEventListener('click', () => {
      btnVision.classList.add('active');
      btnRaw.classList.remove('active');
      mainStreamImg.src = '/stream/vision?t=' + Date.now();
      if (topicBadge) topicBadge.textContent = '/vision/detection_image';
      showToast("Switched to AI Computer Vision Detection Overlay", "info");
    });
  }

  if (btnSnapshot) {
    btnSnapshot.addEventListener('click', () => {
      const link = document.createElement('a');
      link.href = '/api/camera_snapshot?t=' + Date.now();
      link.download = `auron_snapshot_${Date.now()}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showToast("Camera frame snapshot saved to disk", "success");
    });
  }

  if (btnFullscreen && feedCard) {
    btnFullscreen.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        feedCard.requestFullscreen().catch((err) => {
          showToast(`Fullscreen error: ${err.message}`, "error");
        });
      } else {
        document.exitFullscreen();
      }
    });
  }

  // Periodic Target Detections Polling & Health Sync
  setInterval(pollDetectionsAndHealth, 1000);
}

function pollDetectionsAndHealth() {
  fetch('/api/detections')
    .then((res) => res.json())
    .then((data) => {
      const countBadge = document.getElementById('detections-count-badge');
      const container = document.getElementById('detections-list-container');
      if (!container) return;

      const items = data.detections || [];
      if (countBadge) {
        countBadge.textContent = `${items.length} Tracked`;
        countBadge.style.color = items.length > 0 ? 'var(--success)' : 'var(--cyan)';
      }

      if (items.length === 0) {
        container.innerHTML = `<div class="no-detections-msg">Listening for target cubes/cylinders via OpenCV...</div>`;
      } else {
        container.innerHTML = items
          .map(
            (det) => `
          <div class="detection-item">
            <div>
              <strong style="color:#fff;">${det.color ? det.color.toUpperCase() : 'TARGET'}</strong>
              <span style="color:var(--text-muted); font-size:0.7rem; margin-left:6px;">u=${det.pixel_u}, v=${det.pixel_v}</span>
            </div>
            <div style="font-family:monospace; color:var(--cyan);">
              X:${(det.x || 0).toFixed(2)}m Y:${(det.y || 0).toFixed(2)}m Z:${(det.z || 0).toFixed(2)}m
            </div>
          </div>
        `
          )
          .join('');
      }
    })
    .catch(() => {});

  fetch('/api/health')
    .then((res) => res.json())
    .then((data) => {
      const latEl = document.getElementById('camera-latency-val');
      if (latEl && data.camera_latency_sec !== null) {
        const ms = Math.round(data.camera_latency_sec * 1000);
        latEl.textContent = `${ms} ms`;
        latEl.style.color = ms < 100 ? 'var(--success)' : 'var(--warning)';
      }
    })
    .catch(() => {});
}

// -------------------------------------------------------------
// PICTURE-IN-PICTURE (PIP) FLOATING CAMERA
// -------------------------------------------------------------
function initPiPCamera() {
  const pipBox = document.getElementById('pip-camera-box');
  const toolPipBtn = document.getElementById('tool-toggle-pip');
  const pipCloseBtn = document.getElementById('pip-close-btn');

  if (!pipBox) return;

  if (toolPipBtn) {
    toolPipBtn.addEventListener('click', () => {
      const isHidden = pipBox.classList.toggle('hidden');
      toolPipBtn.classList.toggle('active', !isHidden);
    });
  }

  if (pipCloseBtn) {
    pipCloseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      pipBox.classList.add('hidden');
      if (toolPipBtn) toolPipBtn.classList.remove('active');
    });
  }

  // Clicking the floating PiP switches user to full Live Camera tab
  pipBox.addEventListener('click', () => {
    const camTabBtn = document.querySelector('[data-tab="tab-camera"]');
    if (camTabBtn) camTabBtn.click();
  });
}

// -------------------------------------------------------------
// INTERACTIVE HIGH-RES IMAGE LIGHTBOX MODAL
// -------------------------------------------------------------
function initImageLightbox() {
  const modal = document.getElementById('image-lightbox-modal');
  const backdrop = document.getElementById('lightbox-backdrop');
  const closeBtn = document.getElementById('lightbox-close-btn');
  const lightboxImg = document.getElementById('lightbox-img');
  const titleEl = document.getElementById('lightbox-title');
  const descEl = document.getElementById('lightbox-desc');
  const downloadBtn = document.getElementById('lightbox-download-btn');
  const zoomIn = document.getElementById('lightbox-zoom-in');
  const zoomOut = document.getElementById('lightbox-zoom-out');
  const zoomReset = document.getElementById('lightbox-zoom-reset');

  if (!modal || !lightboxImg) return;

  let currentScale = 1.0;

  function updateZoom() {
    lightboxImg.style.transform = `scale(${currentScale})`;
  }

  function openModal(imgSrc, title, desc) {
    lightboxImg.src = imgSrc;
    if (titleEl) titleEl.textContent = title || "Modern Hand Design";
    if (descEl) descEl.textContent = desc || "";
    if (downloadBtn) {
      downloadBtn.href = imgSrc;
      downloadBtn.download = imgSrc.split('/').pop() || 'auron_design.jpg';
    }
    currentScale = 1.0;
    updateZoom();
    modal.classList.add('active');
  }

  function closeModal() {
    modal.classList.remove('active');
    lightboxImg.src = '';
    currentScale = 1.0;
  }

  // Attach click to all gallery items
  document.querySelectorAll('.showcase-item').forEach((item) => {
    item.addEventListener('click', () => {
      const src = item.dataset.image || item.querySelector('img')?.src;
      const title = item.dataset.title || item.querySelector('h4')?.textContent;
      const desc = item.dataset.desc || item.querySelector('p')?.textContent;
      if (src) openModal(src, title, desc);
    });
  });

  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (backdrop) backdrop.addEventListener('click', closeModal);

  if (zoomIn) {
    zoomIn.addEventListener('click', () => {
      currentScale = Math.min(currentScale + 0.25, 3.0);
      updateZoom();
    });
  }

  if (zoomOut) {
    zoomOut.addEventListener('click', () => {
      currentScale = Math.max(currentScale - 0.25, 0.5);
      updateZoom();
    });
  }

  if (zoomReset) {
    zoomReset.addEventListener('click', () => {
      currentScale = 1.0;
      updateZoom();
    });
  }

  // Keyboard shortcut Esc to close
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      closeModal();
    }
  });
}

function updateTelemetryTable(actualPositions, actualGripper) {
  const targetPositions = ArmControls.targetJointsRad;
  const targetGripper = HandControls.currentStrokeMeters;

  for (let i = 1; i <= 6; i++) {
    const idx = i - 1;
    const tgt = targetPositions[idx] || 0.0;
    const act = actualPositions[idx] || 0.0;
    const err = Math.abs(tgt - act);

    const actEl = document.getElementById(`telem-j${i}-act`);
    const tgtEl = document.getElementById(`telem-j${i}-tgt`);
    const errEl = document.getElementById(`telem-j${i}-err`);

    if (actEl) actEl.textContent = `${(act * 180 / Math.PI).toFixed(1)}°`;
    if (tgtEl) tgtEl.textContent = `${(tgt * 180 / Math.PI).toFixed(1)}°`;
    if (errEl) {
      errEl.textContent = `${(err * 180 / Math.PI).toFixed(1)}°`;
      errEl.style.color = err > 0.1 ? 'var(--warning)' : 'var(--cyan)';
    }
  }

  // Gripper
  const actGripEl = document.getElementById('telem-grip-act');
  const tgtGripEl = document.getElementById('telem-grip-tgt');
  const errGripEl = document.getElementById('telem-grip-err');

  if (actGripEl) actGripEl.textContent = `${(actualGripper * 1000).toFixed(1)} mm`;
  if (tgtGripEl) tgtGripEl.textContent = `${(targetGripper * 1000).toFixed(1)} mm`;
  if (errGripEl) {
    const err = Math.abs(targetGripper - actualGripper) * 1000;
    errGripEl.textContent = `${err.toFixed(1)} mm`;
    errGripEl.style.color = err > 2.0 ? 'var(--warning)' : 'var(--cyan)';
  }
}
