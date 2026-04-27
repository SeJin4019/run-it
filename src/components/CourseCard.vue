<script setup>
import { ref } from 'vue'
import MapRoutePicker from './MapRoutePicker.vue'

/**
 * 🏃‍♂️ 코스 카드 컴포넌트
 * 피드 목록에서 코스의 요약 정보(사진, 지도, 이름, 거리 등)를 표시합니다.
 * Vuetify의 VCard를 기반으로 설계되었습니다.
 */

const props = defineProps({
  course: {
    type: Object,
    required: true
  }
})

/**
 * 좋아요 토글 처리 (부모 컴포넌트에 이벤트 전달)
 */
const toggleLike = (e) => {
  e.stopPropagation() // 상세 페이지 이동 방지
  emit('toggle-like', props.course.id)
}
</script>

<template>
  <VCard 
    class="course-card mb-4 animate-fade-in" 
    elevation="0" 
    border
    rounded="lg"
  >
    <!-- 이미지 영역 -->
    <div class="card-media-wrapper">
      <VImg 
        :src="course.image" 
        :alt="course.name" 
        cover 
        aspect-ratio="16/9"
      >
        <template v-slot:placeholder>
          <div class="d-flex align-center justify-center fill-height bg-grey-lighten-4">
            <VProgressCircular indeterminate color="primary" />
          </div>
        </template>
        
        <!-- 난이도 뱃지 (VChip 사용) -->
        <VChip
          class="difficulty-badge"
          :color="course.difficulty === '쉬움' ? 'success' : course.difficulty === '보통' ? 'warning' : 'error'"
          size="small"
          variant="flat"
          label
        >
          {{ course.difficulty }}
        </VChip>
      </VImg>
    </div>

    <VCardText class="pa-4">
      <div class="d-flex justify-space-between align-start mb-2">
        <div>
          <h3 class="text-subtitle-1 font-weight-bold mb-0">{{ course.name }}</h3>
          <p 
            class="text-caption text-grey location-link" 
            @click.stop="$emit('filter-location', course.location)"
          >
            {{ course.location }}
          </p>
        </div>
      </div>

      <!-- 거리/고도 요약 정보 -->
      <div class="d-flex align-center py-2 px-3 bg-grey-lighten-5 rounded-pill mb-4">
        <div class="text-caption">
          거리 <strong class="text-primary">{{ course.distance }}km</strong>
        </div>
        <VDivider vertical class="mx-3" />
        <div class="text-caption">
          고도 <strong class="text-primary">{{ course.elevation }}m</strong>
        </div>
      </div>

      <!-- 액션 버튼 영역 -->
      <div class="d-flex align-center justify-space-between pt-2">
        <div class="d-flex align-center gap-2">
          <VBtn 
            variant="text" 
            size="small" 
            :color="course.isLiked ? 'error' : 'grey'"
            @click="toggleLike"
            class="px-2"
          >
            <VIcon icon="mdi-heart" v-if="course.isLiked" start />
            <VIcon icon="mdi-heart-outline" v-else start />
            {{ course.likes || 0 }}
          </VBtn>
          
          <VBtn variant="text" size="small" color="grey" class="px-2">
            <VIcon icon="mdi-comment-outline" start />
            {{ course.comments?.length || 0 }}
          </VBtn>
        </div>
        <span class="text-caption text-grey">방금 전</span>
      </div>
    </VCardText>
  </VCard>
</template>

<style scoped>
.course-card {
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

/* 마우스 호버 시 떠오르는 효과 적용 */
.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
}

.card-media-wrapper {
  position: relative;
}

.difficulty-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  font-weight: 800;
}

.location-link {
  cursor: pointer;
  transition: color 0.2s;
}

.location-link:hover {
  color: var(--v-theme-primary) !important;
  text-decoration: underline;
}

.gap-2 {
  gap: 8px;
}
</style>
