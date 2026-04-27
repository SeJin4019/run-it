<script setup>
/**
 * 🏔️ 히어로 섹션 컴포넌트
 * 메인 페이지 최상단에 위치하며, 서비스 슬로건과 검색창을 제공합니다.
 * .skills/design-system의 Floating 애니메이션이 적용되어 있습니다.
 */
const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <header class="hero-wrapper mb-8 animate-fade-in">
    <VCard 
      class="hero-card pa-8 text-center d-flex flex-column align-center justify-center" 
      elevation="0"
      rounded="xl"
      color="primary"
    >
      <div class="floating-container">
        <h1 class="text-h4 text-sm-h3 font-weight-black text-white mb-4">
          함께 뛰는 즐거움, 런릿 (Run-it)
        </h1>
        <p class="text-subtitle-1 text-white opacity-80 mb-8">
          우리 동네 이웃들이 추천하는 최고의 러닝 코스를 만나보세요.
        </p>
      </div>

      <!-- 검색창 영역 (Glassmorphism 스타일 적용) -->
      <VSheet 
        class="search-container px-2 py-1" 
        rounded="pill"
        elevation="0"
      >
        <VBtn 
          icon="mdi-crosshairs-gps" 
          variant="text" 
          color="grey-darken-1" 
          size="small"
          class="mr-1"
          @click="$emit('find-me')"
        />
        <VTextField
          :model-value="modelValue"
          @update:model-value="$emit('update:modelValue', $event)"
          placeholder="동네나 코스 이름을 검색해보세요"
          variant="plain"
          hide-details
          density="compact"
          prepend-inner-icon="mdi-magnify"
          class="search-input px-2"
        />
        <VBtn 
          color="primary" 
          rounded="pill" 
          elevation="0" 
          height="40"
          class="px-6 font-weight-bold"
        >
          검색
        </VBtn>
      </VSheet>
    </VCard>
  </header>
</template>

<style scoped>
.hero-wrapper {
  overflow: visible;
}

.hero-card {
  min-height: 280px;
  background: linear-gradient(135deg, #ff8a3d 0%, #ff6b6b 100%) !important;
  position: relative;
  overflow: hidden;
}

/* .skills/design-system: Floating 애니메이션 구현 */
.floating-container {
  animation: floating 3s ease-in-out infinite;
}

@keyframes floating {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}

.search-container {
  width: 100%;
  max-width: 500px;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(5px);
  min-height: 48px;
}

.search-input {
  flex: 1;
}

/* Vuetify 내부 input 요소 정렬 보정 */
:deep(.v-field__input) {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  min-height: 40px !important;
  display: flex !important;
  align-items: center !important;
}

.opacity-80 {
  opacity: 0.8;
}
</style>
