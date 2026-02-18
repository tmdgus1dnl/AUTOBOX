<template>
  <div class="map-editor-overlay" v-if="visible">
    <!-- Toggle Button (always visible) -->
    <button class="editor-toggle-btn" @click="expanded = !expanded" :title="expanded ? 'Close Editor' : 'Open Map Editor'">
      <span v-if="expanded">✕</span>
      <span v-else>🗺️</span>
    </button>

    <!-- Editor Panel -->
    <div class="editor-panel" v-show="expanded" ref="panelRef"
      :style="{ transform: `translate(${panelPos.x}px, ${panelPos.y}px)` }">

      <!-- Drag Handle -->
      <div class="editor-drag-handle" @mousedown="startDrag">
        <span class="drag-icon">⠿</span>
        <span class="editor-title">🗺️ Map Editor</span>
        <span class="dev-badge">DEV</span>
      </div>

      <!-- Tab Navigation -->
      <div class="editor-tabs">
        <button v-for="tab in tabs" :key="tab.id" class="tab-btn" :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id">
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <div class="editor-body">

        <!-- Colors Tab -->
        <div v-if="activeTab === 'colors'" class="tab-content">
          <div class="field-group">
            <label>벽 색상 (Wall)</label>
            <div class="color-row">
              <input type="color" :value="colors.wall" @input="e => updateColor('wall', e.target.value)" />
              <span class="color-hex">{{ colors.wall }}</span>
            </div>
          </div>
          <div class="field-group">
            <label>바닥 색상 (Floor)</label>
            <div class="color-row">
              <input type="color" :value="colors.floor" @input="e => updateColor('floor', e.target.value)" />
              <span class="color-hex">{{ colors.floor }}</span>
            </div>
          </div>
          <div class="field-group">
            <label>배경 색상 (Background)</label>
            <div class="color-row">
              <input type="color" :value="colors.background" @input="e => updateColor('background', e.target.value)" />
              <span class="color-hex">{{ colors.background }}</span>
            </div>
          </div>
          <div class="field-group">
            <label>차량 색상 (Vehicle)</label>
            <div class="color-row">
              <input type="color" :value="colors.vehicle" @input="e => updateColor('vehicle', e.target.value)" />
              <span class="color-hex">{{ colors.vehicle }}</span>
            </div>
          </div>
          <div class="field-group">
            <label>경로 색상 (Path)</label>
            <div class="color-row">
              <input type="color" :value="colors.path" @input="e => updateColor('path', e.target.value)" />
              <span class="color-hex">{{ colors.path }}</span>
            </div>
          </div>
        </div>

        <!-- Labels Tab -->
        <div v-if="activeTab === 'labels'" class="tab-content">
          <div class="add-label-form">
            <input v-model="newLabel.text" placeholder="라벨 텍스트" class="editor-input" />
            <div class="label-pos-row">
              <input v-model.number="newLabel.x" type="number" step="0.5" placeholder="X" class="editor-input small" />
              <input v-model.number="newLabel.y" type="number" step="0.5" placeholder="Y" class="editor-input small" />
            </div>
            <div class="label-style-row">
              <input type="color" v-model="newLabel.color" class="color-input-sm" />
              <select v-model="newLabel.fontSize" class="editor-select">
                <option value="12">12px</option>
                <option value="14">14px</option>
                <option value="16">16px</option>
                <option value="20">20px</option>
                <option value="24">24px</option>
                <option value="32">32px</option>
              </select>
              <button class="btn-add" @click="addLabel">+ 추가</button>
            </div>
          </div>

          <div class="label-list">
            <div v-for="(label, idx) in labels" :key="idx" class="label-item">
              <span class="label-preview" :style="{ color: label.color, fontSize: label.fontSize + 'px' }">
                {{ label.text }}
              </span>
              <span class="label-coords">({{ label.x }}, {{ label.y }})</span>
              <div class="label-actions">
                <button class="btn-icon" @click="editLabel(idx)" title="편집">✏️</button>
                <button class="btn-icon danger" @click="removeLabel(idx)" title="삭제">🗑️</button>
              </div>
            </div>
            <div v-if="labels.length === 0" class="empty-msg">라벨이 없습니다. 위에서 추가하세요.</div>
          </div>
        </div>

        <!-- Config Tab -->
        <div v-if="activeTab === 'config'" class="tab-content">
          <div class="config-section-title">📐 Map Config</div>
          <div class="field-group">
            <label>Resolution <span class="val">{{ mapConfig.resolution }}</span></label>
            <input type="range" :value="mapConfig.resolution" min="0.01" max="0.2" step="0.005"
              @input="e => updateMapConfig('resolution', parseFloat(e.target.value))" />
          </div>
          <div class="field-group">
            <label>Origin X <span class="val">{{ mapConfig.originX }}</span></label>
            <input type="range" :value="mapConfig.originX" min="-50" max="50" step="0.1"
              @input="e => updateMapConfig('originX', parseFloat(e.target.value))" />
          </div>
          <div class="field-group">
            <label>Origin Y <span class="val">{{ mapConfig.originY }}</span></label>
            <input type="range" :value="mapConfig.originY" min="-50" max="50" step="0.1"
              @input="e => updateMapConfig('originY', parseFloat(e.target.value))" />
          </div>
          <div class="field-group">
            <label>Wall Height <span class="val">{{ mapConfig.wallHeight }}</span></label>
            <input type="range" :value="mapConfig.wallHeight" min="0.1" max="5.0" step="0.1"
              @input="e => updateMapConfig('wallHeight', parseFloat(e.target.value))" />
          </div>

          <div class="config-section-title" style="margin-top: 16px;">🚗 Vehicle Config</div>
          <div class="field-group">
            <label>Offset X <span class="val">{{ vehicleConfig.offsetX }}</span></label>
            <input type="range" :value="vehicleConfig.offsetX" min="-50" max="50" step="0.1"
              @input="e => updateVehicleConfig('offsetX', parseFloat(e.target.value))" />
          </div>
          <div class="field-group">
            <label>Offset Y <span class="val">{{ vehicleConfig.offsetY }}</span></label>
            <input type="range" :value="vehicleConfig.offsetY" min="-50" max="50" step="0.1"
              @input="e => updateVehicleConfig('offsetY', parseFloat(e.target.value))" />
          </div>
          <div class="field-group">
            <label>Rotation <span class="val">{{ vehicleConfig.rotation }}°</span></label>
            <input type="range" :value="vehicleConfig.rotation" min="0" max="360" step="1"
              @input="e => updateVehicleConfig('rotation', parseFloat(e.target.value))" />
          </div>
          <div class="field-group">
            <label>Move Scale <span class="val">{{ vehicleConfig.moveScale }}</span></label>
            <input type="range" :value="vehicleConfig.moveScale" min="0.1" max="20" step="0.1"
              @input="e => updateVehicleConfig('moveScale', parseFloat(e.target.value))" />
          </div>
          <div class="field-group">
            <label>Vehicle Size <span class="val">{{ vehicleConfig.size }}</span></label>
            <input type="range" :value="vehicleConfig.size" min="0.1" max="5.0" step="0.1"
              @input="e => updateVehicleConfig('size', parseFloat(e.target.value))" />
          </div>
        </div>
      </div>

      <!-- Bottom Actions -->
      <div class="editor-footer">
        <button class="btn-secondary" @click="resetAll">↺ 초기화</button>
        <button class="btn-primary" @click="saveAll">💾 저장</button>
        <button class="btn-export" @click="exportConfig">📋 Export</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'

const STORAGE_KEY = 'map-editor-config'

const props = defineProps({
  visible: { type: Boolean, default: true }
})

const emit = defineEmits([
  'update:colors',
  'update:mapConfig',
  'update:vehicleConfig',
  'add:label',
  'remove:label',
  'update:labels',
  'reset',
  'rebuild-map'
])

const expanded = ref(false)
const activeTab = ref('colors')
const panelRef = ref(null)
const panelPos = reactive({ x: 20, y: 20 })
let isDragging = false
let dragStart = { x: 0, y: 0 }

const tabs = [
  { id: 'colors', icon: '🎨', label: '색상' },
  { id: 'labels', icon: '🏷️', label: '라벨' },
  { id: 'config', icon: '⚙️', label: '설정' },
]

// Default values
const DEFAULT_COLORS = {
  wall: '#505060',
  floor: '#2a2a3d',
  background: '#1e1e2e',
  vehicle: '#10b981',
  path: '#3b82f6'
}

const DEFAULT_MAP_CONFIG = {
  resolution: 0.05,
  originX: -3.81,
  originY: -20.7,
  wallHeight: 1.5,
}

const DEFAULT_VEHICLE_CONFIG = {
  offsetX: 10.6,
  offsetY: 35.5,
  rotation: 90,
  moveScale: 6,
  size: 1.0
}

const colors = reactive({ ...DEFAULT_COLORS })
const mapConfig = reactive({ ...DEFAULT_MAP_CONFIG })
const vehicleConfig = reactive({ ...DEFAULT_VEHICLE_CONFIG })
const labels = ref([])

const newLabel = reactive({
  text: '',
  x: 0,
  y: 0,
  color: '#ffffff',
  fontSize: 16
})

// -- Color updates --
const updateColor = (key, value) => {
  colors[key] = value
  emit('update:colors', { ...colors })
}

// -- Map config updates --
const updateMapConfig = (key, value) => {
  mapConfig[key] = value
  emit('update:mapConfig', { ...mapConfig })
}

// -- Vehicle config updates --
const updateVehicleConfig = (key, value) => {
  vehicleConfig[key] = value
  emit('update:vehicleConfig', { ...vehicleConfig })
}

// -- Label management --
const addLabel = () => {
  if (!newLabel.text.trim()) return
  const label = {
    text: newLabel.text.trim(),
    x: newLabel.x,
    y: newLabel.y,
    color: newLabel.color,
    fontSize: Number(newLabel.fontSize)
  }
  labels.value.push(label)
  emit('add:label', label)
  newLabel.text = ''
  newLabel.x = 0
  newLabel.y = 0
}

const removeLabel = (idx) => {
  labels.value.splice(idx, 1)
  emit('remove:label', idx)
}

const editLabel = (idx) => {
  const label = labels.value[idx]
  newLabel.text = label.text
  newLabel.x = label.x
  newLabel.y = label.y
  newLabel.color = label.color
  newLabel.fontSize = label.fontSize
  removeLabel(idx)
}

// -- Save / Load / Reset --
const saveAll = () => {
  const config = {
    colors: { ...colors },
    mapConfig: { ...mapConfig },
    vehicleConfig: { ...vehicleConfig },
    labels: [...labels.value]
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
  showToast('설정이 저장되었습니다!')
}

const loadSaved = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return
    const config = JSON.parse(saved)
    if (config.colors) Object.assign(colors, config.colors)
    if (config.mapConfig) Object.assign(mapConfig, config.mapConfig)
    if (config.vehicleConfig) Object.assign(vehicleConfig, config.vehicleConfig)
    if (config.labels) labels.value = config.labels

    // Emit all loaded values
    emit('update:colors', { ...colors })
    emit('update:mapConfig', { ...mapConfig })
    emit('update:vehicleConfig', { ...vehicleConfig })
    if (labels.value.length) {
      emit('update:labels', [...labels.value])
    }
  } catch (e) {
    console.warn('Failed to load map editor config:', e)
  }
}

const resetAll = () => {
  Object.assign(colors, DEFAULT_COLORS)
  Object.assign(mapConfig, DEFAULT_MAP_CONFIG)
  Object.assign(vehicleConfig, DEFAULT_VEHICLE_CONFIG)
  labels.value = []
  emit('reset')
  emit('update:colors', { ...colors })
  emit('update:mapConfig', { ...mapConfig })
  emit('update:vehicleConfig', { ...vehicleConfig })
  emit('update:labels', [])
  showToast('설정이 초기화되었습니다!')
}

const exportConfig = () => {
  const config = {
    MAP_CONFIG: {
      resolution: mapConfig.resolution,
      origin: [mapConfig.originX, mapConfig.originY, 0],
      wallHeight: mapConfig.wallHeight,
      occupiedThresh: 0.65
    },
    VEHICLE_CONFIG: { ...vehicleConfig },
    colors: { ...colors },
    labels: [...labels.value]
  }
  const text = JSON.stringify(config, null, 2)
  navigator.clipboard.writeText(text).then(() => {
    showToast('설정이 클립보드에 복사되었습니다!')
  }).catch(() => {
    console.log('Export config:', text)
    showToast('콘솔에 출력했습니다.')
  })
}

// -- Drag --
const startDrag = (e) => {
  isDragging = true
  dragStart.x = e.clientX - panelPos.x
  dragStart.y = e.clientY - panelPos.y
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  if (!isDragging) return
  panelPos.x = e.clientX - dragStart.x
  panelPos.y = e.clientY - dragStart.y
}

const stopDrag = () => {
  isDragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// -- Toast --
const showToast = (msg) => {
  const toast = document.createElement('div')
  toast.textContent = msg
  toast.style.cssText = `
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
    background: #10b981; color: white; padding: 10px 24px; border-radius: 8px;
    font-size: 13px; font-weight: 600; z-index: 99999; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    animation: fadeIn 0.3s ease;
  `
  document.body.appendChild(toast)
  setTimeout(() => {
    toast.style.opacity = '0'
    toast.style.transition = 'opacity 0.3s ease'
    setTimeout(() => toast.remove(), 300)
  }, 2000)
}

onMounted(() => {
  loadSaved()
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
})

// Expose for parent
defineExpose({ loadSaved, labels, colors, mapConfig, vehicleConfig })
</script>

<style scoped>
.map-editor-overlay {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 100;
  pointer-events: none;
}

.editor-toggle-btn {
  position: fixed;
  top: 80px;
  left: 16px;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(30, 30, 46, 0.9);
  color: white;
  font-size: 18px;
  cursor: pointer;
  z-index: 110;
  pointer-events: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  transition: all 0.2s;
}

.editor-toggle-btn:hover {
  background: rgba(40, 40, 60, 0.95);
  transform: scale(1.05);
}

.editor-panel {
  position: fixed;
  top: 0;
  left: 0;
  width: 320px;
  max-height: calc(100vh - 100px);
  background: rgba(24, 24, 36, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(16px);
  pointer-events: auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #e2e8f0;
  font-size: 13px;
}

.editor-drag-handle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  cursor: grab;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  user-select: none;
}

.editor-drag-handle:active {
  cursor: grabbing;
}

.drag-icon {
  color: rgba(255, 255, 255, 0.3);
  font-size: 14px;
}

.editor-title {
  font-weight: 700;
  font-size: 14px;
  flex: 1;
}

.dev-badge {
  background: #f43f5e;
  color: white;
  font-size: 9px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.editor-tabs {
  display: flex;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.tab-btn {
  flex: 1;
  padding: 8px 0;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.tab-btn:hover {
  color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.03);
}

.tab-btn.active {
  color: #10b981;
  border-bottom-color: #10b981;
  background: rgba(16, 185, 129, 0.05);
}

.editor-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
  max-height: 400px;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-group label {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  display: flex;
  justify-content: space-between;
}

.field-group label .val {
  color: #10b981;
  font-family: monospace;
}

.color-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-row input[type="color"] {
  width: 36px;
  height: 28px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  padding: 0;
}

.color-hex {
  font-family: monospace;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

input[type="range"] {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  outline: none;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #10b981;
  cursor: pointer;
  box-shadow: 0 0 4px rgba(16, 185, 129, 0.4);
}

/* Labels Tab */
.add-label-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.editor-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
  font-size: 12px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.editor-input:focus {
  border-color: #10b981;
}

.editor-input.small {
  width: 100%;
}

.label-pos-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.label-style-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.color-input-sm {
  width: 30px;
  height: 26px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  padding: 0;
}

.editor-select {
  padding: 4px 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
  font-size: 11px;
  outline: none;
}

.btn-add {
  padding: 4px 12px;
  border: none;
  border-radius: 6px;
  background: #10b981;
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.btn-add:hover {
  background: #059669;
}

.label-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}

.label-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.label-preview {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
}

.label-coords {
  font-size: 10px;
  font-family: monospace;
  color: rgba(255, 255, 255, 0.3);
}

.label-actions {
  display: flex;
  gap: 2px;
}

.btn-icon {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.btn-icon:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-icon.danger:hover {
  background: rgba(244, 63, 94, 0.2);
}

.empty-msg {
  text-align: center;
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
  padding: 16px;
}

/* Config Tab */
.config-section-title {
  font-weight: 700;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 4px;
}

/* Footer */
.editor-footer {
  display: flex;
  gap: 6px;
  padding: 10px 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}

.btn-primary,
.btn-secondary,
.btn-export {
  flex: 1;
  padding: 6px 0;
  border: none;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #10b981;
  color: white;
}

.btn-primary:hover {
  background: #059669;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.12);
  color: white;
}

.btn-export {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.btn-export:hover {
  background: rgba(59, 130, 246, 0.25);
}

/* Scrollbar */
.editor-body::-webkit-scrollbar {
  width: 4px;
}

.editor-body::-webkit-scrollbar-track {
  background: transparent;
}

.editor-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
</style>
