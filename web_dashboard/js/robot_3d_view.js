/**
 * Three.js 3D Visualizer for Auron 6-DOF Robot Arm & Modern Dexterous Hand
 * Kinematic simulation matching URDF joint hierarchy & coordinate axes
 */

const Robot3DView = {
  container: null,
  scene: null,
  camera: null,
  renderer: null,
  controls: null,
  robotRoot: null,

  // Kinematic nodes (pivot groups)
  jointNodes: [],
  fingerNodes: [],

  // Materials
  matWhite: null,
  matBlue: null,
  matDarkMetal: null,
  matCyanGlow: null,
  matFingerPad: null,

  // Options
  showGrid: true,
  isWireframe: false,
  gridHelper: null,

  init(containerId = 'canvas-container') {
    this.container = document.getElementById(containerId);
    if (!this.container || typeof THREE === 'undefined') {
      console.warn("Three.js or container not ready for 3D View.");
      return;
    }

    const width = this.container.clientWidth || 600;
    const height = this.container.clientHeight || 450;

    // 1. Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0a0f1d);
    this.scene.fog = new THREE.FogExp2(0x0a0f1d, 0.12);

    // 2. Camera
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.05, 50);
    this.camera.position.set(1.4, 1.1, 1.6);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.domElement.id = 'robot-canvas';
    this.container.appendChild(this.renderer.domElement);

    // 4. Orbit Controls
    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.maxPolarAngle = Math.PI / 2 + 0.05; // Don't go deep below ground
      this.controls.minDistance = 0.4;
      this.controls.maxDistance = 5.0;
      this.controls.target.set(0, 0.45, 0);
      this.controls.update();
    }

    // 5. Lighting
    this.setupLighting();

    // 6. Materials
    this.setupMaterials();

    // 7. Ground & Environment
    this.setupEnvironment();

    // 8. Build Kinematic Chain
    this.buildAuronRobot();

    // 9. Resize handler
    window.addEventListener('resize', () => this.onResize());

    // 10. Render Loop
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);

    console.log("[Robot3DView] Initialized successfully with Auron arm & Modern hand model.");
  },

  setupLighting() {
    // Ambient light
    const ambientLight = new THREE.AmbientLight(0xd0e0ff, 0.7);
    this.scene.add(ambientLight);

    // Key directional light with shadows
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(2.5, 4.0, 2.0);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 2048;
    keyLight.shadow.mapSize.height = 2048;
    keyLight.shadow.camera.near = 0.5;
    keyLight.shadow.camera.far = 10;
    keyLight.shadow.camera.left = -1.5;
    keyLight.shadow.camera.right = 1.5;
    keyLight.shadow.camera.top = 1.5;
    keyLight.shadow.camera.bottom = -1.5;
    keyLight.shadow.bias = -0.0005;
    this.scene.add(keyLight);

    // Soft cyan fill light
    const fillLight = new THREE.DirectionalLight(0x00e5ff, 0.6);
    fillLight.position.set(-2.5, 2.0, -2.0);
    this.scene.add(fillLight);

    // Rim blue light
    const rimLight = new THREE.DirectionalLight(0x2563eb, 0.5);
    rimLight.position.set(0, -1.0, -3.0);
    this.scene.add(rimLight);
  },

  setupMaterials() {
    this.matWhite = new THREE.MeshStandardMaterial({
      color: 0xf3f4f6,
      roughness: 0.22,
      metalness: 0.18
    });

    this.matBlue = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      roughness: 0.35,
      metalness: 0.65
    });

    this.matDarkMetal = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.45,
      metalness: 0.85
    });

    this.matCyanGlow = new THREE.MeshStandardMaterial({
      color: 0x00e5ff,
      emissive: 0x00b4d8,
      emissiveIntensity: 0.9,
      roughness: 0.2,
      metalness: 0.1
    });

    this.matFingerPad = new THREE.MeshStandardMaterial({
      color: 0x334155,
      roughness: 0.8,
      metalness: 0.05
    });
  },

  setupEnvironment() {
    // Ground circular base grid
    this.gridHelper = new THREE.GridHelper(3.0, 30, 0x00e5ff, 0x1e293b);
    this.gridHelper.position.y = 0.001;
    this.scene.add(this.gridHelper);

    // Shadow receiver plane
    const planeGeo = new THREE.PlaneGeometry(10, 10);
    const planeMat = new THREE.ShadowMaterial({ opacity: 0.4 });
    const shadowPlane = new THREE.Mesh(planeGeo, planeMat);
    shadowPlane.rotation.x = -Math.PI / 2;
    shadowPlane.receiveShadow = true;
    this.scene.add(shadowPlane);
  },

  buildAuronRobot() {
    this.robotRoot = new THREE.Group();
    this.robotRoot.name = "AuronRobot";
    this.scene.add(this.robotRoot);

    // BASE LINK (Pedestal on ground)
    const baseGroup = new THREE.Group();
    this.robotRoot.add(baseGroup);

    // Flared pedestal base
    const basePedestal = new THREE.Mesh(
      new THREE.CylinderGeometry(0.12, 0.18, 0.10, 36),
      this.matWhite
    );
    basePedestal.position.y = 0.05;
    basePedestal.castShadow = true;
    basePedestal.receiveShadow = true;
    baseGroup.add(basePedestal);

    // Cyan trim ring at bottom
    const accentRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.178, 0.007, 16, 48),
      this.matCyanGlow
    );
    accentRing.rotation.x = Math.PI / 2;
    accentRing.position.y = 0.008;
    baseGroup.add(accentRing);

    // Collar ring
    const collar = new THREE.Mesh(
      new THREE.CylinderGeometry(0.105, 0.105, 0.02, 32),
      this.matCyanGlow
    );
    collar.position.y = 0.10;
    baseGroup.add(collar);

    // -------------------------------------------------------------
    // JOINT 1: Base Pan (Rotation around Y)
    // -------------------------------------------------------------
    const j1Node = new THREE.Group();
    j1Node.position.set(0, 0.11, 0);
    baseGroup.add(j1Node);
    this.jointNodes[0] = j1Node;

    // Turret Body (Blue & Dark metal)
    const turretBody = new THREE.Mesh(
      new THREE.CylinderGeometry(0.09, 0.10, 0.12, 32),
      this.matBlue
    );
    turretBody.position.y = 0.06;
    turretBody.castShadow = true;
    j1Node.add(turretBody);

    // Waist cyan glowing ring
    const waistRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.092, 0.006, 16, 36),
      this.matCyanGlow
    );
    waistRing.rotation.x = Math.PI / 2;
    waistRing.position.y = 0.08;
    j1Node.add(waistRing);

    // Actuator side hubs
    const sideHubGeo = new THREE.CylinderGeometry(0.055, 0.055, 0.025, 24);
    const leftHub = new THREE.Mesh(sideHubGeo, this.matDarkMetal);
    leftHub.rotation.z = Math.PI / 2;
    leftHub.position.set(-0.095, 0.11, 0);
    j1Node.add(leftHub);

    const rightHub = new THREE.Mesh(sideHubGeo, this.matDarkMetal);
    rightHub.rotation.z = Math.PI / 2;
    rightHub.position.set(0.095, 0.11, 0);
    j1Node.add(rightHub);

    // Cyan turbine center ring
    const leftTurbine = new THREE.Mesh(
      new THREE.TorusGeometry(0.04, 0.005, 12, 24),
      this.matCyanGlow
    );
    leftTurbine.rotation.y = Math.PI / 2;
    leftTurbine.position.set(-0.11, 0.11, 0);
    j1Node.add(leftTurbine);

    const rightTurbine = new THREE.Mesh(
      new THREE.TorusGeometry(0.04, 0.005, 12, 24),
      this.matCyanGlow
    );
    rightTurbine.rotation.y = Math.PI / 2;
    rightTurbine.position.set(0.11, 0.11, 0);
    j1Node.add(rightTurbine);

    // -------------------------------------------------------------
    // JOINT 2: Shoulder Pitch (Rotation around X axis)
    // -------------------------------------------------------------
    const j2Node = new THREE.Group();
    j2Node.position.set(0, 0.11, 0);
    j1Node.add(j2Node);
    this.jointNodes[1] = j2Node;

    // Upper Arm Body
    const upperArmLength = 0.38;
    const upperArmMesh = new THREE.Mesh(
      new THREE.CylinderGeometry(0.065, 0.075, upperArmLength, 28),
      this.matWhite
    );
    upperArmMesh.position.y = upperArmLength / 2;
    upperArmMesh.castShadow = true;
    j2Node.add(upperArmMesh);

    // Parallel hydraulic piston accents (matching screenshot reference)
    const pistonGeo = new THREE.CylinderGeometry(0.012, 0.012, upperArmLength * 0.75, 16);
    const leftPiston = new THREE.Mesh(pistonGeo, this.matDarkMetal);
    leftPiston.position.set(0.05, upperArmLength * 0.45, 0.05);
    j2Node.add(leftPiston);

    const rightPiston = new THREE.Mesh(pistonGeo, this.matDarkMetal);
    rightPiston.position.set(-0.05, upperArmLength * 0.45, 0.05);
    j2Node.add(rightPiston);

    // Mid arm accent cyan ring
    const armRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.072, 0.005, 12, 32),
      this.matCyanGlow
    );
    armRing.rotation.x = Math.PI / 2;
    armRing.position.y = upperArmLength * 0.55;
    j2Node.add(armRing);

    // -------------------------------------------------------------
    // JOINT 3: Elbow Pitch (Rotation around X axis)
    // -------------------------------------------------------------
    const j3Node = new THREE.Group();
    j3Node.position.set(0, upperArmLength, 0);
    j2Node.add(j3Node);
    this.jointNodes[2] = j3Node;

    // Elbow housing
    const elbowHousing = new THREE.Mesh(
      new THREE.CylinderGeometry(0.07, 0.07, 0.16, 28),
      this.matBlue
    );
    elbowHousing.rotation.z = Math.PI / 2;
    elbowHousing.castShadow = true;
    j3Node.add(elbowHousing);

    // Elbow side turbine rings
    const elbowRingL = new THREE.Mesh(
      new THREE.TorusGeometry(0.05, 0.005, 12, 24),
      this.matCyanGlow
    );
    elbowRingL.rotation.y = Math.PI / 2;
    elbowRingL.position.x = -0.082;
    j3Node.add(elbowRingL);

    const elbowRingR = new THREE.Mesh(
      new THREE.TorusGeometry(0.05, 0.005, 12, 24),
      this.matCyanGlow
    );
    elbowRingR.rotation.y = Math.PI / 2;
    elbowRingR.position.x = 0.082;
    j3Node.add(elbowRingR);

    // Forearm Body
    const forearmLength = 0.34;
    const forearmMesh = new THREE.Mesh(
      new THREE.CylinderGeometry(0.052, 0.062, forearmLength, 24),
      this.matWhite
    );
    forearmMesh.position.y = forearmLength / 2;
    forearmMesh.castShadow = true;
    j3Node.add(forearmMesh);

    // Forearm cyan longitudinal LED strip
    const stripGeo = new THREE.BoxGeometry(0.008, forearmLength * 0.7, 0.015);
    const strip = new THREE.Mesh(stripGeo, this.matCyanGlow);
    strip.position.set(0, forearmLength * 0.5, 0.055);
    j3Node.add(strip);

    // -------------------------------------------------------------
    // JOINT 4: Wrist Roll (Rotation around Y axis)
    // -------------------------------------------------------------
    const j4Node = new THREE.Group();
    j4Node.position.set(0, forearmLength, 0);
    j3Node.add(j4Node);
    this.jointNodes[3] = j4Node;

    const wristCollar = new THREE.Mesh(
      new THREE.CylinderGeometry(0.05, 0.052, 0.06, 24),
      this.matDarkMetal
    );
    wristCollar.position.y = 0.03;
    j4Node.add(wristCollar);

    const wristGlowRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.051, 0.004, 12, 28),
      this.matCyanGlow
    );
    wristGlowRing.rotation.x = Math.PI / 2;
    wristGlowRing.position.y = 0.05;
    j4Node.add(wristGlowRing);

    // -------------------------------------------------------------
    // JOINT 5: Wrist Pitch (Rotation around X axis)
    // -------------------------------------------------------------
    const j5Node = new THREE.Group();
    j5Node.position.set(0, 0.06, 0);
    j4Node.add(j5Node);
    this.jointNodes[4] = j5Node;

    const wristJointBox = new THREE.Mesh(
      new THREE.BoxGeometry(0.075, 0.05, 0.05),
      this.matWhite
    );
    wristJointBox.position.y = 0.025;
    wristJointBox.castShadow = true;
    j5Node.add(wristJointBox);

    // -------------------------------------------------------------
    // JOINT 6: Tool Roll (Rotation around Y axis)
    // -------------------------------------------------------------
    const j6Node = new THREE.Group();
    j6Node.position.set(0, 0.05, 0);
    j5Node.add(j6Node);
    this.jointNodes[5] = j6Node;

    // Flange connector
    const flange = new THREE.Mesh(
      new THREE.CylinderGeometry(0.042, 0.042, 0.02, 24),
      this.matDarkMetal
    );
    flange.position.y = 0.01;
    j6Node.add(flange);

    // -------------------------------------------------------------
    // ULTRA-MODERN DEXTEROUS ROBOTIC HAND & FINGERS
    // -------------------------------------------------------------
    this.buildModernDexterousHand(j6Node);
  },

  buildModernDexterousHand(parentJoint) {
    const handGroup = new THREE.Group();
    handGroup.position.set(0, 0.02, 0);
    parentJoint.add(handGroup);

    // Wrist mount ring with bright cyan LED
    const mountRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.043, 0.004, 16, 32),
      this.matCyanGlow
    );
    mountRing.rotation.x = Math.PI / 2;
    mountRing.position.y = 0.005;
    handGroup.add(mountRing);

    // Palm Core: Sleek curved bionic chassis
    const palmCoreGeo = new THREE.BoxGeometry(0.088, 0.065, 0.038);
    const palmCore = new THREE.Mesh(palmCoreGeo, this.matWhite);
    palmCore.position.set(0, 0.038, 0);
    palmCore.castShadow = true;
    handGroup.add(palmCore);

    // Palm dark metallic inner frame plate
    const palmBackPlate = new THREE.Mesh(
      new THREE.BoxGeometry(0.082, 0.06, 0.012),
      this.matDarkMetal
    );
    palmBackPlate.position.set(0, 0.038, -0.016);
    handGroup.add(palmBackPlate);

    // Cyan glowing aesthetic circuit accents on the back of hand
    const palmAccent1 = new THREE.Mesh(
      new THREE.BoxGeometry(0.06, 0.003, 0.002),
      this.matCyanGlow
    );
    palmAccent1.position.set(0, 0.045, 0.02);
    handGroup.add(palmAccent1);

    const palmAccent2 = new THREE.Mesh(
      new THREE.BoxGeometry(0.04, 0.003, 0.002),
      this.matCyanGlow
    );
    palmAccent2.position.set(0, 0.030, 0.02);
    handGroup.add(palmAccent2);

    // Subtle cyan pointlight at palm
    const handLight = new THREE.PointLight(0x00e5ff, 0.8, 0.35);
    handLight.position.set(0, 0.05, 0.04);
    handGroup.add(handLight);

    // 5 ARTICULATED FINGERS (Thumb, Index, Middle, Ring, Pinky)
    this.fingerNodes = [];

    const fingerConfigs = [
      { name: 'Thumb', x: -0.042, y: 0.022, z: 0.008, angleZ: 0.45, angleY: 0.25, len: 0.025, thickness: 0.011 },
      { name: 'Index', x: -0.030, y: 0.071, z: 0.0, angleZ: 0.06, angleY: 0.0, len: 0.034, thickness: 0.0095 },
      { name: 'Middle', x: -0.010, y: 0.074, z: 0.0, angleZ: 0.01, angleY: 0.0, len: 0.038, thickness: 0.0098 },
      { name: 'Ring', x: 0.012, y: 0.071, z: 0.0, angleZ: -0.04, angleY: 0.0, len: 0.034, thickness: 0.0092 },
      { name: 'Pinky', x: 0.032, y: 0.065, z: 0.0, angleZ: -0.09, angleY: 0.0, len: 0.028, thickness: 0.0085 }
    ];

    fingerConfigs.forEach((cfg) => {
      const baseNode = new THREE.Group();
      baseNode.position.set(cfg.x, cfg.y, cfg.z);
      baseNode.rotation.z = cfg.angleZ;
      baseNode.rotation.y = cfg.angleY;
      handGroup.add(baseNode);

      // Knuckle Joint 1 (MCP)
      const knuckle1 = new THREE.Mesh(
        new THREE.CylinderGeometry(cfg.thickness * 1.05, cfg.thickness * 1.05, 0.012, 16),
        this.matCyanGlow
      );
      knuckle1.rotation.z = Math.PI / 2;
      baseNode.add(knuckle1);

      // Phalanx 1 (Proximal)
      const phalanx1Mesh = new THREE.Mesh(
        new THREE.CylinderGeometry(cfg.thickness * 0.9, cfg.thickness, cfg.len, 14),
        this.matWhite
      );
      phalanx1Mesh.position.y = cfg.len / 2;
      phalanx1Mesh.castShadow = true;
      baseNode.add(phalanx1Mesh);

      // Knuckle Joint 2 (PIP)
      const pipNode = new THREE.Group();
      pipNode.position.y = cfg.len;
      baseNode.add(pipNode);

      const knuckle2 = new THREE.Mesh(
        new THREE.CylinderGeometry(cfg.thickness * 0.9, cfg.thickness * 0.9, 0.010, 14),
        this.matDarkMetal
      );
      knuckle2.rotation.z = Math.PI / 2;
      pipNode.add(knuckle2);

      // Phalanx 2 (Intermediate)
      const phalanx2Len = cfg.len * 0.75;
      const phalanx2Mesh = new THREE.Mesh(
        new THREE.CylinderGeometry(cfg.thickness * 0.75, cfg.thickness * 0.85, phalanx2Len, 14),
        this.matWhite
      );
      phalanx2Mesh.position.y = phalanx2Len / 2;
      phalanx2Mesh.castShadow = true;
      pipNode.add(phalanx2Mesh);

      // Knuckle Joint 3 (DIP) & Fingertip
      const dipNode = new THREE.Group();
      dipNode.position.y = phalanx2Len;
      pipNode.add(dipNode);

      const phalanx3Len = cfg.len * 0.55;
      const tipMesh = new THREE.Mesh(
        new THREE.SphereGeometry(cfg.thickness * 0.7, 12, 12),
        this.matFingerPad
      );
      tipMesh.position.y = phalanx3Len;
      dipNode.add(tipMesh);

      // Store references for flexing
      this.fingerNodes.push({
        name: cfg.name,
        baseNode: baseNode,
        pipNode: pipNode,
        dipNode: dipNode,
        defaultAngleZ: cfg.angleZ
      });
    });
  },

  updateJoints(positions) {
    if (!this.jointNodes || this.jointNodes.length < 6) return;

    // Joint 1: Base Pan -> Y-axis
    if (this.jointNodes[0]) {
      this.jointNodes[0].rotation.y = positions[0];
    }
    // Joint 2: Shoulder Pitch -> X-axis (inverted to match robot coordinate convention)
    if (this.jointNodes[1]) {
      this.jointNodes[1].rotation.x = -positions[1];
    }
    // Joint 3: Elbow Pitch -> X-axis
    if (this.jointNodes[2]) {
      this.jointNodes[2].rotation.x = -positions[2];
    }
    // Joint 4: Wrist Roll -> Y-axis
    if (this.jointNodes[3]) {
      this.jointNodes[3].rotation.y = positions[3];
    }
    // Joint 5: Wrist Pitch -> X-axis
    if (this.jointNodes[4]) {
      this.jointNodes[4].rotation.x = -positions[4];
    }
    // Joint 6: Tool Roll -> Y-axis
    if (this.jointNodes[5]) {
      this.jointNodes[5].rotation.y = positions[5];
    }
  },

  updateHandGrip(meterVal) {
    // meterVal is between 0.0 (closed) and 0.035 (fully open)
    // Map to normalized curl factor 0.0 (open) to 1.0 (fully curled/closed)
    const normalized = Math.max(0, Math.min(1, 1.0 - (meterVal / 0.035)));
    this.setHandCurl(normalized);
  },

  setHandCurl(curlFactor) {
    // curlFactor: 0.0 (flat open) to 1.0 (closed fist)
    this.fingerNodes.forEach((finger) => {
      const curlBase = curlFactor * 0.75;
      const curlPip = curlFactor * 0.95;
      const curlDip = curlFactor * 0.85;

      finger.baseNode.rotation.x = curlBase;
      finger.pipNode.rotation.x = curlPip;
      finger.dipNode.rotation.x = curlDip;

      if (finger.name === 'Thumb') {
        finger.baseNode.rotation.z = finger.defaultAngleZ + curlFactor * 0.4;
        finger.baseNode.rotation.y = curlFactor * 0.6;
      }
    });
  },

  applyGesture(gestureName) {
    // Reset all first
    this.setHandCurl(0.0);

    switch (gestureName) {
      case 'open':
        this.setHandCurl(0.0);
        break;
      case 'fist':
        this.setHandCurl(1.0);
        break;
      case 'pinch':
        // Thumb and index curled together
        this.fingerNodes.forEach((f) => {
          if (f.name === 'Thumb' || f.name === 'Index') {
            f.baseNode.rotation.x = 0.8;
            f.pipNode.rotation.x = 0.9;
            f.dipNode.rotation.x = 0.6;
          } else {
            f.baseNode.rotation.x = 0.1;
            f.pipNode.rotation.x = 0.1;
          }
        });
        break;
      case 'peace':
        // Index and Middle open, others closed
        this.fingerNodes.forEach((f) => {
          if (f.name === 'Index' || f.name === 'Middle') {
            f.baseNode.rotation.x = 0.0;
            f.pipNode.rotation.x = 0.0;
            f.dipNode.rotation.x = 0.0;
          } else {
            f.baseNode.rotation.x = 0.9;
            f.pipNode.rotation.x = 1.0;
            f.dipNode.rotation.x = 0.8;
          }
        });
        break;
      case 'point':
        // Only index pointing
        this.fingerNodes.forEach((f) => {
          if (f.name === 'Index') {
            f.baseNode.rotation.x = 0.0;
            f.pipNode.rotation.x = 0.0;
          } else {
            f.baseNode.rotation.x = 0.9;
            f.pipNode.rotation.x = 1.0;
            f.dipNode.rotation.x = 0.8;
          }
        });
        break;
      case 'thumbsup':
        // Thumb up, rest closed
        this.fingerNodes.forEach((f) => {
          if (f.name === 'Thumb') {
            f.baseNode.rotation.x = -0.2;
            f.baseNode.rotation.z = 0.1;
          } else {
            f.baseNode.rotation.x = 0.95;
            f.pipNode.rotation.x = 1.1;
            f.dipNode.rotation.x = 0.9;
          }
        });
        break;
      default:
        this.setHandCurl(0.0);
    }
  },

  setCameraView(viewType) {
    if (!this.controls || !this.camera) return;
    switch (viewType) {
      case 'iso':
        this.camera.position.set(1.4, 1.1, 1.6);
        this.controls.target.set(0, 0.45, 0);
        break;
      case 'front':
        this.camera.position.set(0, 0.55, 2.0);
        this.controls.target.set(0, 0.45, 0);
        break;
      case 'side':
        this.camera.position.set(2.0, 0.55, 0);
        this.controls.target.set(0, 0.45, 0);
        break;
      case 'top':
        this.camera.position.set(0, 2.2, 0.01);
        this.controls.target.set(0, 0.35, 0);
        break;
      case 'hand':
        // Focus closely on the modern end effector hand
        this.camera.position.set(0.35, 0.95, 0.45);
        this.controls.target.set(0, 0.85, 0);
        break;
    }
    this.controls.update();
  },

  toggleGrid() {
    this.showGrid = !this.showGrid;
    if (this.gridHelper) {
      this.gridHelper.visible = this.showGrid;
    }
    return this.showGrid;
  },

  toggleWireframe() {
    this.isWireframe = !this.isWireframe;
    [this.matWhite, this.matBlue, this.matDarkMetal].forEach((mat) => {
      if (mat) mat.wireframe = this.isWireframe;
    });
    return this.isWireframe;
  },

  onResize() {
    if (!this.container || !this.renderer || !this.camera) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  },

  animate() {
    requestAnimationFrame(this.animate);
    if (this.controls) {
      this.controls.update();
    }
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  }
};
