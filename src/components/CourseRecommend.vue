<script setup>
import { computed } from 'vue'
import CourseCard from './CourseCard.vue'

/**
 * 🌟 추천 코스 컴포넌트
 * 좋아요 수가 많거나 최근에 등록된 인기 코스들을 추천합니다.
 */

const props = defineProps({
  courses: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['open-detail', 'toggle-like', 'filter-location'])

/**
 * 인기 코스 (좋아요 순 정렬)
 */
const popularCourses = computed(() => {
  return [...props.courses]
    .sort((a, b) => (b.likes || 0) - (a.likes || 0))
    .slice(0, 5)
})

/**
 * 신규 추천 코스 (최신순)
 */
const recentCourses = computed(() => {
  return [...props.courses].slice(0, 5)
})
</script>

<template>
  <div class="recommend-container animate-fade-in">
    <div class="section-header mb-8 text-center pt-4">
      <h2 class="text-h5 font-weight-black text-primary mb-2">러너들이 선정한 인기 코스 🏆</h2>
      <p class="text-body-2 text-grey">가장 많은 좋아요를 받은 우리 동네 핫플레이스입니다.</p>
    </div>

    <!-- 인기 코스 가로 스크롤 섹션 (또는 리스트) -->
    <div class="mb-10">
      <div class="d-flex align-center mb-4">
        <VIcon icon="mdi-fire" color="error" class="mr-2" />
        <h3 class="text-subtitle-1 font-weight-bold">실시간 베스트 코스</h3>
      </div>
      <div class="course-list">
        <CourseCard 
          v-for="course in popularCourses" 
          :key="course.id" 
          :course="course"
          @click="$emit('open-detail', course)"
          @toggle-like="$emit('toggle-like', $event)"
          @filter-location="$emit('filter-location', $event)"
        />
      </div>
      <div v-if="popularCourses.length === 0" class="text-center py-10 text-grey">
        아직 추천할 코스가 없습니다.
      </div>
    </div>

    <!-- 신규 코스 섹션 -->
    <div class="mb-10">
      <div class="d-flex align-center mb-4">
        <VIcon icon="mdi-new-box" color="success" class="mr-2" />
        <h3 class="text-subtitle-1 font-weight-bold">새로 올라온 추천 코스</h3>
      </div>
      <div class="course-list">
        <CourseCard 
          v-for="course in recentCourses" 
          :key="course.id" 
          :course="course"
          @click="$emit('open-detail', course)"
          @toggle-like="$emit('toggle-like', $event)"
          @filter-location="$emit('filter-location', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.recommend-container {
  padding-bottom: 60px;
}

.course-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
