import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import '@mdi/font/css/materialdesignicons.css' // MDI 아이콘 추가
import { aliases, mdi } from 'vuetify/iconsets/mdi'

/**
 * Vuetify 3 초기화 설정
 * .skills/design-system의 표준을 따라 커스텀 테마를 정의합니다.
 * 아이콘 시스템으로 MDI를 기본으로 설정합니다.
 */
export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#ff8a3d', // 런릿 브랜드 컬러
          secondary: '#f8f9fa',
          accent: '#ff8a3d',
          error: '#ff5252',
          info: '#2196f3',
          success: '#4caf50',
          warning: '#fb8c00',
          background: '#f8f9fa',
          surface: '#ffffff',
        },
      },
    },
  },
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
})
