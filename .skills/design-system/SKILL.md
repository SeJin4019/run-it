---
name: 디자인 시스템 (Design System)
description: 브랜드 일관성을 유지하기 위한 스타일링 가이드입니다.
---

# 디자인 시스템 Skill

## 1. 테마 설정 (`themeConfig.js`)
- 다크/라이트 모드, Primary 컬러 등 전역 테마 설정은 `themeConfig.js`에서 통합 관리합니다.

## 2. 스타일 우선순위
1. **Vuetify 유틸리티 클래스**: Spacing(`pa-4`, `mt-2`), Typography(`text-h5`), Alignment 등을 우선적으로 사용합니다.
2. **Sass 변수**: 공통으로 정의된 SCSS 변수를 참조합니다.
3. **Custom CSS**: 불가피한 경우에만 `<style scoped>`를 사용합니다.

## 3. 공통 디자인 패턴

### Glassmorphism (글래스모피즘)
투명도와 배경 블러를 결합하여 입체감 있는 UI를 구현합니다.
- **Backdrop Blur**: `backdrop-filter: blur(10px);` 적용.
- **Transparency**: 배경색에 낮은 알파 값 적용 (예: `rgba(255, 255, 255, 0.15)`).
- **Border & Shadow**: 은은한 흰색 테두리와 부드러운 그림자로 레이어 깊이감 표현.

### Dynamic Animations (동적 애니메이션)
사용자 경험을 풍부하게 하는 애니메이션 기법입니다.
- **Floating**: `translateY`를 이용한 부드러운 상하 이동 효과.
- **Gradient Transition**: 배경 그라데이션의 `background-position`을 시간에 따라 변경.
- **Staggered**: 리스트 요소들에 `animation-delay`를 순차적으로 부여하여 리듬감 있는 노출.

## 4. 다크 모드 대응 (Dark Mode)
- CSS 변수를 사용하여 테마 전환 시 색상과 투명도가 자동으로 조절되도록 설계합니다.
- `[data-theme='dark']` 셀렉터를 활용하여 전역 변수를 재정의합니다.
