<script setup>
/**
 * 🏷️ 코스 필터 컴포넌트
 * 난이도별(쉬움, 보통, 어려움) 코스를 필터링할 수 있는 버튼 그룹을 제공합니다.
 * Vuetify의 VBtnToggle을 사용하여 상태 관리를 시각화합니다.
 */
const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])

const difficulties = ['전체', '쉬움', '보통', '어려움']
</script>

<template>
  <div class="filter-wrapper mb-6">
    <VBtnToggle
      :model-value="modelValue"
      @update:model-value="$emit('update:modelValue', $event)"
      mandatory
      color="primary"
      variant="text"
      class="filter-toggle"
    >
      <VBtn 
        v-for="diff in difficulties" 
        :key="diff" 
        :value="diff"
        class="filter-btn text-caption font-weight-bold"
        rounded="pill"
        variant="flat"
        :color="modelValue === diff ? 'primary' : 'white'"
      >
        {{ diff }}
      </VBtn>
    </VBtnToggle>
  </div>
</template>

<style scoped>
.filter-wrapper {
  display: flex;
  overflow-x: auto;
  flex-wrap: nowrap;
  -webkit-overflow-scrolling: touch;
  padding: 4px 0;
}

.filter-toggle {
  background: transparent !important;
  display: flex !important;
  gap: 8px;
  height: auto !important;
}

.filter-btn {
  border: 1px solid #e9ecef !important;
  min-width: 70px;
  height: 36px !important;
}

:deep(.v-btn--active) {
  border-color: var(--v-theme-primary) !important;
  font-weight: 900 !important;
}

/* 스크롤바 숨기기 */
.filter-wrapper::-webkit-scrollbar {
  display: none;
}
</style>
