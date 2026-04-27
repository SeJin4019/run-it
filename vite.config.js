import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'

// https://vite.dev/config/
export default defineConfig({
  base: '/run-it/', // GitHub Pages 배포를 위한 설정 (저장소 이름)
  plugins: [
    vue(),
    vuetify({ autoImport: true }),
  ],
})
