/**
 * 시스템 상태 관리 Composable
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { fetchSystemStatus } from '../api'
import { POLLING_INTERVALS } from '../constants'

export function useSystemStatus() {
  // 상태 변수
  const batteryLevel = ref(0)
  const isConnected = ref(false)
  const connectionText = ref('Connecting...')
  const isLoading = ref(false)
  const error = ref(null)

  let timer = null

  /**
   * 시스템 상태 조회
   */
  const getStatus = async () => {
    isLoading.value = true
    error.value = null

    try {
      const res = await fetchSystemStatus()
      const data = res.data.data

      batteryLevel.value = data.battery_level || 0
      isConnected.value = data.is_connected || false

      // 연결 상태 텍스트 설정
      if (data.is_connected) {
        connectionText.value = 'Stable'
      } else {
        connectionText.value = 'Offline'
      }
    } catch (err) {
      console.error('시스템 상태 조회 실패:', err)
      isConnected.value = false
      connectionText.value = 'Error'
      error.value = err.message || '상태 조회에 실패했습니다.'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 폴링 시작
   */
  const startPolling = () => {
    stopPolling()
    timer = setInterval(getStatus, POLLING_INTERVALS.systemStatus)
  }

  /**
   * 폴링 중지
   */
  const stopPolling = () => {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  // 컴포넌트 마운트 시 초기화
  onMounted(() => {
    getStatus()
    startPolling()
  })

  // 컴포넌트 언마운트 시 정리
  onUnmounted(() => {
    stopPolling()
  })

  return {
    // 상태
    batteryLevel,
    isConnected,
    connectionText,
    isLoading,
    error,

    // 메서드
    getStatus,
    startPolling,
    stopPolling
  }
}
