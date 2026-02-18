<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { fetchOcrResults } from '../../api'

const props = defineProps({
  wsEnabled: {
    type: Boolean,
    default: true
  }
})

const results = ref([])
const isLoading = ref(false)
const wsConnection = ref(null)

// Fetch OCR results from API
const loadResults = async () => {
  isLoading.value = true
  try {
    const response = await fetchOcrResults(10)
    results.value = response.data?.data?.items || []
  } catch (error) {
    console.error('OCR 결과 조회 실패:', error)
  } finally {
    isLoading.value = false
  }
}

// Format timestamp
const formatTime = (isoString) => {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// Get status badge class
const getStatusClass = (status) => {
  switch (status) {
    case 'completed': return 'status-success'
    case 'processing': return 'status-processing'
    case 'error': return 'status-error'
    default: return 'status-pending'
  }
}

// Get status text
const getStatusText = (status) => {
  switch (status) {
    case 'completed': return '완료'
    case 'processing': return '처리 중'
    case 'error': return '오류'
    default: return '대기'
  }
}

// Setup WebSocket connection for real-time updates
const setupWebSocket = () => {
  if (!props.wsEnabled) return
  
  try {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`
    
    wsConnection.value = new WebSocket(wsUrl)
    
    wsConnection.value.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        if (message.type === 'ocr_result') {
          // Add new result to the top
          results.value.unshift(message.payload)
          // Keep only last 10 results
          if (results.value.length > 10) {
            results.value = results.value.slice(0, 10)
          }
        }
      } catch (e) {
        console.debug('WebSocket message parse error:', e)
      }
    }
    
    wsConnection.value.onerror = (error) => {
      console.debug('WebSocket error:', error)
    }
    
  } catch (error) {
    console.debug('WebSocket connection failed:', error)
  }
}

onMounted(() => {
  loadResults()
  setupWebSocket()
})

onUnmounted(() => {
  if (wsConnection.value) {
    wsConnection.value.close()
  }
})
</script>

<template>
  <section class="panel ocr-panel">
    <div class="panel-header">
      <h2 class="panel-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-info)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" x2="8" y1="13" y2="13"/>
          <line x1="16" x2="8" y1="17" y2="17"/>
        </svg>
        OCR 인식 결과
        <span class="record-badge">{{ results.length }}건</span>
      </h2>
      <button class="btn-refresh" @click="loadResults" :disabled="isLoading" title="새로고침">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="{ spinning: isLoading }">
          <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
          <path d="M3 3v5h5"/>
          <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
          <path d="M16 16h5v5"/>
        </svg>
      </button>
    </div>
    <div class="panel-body">
      <div v-if="results.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <path d="M7 7h.01"/>
            <path d="M17 7h.01"/>
            <path d="M7 17h.01"/>
            <path d="M17 17h.01"/>
          </svg>
        </div>
        <p class="empty-text">OCR 인식 결과가 없습니다</p>
      </div>
      
      <div v-else class="results-list">
        <div v-for="result in results" :key="result.result_id" class="result-card">
          <div class="result-header">
            <span class="result-time">{{ formatTime(result.processed_at) }}</span>
            <span class="result-status" :class="getStatusClass(result.status)">
              {{ getStatusText(result.status) }}
            </span>
          </div>
          <div class="result-body" v-if="result.status === 'completed'">
            <!-- 운송장번호 & 지역코드 (메인 정보) -->
            <div class="result-main-row">
              <div class="result-field main-field">
                <span class="field-label">운송장번호</span>
                <span class="field-value tracking">{{ result.tracking_number || '-' }}</span>
              </div>
              <div class="result-field main-field">
                <span class="field-label">지역</span>
                <span class="field-value region">{{ result.region_code || '-' }}</span>
              </div>
            </div>
            <!-- 수령인 정보 -->
            <div class="result-info-row" v-if="result.recipient_name || result.recipient_address">
              <div class="result-field">
                <span class="field-label">수령인</span>
                <span class="field-value">{{ result.recipient_name || '-' }}</span>
              </div>
              <div class="result-field address-field" v-if="result.recipient_address">
                <span class="field-label">수령 주소</span>
                <span class="field-value small">{{ result.recipient_address }}</span>
              </div>
            </div>
            <!-- 발송인 정보 -->
            <div class="result-info-row" v-if="result.sender_name || result.sender_address">
              <div class="result-field">
                <span class="field-label">발송인</span>
                <span class="field-value">{{ result.sender_name || '-' }}</span>
              </div>
              <div class="result-field address-field" v-if="result.sender_address">
                <span class="field-label">발송 주소</span>
                <span class="field-value small">{{ result.sender_address }}</span>
              </div>
            </div>
          </div>
          <!-- 에러 상태 -->
          <div class="result-error" v-else-if="result.error">
            <span class="error-text">{{ result.error }}</span>
          </div>
          <!-- 처리 중 -->
          <div class="result-processing" v-else-if="result.status === 'processing'">
            <span class="processing-text">처리 중...</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: var(--glass-panel);
  backdrop-filter: blur(var(--blur-amount));
  border: 1px solid var(--glass-border);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  transition: border-color 0.3s;
  overflow: hidden;
}

.panel:hover {
  border-color: rgba(255, 255, 255, 0.15);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--glass-border);
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.02);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-secondary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.record-badge {
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-secondary);
}

.btn-refresh {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--overlay-dark);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh:hover:not(:disabled) {
  color: var(--text-primary);
  border-color: var(--color-primary);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.panel-body {
  flex: 1;
  padding: 12px;
  min-height: 0;
  overflow-y: auto;
  max-height: 300px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  text-align: center;
}

.empty-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
  color: var(--color-info);
  margin-bottom: 12px;
}

.empty-text {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-card {
  background: var(--overlay-dark);
  border: 1px solid var(--glass-border);
  border-radius: 10px;
  padding: 12px;
  transition: all 0.2s;
}

.result-card:hover {
  border-color: var(--color-primary);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.result-time {
  font-size: 11px;
  font-family: var(--font-family-mono);
  color: var(--text-muted);
}

.result-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
}

.status-success { background: rgba(16, 185, 129, 0.1); color: var(--color-success); border: 1px solid rgba(16, 185, 129, 0.2); }
.status-processing { background: rgba(245, 158, 11, 0.1); color: var(--color-warning); border: 1px solid rgba(245, 158, 11, 0.2); }
.status-error { background: rgba(239, 68, 68, 0.1); color: var(--color-error); border: 1px solid rgba(239, 68, 68, 0.2); }
.status-pending { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border: 1px solid rgba(255, 255, 255, 0.1); }

.result-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-main-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.result-info-row {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.result-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.main-field {
  padding: 8px 10px;
  background: var(--overlay-lighter);
  border-radius: 6px;
}

.address-field {
  min-width: 0;
}

.field-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.field-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.field-value.tracking {
  font-family: var(--font-family-mono);
  color: var(--color-primary);
  font-size: 15px;
}

.field-value.region {
  color: var(--color-success);
  font-weight: 700;
}

.field-value.small {
  font-size: 11px;
  color: var(--text-secondary);
  word-break: break-all;
}

.result-error {
  padding: 8px 10px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 6px;
}

.error-text {
  font-size: 11px;
  color: var(--color-error);
}

.result-processing {
  padding: 8px 10px;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 6px;
  text-align: center;
}

.processing-text {
  font-size: 12px;
  color: var(--color-warning);
}

@media (max-width: 768px) {
  .result-main-row {
    grid-template-columns: 1fr;
  }
  .result-info-row {
    grid-template-columns: 1fr;
  }
}
</style>
