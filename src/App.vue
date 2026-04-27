<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import HeroSection from './components/HeroSection.vue'
import CourseCard from './components/CourseCard.vue'
import CourseFilters from './components/CourseFilters.vue'
import CourseCreate from './components/CourseCreate.vue'
import CourseDetail from './components/CourseDetail.vue'
import CourseRecommend from './components/CourseRecommend.vue'

/**
 * 🏃‍♂️ 런당근 메인 애플리케이션 컴포넌트
 * 동네 러닝 코스 탐색, 상세 보기, 코스 등록 기능을 제어합니다.
 * .skills 표준에 따라 Vuetify 3 기반으로 구성되었습니다.
 */

const currentView = ref('discover') // 'discover', 'recommend', 'create', 'detail'
const selectedDifficulty = ref('전체')
const selectedCourse = ref(null)
const searchQuery = ref('')

const courses = ref([])

/**
 * 앱 초기화 시 로컬 스토리지에서 데이터를 불러옵니다.
 * TODO(Refactor, 2026-04-27): 대용량 데이터를 위해 추후 IndexedDB나 백엔드 연동 고려
 */
onMounted(() => {
  const savedCourses = localStorage.getItem('rundanggeun_courses')
  if (savedCourses) {
    try {
      courses.value = JSON.parse(savedCourses)
    } catch (e) {
      console.error('데이터 로딩 실패:', e)
    }
  }
})

/**
 * 코스 데이터 변경 시마다 로컬 스토리지에 동기화합니다.
 * deep: true 설정을 통해 배열 내부 객체의 변경사항까지 감지합니다.
 */
watch(courses, (newCourses) => {
  try {
    localStorage.setItem('rundanggeun_courses', JSON.stringify(newCourses))
  } catch (e) {
    if (e.name === 'QuotaExceededError') {
      alert('저장 공간이 부족합니다! 사진 용량을 줄여주세요.')
    }
  }
}, { deep: true })

/**
 * 필터링된 코스 목록 계산
 * 검색어와 난이도 필터를 동시에 적용합니다.
 */
const filteredCourses = computed(() => {
  return courses.value.filter(course => {
    const matchesDifficulty = selectedDifficulty.value === '전체' || course.difficulty === selectedDifficulty.value
    const matchesSearch = !searchQuery.value || 
                         course.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         course.location.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchesDifficulty && matchesSearch
  })
})

/**
 * 새로운 코스 등록 처리
 * 코스 배열의 처음에 추가하여 최신순으로 노출합니다.
 */
const handleCreateCourse = (newCourse) => {
  courses.value.unshift({ ...newCourse, comments: [] })
  currentView.value = 'discover'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/**
 * 코스 상세 페이지 오픈
 */
const openDetail = (course) => {
  selectedCourse.value = course
  currentView.value = 'detail'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/**
 * 댓글 업데이트 핸들러
 */
const handleUpdateComments = ({ courseId, comments }) => {
  const course = courses.value.find(c => c.id === courseId)
  if (course) {
    course.comments = comments
  }
}
/**
 * 특정 위치 클릭 시 해당 위치로 검색 필터링
 */
const handleFilterLocation = (location) => {
  searchQuery.value = location
  currentView.value = 'discover'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/**
 * 좋아요 토글 처리 (영구 저장)
 */
const handleToggleLike = (courseId) => {
  const course = courses.value.find(c => c.id === courseId)
  if (course) {
    course.isLiked = !course.isLiked
    course.likes = (course.likes || 0) + (course.isLiked ? 1 : -1)
  }
}

/**
 * 내 위치 기반 코스 탐색
 */
const handleFindMe = () => {
  if (!navigator.geolocation) return
  
  navigator.geolocation.getCurrentPosition((position) => {
    const { latitude, longitude } = position.coords
    
    // 가장 가까운 코스 찾기 (Haversine 공식 유사 구현)
    let closestCourse = null
    let minDistance = Infinity

    courses.value.forEach(course => {
      if (course.path && course.path.length > 0) {
        const startPoint = course.path[0]
        const dist = Math.sqrt(
          Math.pow(startPoint[0] - latitude, 2) + 
          Math.pow(startPoint[1] - longitude, 2)
        )
        if (dist < minDistance) {
          minDistance = dist
          closestCourse = course
        }
      }
    })

    if (closestCourse) {
      searchQuery.value = closestCourse.location
      alert(`내 위치와 가장 가까운 '${closestCourse.location}' 코스를 보여드릴게요!`)
    } else {
      alert('주변에 등록된 코스가 아직 없습니다.')
    }
  })
}
</script>

<template>
  <VApp>
    <!-- 상단 헤더 영역 -->
    <VAppBar flat border height="56">
      <VContainer class="d-flex align-center justify-center">
        <VAppBarTitle class="text-center font-weight-black text-primary">런릿 (Run-it)</VAppBarTitle>
      </VContainer>
    </VAppBar>

    <!-- 메인 컨텐츠 영역 -->
    <VMain class="app-background">
      <VContainer class="max-width-mobile">
        <div v-if="currentView === 'discover'">
          <HeroSection v-model="searchQuery" @find-me="handleFindMe" />
          
          <div class="content-section">
            <div class="section-header animate-fade-in">
              <h2 class="text-h6 font-weight-bold">우리 동네 러닝 게시판</h2>
              <p class="text-caption text-grey">이웃들이 공유한 숨은 러닝 명소를 찾아보세요</p>
            </div>

            <CourseFilters v-model="selectedDifficulty" />

            <div class="course-list">
              <CourseCard 
                v-for="course in filteredCourses" 
                :key="course.id" 
                :course="course" 
                @click="openDetail(course)"
                @filter-location="handleFilterLocation"
                @toggle-like="handleToggleLike"
              />
            </div>

            <!-- 검색 결과 없음 안내 -->
            <VContainer v-if="filteredCourses.length === 0" class="text-center py-12">
              <p class="text-body-1 text-grey-darken-1 mb-4">검색 결과가 없습니다.</p>
              <VBtn color="primary" variant="tonal" @click="selectedDifficulty = '전체'; searchQuery = ''">
                초기화
              </VBtn>
            </VContainer>
          </div>
        </div>

        <!-- 코스 등록 뷰 -->
        <div v-else-if="currentView === 'create'">
          <CourseCreate @create="handleCreateCourse" />
        </div>

        <!-- 추천 코스 뷰 -->
        <div v-else-if="currentView === 'recommend'">
          <CourseRecommend 
            :courses="courses" 
            @open-detail="openDetail" 
            @toggle-like="handleToggleLike"
            @filter-location="handleFilterLocation"
          />
        </div>

        <!-- 코스 상세 뷰 -->
        <div v-else-if="currentView === 'detail'">
          <CourseDetail 
            :course="selectedCourse" 
            @back="currentView = 'discover'"
            @update-comments="handleUpdateComments"
            @filter-location="handleFilterLocation"
            @toggle-like="handleToggleLike"
          />
        </div>
      </VContainer>
    </VMain>

    <!-- 하단 네비게이션 탭 (Glassmorphism 적용) -->
    <VBottomNavigation
      v-model="currentView"
      grow
      class="glass-nav"
      mandatory
    >
      <VBtn value="discover">
        <VIcon icon="mdi-home" />
        <span>홈</span>
      </VBtn>

      <VBtn value="recommend">
        <VIcon icon="mdi-star" />
        <span>추천 코스</span>
      </VBtn>

      <VBtn value="create">
        <VIcon icon="mdi-plus-circle" />
        <span>코스 등록</span>
      </VBtn>
    </VBottomNavigation>

    <!-- 푸터 영역 -->
    <footer class="main-footer py-12 text-center text-grey-lighten-1">
      <VContainer>
        <p class="text-caption">&copy; 2026 런릿 (Run-it) - 이웃과 함께 뛰는 즐거움</p>
      </VContainer>
    </footer>
  </VApp>
</template>

<style>
/* 전역 스타일 설정 */
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

.app-background {
  background-color: #f8f9fa;
}

.max-width-mobile {
  max-width: 768px !important;
  margin: 0 auto;
}

.content-section {
  padding: 1.5rem 0 4rem;
}

.section-header {
  margin-bottom: 1.5rem;
}

/* 글래스모피즘 네비게이션 바 */
.glass-nav {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(0, 0, 0, 0.05) !important;
  box-shadow: none !important;
}

.animate-fade-in {
  animation: slideUp 0.3s ease-out forwards;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.main-footer {
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}
</style>




