import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
// import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // mock 모드 여부 확인
  const isMockMode = mode === 'mock'

  return {
    plugins: [
      vue(),
      // vueDevTools(), // DevTools 버튼 숨김
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
    define: {
      // mock 모드일 때 VITE_MOCK_MODE 환경변수 주입
      ...(isMockMode && {
        'import.meta.env.VITE_MOCK_MODE': JSON.stringify('true')
      })
    }
  }
})
