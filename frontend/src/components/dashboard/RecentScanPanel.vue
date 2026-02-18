<script setup>
defineProps({
  scan: {
    type: Object,
    default: null
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
  <section class="panel scan-panel" v-if="scan">
    <div class="panel-header">
      <h2 class="panel-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <path d="m9 12 2 2 4-4" />
        </svg>
        최근 인식
      </h2>
      <span class="scan-status" :class="scan.status.toLowerCase()">{{ scan.status }}</span>
    </div>
    <div class="panel-body scan-body">
      <div class="scan-main">
        <span class="scan-dest-label">목적지</span>
        <span class="scan-dest-value">{{ scan.destination }}</span>
      </div>
      <div class="scan-info-grid">
        <div class="scan-info-item">
          <span class="info-label">운송장</span>
          <span class="info-value">{{ scan.waybill }}</span>
        </div>
        <div class="scan-info-item">
          <span class="info-label">신뢰도</span>
          <span class="info-value highlight">{{ scan.matchRate }}</span>
        </div>
        <div class="scan-info-item">
          <span class="info-label">처리시간</span>
          <span class="info-value">{{ formatProcessTime(scan.processTime) }}</span>
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
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
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
  padding: 16px 20px;
  border-bottom: 1px solid var(--glass-border);
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.02);
  flex-wrap: wrap;
  gap: 12px;
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
  white-space: nowrap;
  flex-shrink: 0;
  letter-spacing: 0.05em;
}

.panel-body {
  flex: 1;
  padding: 20px;
  min-height: 200px;
  overflow-y: auto;
  position: relative;
}

/* Scan Panel Specific */
.scan-panel {
  min-width: 280px;
}

.scan-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scan-status {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.scan-status.완료 { background: rgba(16, 185, 129, 0.1); color: var(--color-success); border: 1px solid rgba(16, 185, 129, 0.2); }
.scan-status.이동 { background: rgba(245, 158, 11, 0.1); color: var(--color-warning); border: 1px solid rgba(245, 158, 11, 0.2); }
.scan-status.대기 { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border: 1px solid rgba(255, 255, 255, 0.1); }

.scan-main {
  text-align: center;
  padding: 16px;
  background: var(--overlay-dark);
  border-radius: 12px;
  border: 1px solid var(--glass-border);
}

.scan-dest-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 4px;
}

.scan-dest-value {
  display: block;
  font-size: 36px;
  font-weight: 800;
  color: var(--color-primary);
  text-shadow: 0 0 20px var(--color-primary-glow);
}

.scan-info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.scan-info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  background: var(--overlay-lighter);
  border-radius: 8px;
  gap: 4px;
}

.info-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-family-mono);
}

.info-value.highlight {
  color: var(--color-success);
}

@media (max-width: 1200px) {
  .scan-panel { grid-column: 2; grid-row: 1; }
}

@media (max-width: 768px) {
  .scan-panel { grid-column: 1; }
}
</style>
