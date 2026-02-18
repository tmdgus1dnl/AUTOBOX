/**
 * 테마 관리 Composable
 * 라이트/다크 모드 전환 기능
 */
import { ref, watch, onMounted } from 'vue'

const THEME_KEY = 'logitwin-theme'

// 전역 상태 (싱글톤)
const theme = ref('dark')

export function useTheme() {
  /**
   * 테마 초기화 (localStorage에서 불러오기)
   */
  const initTheme = () => {
    const savedTheme = localStorage.getItem(THEME_KEY)
    if (savedTheme) {
      theme.value = savedTheme
    } else {
      // 시스템 기본 설정 확인
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      theme.value = prefersDark ? 'dark' : 'light'
    }
    applyTheme()
  }

  /**
   * 테마 적용 (HTML 속성 설정)
   */
  const applyTheme = () => {
    document.documentElement.setAttribute('data-theme', theme.value)
    localStorage.setItem(THEME_KEY, theme.value)
  }

  /**
   * 테마 토글
   */
  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    applyTheme()
  }

  /**
   * 특정 테마로 설정
   */
  const setTheme = (newTheme) => {
    if (newTheme === 'dark' || newTheme === 'light') {
      theme.value = newTheme
      applyTheme()
    }
  }

  /**
   * 다크 모드 여부
   */
  const isDark = () => theme.value === 'dark'

  // 컴포넌트 마운트 시 초기화
  onMounted(() => {
    initTheme()
  })

  return {
    theme,
    toggleTheme,
    setTheme,
    isDark,
    initTheme
  }
}
