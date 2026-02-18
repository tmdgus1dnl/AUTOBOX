<script setup>
defineProps({
  summary: {
    type: Object,
    required: true
  }
})

const formatProcessTime = (seconds) => {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds}초`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}분 ${secs}초`
}
</script>

<template>
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-icon total">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m7.5 4.27 9 5.15" />
          <path
            d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
        </svg>
      </div>
      <div class="stat-content">
        <span class="stat-value">{{ summary.total }}</span>
        <span class="stat-label">총 처리량</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon success">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <polyline points="22 4 12 14.01 9 11.01" />
        </svg>
      </div>
      <div class="stat-content">
        <span class="stat-value success">{{ summary.completed }}</span>
        <span class="stat-label">완료</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon rate">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 20v-6M6 20V10M18 20V4" />
        </svg>
      </div>
      <div class="stat-content">
        <span class="stat-value">{{ summary.successRate }}<small>%</small></span>
        <span class="stat-label">성공률</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon time">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
      </div>
      <div class="stat-content">
        <span class="stat-value">{{ formatProcessTime(summary.avgProcessTime) }}</span>
        <span class="stat-label">평균 처리 시간</span>
      </div>
    </div>

    <!-- 추가 액션 버튼 영역 (다운로드, 새로고침 등) -->
    <div class="stats-actions" v-if="$slots.actions">
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<style scoped>
.stats-grid {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
  width: 100%;
}

.stats-grid>.stat-card {
  flex: 1;
  min-width: 0;
  /* flex item 축소 허용 */
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  /* 패딩 축소로 카드 높이 감소 */
  padding: 14px 16px;
  background: var(--glass-panel);
  backdrop-filter: blur(var(--blur-amount));
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  transition: all 0.3s;
  min-width: 0;
}

.stat-card:hover {
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.stat-card.has-error {
  border-color: rgba(239, 68, 68, 0.3);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.1);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  /* 아이콘 박스 크기 축소 (56px -> 48px) */
  width: 48px;
  height: 48px;
  border-radius: 14px;
  flex-shrink: 0;
}

.stat-icon.total {
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-primary);
}

.stat-icon.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-success);
}

.stat-icon.rate {
  background: rgba(245, 158, 11, 0.1);
  color: var(--color-warning);
}

.stat-icon.time {
  background: rgba(14, 165, 233, 0.1);
  color: var(--color-info);
}

.stat-icon.error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-error);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  overflow: hidden;
}

.stat-value {
  /* 폰트 사이즈 미세 조정 (28px -> 26px) */
  font-size: 26px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
  font-family: var(--font-family-mono);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-value small {
  font-size: 16px;
  font-weight: 600;
}

.stat-value.success {
  color: var(--color-success);
}

.stat-value.error {
  color: var(--color-error);
}

.stat-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (min-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (max-width: 1199px) and (min-width: 769px) {
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
  }

  .stat-card {
    padding: 16px;
    gap: 12px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
  }

  .stat-icon svg {
    width: 24px;
    height: 24px;
  }

  .stat-value {
    font-size: 24px;
  }

  .stat-label {
    font-size: 10px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .stat-card:last-child:nth-child(odd) {
    grid-column: span 2;
  }

  .stat-card {
    padding: 12px;
    gap: 10px;
    flex-direction: column;
    align-items: flex-start;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
  }

  .stat-icon svg {
    width: 20px;
    height: 20px;
  }

  .stat-value {
    font-size: 22px;
  }
}

.stats-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
  /* 우측 정렬 */
  align-items: center;
}

/* HomeView에서 주입될 버튼 스타일 */
:deep(.btn-action) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: var(--glass-panel);
  border: 1px solid var(--glass-border);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  backdrop-filter: blur(var(--blur-amount));
}

:deep(.btn-action:hover) {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.2);
}

:deep(.btn-action.excel:hover) {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
}

@media (max-width: 1200px) {
  .stats-actions {
    margin-left: 0;
  }
}
</style>