/**
 * 알림 관리 Composable
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { fetchAlerts, resolveAlert } from '../api'
import { POLLING_INTERVALS } from '../constants'

// 전역 상태 (싱글톤)
const alerts = ref([])
const isLoading = ref(false)

let refreshInterval = null
let isInitialized = false

export function useAlerts() {
  /**
   * 알림 목록 로드
   */
  const loadAlerts = async () => {
    isLoading.value = true
    try {
      const res = await fetchAlerts({ resolved: false, size: 50 })
      alerts.value = res.data.data?.items || res.data.data || []
    } catch (err) {
      console.error('알림 로드 실패:', err)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 알림 해결 처리
   */
  const resolve = async (alertId) => {
    try {
      await resolveAlert(alertId)
      await loadAlerts()
    } catch (err) {
      console.error('알림 해결 실패:', err)
    }
  }

  /**
   * 폴링 시작
   */
  const startPolling = () => {
    if (refreshInterval) return
    refreshInterval = setInterval(loadAlerts, POLLING_INTERVALS.alerts || 30000)
  }

  /**
   * 폴링 중지
   */
  const stopPolling = () => {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }

  // 컴포넌트 마운트 시 초기화 (한 번만)
  onMounted(() => {
    if (!isInitialized) {
      loadAlerts()
      startPolling()
      isInitialized = true
    }
  })

  return {
    alerts,
    isLoading,
    loadAlerts,
    resolve,
    startPolling,
    stopPolling
  }
}
