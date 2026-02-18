<template>
  <div class="live-view">
    <!-- Map Editor Panel (Dev Only) -->
    <MapEditorPanel v-if="isDevMode" :visible="isDevMode" @update:colors="onColorsChange"
      @update:mapConfig="onMapConfigChange" @update:vehicleConfig="onVehicleConfigChange" @add:label="onAddLabel"
      @remove:label="onRemoveLabel" @update:labels="onLabelsUpdate" @reset="onEditorReset" ref="editorRef" />

    <!-- Main Map Area (Left/Center) -->
    <div class="map-layer">
      <div class="map-container-3d" ref="mapContainer3D"></div>

      <!-- Map Overlay Controls (Minimal) -->
      <div class="map-overlay-header">
        <div class="map-title-badge">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="var(--color-primary)" stroke-width="2">
            <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21" />
            <line x1="9" x2="9" y1="3" y2="18" />
            <line x1="15" x2="15" y1="6" y2="21" />
          </svg>
          <span>실시간 3D 맵</span>
        </div>
      </div>
    </div>

    <!-- Resizable Right Sidebar -->
    <aside class="monitoring-sidebar" :style="{ width: sidebarWidth + 'px' }">
      <div class="resize-handle" @mousedown="startResize"></div>
      <div class="sidebar-header">
        <h2>Monitoring</h2>
        <span class="live-indicator">LIVE</span>
      </div>

      <div class="sidebar-content">
        <!-- 1. Camera Feed Section -->
        <div class="sidebar-section camera-section">
          <div class="section-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2">
              <path d="M23 7l-7 5 7 5V7z" />
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
            </svg>
            Camera Feed
          </div>
          <div class="camera-container">
            <!-- MediaMTX WebRTC Live Stream -->
            <!-- Add pointer-events-none when resizing to prevent iframe from capturing mouse events -->
            <iframe v-if="isStreamConnected" :src="streamUrl" class="video-stream"
              :class="{ 'pointer-events-none': isResizing }" frameborder="0" allowfullscreen @load="onStreamLoad"
              @error="onStreamError"></iframe>

            <!-- Connection Placeholder -->
            <div class="video-placeholder" v-else>
              <div class="placeholder-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="1.5">
                  <path d="M15 10l5 5-5 5" />
                  <path d="M4 4v7a4 4 0 0 0 4 4h12" />
                </svg>
              </div>
              <span>Signal Lost</span>
              <button class="btn-retry-text" @click="connectStream">Reconnect</button>
            </div>

            <!-- Overlay Info -->
            <div class="camera-overlay">
              <span class="cam-id">CAM:01</span>
              <span class="timestamp-small">{{ currentTime }}</span>
            </div>
          </div>

          <div class="connection-status">
            <span class="status-dot-sm" :class="isStreamConnected ? 'online' : 'offline'"></span>
            {{ isStreamConnected ? 'Online' : 'Offline' }}
          </div>
        </div>

        <!-- 2. Vehicle Status Section -->
        <div class="sidebar-section status-section">
          <div class="section-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
            Vehicle Status
          </div>

          <div class="status-card">
            <div class="status-row">
              <span class="label">Connection</span>
              <span class="value-badge" :class="isVehicleConnected ? 'connected' : 'disconnected'">
                {{ isVehicleConnected ? 'Connected' : 'Disconnected' }}
              </span>
            </div>
            <div class="status-row">
              <span class="label">Mode</span>
              <span class="value-text">{{ vehicleStatus.mode }}</span>
            </div>

            <div class="status-grid-compact">
              <div class="stat-item">
                <span class="stat-val">{{ vehicleStatus.speed }} <small>km/h</small></span>
                <span class="stat-label">Speed</span>
              </div>
              <div class="stat-item">
                <span class="stat-val" :class="{ 'text-red': vehicleStatus.battery < 20 }">
                  {{ vehicleStatus.battery }} <small>%</small>
                </span>
                <span class="stat-label">Battery</span>
              </div>
              <div class="stat-item">
                <span class="stat-val">{{ vehicleStatus.distanceToTarget }} <small>m</small></span>
                <span class="stat-label">Dist</span>
              </div>
              <div class="stat-item">
                <span class="stat-val">{{ vehicleStatus.eta }} <small>s</small></span>
                <span class="stat-label">ETA</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Map Controls Section -->
        <div class="sidebar-section control-section">
          <div class="section-title">Map Controls</div>
          <div class="control-buttons">
            <button class="ctrl-btn" @click="zoomIn3D" title="Zoom In">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
                <line x1="11" y1="8" x2="11" y2="14" />
                <line x1="8" y1="11" x2="14" y2="11" />
              </svg>
            </button>
            <button class="ctrl-btn" @click="zoomOut3D" title="Zoom Out">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
                <line x1="8" y1="11" x2="14" y2="11" />
              </svg>
            </button>
            <button class="ctrl-btn" @click="resetView3D" title="Reset View">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2">
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                <path d="M3 3v5h5" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Dev Mode Debug Controls (npm run dev에서만 표시) -->
        <div v-if="isDevMode" class="debug-panel">
          <div class="debug-header">🔧 Debug Controls (Dev Only)</div>
          <div class="debug-info">
            <span>RC: ({{ vehicle.x.toFixed(2) }}, {{ vehicle.y.toFixed(2) }})</span>
            <span>Offset: ({{ debugOffset.x.toFixed(1) }}, {{ debugOffset.y.toFixed(1) }})</span>
          </div>
          <div class="debug-buttons">
            <button class="debug-btn" @click="debugOffset.y += 1">↑</button>
            <div class="debug-row">
              <button class="debug-btn" @click="debugOffset.x -= 1">←</button>
              <button class="debug-btn reset" @click="debugOffset.x = 0; debugOffset.y = 0">⟲</button>
              <button class="debug-btn" @click="debugOffset.x += 1">→</button>
            </div>
            <button class="debug-btn" @click="debugOffset.y -= 1">↓</button>
          </div>
        </div>

      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { startWaybillScan, startSorting, completeSorting, fetchWaybills, fetchVehiclePosition, fetchRcState, fetchMapData, fetchSensorStatus, getMockMode } from '../api'
import { useTheme } from '../composables/useTheme'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js'
import MapEditorPanel from '../components/MapEditorPanel.vue'

// Theme
const { theme, isDark } = useTheme()

// Config
const MAP_CONFIG = {
  resolution: 0.05,
  origin: [-3.81, -20.7, 0],
  wallHeight: 1.5,
  occupiedThresh: 0.65
}

// ========== 차량 설정 (여기서 모든 값을 조정하세요!) ==========
const VEHICLE_CONFIG = {
  // 시작 위치 보정 (미터)
  offsetX: 10.6,
  offsetY: 35.5,

  // 회전 보정 (도, + = 시계방향)
  rotation: 90,

  // 이동 스케일 (1.0 = RC 1m당 맵 1m)
  moveScale: 6,

  // 차량 물리적 크기 (배율)
  size: 1.0
}
// =============================================================

// State
const currentTime = ref('')
const isScanning = ref(false)
const isLoading = ref(true)
const isMockMode = getMockMode()
const isDevMode = import.meta.env.DEV  // npm run dev에서만 true

// Stream
const isStreamConnected = ref(false)
const streamError = ref('')
const streamUrl = ref('/stream/cam1/')

// Draggable Modal State
// Draggable Modal State (Removed)

// 3D Map
const mapContainer3D = ref(null)
let scene, camera, renderer, controls, vehicleMesh, mapMesh, floorMesh, worldGroup, pathMesh
let css2dRenderer = null
const labelObjects = ref([])  // CSS2DObject 배열
const editorRef = ref(null)

// Editor-driven reactive configs
const editorColors = ref(null)
const editorMapConfig = ref(null)
const editorVehicleConfig = ref(null)
let animationFrameId = null

const vehicle = ref({ x: 0, y: 0, angle: 0 })
const vehiclePath = ref([])  // 차량 경로 데이터
const vehicleStatus = ref({ mode: 'IDLE', speed: 0, battery: 100, distanceToTarget: 0, eta: 0 })
const isVehicleConnected = ref(false)
const isVideoVisible = ref(true)
const debugOffset = ref({ x: 0, y: 0 })  // 디버그용 수동 오프셋
const lastValidAngle = ref(0) // 마지막으로 유효한 회전각 (노이즈 필터링용)
let timeInterval = null

// Sidebar Resize State
const sidebarWidth = ref(380)
const isResizing = ref(false)

// Functions
const connectStream = () => {
  streamError.value = ''
  isStreamConnected.value = true
}

const onStreamLoad = () => {
  streamError.value = ''
  console.log('Stream Connected')
}

const onStreamError = () => {
  isStreamConnected.value = false
  streamError.value = 'Stream Failed'
}

const updateTime = () => {
  currentTime.value = new Date().toLocaleTimeString('ko-KR', { hour12: false })
}

const loadVehiclePosition = async () => {
  try {
    // 새로운 RC State API 사용 (MQTT 로그에서 읽기)
    const res = await fetchRcState()
    if (res.data?.success && res.data?.data) {
      const data = res.data.data
      // RC 좌표는 미터 단위 - 3D 맵에서 그대로 사용
      // 1도 이하 변화 무시 로직
      const rawTheta = data.theta || 0
      if (Math.abs(rawTheta - lastValidAngle.value) > 1.0) {
        lastValidAngle.value = rawTheta
      }

      vehicle.value = {
        x: data.x || 0,
        y: data.y || 0,
        angle: lastValidAngle.value  // 필터링된 각도 사용
      }
      vehicleStatus.value = {
        mode: data.state || 'IDLE',
        speed: Math.round(Math.abs(data.speed || 0) * 3.6 * 100) / 100,  // m/s -> km/h
        battery: 100,  // RC에서 배터리 정보 없음, 기본값 사용
        distanceToTarget: Math.round((data.remain_dist || 0) * 100) / 100,
        eta: Math.round(data.remain_time || 0)
      }

      // connected 필드로 연결 상태 판단
      isVehicleConnected.value = res.data.connected || false

      // 경로 데이터 파싱
      if (data.path) {
        try {
          const parsedPath = typeof data.path === 'string' ? JSON.parse(data.path) : data.path
          vehiclePath.value = parsedPath || []
        } catch (e) {
          vehiclePath.value = []
        }
      } else {
        vehiclePath.value = []
      }
    } else {
      isVehicleConnected.value = false
      vehiclePath.value = []
    }
  } catch (err) {
    console.error('RC State Error:', err)
    isVehicleConnected.value = false
    vehiclePath.value = []
  }
}

// 3D Setup
const init3DMap = () => {
  if (!mapContainer3D.value) return
  const container = mapContainer3D.value
  const width = container.clientWidth
  const height = container.clientHeight

  scene = new THREE.Scene()
  // Adjust background color to be slightly darker/technical
  const sceneBgColor = isDark() ? 0x1e1e2e : 0xdbeafe
  scene.background = new THREE.Color(sceneBgColor)

  // World Group for all map elements
  worldGroup = new THREE.Group()
  // Rotate 90 degrees more to the right (Clockwise) relative to previous state (-PI/2)
  // Previous: -Math.PI / 2
  // New: -Math.PI
  worldGroup.rotation.y = -Math.PI
  scene.add(worldGroup)

  // Orthographic Camera for 2D Plan View
  const aspect = width / height
  const frustumSize = 100 // Increased from 60 to 100 for smaller initial zoom (zoomed out)
  camera = new THREE.OrthographicCamera(
    frustumSize * aspect / -2,
    frustumSize * aspect / 2,
    frustumSize / 2,
    frustumSize / -2,
    0.1,
    2000
  )

  // Top-down view (looking strictly from Y axis)
  camera.position.set(0, 100, 0)
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  container.appendChild(renderer.domElement)

  // CSS2D Renderer for text labels
  css2dRenderer = new CSS2DRenderer()
  css2dRenderer.setSize(width, height)
  css2dRenderer.domElement.style.position = 'absolute'
  css2dRenderer.domElement.style.top = '0'
  css2dRenderer.domElement.style.left = '0'
  css2dRenderer.domElement.style.pointerEvents = 'none'
  container.appendChild(css2dRenderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableRotate = false // Disable rotation for strict 2D view
  controls.enableZoom = true
  controls.enablePan = true
  controls.screenSpacePanning = true // Pan up/down instead of forward/backward
  controls.dampingFactor = 0.05
  controls.enableDamping = true

  addLights()
  createSlamMap()
  createVehicle()
  restoreEditorLabels()
  animate()
  window.addEventListener('resize', handleResize)
}

const addLights = () => {
  scene.add(new THREE.AmbientLight(0xffffff, 0.6))
  const mainLight = new THREE.DirectionalLight(0xffffff, 0.7)
  mainLight.position.set(20, 100, 30) // Light from top
  mainLight.castShadow = true
  mainLight.shadow.mapSize.set(2048, 2048)
  // Shadow camera frustum needs to cover the map area
  const d = 50
  mainLight.shadow.camera.left = -d
  mainLight.shadow.camera.right = d
  mainLight.shadow.camera.top = d
  mainLight.shadow.camera.bottom = -d
  scene.add(mainLight)
}

const createSlamMap = () => {
  const loader = new THREE.TextureLoader()
  loader.load('/testMap12.png', (texture) => {
    const image = texture.image
    const width = 1000 // Approximate
    const height = 1000

    const canvas = document.createElement('canvas')
    canvas.width = image.width
    canvas.height = image.height
    const ctx = canvas.getContext('2d')
    ctx.drawImage(image, 0, 0)
    const imgData = ctx.getImageData(0, 0, image.width, image.height)
    const data = imgData.data

    const wallPositions = []
    const res = MAP_CONFIG.resolution
    const originX = MAP_CONFIG.origin[0]
    const originY = MAP_CONFIG.origin[1]

    // Floor
    const floorWidth = image.width * res
    const floorHeight = image.height * res
    const floorCenterX = originX + (image.width * res) / 2
    const floorCenterY = originY + (image.height * res) / 2

    const floorColor = isDark() ? 0x2a2a3d : 0xc8d1dc
    floorMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(floorWidth, floorHeight),
      new THREE.MeshStandardMaterial({ color: floorColor, roughness: 0.9 })
    )
    floorMesh.rotation.x = -Math.PI / 2
    // floorMesh.rotation.z = -Math.PI / 2 // Removed individual rotation
    floorMesh.position.set(floorCenterX, -0.01, -floorCenterY)
    floorMesh.receiveShadow = true
    worldGroup.add(floorMesh) // Add to worldGroup

    if (controls) {
      // Calculate world position for camera target
      // The floor center is (floorCenterX, 0, -floorCenterY) in LOCAL worldGroup space.
      // worldGroup rotation is -Math.PI (180 degrees around Y axis)
      // After 180deg Y rotation: x' = -x, z' = -z

      const targetLocal = new THREE.Vector3(floorCenterX, 0, -floorCenterY)
      const targetWorld = targetLocal.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), -Math.PI)

      controls.target.copy(targetWorld)
      controls.update()

      // Position camera directly above the target for centered top-down view
      camera.position.set(targetWorld.x, 100, targetWorld.z)
      camera.lookAt(targetWorld)
    }

    // Walls
    for (let row = 0; row < image.height; row++) {
      for (let col = 0; col < image.width; col++) {
        const index = (row * image.width + col) * 4
        if (data[index] < 100) {
          const worldX = originX + col * res
          const worldY = originY + (image.height - 1 - row) * res
          wallPositions.push({ x: worldX, z: -worldY })
        }
      }
    }

    const wallColor = isDark() ? 0x505060 : 0x64748b
    const wallGeo = new THREE.BoxGeometry(res, MAP_CONFIG.wallHeight, res)
    const wallMat = new THREE.MeshStandardMaterial({ color: wallColor, roughness: 0.7 })
    mapMesh = new THREE.InstancedMesh(wallGeo, wallMat, wallPositions.length)
    mapMesh.castShadow = true
    mapMesh.receiveShadow = true

    const dummy = new THREE.Object3D()
    for (let i = 0; i < wallPositions.length; i++) {
      const pos = wallPositions[i]
      dummy.position.set(pos.x, MAP_CONFIG.wallHeight / 2, pos.z)
      dummy.updateMatrix()
      mapMesh.setMatrixAt(i, dummy.matrix)
    }

    // mapMesh.rotation.y = -Math.PI / 2 // Removed individual rotation

    mapMesh.instanceMatrix.needsUpdate = true
    worldGroup.add(mapMesh) // Add to worldGroup
  })
}

const createVehicle = () => {
  vehicleMesh = new THREE.Group()

  // VEHICLE_CONFIG.size로 차량 크기 조정
  const scale = VEHICLE_CONFIG.size

  // 차량 본체 (1.8m x 0.9m x 2.7m - 실제 차량 크기와 유사)
  const body = new THREE.Mesh(
    new THREE.BoxGeometry(1.8 * scale, 0.9 * scale, 2.7 * scale),
    new THREE.MeshStandardMaterial({ color: 0x10b981, roughness: 0.4, metalness: 0.4 })
  )
  body.position.y = 0.6 * scale
  body.castShadow = true
  vehicleMesh.add(body)

  // 바퀴
  const wheelGeo = new THREE.CylinderGeometry(0.3 * scale, 0.3 * scale, 0.3 * scale, 12)
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x1f2937 })
  const wheelPos = [[-0.7, -1.0], [0.7, -1.0], [-0.7, 1.0], [0.7, 1.0]]
  wheelPos.forEach(([x, z]) => {
    const wheel = new THREE.Mesh(wheelGeo, wheelMat)
    wheel.rotation.z = Math.PI / 2
    wheel.position.set(x * scale, 0.3 * scale, z * scale)
    vehicleMesh.add(wheel)
  })

  // 전방 표시 (노란색 헤드라이트)
  const light = new THREE.Mesh(
    new THREE.BoxGeometry(1.2 * scale, 0.15 * scale, 0.15 * scale),
    new THREE.MeshBasicMaterial({ color: 0xffff00 })
  )
  light.position.set(0, 0.8 * scale, -1.4 * scale)
  vehicleMesh.add(light)

  worldGroup.add(vehicleMesh)
}

const animate = () => {
  animationFrameId = requestAnimationFrame(animate)
  controls?.update()

  // Apply editor-driven vehicle config overrides
  const vc = editorVehicleConfig.value || VEHICLE_CONFIG
  if (vehicleMesh) {
    // 차량 항상 표시 (연결 상태와 무관하게 위치 확인용)
    vehicleMesh.visible = true

    // VEHICLE_CONFIG 사용 + 디버그 오프셋 적용 (에디터 오버라이드 적용)
    const { offsetX, offsetY, rotation, moveScale } = vc

    // IDLE/READY_TO_LOAD 상태일 때는 기본 보정값 위치에 고정
    const isIdle = vehicleStatus.value.mode === 'IDLE' || vehicleStatus.value.mode === 'READY_TO_LOAD'

    let mapX, mapZ
    if (isIdle) {
      // IDLE 상태: 보정값 위치에 고정
      mapX = offsetX + debugOffset.value.x
      mapZ = -(offsetY + debugOffset.value.y)
    } else {
      // 이동 중: RC 좌표 반영
      const rcX = vehicle.value.x + debugOffset.value.x
      const rcY = vehicle.value.y + debugOffset.value.y
      mapX = (rcX * moveScale) + offsetX
      mapZ = -((rcY * moveScale) + offsetY)
    }

    vehicleMesh.position.set(mapX, 0.5, mapZ)
    vehicleMesh.position.set(mapX, 0.5, mapZ)
    // VEHICLE_CONFIG.rotation + Telemetry Angle (filtered)
    vehicleMesh.rotation.y = Math.PI + ((rotation + vehicle.value.angle) * Math.PI / 180)

    // 연결 상태에 따라 색상 변경
    const bodyMesh = vehicleMesh.children[0]
    if (bodyMesh && bodyMesh.material) {
      bodyMesh.material.color.setHex(isVehicleConnected.value ? 0x10b981 : 0x6b7280)
    }

    // 경로 라인 렌더링 (굵은 튜브로 표시)
    if (vehiclePath.value && vehiclePath.value.length > 1) {
      // 기존 경로 제거
      if (pathMesh) {
        worldGroup.remove(pathMesh)
        pathMesh.geometry.dispose()
        pathMesh.material.dispose()
      }

      // 경로 포인트를 3D 좌표로 변환
      const points = vehiclePath.value.map(p => {
        const px = (p.x * moveScale) + offsetX + debugOffset.value.x
        const pz = -((p.y * moveScale) + offsetY + debugOffset.value.y)
        return new THREE.Vector3(px, 0.3, pz)
      })

      // TubeGeometry로 굵은 경로 생성
      const curve = new THREE.CatmullRomCurve3(points)
      const geometry = new THREE.TubeGeometry(curve, points.length * 2, 0.3, 8, false)
      const material = new THREE.MeshBasicMaterial({
        color: 0x3b82f6,  // 파란색 경로
        transparent: true,
        opacity: 0.8
      })
      pathMesh = new THREE.Mesh(geometry, material)
      worldGroup.add(pathMesh)
    } else if (pathMesh) {
      // 경로가 없으면 제거
      worldGroup.remove(pathMesh)
      pathMesh.geometry.dispose()
      pathMesh.material.dispose()
      pathMesh = null
    }
  }
  renderer?.render(scene, camera)
  css2dRenderer?.render(scene, camera)
}

const handleResize = () => {
  if (!mapContainer3D.value || !camera || !renderer) return
  const w = mapContainer3D.value.clientWidth
  const h = mapContainer3D.value.clientHeight

  // Orthographic camera resize
  const aspect = w / h
  const frustumSize = 60
  camera.left = -frustumSize * aspect / 2
  camera.right = frustumSize * aspect / 2
  camera.top = frustumSize / 2
  camera.bottom = -frustumSize / 2

  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
  css2dRenderer?.setSize(w, h)
}

const zoomIn3D = () => {
  if (camera) {
    camera.zoom = Math.min(camera.zoom + 0.1, 5) // Max zoom limit
    camera.updateProjectionMatrix()
    renderer?.render(scene, camera)
  }
}

const zoomOut3D = () => {
  if (camera) {
    camera.zoom = Math.max(camera.zoom - 0.1, 0.1) // Min zoom limit
    camera.updateProjectionMatrix()
    renderer?.render(scene, camera)
  }
}

const resetView3D = () => {
  if (camera && controls) {
    // Reset Zoom
    camera.zoom = 1
    camera.updateProjectionMatrix()

    // Reset Position (matches the one in animate/controls logic)
    // We need to re-center based on map if possible, but hardcoded valid position is fine
    // Previously: camera.position.set(5, 100, 5) -> changed Y to 100
    // And target needs to be reset.
    // However, since we dynamically set target based on floor center, we should maybe re-calculate that?
    // Or just reset to a reasonable default.

    // Actually best to re-focus on the calculated target if available.
    // But since `target` is set inside `createSlamMap` heavily, let's just reset zoom for now
    // and maybe put camera back to 0, 100, 0 local?

    camera.position.set(0, 100, 0)
    controls.reset() // This might reset target to 0,0,0

    // Re-apply target if we knew it... 
    // Let's just rely on OrbitControls to handle rotation limit etc.
    renderer?.render(scene, camera)
  }
}

// Sidebar Resize Functions
const startResize = () => {
  isResizing.value = true
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const onResize = (e) => {
  if (!isResizing.value) return
  const newWidth = window.innerWidth - e.clientX
  if (newWidth >= 280 && newWidth <= 600) {
    sidebarWidth.value = newWidth
    nextTick(() => handleResize())
  }
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  // Final resize update
  nextTick(() => handleResize())
}

// ========== Map Editor Event Handlers ==========
const onColorsChange = (colors) => {
  editorColors.value = colors
  if (scene) {
    scene.background = new THREE.Color(colors.background)
  }
  if (floorMesh) {
    floorMesh.material.color.set(colors.floor)
  }
  if (mapMesh) {
    mapMesh.material.color.set(colors.wall)
  }
  if (vehicleMesh) {
    const bodyMesh = vehicleMesh.children[0]
    if (bodyMesh && bodyMesh.material) {
      bodyMesh.material.color.set(colors.vehicle)
    }
  }
}

const onMapConfigChange = (config) => {
  editorMapConfig.value = config
  // Map config changes require rebuild
  MAP_CONFIG.resolution = config.resolution
  MAP_CONFIG.origin[0] = config.originX
  MAP_CONFIG.origin[1] = config.originY
  MAP_CONFIG.wallHeight = config.wallHeight
  rebuildMap()
}

const onVehicleConfigChange = (config) => {
  editorVehicleConfig.value = config
  // Vehicle config is read in animate() loop, no rebuild needed
}

const onAddLabel = (label) => {
  addLabelToScene(label)
}

const onRemoveLabel = (idx) => {
  if (labelObjects.value[idx]) {
    worldGroup.remove(labelObjects.value[idx])
    labelObjects.value.splice(idx, 1)
  }
}

const onLabelsUpdate = (labels) => {
  // Remove all existing labels
  labelObjects.value.forEach(obj => worldGroup.remove(obj))
  labelObjects.value = []
  // Re-add all
  labels.forEach(label => addLabelToScene(label))
}

const onEditorReset = () => {
  // Remove all labels
  labelObjects.value.forEach(obj => worldGroup.remove(obj))
  labelObjects.value = []
  editorColors.value = null
  editorMapConfig.value = null
  editorVehicleConfig.value = null
  // Rebuild with defaults
  rebuildMap()
}

const addLabelToScene = (label) => {
  if (!worldGroup) return
  const div = document.createElement('div')
  div.textContent = label.text
  div.style.color = label.color || '#ffffff'
  div.style.fontSize = (label.fontSize || 16) + 'px'
  div.style.fontWeight = '700'
  div.style.textShadow = '0 0 6px rgba(0,0,0,0.8), 0 0 12px rgba(0,0,0,0.5)'
  div.style.pointerEvents = 'none'
  div.style.whiteSpace = 'nowrap'
  div.style.userSelect = 'none'

  const labelObj = new CSS2DObject(div)
  // Position in world coords (x = label.x, z = -label.y, y slightly above floor)
  labelObj.position.set(label.x, 1.0, -label.y)
  worldGroup.add(labelObj)
  labelObjects.value.push(labelObj)
}

const restoreEditorLabels = () => {
  if (!editorRef.value) return
  const labels = editorRef.value.labels
  if (labels && labels.length > 0) {
    labels.forEach(label => addLabelToScene(label))
  }
}

const rebuildMap = () => {
  // Remove old map and floor
  if (mapMesh) {
    worldGroup.remove(mapMesh)
    mapMesh.geometry.dispose()
    mapMesh.material.dispose()
    mapMesh = null
  }
  if (floorMesh) {
    worldGroup.remove(floorMesh)
    floorMesh.geometry.dispose()
    floorMesh.material.dispose()
    floorMesh = null
  }
  createSlamMap()
}

onMounted(async () => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  await loadVehiclePosition()
  await nextTick()
  init3DMap()
  if (!isMockMode) {
    setInterval(loadVehiclePosition, 1000)
  }
  connectStream()
})

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval)
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
  if (renderer) renderer.dispose()
  if (css2dRenderer) {
    css2dRenderer.domElement.remove()
  }
})

watch(theme, () => {
  if (!scene) return
  const isDarkMode = isDark()
  scene.background = new THREE.Color(isDarkMode ? 0x1a1a2e : 0xe2e8f0)
  if (floorMesh) floorMesh.material.color.setHex(isDarkMode ? 0x2a2a3d : 0xc8d1dc)
  if (mapMesh) mapMesh.material.color.setHex(isDarkMode ? 0x505060 : 0x64748b)
})
</script>

<style scoped>
.live-view {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--bg-primary);
}

/* Map Layer (Background) */
.map-layer {
  position: absolute;
  inset: 0;
  z-index: 1;
}

.map-panel {
  width: 100%;
  height: 100%;
  position: relative;
  background: var(--bg-secondary);
}

.map-container-3d {
  width: 100%;
  height: 100%;
}

/* Map specific controls floating on top left/right */
.map-controls {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 12px;
}

.map-title-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--glass-panel);
  backdrop-filter: blur(8px);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  font-weight: 700;
  font-size: 14px;
  color: var(--text-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.divider {
  color: var(--glass-border);
  font-weight: 300;
}

.vehicle-status-text {
  font-size: 12px;
  font-weight: 600;
}

.vehicle-status-text.connected {
  color: var(--color-success);
}

.vehicle-status-text.disconnected {
  color: var(--text-muted);
}

.map-btn-group {
  display: flex;
  gap: 4px;
  background: var(--glass-panel);
  padding: 4px;
  border-radius: 10px;
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(8px);
}

.map-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.map-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

/* Layout */
.live-view {
  display: flex;
  height: calc(100vh - 64px);
  background: var(--bg-primary);
  overflow: hidden;
  position: relative;
}

.map-layer {
  flex: 1;
  position: relative;
  background: #e2e8f0;
}

.dark-mode .map-layer {
  background: #1e1e2e;
}

.map-container-3d {
  width: 100%;
  height: 100%;
}

/* Sidebar */
.monitoring-sidebar {
  /* width: 320px; Removed for dynamic width */
  min-width: 280px;
  max-width: 600px;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 10;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.05);
  position: relative;
}

.resize-handle {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 12px;
  /* Increased hit area */
  transform: translateX(-50%);
  /* Center on the border */
  cursor: col-resize;
  z-index: 50;
  /* Higher z-index */
  background: transparent;
  transition: all 0.2s;
}

.resize-handle:hover,
.resize-handle:active,
.monitoring-sidebar.resizing .resize-handle {
  background: rgba(16, 185, 129, 0.5);
  /* Visible color on interaction */
}

/* Helper class */
.pointer-events-none {
  pointer-events: none;
}

.sidebar-header {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}

.sidebar-header h2 {
  font-size: 14px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.live-indicator {
  background: #ef4444;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 800;
  animation: pulse 2s infinite;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Sections */
.sidebar-section {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  background: rgba(0, 0, 0, 0.02);
  border-bottom: 1px solid var(--border-color);
}

/* Camera */
.camera-container {
  width: 100%;
  aspect-ratio: 4/3;
  background: #000;
  position: relative;
}

.video-stream {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #52525b;
  gap: 8px;
}

.camera-overlay {
  position: absolute;
  top: 8px;
  left: 8px;
  display: flex;
  gap: 6px;
  pointer-events: none;
}

.cam-id {
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}

.timestamp-small {
  background: rgba(0, 0, 0, 0.6);
  color: #10b981;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-family: monospace;
}

.connection-status {
  padding: 8px 12px;
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 6px;
  border-top: 1px solid var(--border-color);
}

.status-dot-sm {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot-sm.online {
  background: #10b981;
  box-shadow: 0 0 4px #10b981;
}

.status-dot-sm.offline {
  background: #52525b;
}

/* Status Card */
.status-card {
  padding: 12px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 12px;
  align-items: center;
}

.status-row .label {
  color: var(--text-muted);
}

.value-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.value-badge.connected {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.value-badge.disconnected {
  background: rgba(244, 63, 94, 0.1);
  color: #f43f5e;
}

.value-text {
  font-weight: 600;
  color: var(--text-primary);
}

.status-grid-compact {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.stat-item {
  background: var(--bg-tertiary);
  padding: 8px;
  border-radius: 6px;
  text-align: center;
}

.stat-val {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-val.text-red {
  color: #f43f5e;
}

.stat-val small {
  font-size: 10px;
  color: var(--text-muted);
}

.stat-label {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
  display: block;
}

/* Map Controls in Sidebar */
.control-buttons {
  padding: 12px;
  display: flex;
  justify-content: space-around;
  gap: 8px;
}

.ctrl-btn {
  flex: 1;
  height: 36px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.ctrl-btn:hover {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

/* Map Overlay */
.map-overlay-header {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 5;
  pointer-events: none;
}

.map-title-badge {
  background: var(--glass-panel);
  backdrop-filter: blur(8px);
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid var(--glass-border);
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: var(--text-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  pointer-events: auto;
}

.placeholder-icon {
  margin-bottom: 8px;
  opacity: 0.5;
}

.btn-retry-text {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.btn-retry-text:hover {
  border-color: var(--text-primary);
  color: var(--text-primary);
}

@keyframes pulse {
  0% {
    opacity: 1;
  }

  50% {
    opacity: 0.6;
  }

  100% {
    opacity: 1;
  }
}

/* Debug Panel (Dev Mode Only) */
.debug-panel {
  background: rgba(255, 100, 100, 0.1);
  border: 2px dashed #ff6b6b;
  border-radius: 8px;
  padding: 12px;
  margin-top: 16px;
}

.debug-header {
  font-weight: bold;
  color: #ff6b6b;
  margin-bottom: 8px;
  font-size: 14px;
}

.debug-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  font-family: monospace;
  margin-bottom: 12px;
  color: var(--text-secondary);
}

.debug-buttons {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.debug-row {
  display: flex;
  gap: 4px;
}

.debug-btn {
  width: 40px;
  height: 40px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  border-radius: 6px;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.15s;
}

.debug-btn:hover {
  background: var(--accent-color);
  color: white;
}

.debug-btn.reset {
  font-size: 16px;
}
</style>