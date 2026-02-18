/**
 * ApexCharts 공통 설정
 * 테마 시스템 지원 (라이트/다크)
 */

/**
 * 현재 테마 가져오기
 */
const getCurrentTheme = () => {
  return document.documentElement.getAttribute('data-theme') || 'dark'
}

/**
 * 테마별 차트 색상
 */
const getThemeColors = () => {
  const isDark = getCurrentTheme() === 'dark'

  return {
    text: isDark ? '#94a3b8' : '#475569',
    grid: isDark ? '#1e293b' : '#cbd5e1',
    background: 'transparent',
    completed: '#10b981',
    totalCompleted: '#10b981',
    pending: isDark ? '#475569' : '#64748b',  // 라이트 모드에서 더 진한 회색으로 변경
    region: '#3b82f6'
  }
}

/**
 * 기본 차트 옵션 생성
 * @param {Object} options - 추가 옵션
 * @returns {Object} 차트 옵션 객체
 */
export const getBaseChartOptions = (options = {}) => {
  const colors = getThemeColors()
  const isDark = getCurrentTheme() === 'dark'

  return {
    chart: {
      type: 'bar',
      stacked: false,
      toolbar: { show: false },
      background: 'transparent',
      fontFamily: 'Noto Sans KR, sans-serif',
      height: '100%',
      parentHeightOffset: 0,
      animations: { enabled: false },
      ...options.chart
    },
    theme: { mode: isDark ? 'dark' : 'light' },
    tooltip: {
      theme: isDark ? 'dark' : 'light',
      style: {
        fontSize: '12px',
        fontFamily: 'Noto Sans KR, sans-serif'
      }
    },
    legend: { show: false },
    dataLabels: { enabled: false },
    grid: {
      borderColor: colors.grid,
      strokeDashArray: 4,
      xaxis: { lines: { show: false } },
      padding: { top: 10, right: 0, bottom: 0, left: 20 },
      ...options.grid
    },
    ...options
  }
}

/**
 * 대시보드 바 차트 옵션 생성
 * @param {number} maxValue - Y축 최대값
 * @returns {Object} 차트 옵션 객체
 */
export const getDashboardBarChartOptions = (maxValue = 10) => {
  const colors = getThemeColors()

  return getBaseChartOptions({
    chart: {
      type: 'bar',
      stacked: false,
      toolbar: { show: false },
      background: 'transparent',
      fontFamily: 'Noto Sans KR, sans-serif',
      height: '100%',
      parentHeightOffset: 0,
      animations: { enabled: false }
    },
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: '55%',
        borderRadius: 4,
        borderRadiusApplication: 'end'
      }
    },
    stroke: { show: true, width: 2, colors: ['transparent'] },
    xaxis: {
      labels: {
        style: {
          colors: colors.text,
          fontSize: '12px',
          fontWeight: 600
        }
      },
      axisBorder: { show: false },
      axisTicks: { show: false }
    },
    yaxis: {
      min: 0,
      max: maxValue,
      tickAmount: 5,
      labels: {
        style: {
          colors: colors.text,
          fontSize: '11px'
        },
        formatter: (val) => val.toFixed(0),
        minWidth: 30,
        maxWidth: 30
      }
    }
  })
}

// 하위 호환성을 위한 별칭
export const getDarkChartOptions = getBaseChartOptions
