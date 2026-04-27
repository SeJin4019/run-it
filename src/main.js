import { createApp } from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import './style.css'

/**
 * Vue 앱 초기화
 * 런릿 (Run-it) 애플리케이션의 디자인 시스템과 플러그인을 설정합니다.
 */
const app = createApp(App)
app.use(vuetify)
app.mount('#app')
