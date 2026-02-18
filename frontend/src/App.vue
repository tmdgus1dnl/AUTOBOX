<script setup>
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import TopNavigation from './components/TopNavigation.vue'
import { useTheme } from './composables'

// 테마 초기화
const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})
</script>

<template>
  <div class="app-layout">
    <TopNavigation />
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style>
/* Global App Styles */
#app {
  /* [중요] 모바일 브라우저 주소창 대응 (Dynamic Viewport Height) */
  height: 100dvh; 
  width: 100%;
  min-width: 320px;
  background: var(--bg-gradient);
  color: var(--text-primary);
  /* 앱 쉘 구조이므로 최상위 스크롤은 막습니다 */
  overflow: hidden;
  position: fixed; /* iOS 스크롤 튕김 방지 */
}
</style>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: transparent;
}

/* 메인 콘텐츠 - 네비게이션 제외한 나머지 공간 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
  
  /* 내부 스크롤 활성화 */
  overflow-y: auto;
  overflow-x: hidden;
  
  /* [핵심 수정] 하단 탭바(70px) + 여유공간(20px) + 디바이스 하단 Safe Area */
  padding-bottom: calc(70px + 20px + env(safe-area-inset-bottom));
  
  /* iOS 부드러운 스크롤 */
  -webkit-overflow-scrolling: touch;
}

/* 태블릿/데스크탑 (가로가 넓을 때) */
@media (min-width: 768px) {
  .main-content {
    /* 태블릿 이상에서는 여유 공간을 조금 줄여도 됨 */
    padding-bottom: calc(80px + env(safe-area-inset-bottom));
  }
}
</style>