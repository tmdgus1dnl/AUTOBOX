<script setup>
import { computed, ref } from 'vue'
import { useDashboard } from '../composables'
import { getDashboardBarChartOptions } from '../config/chartOptions'
import { sendBoxCountCommand } from '../api'
import { StatsGrid, ChartPanel, RecentScanPanel, LogisticsTable } from '../components/dashboard'

// Composable 사용
const {
  maxDate,
  selectedDate,
  chartSeries,
  chartMax,
  filteredLogisticsData,
  latestScan,
  filterRegion,
  filterStatus,
  loadData,
  todaySummary,
  downloadExcel
} = useDashboard()

// 날짜 이동 함수
const changeDate = (days) => {
  const current = new Date(selectedDate.value)
  current.setDate(current.getDate() + days)
  const today = new Date(maxDate.value)
  if (current <= today) {
    selectedDate.value = current.toISOString().split('T')[0]
  }
}


// 오늘 날짜로 이동
const goToToday = () => {
  selectedDate.value = maxDate.value
}

// 오늘인지 확인
const isToday = computed(() => selectedDate.value === maxDate.value)

// 선택된 날짜 포맷 (표시용)
const formattedDate = computed(() => {
  const date = new Date(selectedDate.value)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const weekdays = ['일', '월', '화', '수', '목', '금', '토']
  const weekday = weekdays[date.getDay()]
  return `${month}/${day} (${weekday})`
})

// 목표 박스 수
const targetBoxCount = ref(0)

// 토스트 알림 상태
const toastVisible = ref(false)
const toastLoading = ref(false)
const toastResult = ref(null)
let toastTimer = null

// 토스트 표시 (자동 닫힘)
const showToast = (result, duration = 3000) => {
  toastResult.value = result
  toastVisible.value = true
  toastLoading.value = false

  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastVisible.value = false
    toastResult.value = null
  }, duration)
}

// 박스 개수 전송 (토스트 방식)
const sendBoxCount = async () => {
  if (targetBoxCount.value <= 0) {
    showToast({ success: false, message: '박스 개수를 1개 이상 입력해주세요.' })
    return
  }

  // 로딩 토스트 표시
  toastLoading.value = true
  toastVisible.value = true
  toastResult.value = null

  try {
    const response = await sendBoxCountCommand(targetBoxCount.value)
    showToast({
      success: true,
      message: `물량 ${targetBoxCount.value}개 입력 완료`,
      boxCount: targetBoxCount.value
    })
  } catch (error) {
    console.error('박스 개수 전송 실패:', error)
    showToast({ success: false, message: '전송 실패. 다시 시도해주세요.' })
  }
}

// 지역 선택 핸들러 (차트 클릭 시)
const onRegionSelected = (regionName) => {
  if (regionName === '전체') {
    filterRegion.value = ''
    return
  }
  // 토글 기능: 이미 선택된 지역이면 필터 해제
  if (filterRegion.value === regionName) {
    filterRegion.value = ''
  } else {
    filterRegion.value = regionName
  }
}

// 차트 옵션
const chartOptions = computed(() => getDashboardBarChartOptions(chartMax.value))

// 엑셀 다운로드 모달 상태
const isDownloadModalOpen = ref(false)
const downloadMode = ref('range') // 'range' or 'all'
const downloadRange = ref({
  start: new Date(new Date().setDate(new Date().getDate() - 7)).toISOString().split('T')[0], // 기본값: 7일 전
  end: maxDate.value // 기본값: 오늘
})

const openDownloadModal = () => {
  isDownloadModalOpen.value = true
  // 모달 열릴 때 기본값 설정 (오늘 날짜)
  downloadRange.value.end = maxDate.value
  // 시작일은 종료일로부터 7일 전으로 설정 (종료일이 변경될 경우 다시 계산)
  const endDate = new Date(downloadRange.value.end);
  endDate.setDate(endDate.getDate() - 7);
  downloadRange.value.start = endDate.toISOString().split('T')[0];
}
const closeDownloadModal = () => {
  isDownloadModalOpen.value = false
  downloadMode.value = 'range' // 모달 닫을 때 모드 초기화
}

const handleDownload = () => {
  if (downloadMode.value === 'range') {
    if (!downloadRange.value.start || !downloadRange.value.end) {
      showToast({ success: false, message: '다운로드 기간을 선택해주세요.' })
      return
    }
    downloadExcel(downloadRange.value.start, downloadRange.value.end)
  } else {
    downloadExcel() // 인자 없으면 전체 다운로드
  }
  closeDownloadModal()
}
</script>

<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <!-- Empty header or maybe move toast here later -->
    </header>

    <!-- 박스 전송 + 날짜 선택 카드 + 통계 그리드 -->
    <div class="stats-row">
      <!-- 박스 개수 전송 (인라인) -->
      <div class="send-card">
        <div class="send-input-group">
          <div class="icon-box">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </div>
          <input type="number" v-model="targetBoxCount" placeholder="0" min="1" @keyup.enter="sendBoxCount" />
          <span class="unit">EA</span>
        </div>
        <button class="btn-send" @click="sendBoxCount" :disabled="toastLoading">
          <svg v-if="!toastLoading" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
          <span v-else class="loader"></span>
          {{ toastLoading ? '' : '전송' }}
        </button>
      </div>

      <!-- 날짜 선택 -->
      <div class="date-nav-card">
        <div class="nav-icon date-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        </div>
        <div class="date-controls">
          <button class="btn-nav" @click="changeDate(-1)">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
          <span class="current-date" @click="$refs.dateInput.showPicker()">
            {{ formattedDate }}
            <input ref="dateInput" type="date" v-model="selectedDate" :max="maxDate" class="date-input-hidden" />
          </span>
          <button class="btn-nav" @click="changeDate(1)" :disabled="isToday">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
        </div>
        <div class="quick-dates">
          <button class="btn-chip" :class="{ active: isToday }" @click="goToToday">오늘</button>
        </div>
      </div>

      <!-- 통계 그리드 (버튼 이동됨) -->
      <!-- 통계 그리드 (버튼 이동됨) -->
      <StatsGrid :summary="todaySummary">
        <template #actions>
          <!-- 엑셀 다운로드 (팝오버 래퍼) -->
          <div class="download-menu-wrapper">
            <button class="btn-action excel" @click="isDownloadModalOpen = !isDownloadModalOpen" title="엑셀 다운로드"
              :class="{ 'active': isDownloadModalOpen }">
              <!-- 엑셀 아이콘 -->
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="8" y1="13" x2="16" y2="13"></line>
                <line x1="8" y1="17" x2="16" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </button>

            <!-- 팝오버 메뉴 -->
            <div v-if="isDownloadModalOpen" class="download-popover">
              <div class="popover-header">
                <h3>엑셀 다운로드</h3>
                <button class="btn-close-sm" @click="closeDownloadModal">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
              <div class="popover-body">
                <div class="tab-group-sm">
                  <button class="tab-chip" :class="{ active: downloadMode === 'range' }"
                    @click="downloadMode = 'range'">기간 선택</button>
                  <button class="tab-chip" :class="{ active: downloadMode === 'all' }"
                    @click="downloadMode = 'all'">전체</button>
                </div>

                <div v-if="downloadMode === 'range'" class="range-inputs">
                  <div class="picker-row">
                    <span class="label">From</span>
                    <input type="date" v-model="downloadRange.start" :max="downloadRange.end || maxDate">
                  </div>
                  <div class="picker-row">
                    <span class="label">To</span>
                    <input type="date" v-model="downloadRange.end" :min="downloadRange.start" :max="maxDate">
                  </div>
                </div>

                <div v-else class="info-text">
                  전체 데이터를 다운로드합니다.
                </div>
              </div>
              <div class="popover-footer">
                <button class="btn-primary-sm" @click="handleDownload">
                  다운로드
                </button>
              </div>
            </div>

            <!-- 백드롭 (클릭 시 닫힘용, 투명) -->
            <div v-if="isDownloadModalOpen" class="transparent-backdrop" @click="closeDownloadModal"></div>
          </div>

          <button class="btn-action" @click="loadData" title="새로고침">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
              <path d="M3 3v5h5"></path>
              <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"></path>
              <path d="M16 16h5v5"></path>
            </svg>
          </button>
        </template>
      </StatsGrid>
    </div>

    <div class="main-content">
      <div class="left-column">
        <ChartPanel :options="chartOptions" :series="chartSeries" @select-region="onRegionSelected" />
      </div>
      <LogisticsTable :data="filteredLogisticsData" :expanded="true" v-model:filterRegion="filterRegion"
        v-model:filterStatus="filterStatus" />
    </div>

    <!-- 기존 모달 제거됨 -->

    <!-- 토스트 알림 (좌측 하단) -->
    <Transition name="toast">
      <div v-if="toastVisible" class="toast-notification"
        :class="{ 'toast-success': toastResult?.success, 'toast-error': !toastLoading && !toastResult?.success }">
        <div class="toast-icon" v-if="toastLoading">
          <svg class="spinner" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
        </div>
        <div class="toast-icon" v-else-if="toastResult?.success">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
        <div class="toast-icon" v-else>
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        </div>
        <span class="toast-message">{{ toastLoading ? '전송 중...' : toastResult?.message }}</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* =================================================================
   기본 레이아웃
   ================================================================= */
.dashboard {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  min-height: 550px;
  padding: 12px 20px 0 20px;
  gap: 10px;
  box-sizing: border-box;
  overflow-y: auto;
  overflow-x: hidden;
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif;
}

.dashboard button,
.dashboard input,
.dashboard select,
.dashboard textarea {
  font-family: inherit;
}

/* Header */
.dashboard-header {
  height: 0;
  display: none;
}

/* 날짜 + 통계 행 */
.stats-row {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
  width: 100%;
}

.stats-row :deep(.stats-grid) {
  flex: 1;
  min-width: 0;
}

/* 박스 전송 카드 (인라인) */
.send-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--glass-panel);
  backdrop-filter: blur(var(--blur-amount));
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  transition: all 0.3s;
  flex-shrink: 0;
}

.send-card:hover {
  border-color: rgba(99, 102, 241, 0.4);
}

.send-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.05);
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid transparent;
}

.send-input-group:focus-within {
  border-color: var(--color-primary);
  background: rgba(99, 102, 241, 0.05);
}

.icon-box {
  color: var(--color-primary);
  display: flex;
  align-items: center;
}

.send-input-group input {
  width: 60px;
  background: transparent;
  border: none;
  font-family: var(--font-family-mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  text-align: right;
  outline: none;
}

.unit {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
}

.btn-send {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  height: 40px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark, #4f46e5));
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 12px var(--color-primary-glow);
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-send:hover:not(:disabled) {
  transform: translateY(-1px);
}

.btn-send:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Loader */
.loader {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 날짜 네비게이션 카드 */
.date-nav-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 20px;
  background: var(--glass-panel);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  backdrop-filter: blur(var(--blur-amount));
}

.nav-icon {
  width: 44px;
  height: 44px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-primary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.date-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-nav {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--glass-border);
  background: transparent;
  border-radius: 8px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-nav:hover:not(:disabled) {
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.btn-nav:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.current-date {
  font-family: var(--font-family-mono);
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
  min-width: 140px;
  text-align: center;
  position: relative;
  cursor: pointer;
}

.date-input-hidden {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.quick-dates {
  display: flex;
  gap: 6px;
  margin-left: 8px;
}

.btn-chip {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
  cursor: pointer;
  font-weight: 600;
}

.btn-chip:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.btn-chip.active {
  background: var(--color-primary);
  color: white;
}


/* Main Content Layout (Desktop Grid - 2열) */
.main-content {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 12px;
  flex: 1;
  min-height: 0;
  padding-bottom: 20px;
}

.left-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.left-column> :deep(.panel) {
  flex: 1;
  min-height: 0;
}

/* Modal Styling */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  width: 400px;
  background: var(--bg-secondary);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  animation: modalPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalPop {
  from {
    transform: scale(0.95);
    opacity: 0;
  }

  to {
    transform: scale(1);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.btn-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
}

.btn-close:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
}

.download-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  padding: 4px;
  background: var(--bg-primary);
  border-radius: 8px;
}

.tab-btn {
  flex: 1;
  padding: 8px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.range-picker {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.date-input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.date-input-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
}

.date-input-group input {
  padding: 10px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-family: var(--font-family-mono);
}

.all-info {
  text-align: center;
  padding: 20px 0;
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.5;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  background: var(--bg-tertiary);
}

.btn-secondary {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary {
  padding: 8px 16px;
  background: var(--color-primary);
  border: none;
  color: white;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Toast Notification (Left Bottom) */
.toast-notification {
  position: fixed;
  bottom: calc(90px + env(safe-area-inset-bottom));
  left: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: rgba(15, 23, 42, 0.9);
  /* Dark background */
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  min-width: 280px;
}

.toast-success {
  border-left: 4px solid #10b981;
}

.toast-error {
  border-left: 4px solid #ef4444;
}

.toast-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

/* Spinner for Toast */
.toast-icon .spinner {
  animation: spin 1s linear infinite;
  stroke: #94a3b8;
}

.toast-success .toast-icon {
  color: #10b981;
}

.toast-error .toast-icon {
  color: #ef4444;
}

.toast-message {
  font-size: 14px;
  font-weight: 500;
  color: #f1f5f9;
}

/* Toast Transition */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* Responsive */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-row {
    flex-wrap: wrap;
  }

  .send-card,
  .date-nav-card {
    flex: 1;
    min-width: 100%;
  }
}

/* 모바일 차트 패널 최적화 */
@media (max-width: 768px) {
  .main-content> :first-child :deep(.panel) {
    min-height: 350px;
    display: flex;
    flex-direction: column;
  }

  .main-content> :first-child :deep(.panel-body) {
    padding: 10px 0 0 0 !important;
    overflow: visible !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    align-items: center !important;
    height: 100% !important;
  }

  .main-content> :first-child :deep(.apexcharts-canvas) {
    margin: 0 auto !important;
    transform: translateY(-5px);
  }
}

/* =================================================================
   Excel Download Popover
   ================================================================= */
.download-menu-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.btn-action.excel.active {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
}

.download-popover {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  width: 280px;
  background: var(--glass-panel);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  z-index: 2000;
  overflow: hidden;
  animation: popDown 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform-origin: top right;
}

@keyframes popDown {
  from {
    opacity: 0;
    transform: scale(0.95);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}

.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.03);
}

.popover-header h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.2px;
}

.btn-close-sm {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.btn-close-sm:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.1);
}

.popover-body {
  padding: 14px;
}

.tab-group-sm {
  display: flex;
  background: rgba(0, 0, 0, 0.2);
  padding: 2px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.tab-chip {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
}

.tab-chip.active {
  background: var(--glass-panel);
  color: var(--text-primary);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.range-inputs {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.picker-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.picker-row .label {
  width: 30px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
}

.picker-row input[type="date"] {
  flex: 1;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--glass-border);
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 12px;
  color: var(--text-primary);
  outline: none;
  font-family: var(--font-family-mono);
}

.picker-row input[type="date"]:focus {
  border-color: var(--color-primary);
}

.info-text {
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  padding: 12px 0;
  line-height: 1.4;
}

.popover-footer {
  padding: 10px 14px;
  border-top: 1px solid var(--glass-border);
  display: flex;
  justify-content: flex-end;
  background: rgba(255, 255, 255, 0.02);
}

.btn-primary-sm {
  background: var(--color-primary);
  color: white;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary-sm:hover {
  background: var(--color-primary-dark, #4f46e5);
}

.transparent-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1050;
  /* Popover 아래, 다른 요소 위 */
  cursor: default;
}
</style>