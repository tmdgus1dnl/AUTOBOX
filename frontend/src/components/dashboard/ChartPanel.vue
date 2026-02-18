<script setup>
import { ref, computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import { REGION_COLORS, CHART_COLORS } from '../../constants'

const props = defineProps({
  options: {
    type: Object,
    required: true
  },
  series: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['select-region'])

const chartType = ref('bar')

const chartTypes = [
  { value: 'bar', label: '막대' },
  { value: 'pie', label: '파이' }
]

// 파이 차트용 색상
const pieColors = REGION_COLORS

// 차트 타입에 따른 옵션 조정
const adjustedOptions = computed(() => {
  const baseOptions = { ...props.options }

  // 파이 차트용 옵션 (전체 제외한 지역별 완료 건수)
  if (chartType.value === 'pie') {
    const completedData = props.series[0]?.data || []
    const labels = completedData
      .filter(d => d.x !== '전체')
      .map(d => d.x)

    return {
      chart: {
        type: 'pie',
        background: 'transparent',
        events: {
          dataPointSelection: (event, chartContext, config) => {
            const label = config.w.config.labels[config.dataPointIndex]
            if (label) emit('select-region', label)
          }
        }
      },
      labels,
      colors: pieColors,
      legend: {
        position: 'bottom',
        labels: { colors: 'var(--text-secondary)' }
      },
      dataLabels: {
        enabled: true,
        formatter: (val, opts) => opts.w.globals.series[opts.seriesIndex],
        style: {
          fontSize: '14px',
          fontFamily: 'inherit',
          fontWeight: 600,
          colors: ['#ffffff']
        },
        dropShadow: {
          enabled: true,
          top: 1,
          left: 1,
          blur: 1,
          color: '#000',
          opacity: 0.45
        }
      },
      stroke: { width: 1, colors: ['#1e1e1e'] },
      tooltip: { theme: 'dark' }
    }
  }

  // 막대 차트용 옵션
  return {
    ...baseOptions,
    chart: {
      ...baseOptions.chart,
      type: 'bar',
      toolbar: { show: false },
      events: {
        dataPointSelection: (event, chartContext, config) => {
          // Bar 차트는 series 데이터에서 x값을 가져옴
          const seriesIndex = config.seriesIndex
          const dataPointIndex = config.dataPointIndex
          const dataPoint = config.w.config.series[seriesIndex]?.data[dataPointIndex]

          if (dataPoint && dataPoint.x) {
            emit('select-region', dataPoint.x)
          }
        }
      }
    },
    plotOptions: {
      ...baseOptions.plotOptions,
      bar: {
        ...baseOptions.plotOptions?.bar,
        distributed: true
      }
    },
    colors: [CHART_COLORS.pending, ...REGION_COLORS],
    legend: { show: false }
  }
})

// 차트 타입에 따른 시리즈 데이터 조정
const adjustedSeries = computed(() => {
  if (chartType.value === 'pie') {
    // 파이 차트: 전체 제외한 완료+미완료 건수 합계 배열
    const completedData = props.series[0]?.data || []
    const pendingData = props.series[1]?.data || []

    // 전체 제외한 지역별 데이터
    const regionData = completedData
      .filter(d => d.x !== '전체')
      .map((item, index) => {
        const completed = item.y || 0
        const pending = pendingData.find(p => p.x === item.x)?.y || 0
        return completed + pending
      })

    return regionData
  }

  // 막대 차트: 완료+미완료 합쳐서 하나로 표시
  const completedData = props.series[0]?.data || []
  const pendingData = props.series[1]?.data || []

  return [{
    name: '전체 현황',
    data: completedData.map((d, i) => {
      const pendingVal = pendingData[i]?.y || 0
      const totalVal = (d.y || 0) + pendingVal

      // '전체'인 경우 회색으로, 배송 지역은 해당 지역 색상 유지
      const color = d.x === '전체' ? '#64748b' : d.fillColor

      return {
        x: d.x,
        y: totalVal,
        fillColor: color
      }
    })
  }]
})


</script>

<template>
  <section class="panel chart-panel">
    <div class="panel-header">
      <h2 class="panel-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none"
          stroke="var(--color-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 3v18h18" />
          <path d="M18 17V9" />
          <path d="M13 17V5" />
          <path d="M8 17v-3" />
        </svg>
        지역별 현황
      </h2>
      <div class="chart-controls">
        <div class="chart-type-selector">
          <button v-for="type in chartTypes" :key="type.value"
            :class="['type-btn', { active: chartType === type.value }]" @click="chartType = type.value"
            :title="type.label">
            {{ type.label }}
          </button>
        </div>
        <div class="chart-legend" v-if="false">
          <span class="legend-item"><span class="legend-dot completed"></span>완료</span>
          <span class="legend-item"><span class="legend-dot pending"></span>미완료</span>
        </div>
      </div>
    </div>

    <div class="panel-body chart-body">
      <div class="chart-wrapper">
        <VueApexCharts :type="chartType" height="100%" width="100%" :options="adjustedOptions"
          :series="adjustedSeries" />
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
  /* 부모(HomeView)에서 높이를 제어할 수 있도록 flex 설정 */
  flex: 1;
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
  padding: 14px 18px;
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
  min-height: 0;
  padding: 0;
  /* position: relative; 제거 - 불필요한 레이어 생성 방지 */
  display: flex;
  /* Flexbox로 변경하여 내부 요소 꽉 채우기 */
  flex-direction: column;
}

.chart-body {
  /* 패딩을 최소화하여 차트 영역 확보 */
  padding: 10px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

/* 차트 래퍼: 무조건 부모 크기를 꽉 채우도록 설정 */
.chart-wrapper {
  flex: 1;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  /* 바닥 정렬 -> 중앙 정렬로 변경하여 파이 차트 짤림 방지 */
  overflow: hidden;
}

/* ApexCharts 강제 스타일링 */
:deep(.vue-apexcharts) {
  width: 100% !important;
  height: 100% !important;
  display: flex;
  justify-content: center;
  align-items: center;
}

:deep(.apexcharts-canvas) {
  width: 100% !important;
  height: 100% !important;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.chart-type-selector {
  display: flex;
  gap: 4px;
  background: var(--overlay-light, rgba(0, 0, 0, 0.08));
  padding: 4px;
  border-radius: 8px;
  border: 1px solid var(--glass-border);
}

.type-btn {
  padding: 6px 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.type-btn:hover {
  color: var(--text-secondary);
  background: var(--overlay-lighter, rgba(99, 102, 241, 0.08));
}

.type-btn.active {
  color: var(--color-primary);
  background: rgba(99, 102, 241, 0.2);
  box-shadow: 0 1px 3px rgba(99, 102, 241, 0.2);
}

.chart-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.legend-dot.completed {
  background: #10b981;
}

/* emerald-500 */
.legend-dot.pending {
  background: #f59e0b;
}

/* amber-500 */

/* 반응형 처리:
   HomeView.vue에서 이미 레이아웃을 제어하고 있으므로,
   여기서는 내부적인 미세 조정만 수행합니다.
*/

@media (max-width: 768px) {
  .chart-body {
    /* 모바일에서는 패딩을 더 줄여서 공간 확보 */
    padding: 0 5px 5px 5px;
  }

  /* 범례 폰트 사이즈 조정 */
  .legend-item {
    font-size: 11px;
  }

  .chart-controls {
    gap: 10px;
  }

  .type-btn {
    padding: 4px 8px;
    font-size: 10px;
  }
}
</style>