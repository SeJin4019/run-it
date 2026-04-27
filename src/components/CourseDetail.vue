<script setup>
import { ref } from 'vue'
import MapRoutePicker from './MapRoutePicker.vue'

/**
 * 📖 코스 상세 보기 컴포넌트
 * 특정 코스의 상세 정보, 전체 지도, 댓글 목록을 표시합니다.
 * .skills 표준 디자인 가이드에 따라 상세한 메타데이터를 노출합니다.
 */

const props = defineProps({
  course: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['back', 'update-comments', 'toggle-like', 'filter-location'])

const newComment = ref('')
const comments = ref(props.course.comments || [])

/**
 * 새 댓글 추가 처리
 */
const addComment = () => {
  if (!newComment.value.trim()) return
  
  const comment = {
    id: Date.now(),
    text: newComment.value,
    date: new Date().toLocaleString('ko-KR'),
    user: '이웃러너'
  }
  
  comments.value.push(comment)
  emit('update-comments', { courseId: props.course.id, comments: comments.value })
  newComment.value = ''
}
</script>

<template>
  <div class="detail-container animate-fade-in">
    <!-- 상단 툴바 (스티키 헤더) -->
    <VToolbar flat border class="sticky-top bg-white px-2">
      <VBtn icon="mdi-arrow-left" @click="$emit('back')" color="primary" />
      <VToolbarTitle class="text-subtitle-1 font-weight-bold">
        {{ course.name }}
      </VToolbarTitle>
      <VSpacer />
      <VBtn 
        :icon="course.isLiked ? 'mdi-heart' : 'mdi-heart-outline'" 
        :color="course.isLiked ? 'error' : 'grey-darken-1'" 
        @click="$emit('toggle-like', course.id)"
      />
    </VToolbar>

    <div class="content-body">
      <!-- 메인 이미지 섹션 -->
      <VImg :src="course.image" :alt="course.name" cover height="250" class="rounded-0" />

      <VContainer class="pa-6">
        <!-- 기본 정보 섹션 -->
        <div class="d-flex align-center justify-space-between mb-6">
          <div 
            class="d-flex align-center text-grey location-link" 
            @click="$emit('filter-location', course.location)"
          >
            <VIcon icon="mdi-map-marker" size="18" class="mr-1" />
            <span class="text-body-2">{{ course.location }}</span>
          </div>
          <VChip
            :color="course.difficulty === '쉬움' ? 'success' : course.difficulty === '보통' ? 'warning' : 'error'"
            size="small"
            label
            class="font-weight-bold"
          >
            {{ course.difficulty }}
          </VChip>
        </div>

        <!-- 핵심 스탯 그리드 -->
        <VRow class="mb-8">
          <VCol cols="6">
            <VCard flat border class="text-center pa-4 rounded-xl bg-grey-lighten-5">
              <div class="text-caption text-grey mb-1">거리</div>
              <div class="text-h6 font-weight-black text-primary">{{ course.distance }}km</div>
            </VCard>
          </VCol>
          <VCol cols="6">
            <VCard flat border class="text-center pa-4 rounded-xl bg-grey-lighten-5">
              <div class="text-caption text-grey mb-1">상승 고도</div>
              <div class="text-h6 font-weight-black text-primary">{{ course.elevation }}m</div>
            </VCard>
          </VCol>
        </VRow>

        <!-- 주차 및 코스 후기 섹션 -->
        <VCard flat border class="pa-4 rounded-xl mb-8 border-dashed">
          <div class="d-flex align-center mb-3">
            <VIcon icon="mdi-car" color="primary" class="mr-2" />
            <span class="text-subtitle-2 font-weight-bold">주차 정보:</span>
            <span class="ml-2 text-body-2">{{ course.parking || '정보 없음' }}</span>
          </div>
          <VDivider class="my-3" />
          <div v-if="course.description">
            <div class="d-flex align-center mb-2">
              <VIcon icon="mdi-comment-quote-outline" color="primary" class="mr-2" />
              <span class="text-subtitle-2 font-weight-bold">코스 후기</span>
            </div>
            <p class="text-body-2 text-grey-darken-2 line-height-relaxed">
              {{ course.description }}
            </p>
          </div>
          <div v-else class="text-caption text-grey italic">등록된 후기가 없습니다.</div>
        </VCard>

        <!-- 코스 지도 섹션 -->
        <div class="mb-10">
          <h3 class="text-h6 font-weight-bold mb-4">코스 지도</h3>
          <div class="detail-map-wrapper">
            <MapRoutePicker :modelValue="course.path" readOnly />
          </div>
        </div>

        <!-- 댓글 섹션 -->
        <div class="comment-section">
          <h3 class="text-h6 font-weight-bold mb-6">댓글 {{ comments.length }}</h3>
          
          <div class="comment-list mb-8">
            <div v-for="comment in comments" :key="comment.id" class="comment-item py-4">
              <div class="d-flex align-center mb-1">
                <span class="text-subtitle-2 font-weight-bold mr-2">{{ comment.user }}</span>
                <span class="text-caption text-grey">{{ comment.date }}</span>
              </div>
              <p class="text-body-2 text-grey-darken-3">{{ comment.text }}</p>
            </div>
            
            <div v-if="comments.length === 0" class="text-center py-10 text-grey text-body-2">
              첫 댓글을 남겨보세요!
            </div>
          </div>
        </div>
      </VContainer>
    </div>

    <!-- 하단 댓글 입력 영역 (Glassmorphism) -->
    <div class="comment-input-footer">
      <VContainer class="max-width-mobile px-4 py-2">
        <VTextField
          v-model="newComment"
          placeholder="따뜻한 댓글을 남겨주세요"
          variant="solo"
          flat
          hide-details
          rounded="pill"
          density="comfortable"
          bg-color="grey-lighten-4"
          @keyup.enter="addComment"
        >
          <template v-slot:append-inner>
            <VBtn 
              color="primary" 
              icon="mdi-send" 
              variant="text" 
              size="small"
              @click="addComment"
            />
          </template>
        </VTextField>
      </VContainer>
    </div>
  </div>
</template>

<style scoped>
.detail-container {
  background: white;
  min-height: 100vh;
  padding-bottom: 80px;
}

.sticky-top {
  position: sticky;
  top: 56px; /* AppBar height */
  z-index: 100;
}

.detail-map-wrapper {
  height: 320px;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}

.location-link {
  cursor: pointer;
  transition: color 0.2s;
}

.location-link:hover {
  color: var(--v-theme-primary) !important;
}

.comment-item {
  border-bottom: 1px solid #f1f3f5;
}

.comment-input-footer {
  position: fixed;
  bottom: 64px; /* BottomNav height */
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border-top: 1px solid #f1f3f5;
  z-index: 200;
}

.line-height-relaxed {
  line-height: 1.6 !important;
}

.border-dashed {
  border-style: dashed !important;
  border-width: 2px !important;
}

.max-width-mobile {
  max-width: 768px;
  margin: 0 auto;
}
</style>
