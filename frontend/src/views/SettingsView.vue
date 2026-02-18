<script setup>
import { ref, onMounted } from 'vue'
import { useTheme } from '../composables'
import { getMockMode, resetAllWaybills, fetchOcrStatus } from '../api'
import { OcrResultsPanel } from '../components/dashboard'

const { theme, toggleTheme } = useTheme()
const isMockMode = getMockMode()

// 물류 초기화 관련 상태
const isResetting = ref(false)
const resetResult = ref(null)

// 물류 데이터 초기화
const handleResetLogistics = async () => {
  if (!confirm('⚠️ 경고: 모든 운송장 데이터가 삭제됩니다.\n\n이 작업은 되돌릴 수 없습니다. 계속하시겠습니까?')) {
    return
  }
  
  isResetting.value = true
  resetResult.value = null
  
  try {
    const response = await resetAllWaybills()
    const data = response.data
    
    if (data.success) {
      resetResult.value = { success: true, message: data.message || `${data.deleted_count}개의 데이터가 삭제되었습니다.` }
      alert(`✅ ${data.message || `${data.deleted_count}개의 운송장 데이터가 삭제되었습니다.`}`)
    } else {
      throw new Error('삭제 실패')
    }
  } catch (e) {
    console.error('물류 초기화 실패:', e)
    resetResult.value = { success: false, message: e.message }
    alert(`❌ 초기화 실패: ${e.message}`)
  } finally {
    isResetting.value = false
  }
}

// OCR 서비스 상태
const ocrStatus = ref(null)
const isLoadingOcrStatus = ref(false)

const loadOcrStatus = async () => {
  isLoadingOcrStatus.value = true
  try {
    const response = await fetchOcrStatus()
    ocrStatus.value = response.data?.data || null
  } catch (e) {
    console.error('OCR 상태 조회 실패:', e)
    ocrStatus.value = null
  } finally {
    isLoadingOcrStatus.value = false
  }
}


// 백엔드 설정 (Docker 환경: 현재 호스트 사용, 로컬 개발: localhost)
const backendUrl = ref(window.location.origin || 'http://localhost')
const backendApiPath = ref('/api/v1')
const backendConnected = ref(false)
const backendTesting = ref(false)

// 라즈베리파이 설정
const raspberryPiIp = ref('192.168.0.100')
const raspberryPiPort = ref('1883')
const raspberryPiTopic = ref('autobox/command')
const raspberryPiConnected = ref(false)
const raspberryPiTesting = ref(false)

// MQTT 설정
const mqttBroker = ref('mqtt://localhost')
const mqttPort = ref('1883')

// 설정 저장/불러오기
const STORAGE_KEY = 'autobox_settings'

const loadSettings = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const settings = JSON.parse(saved)
      backendUrl.value = settings.backendUrl || backendUrl.value
      backendApiPath.value = settings.backendApiPath || backendApiPath.value
      raspberryPiIp.value = settings.raspberryPiIp || raspberryPiIp.value
      raspberryPiPort.value = settings.raspberryPiPort || raspberryPiPort.value
      raspberryPiTopic.value = settings.raspberryPiTopic || raspberryPiTopic.value
      mqttBroker.value = settings.mqttBroker || mqttBroker.value
      mqttPort.value = settings.mqttPort || mqttPort.value

    }
  } catch (e) {
    console.error('설정 불러오기 실패:', e)
  }
}

const saveSettings = () => {
  try {
    const settings = {
      backendUrl: backendUrl.value,
      backendApiPath: backendApiPath.value,
      raspberryPiIp: raspberryPiIp.value,
      raspberryPiPort: raspberryPiPort.value,
      raspberryPiTopic: raspberryPiTopic.value,
      mqttBroker: mqttBroker.value,
      mqttPort: mqttPort.value,

    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    alert('설정이 저장되었습니다.')
  } catch (e) {
    console.error('설정 저장 실패:', e)
    alert('설정 저장에 실패했습니다.')
  }
}

// 백엔드 연결 테스트
const testBackendConnection = async () => {
  backendTesting.value = true
  backendConnected.value = false
  
  try {
    const url = `${backendUrl.value}${backendApiPath.value}/system/status`
    const response = await fetch(url, { 
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(5000)
    })
    
    if (response.ok) {
      backendConnected.value = true
      alert('백엔드 서버 연결 성공!')
    } else {
      throw new Error(`HTTP ${response.status}`)
    }
  } catch (e) {
    backendConnected.value = false
    alert(`백엔드 연결 실패: ${e.message}`)
  } finally {
    backendTesting.value = false
  }
}

// 라즈베리파이 연결 테스트 (백엔드를 통해)
const testRaspberryPiConnection = async () => {
  raspberryPiTesting.value = true
  raspberryPiConnected.value = false
  
  try {
    const url = `${backendUrl.value}${backendApiPath.value}/vehicle/command`
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        command: 'ping',
        vehicle_id: 'AGV-001',
        parameters: {
          raspberry_pi_ip: raspberryPiIp.value,
          raspberry_pi_port: raspberryPiPort.value
        }
      }),
      signal: AbortSignal.timeout(10000)
    })
    
    if (response.ok) {
      raspberryPiConnected.value = true
      alert('라즈베리파이 연결 성공!')
    } else {
      throw new Error(`HTTP ${response.status}`)
    }
  } catch (e) {
    raspberryPiConnected.value = false
    alert(`라즈베리파이 연결 실패: ${e.message}\n\n백엔드 서버가 실행 중인지 확인해주세요.`)
  } finally {
    raspberryPiTesting.value = false
  }
}

onMounted(() => {
  loadSettings()
  loadOcrStatus()
})
</script>

<template>
  <div class="settings-page">
    <header class="settings-header">
      <h1 class="settings-title">설정</h1>
      <button class="save-btn" @click="saveSettings">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
          <polyline points="17 21 17 13 7 13 7 21"/>
          <polyline points="7 3 7 8 15 8"/>
        </svg>
        저장
      </button>
    </header>

    <div class="settings-content">
      <!-- 백엔드 서버 설정 -->
      <section class="settings-section">
        <h2 class="section-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="20" height="8" x="2" y="2" rx="2" ry="2"/>
            <rect width="20" height="8" x="2" y="14" rx="2" ry="2"/>
            <line x1="6" x2="6.01" y1="6" y2="6"/>
            <line x1="6" x2="6.01" y1="18" y2="18"/>
          </svg>
          백엔드 서버
        </h2>
        <div class="settings-card">
          <div class="setting-input-item">
            <label class="input-label">서버 URL</label>
            <div class="input-row">
              <input 
                type="text" 
                v-model="backendUrl" 
                class="setting-input"
                placeholder="http://localhost"
              />
            </div>
          </div>

          <div class="setting-input-item">
            <label class="input-label">API 경로</label>
            <div class="input-row">
              <input 
                type="text" 
                v-model="backendApiPath" 
                class="setting-input"
                placeholder="/api/v1"
              />
            </div>
          </div>

          <div class="setting-input-item">
            <label class="input-label">전체 엔드포인트</label>
            <div class="endpoint-preview">
              {{ backendUrl }}{{ backendApiPath }}
            </div>
          </div>

          <div class="setting-action-item">
            <button 
              class="test-btn" 
              :class="{ testing: backendTesting, success: backendConnected }"
              @click="testBackendConnection"
              :disabled="backendTesting"
            >
              <svg v-if="backendTesting" class="spinner" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              <svg v-else-if="backendConnected" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/>
                <path d="m12 5 7 7-7 7"/>
              </svg>
              {{ backendTesting ? '테스트 중...' : backendConnected ? '연결됨' : '연결 테스트' }}
            </button>
          </div>
        </div>
      </section>

      <!-- 라즈베리파이 설정 -->
      <section class="settings-section">
        <h2 class="section-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="4" width="16" height="16" rx="2" ry="2"/>
            <rect x="9" y="9" width="6" height="6"/>
            <line x1="9" x2="9" y1="1" y2="4"/>
            <line x1="15" x2="15" y1="1" y2="4"/>
            <line x1="9" x2="9" y1="20" y2="23"/>
            <line x1="15" x2="15" y1="20" y2="23"/>
            <line x1="20" x2="23" y1="9" y2="9"/>
            <line x1="20" x2="23" y1="14" y2="14"/>
            <line x1="1" x2="4" y1="9" y2="9"/>
            <line x1="1" x2="4" y1="14" y2="14"/>
          </svg>
          라즈베리파이 (임베디드)
        </h2>
        <div class="settings-card">
          <div class="setting-input-item">
            <label class="input-label">IP 주소</label>
            <div class="input-row">
              <input 
                type="text" 
                v-model="raspberryPiIp" 
                class="setting-input"
                placeholder="192.168.0.100"
              />
            </div>
          </div>

          <div class="setting-input-item">
            <label class="input-label">포트</label>
            <div class="input-row">
              <input 
                type="text" 
                v-model="raspberryPiPort" 
                class="setting-input"
                placeholder="1883"
              />
            </div>
          </div>

          <div class="setting-input-item">
            <label class="input-label">MQTT 토픽</label>
            <div class="input-row">
              <input 
                type="text" 
                v-model="raspberryPiTopic" 
                class="setting-input"
                placeholder="autobox/command"
              />
            </div>
          </div>

          <div class="setting-action-item">
            <button 
              class="test-btn" 
              :class="{ testing: raspberryPiTesting, success: raspberryPiConnected }"
              @click="testRaspberryPiConnection"
              :disabled="raspberryPiTesting"
            >
              <svg v-if="raspberryPiTesting" class="spinner" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              <svg v-else-if="raspberryPiConnected" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/>
                <path d="m12 5 7 7-7 7"/>
              </svg>
              {{ raspberryPiTesting ? '테스트 중...' : raspberryPiConnected ? '연결됨' : '연결 테스트' }}
            </button>
            <span class="test-hint">* 백엔드 서버를 통해 라즈베리파이에 연결합니다</span>
          </div>
        </div>
      </section>

      <!-- 테마 설정 -->
      <section class="settings-section">
        <h2 class="section-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="4"/>
            <path d="M12 2v2"/>
            <path d="M12 20v2"/>
            <path d="m4.93 4.93 1.41 1.41"/>
            <path d="m17.66 17.66 1.41 1.41"/>
            <path d="M2 12h2"/>
            <path d="M20 12h2"/>
            <path d="m6.34 17.66-1.41 1.41"/>
            <path d="m19.07 4.93-1.41 1.41"/>
          </svg>
          화면
        </h2>
        <div class="settings-card">
          <div class="setting-item" @click="toggleTheme">
            <div class="setting-info">
              <div class="setting-icon">
                <svg v-if="theme === 'dark'" xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="4"/>
                  <path d="M12 2v2"/>
                  <path d="M12 20v2"/>
                  <path d="m4.93 4.93 1.41 1.41"/>
                  <path d="m17.66 17.66 1.41 1.41"/>
                  <path d="M2 12h2"/>
                  <path d="M20 12h2"/>
                  <path d="m6.34 17.66-1.41 1.41"/>
                  <path d="m19.07 4.93-1.41 1.41"/>
                </svg>
              </div>
              <div class="setting-text">
                <span class="setting-label">테마</span>
                <span class="setting-value">{{ theme === 'dark' ? '다크 모드' : '라이트 모드' }}</span>
              </div>
            </div>
            <div class="setting-action">
              <div class="toggle-switch" :class="{ active: theme === 'dark' }">
                <div class="toggle-thumb"></div>
              </div>
            </div>
          </div>
        </div>
      </section>


      <!-- 시스템 정보 -->
      <section class="settings-section">
        <h2 class="section-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 16v-4"/>
            <path d="M12 8h.01"/>
          </svg>
          시스템 정보
        </h2>
        <div class="settings-card">
          <div class="setting-item readonly">
            <div class="setting-info">
              <div class="setting-icon mode">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
                </svg>
              </div>
              <div class="setting-text">
                <span class="setting-label">동작 모드</span>
                <span class="setting-value" :class="isMockMode ? 'mock' : 'live'">
                  {{ isMockMode ? '🎭 목업 모드 (테스트 데이터)' : '🟢 실제 서버 연결' }}
                </span>
              </div>
            </div>
          </div>

          <div class="setting-item readonly">
            <div class="setting-info">
              <div class="setting-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
                  <circle cx="12" cy="10" r="3"/>
                </svg>
              </div>
              <div class="setting-text">
                <span class="setting-label">앱 버전</span>
                <span class="setting-value mono">v1.0.0</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 데이터 관리 -->
      <section class="settings-section">
        <h2 class="section-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18"/>
            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
            <line x1="10" x2="10" y1="11" y2="17"/>
            <line x1="14" x2="14" y1="11" y2="17"/>
          </svg>
          데이터 관리
        </h2>
        <div class="settings-card">
          <div class="setting-item danger-item">
            <div class="setting-info">
              <div class="setting-icon danger">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/>
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                </svg>
              </div>
              <div class="setting-text">
                <span class="setting-label">물류 데이터 초기화</span>
                <span class="setting-value">모든 운송장, 스캔 로그, 매핑 데이터를 삭제합니다</span>
              </div>
            </div>
            <div class="setting-action">
              <button 
                class="reset-btn" 
                :class="{ resetting: isResetting }"
                @click="handleResetLogistics"
                :disabled="isResetting"
              >
                <svg v-if="isResetting" class="spinner" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/>
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                </svg>
                {{ isResetting ? '삭제 중...' : '초기화' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- OCR 디버깅 (개발자용) -->
      <section class="settings-section full-width">
        <h2 class="section-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          OCR 디버깅 (개발자용)
        </h2>
        <div class="settings-card">
          <div class="setting-item readonly">
            <div class="setting-info">
              <div class="setting-icon" :class="ocrStatus?.enabled ? 'success' : ''">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path v-if="ocrStatus?.enabled" d="m9 12 2 2 4-4"/>
                  <path v-else d="M15 9l-6 6M9 9l6 6"/>
                </svg>
              </div>
              <div class="setting-text">
                <span class="setting-label">OCR 서비스 상태</span>
                <span class="setting-value" :class="ocrStatus?.enabled ? 'live' : 'mock'">
                  {{ ocrStatus?.enabled ? '🟢 활성화됨' : '⚫ 비활성화됨' }}
                </span>
              </div>
            </div>
            <button class="test-btn" @click="loadOcrStatus" :disabled="isLoadingOcrStatus">
              <svg v-if="isLoadingOcrStatus" class="spinner" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              <span v-else>새로고침</span>
            </button>
          </div>

          <div class="setting-input-item" v-if="ocrStatus">
            <label class="input-label">감시 디렉토리</label>
            <div class="endpoint-preview">{{ ocrStatus.watch_directory }}</div>
          </div>

          <div class="setting-input-item" v-if="ocrStatus">
            <label class="input-label">OCR API URL</label>
            <div class="endpoint-preview">{{ ocrStatus.api_url }}</div>
          </div>

          <div class="setting-input-item" v-if="ocrStatus">
            <label class="input-label">처리된 결과 수</label>
            <div class="endpoint-preview">{{ ocrStatus.results_count }}건</div>
          </div>
        </div>

        <!-- OCR 결과 패널 -->
        <div class="ocr-debug-panel">
          <OcrResultsPanel :wsEnabled="true" />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  height: 100%;
  overflow-y: auto;
  padding: 16px 20px;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.settings-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.save-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--color-primary);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn:hover {
  background: var(--color-primary-dark, #4f46e5);
  transform: translateY(-1px);
}

.settings-content {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  max-width: 1200px;
}

.settings-section {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 8px 4px;
}

.settings-card {
  background: var(--glass-panel);
  backdrop-filter: blur(var(--blur-amount));
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  overflow: hidden;
}

/* 입력 필드 스타일 */
.setting-input-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--glass-border);
}

.setting-input-item:last-child {
  border-bottom: none;
}

.input-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.input-row {
  display: flex;
  gap: 8px;
}

.setting-input {
  flex: 1;
  padding: 10px 12px;
  background: var(--overlay-dark);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 13px;
  font-family: var(--font-family-mono);
  transition: all 0.2s;
}

.setting-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-glow);
}

.setting-input::placeholder {
  color: var(--text-muted);
}

.endpoint-preview {
  padding: 10px 12px;
  background: var(--overlay-lighter);
  border-radius: 8px;
  font-family: var(--font-family-mono);
  font-size: 12px;
  color: var(--color-primary);
  word-break: break-all;
}

/* 액션 아이템 */
.setting-action-item {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.test-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  background: var(--overlay-lighter);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.test-btn:hover:not(:disabled) {
  background: var(--overlay-light);
  border-color: var(--color-primary);
}

.test-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.test-btn.testing {
  color: var(--color-warning);
  border-color: var(--color-warning);
}

.test-btn.success {
  color: var(--color-success);
  border-color: var(--color-success);
  background: rgba(16, 185, 129, 0.1);
}

.test-btn .spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.test-hint {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
}

/* 토글 아이템 */
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
}

.setting-item:not(:last-child) {
  border-bottom: 1px solid var(--glass-border);
}

.setting-item:hover:not(.readonly) {
  background: var(--overlay-lighter);
}

.setting-item.readonly {
  cursor: default;
}

.setting-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.setting-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--overlay-lighter);
  border-radius: 8px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.setting-icon.mode {
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-primary);
}

.setting-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.setting-value {
  font-size: 13px;
  color: var(--text-muted);
}

.setting-value.mono {
  font-family: var(--font-family-mono);
  font-size: 12px;
}

.setting-value.mock {
  color: var(--color-warning);
}

.setting-value.live {
  color: var(--color-success);
}

/* Toggle Switch */
.toggle-switch {
  width: 44px;
  height: 24px;
  background: var(--overlay-dark);
  border-radius: 12px;
  padding: 2px;
  transition: all 0.2s;
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-switch.active {
  background: var(--color-primary);
}

.toggle-thumb {
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-switch.active .toggle-thumb {
  transform: translateX(20px);
}

/* Responsive */
@media (max-width: 900px) {
  .settings-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .settings-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .save-btn {
    width: 100%;
    justify-content: center;
  }
}

/* Danger/Reset Button Styles */
.setting-icon.danger {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-error, #ef4444);
}

.danger-item {
  border-left: 3px solid var(--color-error, #ef4444);
}

.reset-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 20px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid var(--color-error, #ef4444);
  border-radius: 8px;
  color: var(--color-error, #ef4444);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn:hover:not(:disabled) {
  background: var(--color-error, #ef4444);
  color: white;
}

.reset-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.reset-btn.resetting {
  background: rgba(239, 68, 68, 0.2);
}

.reset-btn .spinner {
  animation: spin 1s linear infinite;
}

/* Full Width Section */
.full-width {
  grid-column: 1 / -1;
}

/* Success Icon */
.setting-icon.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-success, #10b981);
}

/* OCR Debug Panel */
.ocr-debug-panel {
  margin-top: 16px;
}
</style>
