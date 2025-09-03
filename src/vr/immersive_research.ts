/**
 * Immersive Research Experience for AI Scholar
 * AR/VR research environments with 3D knowledge visualization
 */
import * as THREE from 'three';
import { ARButton } from 'three/examples/jsm/webxr/ARButton.js';
import { VRButton } from 'three/examples/jsm/webxr/VRButton.js';
import { XRControllerModelFactory } from 'three/examples/jsm/webxr/XRControllerModelFactory.js';

interface ResearchNode {
  id: string;
  title: string;
  type: 'paper' | 'author' | 'concept' | 'dataset' | 'method';
  position: THREE.Vector3;
  connections: string[];
  metadata: {
    citations: number;
    year: number;
    field: string;
    importance: number;
  };
  content?: string;
}

interface KnowledgeGraph {
  nodes: ResearchNode[];
  edges: Array<{
    source: string;
    target: string;
    type: string;
    strength: number;
  }>;
}

interface VRSession {
  sessionId: string;
  userId: string;
  participants: string[];
  startTime: Date;
  environment: '3d_knowledge_space' | 'virtual_lab' | 'collaboration_room';
  sharedObjects: Map<string, any>;
}

class ImmersiveResearchEnvironment {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private vrEnabled: boolean = false;
  private arEnabled: boolean = false;
  private controllers: THREE.Group[] = [];
  private knowledgeGraph: KnowledgeGraph | null = null;
  private currentSession: VRSession | null = null;
  private nodeObjects: Map<string, THREE.Object3D> = new Map();
  private connectionLines: Map<string, THREE.Line> = new Map();

  constructor(container: HTMLElement) {
    this.initializeScene();
    this.setupRenderer(container);
    this.setupCamera();
    this.setupLighting();
    this.setupControls();
    this.setupEventListeners();
  }

  private initializeScene(): void {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0a0a0a);
    
    // Add subtle grid for spatial reference
    const gridHelper = new THREE.GridHelper(100, 100, 0x333333, 0x111111);
    gridHelper.position.y = -5;
    this.scene.add(gridHelper);
  }

  private setupRenderer(container: HTMLElement): void {
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.xr.enabled = true;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    
    container.appendChild(this.renderer.domElement);

    // Add VR/AR buttons
    if (navigator.xr) {
      this.setupXRButtons(container);
    }
  }

  private setupXRButtons(container: HTMLElement): void {
    // VR Button
    navigator.xr?.isSessionSupported('immersive-vr').then((supported) => {
      if (supported) {
        const vrButton = VRButton.createButton(this.renderer);
        vrButton.addEventListener('click', () => {
          this.vrEnabled = true;
          this.setupVRControllers();
        });
        container.appendChild(vrButton);
      }
    });

    // AR Button
    navigator.xr?.isSessionSupported('immersive-ar').then((supported) => {
      if (supported) {
        const arButton = ARButton.createButton(this.renderer);
        arButton.addEventListener('click', () => {
          this.arEnabled = true;
          this.setupARFeatures();
        });
        container.appendChild(arButton);
      }
    });
  }

  private setupCamera(): void {
    this.camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    this.camera.position.set(0, 10, 20);
    this.camera.lookAt(0, 0, 0);
  }

  private setupLighting(): void {
    // Ambient light
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    this.scene.add(ambientLight);

    // Directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    this.scene.add(directionalLight);

    // Point lights for atmosphere
    const pointLight1 = new THREE.PointLight(0x4080ff, 0.5, 50);
    pointLight1.position.set(-20, 10, -20);
    this.scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xff4080, 0.5, 50);
    pointLight2.position.set(20, 10, 20);
    this.scene.add(pointLight2);
  }

  private setupControls(): void {
    // Mouse/keyboard controls for non-VR mode
    window.addEventListener('keydown', (event) => {
      switch (event.code) {
        case 'KeyW':
          this.camera.position.z -= 1;
          break;
        case 'KeyS':
          this.camera.position.z += 1;
          break;
        case 'KeyA':
          this.camera.position.x -= 1;
          break;
        case 'KeyD':
          this.camera.position.x += 1;
          break;
        case 'Space':
          this.camera.position.y += 1;
          break;
        case 'ShiftLeft':
          this.camera.position.y -= 1;
          break;
      }
    });

    // Mouse controls
    let mouseDown = false;
    let mouseX = 0;
    let mouseY = 0;

    this.renderer.domElement.addEventListener('mousedown', (event) => {
      mouseDown = true;
      mouseX = event.clientX;
      mouseY = event.clientY;
    });

    this.renderer.domElement.addEventListener('mouseup', () => {
      mouseDown = false;
    });

    this.renderer.domElement.addEventListener('mousemove', (event) => {
      if (!mouseDown) return;

      const deltaX = event.clientX - mouseX;
      const deltaY = event.clientY - mouseY;

      this.camera.rotation.y -= deltaX * 0.01;
      this.camera.rotation.x -= deltaY * 0.01;

      mouseX = event.clientX;
      mouseY = event.clientY;
    });
  }

  private setupVRControllers(): void {
    const controllerModelFactory = new XRControllerModelFactory();

    // Controller 1
    const controller1 = this.renderer.xr.getController(0);
    controller1.addEventListener('selectstart', this.onSelectStart.bind(this));
    controller1.addEventListener('selectend', this.onSelectEnd.bind(this));
    this.scene.add(controller1);

    const controllerGrip1 = this.renderer.xr.getControllerGrip(0);
    controllerGrip1.add(controllerModelFactory.createControllerModel(controllerGrip1));
    this.scene.add(controllerGrip1);

    // Controller 2
    const controller2 = this.renderer.xr.getController(1);
    controller2.addEventListener('selectstart', this.onSelectStart.bind(this));
    controller2.addEventListener('selectend', this.onSelectEnd.bind(this));
    this.scene.add(controller2);

    const controllerGrip2 = this.renderer.xr.getControllerGrip(1);
    controllerGrip2.add(controllerModelFactory.createControllerModel(controllerGrip2));
    this.scene.add(controllerGrip2);

    this.controllers = [controller1, controller2];

    // Add laser pointers
    this.addLaserPointers();
  }

  private addLaserPointers(): void {
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0, 0, -1)
    ]);

    const material = new THREE.LineBasicMaterial({ color: 0xff0000 });

    this.controllers.forEach(controller => {
      const line = new THREE.Line(geometry, material);
      line.name = 'laser';
      line.scale.z = 5;
      controller.add(line);
    });
  }

  private setupARFeatures(): void {
    // AR-specific setup
    this.scene.background = null; // Transparent background for AR
    
    // Add AR-specific UI elements
    this.createARInterface();
  }

  private createARInterface(): void {
    // Create floating UI panels for AR
    const panelGeometry = new THREE.PlaneGeometry(2, 1.5);
    const panelMaterial = new THREE.MeshBasicMaterial({
      color: 0x000000,
      opacity: 0.8,
      transparent: true
    });

    const infoPanel = new THREE.Mesh(panelGeometry, panelMaterial);
    infoPanel.position.set(-3, 2, -2);
    infoPanel.name = 'ar-info-panel';
    this.scene.add(infoPanel);

    // Add text to panel (would use TextGeometry or HTML overlay in production)
    this.addTextToPanel(infoPanel, 'Research Information');
  }

  private addTextToPanel(panel: THREE.Mesh, text: string): void {
    // In production, use TextGeometry or HTML overlay
    // For now, create a simple text representation
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d')!;
    canvas.width = 512;
    canvas.height = 256;
    
    context.fillStyle = '#ffffff';
    context.font = '24px Arial';
    context.fillText(text, 20, 50);
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.MeshBasicMaterial({ map: texture, transparent: true });
    panel.material = material;
  }

  private setupEventListeners(): void {
    window.addEventListener('resize', this.onWindowResize.bind(this));
  }

  private onWindowResize(): void {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  private onSelectStart(event: any): void {
    const controller = event.target;
    
    // Raycast to find intersected objects
    const raycaster = new THREE.Raycaster();
    const tempMatrix = new THREE.Matrix4();
    
    tempMatrix.identity().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(tempMatrix);

    const intersects = raycaster.intersectObjects(this.scene.children, true);
    
    if (intersects.length > 0) {
      const intersected = intersects[0].object;
      this.handleObjectSelection(intersected);
    }
  }

  private onSelectEnd(event: any): void {
    // Handle selection end
  }

  private handleObjectSelection(object: THREE.Object3D): void {
    // Handle selection of research nodes or UI elements
    if (object.userData.type === 'research_node') {
      this.displayNodeInformation(object.userData.nodeId);
    } else if (object.userData.type === 'ui_element') {
      this.handleUIInteraction(object.userData.action);
    }
  }

  /**
   * Create 3D knowledge space from research data
   */
  async create3DKnowledgeSpace(researchTopic: string): Promise<void> {
    console.log(`🌌 Creating 3D knowledge space for: ${researchTopic}`);

    // Fetch knowledge graph data
    this.knowledgeGraph = await this.fetchKnowledgeGraph(researchTopic);
    
    // Clear existing objects
    this.clearKnowledgeSpace();
    
    // Create 3D nodes
    this.createResearchNodes();
    
    // Create connections
    this.createConnections();
    
    // Add interactive elements
    this.addInteractiveElements();
    
    // Animate entrance
    this.animateKnowledgeSpaceEntrance();
  }

  private async fetchKnowledgeGraph(topic: string): Promise<KnowledgeGraph> {
    // Mock knowledge graph - in production, fetch from backend
    const mockNodes: ResearchNode[] = [
      {
        id: 'node_1',
        title: 'Deep Learning Fundamentals',
        type: 'concept',
        position: new THREE.Vector3(0, 0, 0),
        connections: ['node_2', 'node_3'],
        metadata: { citations: 1500, year: 2020, field: 'AI', importance: 0.9 }
      },
      {
        id: 'node_2', 
        title: 'Neural Network Architectures',
        type: 'method',
        position: new THREE.Vector3(10, 5, -5),
        connections: ['node_1', 'node_4'],
        metadata: { citations: 800, year: 2021, field: 'AI', importance: 0.7 }
      },
      {
        id: 'node_3',
        title: 'ImageNet Dataset',
        type: 'dataset',
        position: new THREE.Vector3(-8, 3, 8),
        connections: ['node_1', 'node_5'],
        metadata: { citations: 2000, year: 2019, field: 'CV', importance: 0.95 }
      },
      {
        id: 'node_4',
        title: 'Attention Mechanisms',
        type: 'concept',
        position: new THREE.Vector3(15, -2, 10),
        connections: ['node_2'],
        metadata: { citations: 1200, year: 2022, field: 'NLP', importance: 0.8 }
      },
      {
        id: 'node_5',
        title: 'Computer Vision Applications',
        type: 'paper',
        position: new THREE.Vector3(-12, -4, 15),
        connections: ['node_3'],
        metadata: { citations: 600, year: 2023, field: 'CV', importance: 0.6 }
      }
    ];

    const mockEdges = [
      { source: 'node_1', target: 'node_2', type: 'uses', strength: 0.8 },
      { source: 'node_1', target: 'node_3', type: 'trained_on', strength: 0.9 },
      { source: 'node_2', target: 'node_4', type: 'incorporates', strength: 0.7 },
      { source: 'node_3', target: 'node_5', type: 'enables', strength: 0.6 }
    ];

    return { nodes: mockNodes, edges: mockEdges };
  }

  private clearKnowledgeSpace(): void {
    // Remove existing nodes and connections
    this.nodeObjects.forEach(obj => this.scene.remove(obj));
    this.connectionLines.forEach(line => this.scene.remove(line));
    this.nodeObjects.clear();
    this.connectionLines.clear();
  }

  private createResearchNodes(): void {
    if (!this.knowledgeGraph) return;

    this.knowledgeGraph.nodes.forEach(node => {
      const nodeObject = this.createNodeObject(node);
      this.scene.add(nodeObject);
      this.nodeObjects.set(node.id, nodeObject);
    });
  }

  private createNodeObject(node: ResearchNode): THREE.Object3D {
    const group = new THREE.Group();
    
    // Node geometry based on type
    let geometry: THREE.BufferGeometry;
    let material: THREE.Material;
    
    switch (node.type) {
      case 'paper':
        geometry = new THREE.BoxGeometry(2, 0.1, 1.5);
        material = new THREE.MeshLambertMaterial({ color: 0x4CAF50 });
        break;
      case 'author':
        geometry = new THREE.SphereGeometry(1, 16, 16);
        material = new THREE.MeshLambertMaterial({ color: 0x2196F3 });
        break;
      case 'concept':
        geometry = new THREE.OctahedronGeometry(1.2);
        material = new THREE.MeshLambertMaterial({ color: 0xFF9800 });
        break;
      case 'dataset':
        geometry = new THREE.CylinderGeometry(1, 1, 2);
        material = new THREE.MeshLambertMaterial({ color: 0x9C27B0 });
        break;
      case 'method':
        geometry = new THREE.ConeGeometry(1, 2);
        material = new THREE.MeshLambertMaterial({ color: 0xF44336 });
        break;
      default:
        geometry = new THREE.SphereGeometry(1);
        material = new THREE.MeshLambertMaterial({ color: 0x607D8B });
    }

    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    
    // Scale based on importance
    const scale = 0.5 + (node.metadata.importance * 1.5);
    mesh.scale.setScalar(scale);
    
    // Add glow effect for highly cited papers
    if (node.metadata.citations > 1000) {
      const glowGeometry = new THREE.SphereGeometry(scale * 1.2);
      const glowMaterial = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.2
      });
      const glow = new THREE.Mesh(glowGeometry, glowMaterial);
      group.add(glow);
    }
    
    group.add(mesh);
    group.position.copy(node.position);
    
    // Add metadata
    group.userData = {
      type: 'research_node',
      nodeId: node.id,
      nodeData: node
    };
    
    // Add floating label
    this.addNodeLabel(group, node.title);
    
    return group;
  }

  private addNodeLabel(nodeGroup: THREE.Group, title: string): void {
    // Create text label (simplified - in production use TextGeometry or HTML overlay)
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d')!;
    canvas.width = 256;
    canvas.height = 64;
    
    context.fillStyle = '#ffffff';
    context.font = '16px Arial';
    context.textAlign = 'center';
    context.fillText(title.substring(0, 20) + '...', 128, 32);
    
    const texture = new THREE.CanvasTexture(canvas);
    const labelMaterial = new THREE.SpriteMaterial({ map: texture });
    const label = new THREE.Sprite(labelMaterial);
    label.position.y = 2;
    label.scale.set(4, 1, 1);
    
    nodeGroup.add(label);
  }

  private createConnections(): void {
    if (!this.knowledgeGraph) return;

    this.knowledgeGraph.edges.forEach(edge => {
      const sourceNode = this.nodeObjects.get(edge.source);
      const targetNode = this.nodeObjects.get(edge.target);
      
      if (sourceNode && targetNode) {
        const connection = this.createConnectionLine(
          sourceNode.position,
          targetNode.position,
          edge.strength
        );
        this.scene.add(connection);
        this.connectionLines.set(`${edge.source}-${edge.target}`, connection);
      }
    });
  }

  private createConnectionLine(
    start: THREE.Vector3,
    end: THREE.Vector3,
    strength: number
  ): THREE.Line {
    const geometry = new THREE.BufferGeometry().setFromPoints([start, end]);
    
    // Line color and opacity based on connection strength
    const color = new THREE.Color().setHSL(0.6 * strength, 1, 0.5);
    const material = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.3 + (strength * 0.7)
    });
    
    return new THREE.Line(geometry, material);
  }

  private addInteractiveElements(): void {
    // Add control panel
    this.createControlPanel();
    
    // Add search interface
    this.createSearchInterface();
    
    // Add filter controls
    this.createFilterControls();
  }

  private createControlPanel(): void {
    const panelGeometry = new THREE.PlaneGeometry(4, 3);
    const panelMaterial = new THREE.MeshBasicMaterial({
      color: 0x1a1a1a,
      transparent: true,
      opacity: 0.9
    });
    
    const panel = new THREE.Mesh(panelGeometry, panelMaterial);
    panel.position.set(-15, 5, 0);
    panel.lookAt(this.camera.position);
    
    // Add buttons (simplified)
    this.addControlButtons(panel);
    
    this.scene.add(panel);
  }

  private addControlButtons(panel: THREE.Mesh): void {
    const buttonGeometry = new THREE.PlaneGeometry(1.5, 0.5);
    
    const buttons = [
      { text: 'Filter by Year', action: 'filter_year', position: [0, 1, 0.01] },
      { text: 'Show Citations', action: 'show_citations', position: [0, 0.3, 0.01] },
      { text: 'Cluster Topics', action: 'cluster_topics', position: [0, -0.4, 0.01] },
      { text: 'Reset View', action: 'reset_view', position: [0, -1.1, 0.01] }
    ];
    
    buttons.forEach(buttonData => {
      const buttonMaterial = new THREE.MeshBasicMaterial({ color: 0x4CAF50 });
      const button = new THREE.Mesh(buttonGeometry, buttonMaterial);
      button.position.set(...buttonData.position);
      button.userData = {
        type: 'ui_element',
        action: buttonData.action
      };
      
      // Add text label
      this.addButtonLabel(button, buttonData.text);
      
      panel.add(button);
    });
  }

  private addButtonLabel(button: THREE.Mesh, text: string): void {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d')!;
    canvas.width = 256;
    canvas.height = 64;
    
    context.fillStyle = '#ffffff';
    context.font = '20px Arial';
    context.textAlign = 'center';
    context.fillText(text, 128, 40);
    
    const texture = new THREE.CanvasTexture(canvas);
    const labelMaterial = new THREE.MeshBasicMaterial({ map: texture });
    button.material = labelMaterial;
  }

  private createSearchInterface(): void {
    // Create floating search bar
    const searchGeometry = new THREE.PlaneGeometry(6, 1);
    const searchMaterial = new THREE.MeshBasicMaterial({
      color: 0x333333,
      transparent: true,
      opacity: 0.8
    });
    
    const searchBar = new THREE.Mesh(searchGeometry, searchMaterial);
    searchBar.position.set(0, 12, -5);
    searchBar.userData = {
      type: 'ui_element',
      action: 'search'
    };
    
    this.addTextToPanel(searchBar, 'Search Research...');
    this.scene.add(searchBar);
  }

  private createFilterControls(): void {
    // Create filter sliders and toggles
    const filterPanel = new THREE.Group();
    filterPanel.position.set(15, 5, 0);
    
    // Year filter slider
    const yearSlider = this.createSlider('Year Range', 2015, 2024);
    yearSlider.position.y = 2;
    filterPanel.add(yearSlider);
    
    // Citation filter slider
    const citationSlider = this.createSlider('Min Citations', 0, 2000);
    citationSlider.position.y = 0;
    filterPanel.add(citationSlider);
    
    // Field toggles
    const fieldToggles = this.createFieldToggles();
    fieldToggles.position.y = -2;
    filterPanel.add(fieldToggles);
    
    this.scene.add(filterPanel);
  }

  private createSlider(label: string, min: number, max: number): THREE.Group {
    const sliderGroup = new THREE.Group();
    
    // Slider track
    const trackGeometry = new THREE.CylinderGeometry(0.05, 0.05, 4);
    const trackMaterial = new THREE.MeshBasicMaterial({ color: 0x666666 });
    const track = new THREE.Mesh(trackGeometry, trackMaterial);
    track.rotation.z = Math.PI / 2;
    sliderGroup.add(track);
    
    // Slider handle
    const handleGeometry = new THREE.SphereGeometry(0.2);
    const handleMaterial = new THREE.MeshBasicMaterial({ color: 0x4CAF50 });
    const handle = new THREE.Mesh(handleGeometry, handleMaterial);
    handle.userData = {
      type: 'ui_element',
      action: 'slider',
      label: label,
      min: min,
      max: max
    };
    sliderGroup.add(handle);
    
    // Label
    const labelSprite = this.createTextSprite(label);
    labelSprite.position.y = 0.8;
    sliderGroup.add(labelSprite);
    
    return sliderGroup;
  }

  private createFieldToggles(): THREE.Group {
    const toggleGroup = new THREE.Group();
    
    const fields = ['AI', 'CV', 'NLP', 'ML', 'Robotics'];
    
    fields.forEach((field, index) => {
      const toggle = this.createToggle(field);
      toggle.position.x = (index - 2) * 1.5;
      toggleGroup.add(toggle);
    });
    
    return toggleGroup;
  }

  private createToggle(label: string): THREE.Group {
    const toggleGroup = new THREE.Group();
    
    // Toggle button
    const buttonGeometry = new THREE.BoxGeometry(0.8, 0.4, 0.2);
    const buttonMaterial = new THREE.MeshBasicMaterial({ color: 0x4CAF50 });
    const button = new THREE.Mesh(buttonGeometry, buttonMaterial);
    button.userData = {
      type: 'ui_element',
      action: 'toggle',
      label: label,
      active: true
    };
    toggleGroup.add(button);
    
    // Label
    const labelSprite = this.createTextSprite(label);
    labelSprite.position.y = -0.8;
    labelSprite.scale.setScalar(0.5);
    toggleGroup.add(labelSprite);
    
    return toggleGroup;
  }

  private createTextSprite(text: string): THREE.Sprite {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d')!;
    canvas.width = 256;
    canvas.height = 64;
    
    context.fillStyle = '#ffffff';
    context.font = '24px Arial';
    context.textAlign = 'center';
    context.fillText(text, 128, 40);
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture });
    return new THREE.Sprite(material);
  }

  private animateKnowledgeSpaceEntrance(): void {
    // Animate nodes appearing
    this.nodeObjects.forEach((nodeObj, index) => {
      nodeObj.scale.setScalar(0);
      
      setTimeout(() => {
        this.animateNodeAppearance(nodeObj);
      }, index * 200);
    });
    
    // Animate connections appearing
    setTimeout(() => {
      this.animateConnectionsAppearance();
    }, this.nodeObjects.size * 200 + 500);
  }

  private animateNodeAppearance(nodeObj: THREE.Object3D): void {
    const targetScale = nodeObj.userData.nodeData?.metadata.importance || 1;
    
    const animate = () => {
      if (nodeObj.scale.x < targetScale) {
        nodeObj.scale.addScalar(0.05);
        requestAnimationFrame(animate);
      }
    };
    
    animate();
  }

  private animateConnectionsAppearance(): void {
    this.connectionLines.forEach((line, index) => {
      line.material.opacity = 0;
      
      setTimeout(() => {
        this.animateLineAppearance(line);
      }, index * 100);
    });
  }

  private animateLineAppearance(line: THREE.Line): void {
    const targetOpacity = (line.material as THREE.LineBasicMaterial).opacity;
    (line.material as THREE.LineBasicMaterial).opacity = 0;
    
    const animate = () => {
      const material = line.material as THREE.LineBasicMaterial;
      if (material.opacity < targetOpacity) {
        material.opacity += 0.02;
        requestAnimationFrame(animate);
      }
    };
    
    animate();
  }

  private displayNodeInformation(nodeId: string): void {
    const node = this.knowledgeGraph?.nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    // Create information panel
    this.createInformationPanel(node);
    
    // Highlight connected nodes
    this.highlightConnectedNodes(nodeId);
  }

  private createInformationPanel(node: ResearchNode): void {
    // Remove existing info panel
    const existingPanel = this.scene.getObjectByName('info-panel');
    if (existingPanel) {
      this.scene.remove(existingPanel);
    }
    
    // Create new info panel
    const panelGeometry = new THREE.PlaneGeometry(6, 4);
    const panelMaterial = new THREE.MeshBasicMaterial({
      color: 0x1a1a1a,
      transparent: true,
      opacity: 0.9
    });
    
    const panel = new THREE.Mesh(panelGeometry, panelMaterial);
    panel.position.set(0, 8, -10);
    panel.lookAt(this.camera.position);
    panel.name = 'info-panel';
    
    // Add information text
    const infoText = `
Title: ${node.title}
Type: ${node.type}
Citations: ${node.metadata.citations}
Year: ${node.metadata.year}
Field: ${node.metadata.field}
Importance: ${(node.metadata.importance * 100).toFixed(1)}%
    `;
    
    this.addTextToPanel(panel, infoText);
    this.scene.add(panel);
  }

  private highlightConnectedNodes(nodeId: string): void {
    // Reset all node materials
    this.nodeObjects.forEach(nodeObj => {
      const mesh = nodeObj.children.find(child => child instanceof THREE.Mesh) as THREE.Mesh;
      if (mesh && mesh.material instanceof THREE.MeshLambertMaterial) {
        mesh.material.emissive.setHex(0x000000);
      }
    });
    
    // Highlight connected nodes
    const connections = this.knowledgeGraph?.edges.filter(
      edge => edge.source === nodeId || edge.target === nodeId
    ) || [];
    
    connections.forEach(connection => {
      const connectedNodeId = connection.source === nodeId ? connection.target : connection.source;
      const connectedNodeObj = this.nodeObjects.get(connectedNodeId);
      
      if (connectedNodeObj) {
        const mesh = connectedNodeObj.children.find(child => child instanceof THREE.Mesh) as THREE.Mesh;
        if (mesh && mesh.material instanceof THREE.MeshLambertMaterial) {
          mesh.material.emissive.setHex(0x444444);
        }
      }
    });
  }

  private handleUIInteraction(action: string): void {
    switch (action) {
      case 'filter_year':
        this.filterByYear();
        break;
      case 'show_citations':
        this.toggleCitationDisplay();
        break;
      case 'cluster_topics':
        this.clusterByTopics();
        break;
      case 'reset_view':
        this.resetView();
        break;
      case 'search':
        this.openSearchInterface();
        break;
    }
  }

  private filterByYear(): void {
    // Implement year filtering
    console.log('Filtering by year...');
  }

  private toggleCitationDisplay(): void {
    // Toggle citation visualization
    console.log('Toggling citation display...');
  }

  private clusterByTopics(): void {
    // Cluster nodes by research topics
    console.log('Clustering by topics...');
  }

  private resetView(): void {
    // Reset camera and view
    this.camera.position.set(0, 10, 20);
    this.camera.lookAt(0, 0, 0);
  }

  private openSearchInterface(): void {
    // Open search interface
    console.log('Opening search interface...');
  }

  /**
   * Start virtual collaboration session
   */
  async virtualCollaboration(participants: string[]): Promise<VRSession> {
    const session: VRSession = {
      sessionId: `vr_session_${Date.now()}`,
      userId: 'current_user', // Would get from auth
      participants: participants,
      startTime: new Date(),
      environment: 'collaboration_room',
      sharedObjects: new Map()
    };

    this.currentSession = session;

    // Create collaboration environment
    await this.createCollaborationRoom();

    // Add participant avatars
    this.addParticipantAvatars(participants);

    // Setup shared interaction
    this.setupSharedInteraction();

    console.log(`🤝 Virtual collaboration session started with ${participants.length} participants`);
    
    return session;
  }

  private async createCollaborationRoom(): void {
    // Create virtual meeting room
    const roomGeometry = new THREE.BoxGeometry(30, 15, 30);
    const roomMaterial = new THREE.MeshLambertMaterial({
      color: 0x2a2a2a,
      transparent: true,
      opacity: 0.1
    });
    
    const room = new THREE.Mesh(roomGeometry, roomMaterial);
    room.name = 'collaboration-room';
    this.scene.add(room);

    // Add virtual whiteboards
    this.addVirtualWhiteboards();

    // Add shared document viewers
    this.addSharedDocumentViewers();
  }

  private addVirtualWhiteboards(): void {
    const whiteboardGeometry = new THREE.PlaneGeometry(8, 6);
    const whiteboardMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff });
    
    // Front whiteboard
    const frontBoard = new THREE.Mesh(whiteboardGeometry, whiteboardMaterial);
    frontBoard.position.set(0, 3, -14);
    frontBoard.name = 'whiteboard-front';
    this.scene.add(frontBoard);
    
    // Side whiteboards
    const leftBoard = new THREE.Mesh(whiteboardGeometry, whiteboardMaterial);
    leftBoard.position.set(-14, 3, 0);
    leftBoard.rotation.y = Math.PI / 2;
    leftBoard.name = 'whiteboard-left';
    this.scene.add(leftBoard);
  }

  private addSharedDocumentViewers(): void {
    // Create floating document viewers
    const viewerGeometry = new THREE.PlaneGeometry(4, 6);
    const viewerMaterial = new THREE.MeshBasicMaterial({
      color: 0x1a1a1a,
      transparent: true,
      opacity: 0.9
    });
    
    const docViewer = new THREE.Mesh(viewerGeometry, viewerMaterial);
    docViewer.position.set(8, 4, -8);
    docViewer.name = 'document-viewer';
    this.scene.add(docViewer);
  }

  private addParticipantAvatars(participants: string[]): void {
    participants.forEach((participantId, index) => {
      const avatar = this.createAvatar(participantId);
      
      // Position avatars in a circle
      const angle = (index / participants.length) * Math.PI * 2;
      const radius = 8;
      avatar.position.set(
        Math.cos(angle) * radius,
        0,
        Math.sin(angle) * radius
      );
      
      this.scene.add(avatar);
    });
  }

  private createAvatar(participantId: string): THREE.Group {
    const avatarGroup = new THREE.Group();
    
    // Simple avatar representation
    const headGeometry = new THREE.SphereGeometry(0.5);
    const headMaterial = new THREE.MeshLambertMaterial({ color: 0xffdbac });
    const head = new THREE.Mesh(headGeometry, headMaterial);
    head.position.y = 1.5;
    
    const bodyGeometry = new THREE.CylinderGeometry(0.3, 0.4, 1.2);
    const bodyMaterial = new THREE.MeshLambertMaterial({ color: 0x4CAF50 });
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    body.position.y = 0.6;
    
    avatarGroup.add(head);
    avatarGroup.add(body);
    
    // Add name label
    const nameLabel = this.createTextSprite(participantId);
    nameLabel.position.y = 2.5;
    avatarGroup.add(nameLabel);
    
    avatarGroup.userData = {
      type: 'avatar',
      participantId: participantId
    };
    
    return avatarGroup;
  }

  private setupSharedInteraction(): void {
    // Setup shared object manipulation
    // In production, this would sync with other participants
    console.log('Setting up shared interaction...');
  }

  /**
   * Create immersive data visualization
   */
  async dataVisualizationVR(dataset: any): Promise<void> {
    console.log('🎯 Creating immersive data visualization...');

    // Clear existing visualization
    this.clearDataVisualization();

    // Create 3D data representation based on dataset type
    if (dataset.type === 'network') {
      await this.createNetworkVisualization(dataset);
    } else if (dataset.type === 'timeseries') {
      await this.createTimeSeriesVisualization(dataset);
    } else if (dataset.type === 'multidimensional') {
      await this.createMultiDimensionalVisualization(dataset);
    }

    // Add interactive controls
    this.addDataVisualizationControls();
  }

  private clearDataVisualization(): void {
    // Remove existing data visualization objects
    const dataObjects = this.scene.children.filter(obj => 
      obj.userData.type === 'data_visualization'
    );
    dataObjects.forEach(obj => this.scene.remove(obj));
  }

  private async createNetworkVisualization(dataset: any): Promise<void> {
    // Create 3D network visualization
    const nodes = dataset.nodes || [];
    const edges = dataset.edges || [];

    // Create nodes
    nodes.forEach((node: any, index: number) => {
      const nodeGeometry = new THREE.SphereGeometry(node.size || 0.5);
      const nodeColor = new THREE.Color().setHSL(node.category * 0.1, 0.7, 0.5);
      const nodeMaterial = new THREE.MeshLambertMaterial({ color: nodeColor });
      const nodeMesh = new THREE.Mesh(nodeGeometry, nodeMaterial);
      
      // Position nodes in 3D space
      const phi = Math.acos(-1 + (2 * index) / nodes.length);
      const theta = Math.sqrt(nodes.length * Math.PI) * phi;
      const radius = 10;
      
      nodeMesh.position.setFromSphericalCoords(radius, phi, theta);
      nodeMesh.userData = {
        type: 'data_visualization',
        subtype: 'network_node',
        data: node
      };
      
      this.scene.add(nodeMesh);
    });

    // Create edges
    edges.forEach((edge: any) => {
      const sourceNode = nodes[edge.source];
      const targetNode = nodes[edge.target];
      
      if (sourceNode && targetNode) {
        const geometry = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3().setFromSphericalCoords(10, sourceNode.phi, sourceNode.theta),
          new THREE.Vector3().setFromSphericalCoords(10, targetNode.phi, targetNode.theta)
        ]);
        
        const material = new THREE.LineBasicMaterial({
          color: 0x888888,
          transparent: true,
          opacity: edge.weight || 0.5
        });
        
        const line = new THREE.Line(geometry, material);
        line.userData = {
          type: 'data_visualization',
          subtype: 'network_edge'
        };
        
        this.scene.add(line);
      }
    });
  }

  private async createTimeSeriesVisualization(dataset: any): Promise<void> {
    // Create 3D time series visualization
    const data = dataset.data || [];
    
    const geometry = new THREE.BufferGeometry();
    const positions = [];
    const colors = [];
    
    data.forEach((point: any, index: number) => {
      positions.push(
        index * 0.1 - (data.length * 0.05), // X: time
        point.value * 5, // Y: value
        0 // Z
      );
      
      // Color based on value
      const color = new THREE.Color().setHSL(point.value * 0.3, 1, 0.5);
      colors.push(color.r, color.g, color.b);
    });
    
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    
    const material = new THREE.LineBasicMaterial({ vertexColors: true });
    const line = new THREE.Line(geometry, material);
    
    line.userData = {
      type: 'data_visualization',
      subtype: 'timeseries'
    };
    
    this.scene.add(line);
  }

  private async createMultiDimensionalVisualization(dataset: any): Promise<void> {
    // Create 3D scatter plot for multidimensional data
    const data = dataset.data || [];
    
    data.forEach((point: any) => {
      const geometry = new THREE.SphereGeometry(0.1);
      const color = new THREE.Color().setHSL(
        point.category * 0.1,
        0.8,
        0.6
      );
      const material = new THREE.MeshBasicMaterial({ color });
      const sphere = new THREE.Mesh(geometry, material);
      
      sphere.position.set(
        point.x || 0,
        point.y || 0,
        point.z || 0
      );
      
      sphere.userData = {
        type: 'data_visualization',
        subtype: 'scatter_point',
        data: point
      };
      
      this.scene.add(sphere);
    });
  }

  private addDataVisualizationControls(): void {
    // Add controls for data visualization
    const controlsPanel = new THREE.Group();
    controlsPanel.position.set(-12, 8, -5);
    
    // Add control buttons
    const controls = [
      { text: 'Rotate View', action: 'rotate_view' },
      { text: 'Filter Data', action: 'filter_data' },
      { text: 'Change Scale', action: 'change_scale' },
      { text: 'Export View', action: 'export_view' }
    ];
    
    controls.forEach((control, index) => {
      const button = this.createControlButton(control.text, control.action);
      button.position.y = -index * 1.2;
      controlsPanel.add(button);
    });
    
    this.scene.add(controlsPanel);
  }

  private createControlButton(text: string, action: string): THREE.Mesh {
    const geometry = new THREE.PlaneGeometry(2, 0.8);
    const material = new THREE.MeshBasicMaterial({ color: 0x4CAF50 });
    const button = new THREE.Mesh(geometry, material);
    
    button.userData = {
      type: 'ui_element',
      action: action
    };
    
    this.addButtonLabel(button, text);
    
    return button;
  }

  /**
   * Start the render loop
   */
  startRendering(): void {
    this.renderer.setAnimationLoop(() => {
      this.render();
    });
  }

  private render(): void {
    // Update animations
    this.updateAnimations();
    
    // Render scene
    this.renderer.render(this.scene, this.camera);
  }

  private updateAnimations(): void {
    // Rotate knowledge graph nodes slowly
    this.nodeObjects.forEach(nodeObj => {
      nodeObj.rotation.y += 0.005;
    });
    
    // Animate connection lines
    this.connectionLines.forEach(line => {
      const material = line.material as THREE.LineBasicMaterial;
      material.opacity = 0.3 + Math.sin(Date.now() * 0.001) * 0.2;
    });
  }

  /**
   * Cleanup resources
   */
  dispose(): void {
    this.renderer.dispose();
    this.scene.clear();
    
    // Dispose geometries and materials
    this.nodeObjects.forEach(obj => {
      obj.traverse(child => {
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose();
          if (Array.isArray(child.material)) {
            child.material.forEach(material => material.dispose());
          } else {
            child.material.dispose();
          }
        }
      });
    });
  }
}

export default ImmersiveResearchEnvironment;
export type { KnowledgeGraph, ResearchNode, VRSession };
