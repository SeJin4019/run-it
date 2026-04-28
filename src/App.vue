<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import HeroSection from './components/HeroSection.vue'
import CourseCard from './components/CourseCard.vue'
import CourseFilters from './components/CourseFilters.vue'
import CourseCreate from './components/CourseCreate.vue'
import CourseDetail from './components/CourseDetail.vue'
import CourseRecommend from './components/CourseRecommend.vue'
import AuthDialog from './components/AuthDialog.vue'
import RunningRecord from './components/RunningRecord.vue'
import UserHistory from './components/UserHistory.vue'
import CommunityView from './components/CommunityView.vue'
import ShoeManagement from './components/ShoeManagement.vue'
import LiveMap from './components/LiveMap.vue'

/**
 * 🏃‍♂️ 런당근 메인 애플리케이션 컴포넌트
 * 동네 러닝 코스 탐색, 상세 보기, 코스 등록 기능을 제어합니다.
 * .skills 표준에 따라 Vuetify 3 기반으로 구성되었습니다.
 */

const API_URL = import.meta.env.VITE_API_URL || `http://127.0.0.1:8000/api`

const currentView = ref('discover') // 'discover', 'recommend', 'create', 'detail', 'record', 'history', 'shoes'
const selectedDifficulty = ref('전체')
const selectedCourse = ref(null)
const searchQuery = ref('')

// 인증 및 기록 상태
const isLoggedIn = ref(false)
const currentUser = ref(null)
const showAuthDialog = ref(false)
const prefilledCourseData = ref(null) // 기록 종료 후 추천 경로 등록용 데이터

// 커뮤니티 및 장비 데이터 상태
const globalUsers = ref([])
const globalRecords = ref([])
const userShoes = ref([])
const liveFriends = ref([]) // 실시간 친구 위치
const previousLiveFriends = ref([]) // 이전 상태 저장용
const pendingRequests = ref([]) // 대기 중인 친구 요청
const selectedFriend = ref(null)
const liveFriendsTimer = ref(null)
const showFriendProfile = ref(false)
const showLiveMap = ref(false) // 실시간 지도 팝업
const liveMapFriend = ref(null) // 현재 지도에서 보고 있는 친구

// 알림용 스낵바 상태
const snackbar = ref({
  show: false,
  text: '',
  color: 'primary',
  friend: null
})

const courses = ref([])

// 현재 유저의 기록 계산
const myRecords = computed(() => {
  if (!currentUser.value) return []
  return globalRecords.value.filter(r => r.userId === currentUser.value.id)
})

/**
 * 앱 초기화 시 백엔드에서 데이터를 불러옵니다.
 */
onMounted(async () => {
  // 코스 목록 불러오기
  try {
    const res = await fetch(`${API_URL}/courses`)
    if (res.ok) {
      courses.value = await res.json()
    }
  } catch (e) {
    console.error('코스 로딩 실패:', e)
  }

  // 로그인 세션 확인 (일정 시간 후 만료 처리)
  const savedToken = localStorage.getItem('rundanggeun_token')
  const savedUser = localStorage.getItem('rundanggeun_user')
  const savedExpiry = localStorage.getItem('rundanggeun_expiry')
  
  if (savedToken && savedUser && savedExpiry) {
    const now = new Date().getTime()
    if (now > parseInt(savedExpiry)) {
      // 세션 만료됨
      alert('로그인 세션이 만료되었습니다. 다시 로그인해주세요.')
      handleLogout(false) // 만료로 인한 조용히 로그아웃
    } else {
      currentUser.value = JSON.parse(savedUser)
      isLoggedIn.value = true
      fetchUserRecords()
      fetchUserShoes()
      startLiveFriendsPolling()
    }
  } else if (savedToken && savedUser) {
     // 구버전(만료시간 없는) 데이터 호환성
      currentUser.value = JSON.parse(savedUser)
      isLoggedIn.value = true
      fetchUserRecords()
  }

  // 전체 유저 목록 불러오기 (커뮤니티용)
  try {
    const res = await fetch(`${API_URL}/users`)
    if (res.ok) {
      globalUsers.value = await res.json()
    }
  } catch (e) {
    console.error('유저 로딩 실패:', e)
  }
})

const fetchUserRecords = async () => {
  if (!currentUser.value) return
  try {
    const res = await fetch(`${API_URL}/records/${currentUser.value.id}`)
    if (res.ok) {
      globalRecords.value = await res.json()
    }
  } catch (e) {
    console.error('기록 로딩 실패:', e)
  }
}

const fetchUserShoes = async () => {
  if (!currentUser.value) return
  try {
    const res = await fetch(`${API_URL}/shoes/${currentUser.value.id}`)
    if (res.ok) {
      userShoes.value = await res.json()
    }
  } catch (e) {
    console.error('신발 로딩 실패:', e)
  }
}

const fetchLiveFriends = async () => {
  if (!currentUser.value || !isLoggedIn.value) return
  fetchPendingRequests()
  try {
    const res = await fetch(`${API_URL}/live/friends?user_id=${currentUser.value.id}`)
    if (res.ok) {
      const newData = await res.json()
      
      // 알림 로직: 처음 로딩 시에는 알림을 띄우지 않고, 이후 추가된 친구만 알림
      if (previousLiveFriends.value.length > 0) {
        newData.forEach(friend => {
          const isNewlyRunning = !previousLiveFriends.value.some(p => p.user_id === friend.user_id)
          if (isNewlyRunning) {
            showRunningNotification(friend)
          }
        });
      }
      
      liveFriends.value = newData
      previousLiveFriends.value = newData
    }
  } catch (e) {
    console.error('실시간 친구 위치 로딩 실패:', e)
  }
}

const showRunningNotification = (friend) => {
  snackbar.value = {
    show: true,
    text: `🔥 ${friend.name}님이 지금 러닝을 시작했습니다!`,
    color: 'error',
    friend: friend
  }
}

const openFriendMap = (friend) => {
  if (!friend) return
  liveMapFriend.value = friend
  showLiveMap.value = true
}

const fetchPendingRequests = async () => {
  if (!currentUser.value || !isLoggedIn.value) return
  try {
    const res = await fetch(`${API_URL}/users/friend-requests/${currentUser.value.id}`)
    if (res.ok) {
      pendingRequests.value = await res.json()
    }
  } catch (e) {
    console.error('친구 요청 로딩 실패:', e)
  }
}

const handleAcceptRequest = async (requestId) => {
  try {
    const res = await fetch(`${API_URL}/users/friend-requests/accept?request_id=${requestId}`, {
      method: 'POST'
    })
    if (res.ok) {
      const data = await res.json()
      alert(data.message)
      fetchPendingRequests()
      // 전체 유저 및 내 정보 갱신
      const userRes = await fetch(`${API_URL}/users`)
      if (userRes.ok) {
        globalUsers.value = await userRes.json()
        const updatedMe = globalUsers.value.find(u => u.id === currentUser.value.id)
        if (updatedMe) {
          currentUser.value = updatedMe
          localStorage.setItem('rundanggeun_user', JSON.stringify(updatedMe))
        }
      }
    }
  } catch (e) {
    console.error('요청 수락 실패:', e)
  }
}

const handleDeclineRequest = async (requestId) => {
  try {
    const res = await fetch(`${API_URL}/users/friend-requests/decline?request_id=${requestId}`, {
      method: 'POST'
    })
    if (res.ok) {
      alert('요청을 거절했습니다.')
      fetchPendingRequests()
    }
  } catch (e) {
    console.error('요청 거절 실패:', e)
  }
}

const startLiveFriendsPolling = () => {
  fetchLiveFriends()
  if (liveFriendsTimer.value) clearInterval(liveFriendsTimer.value)
  liveFriendsTimer.value = setInterval(fetchLiveFriends, 10000) // 10초마다 갱신
}

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

/**
 * 로그인 처리
 */
const handleLogin = (authResponse) => {
  currentUser.value = authResponse.user
  isLoggedIn.value = true
  
  // 2시간 후 만료로 설정 (밀리초 단위)
  const expiresIn = 2 * 60 * 60 * 1000
  const expiryTime = new Date().getTime() + expiresIn
  
  localStorage.setItem('rundanggeun_token', authResponse.access_token)
  localStorage.setItem('rundanggeun_user', JSON.stringify(authResponse.user))
  localStorage.setItem('rundanggeun_expiry', expiryTime.toString())
  
  fetchUserRecords()
  fetchUserShoes()
  startLiveFriendsPolling()
}

/**
 * 로그아웃 처리
 */
const handleLogout = (requireConfirm = true) => {
  if (requireConfirm && !confirm('로그아웃 하시겠습니까?')) {
    return
  }
  isLoggedIn.value = false
  currentUser.value = null
  localStorage.removeItem('rundanggeun_token')
  localStorage.removeItem('rundanggeun_user')
  localStorage.removeItem('rundanggeun_expiry')
  currentView.value = 'discover'
}

/**
 * 코스 등록
 */
const handleCreateCourse = async (courseData) => {
  if (!isLoggedIn.value) return

  try {
    const res = await fetch(`${API_URL}/courses?user_id=${currentUser.value.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(courseData)
    })
    
    if (res.ok) {
      const newCourse = await res.json()
      courses.value.unshift(newCourse)
      prefilledCourseData.value = null // 데이터 초기화
      currentView.value = 'discover'
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  } catch (e) {
    console.error('코스 등록 실패:', e)
  }
}

/**
 * 코스 삭제 핸들러
 */
const handleDeleteCourse = async (courseId) => {
  if (!isLoggedIn.value) return

  if (!confirm('정말로 이 코스를 삭제하시겠습니까?')) return

  try {
    const res = await fetch(`${API_URL}/courses/${courseId}?user_id=${currentUser.value.id}`, {
      method: 'DELETE'
    })
    
    if (res.ok) {
      courses.value = courses.value.filter(c => c.id !== courseId)
      if (currentView.value === 'detail') {
        currentView.value = 'discover'
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }
    }
  } catch (e) {
    console.error('코스 삭제 실패:', e)
  }
}

/**
 * 러닝 기록 저장
 */
const handleSaveRecord = async (record) => {
  if (!isLoggedIn.value) return

  try {
    const res = await fetch(`${API_URL}/records?user_id=${currentUser.value.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record)
    })
    
    if (res.ok) {
      const newRecord = await res.json()
      globalRecords.value.push(newRecord)
      // fetchUserRecords() // 필요 시 최신화
    }
  } catch (e) {
    console.error('기록 저장 실패:', e)
  }
}

/**
 * 기록된 경로를 추천 코스 등록으로 연동
 */
const handleRecommendRoute = (data) => {
  prefilledCourseData.value = {
    path: data.path,
    distance: data.distance
  }
  currentView.value = 'create'
}

const openFriendProfile = (friend) => {
  selectedFriend.value = friend
  showFriendProfile.value = true
}

const handleAddFriendByEmail = async (email) => {
  if (!currentUser.value) return
  try {
    const res = await fetch(`${API_URL}/users/add-friend?user_id=${currentUser.value.id}&friend_email=${email}`, {
      method: 'POST'
    })
    const data = await res.json()
    if (res.ok) {
      alert(data.message)
      // 사용자 목록 및 본인 정보 갱신
      const userRes = await fetch(`${API_URL}/users`)
      if (userRes.ok) {
        globalUsers.value = await userRes.json()
        const updatedMe = globalUsers.value.find(u => u.id === currentUser.value.id)
        if (updatedMe) {
          currentUser.value = updatedMe
          localStorage.setItem('rundanggeun_user', JSON.stringify(updatedMe))
        }
      }
    } else {
      alert(data.detail || '친구 추가에 실패했습니다.')
    }
  } catch (e) {
    console.error('친구 추가 실패:', e)
    alert('서버 연결에 실패했습니다.')
  }
}

const handleAddFriend = async (friendId) => {
  if (!currentUser.value) return
  try {
    // 이미 친구 추가 로직이 있으므로 이메일을 찾아서 호출하거나 별도 ID 기반 API 사용
    const friend = globalUsers.value.find(u => u.id === friendId)
    if (friend) {
      await handleAddFriendByEmail(friend.email)
    }
  } catch (e) {
    console.error('친구 추가 실패:', e)
  }
}

const handleRemoveFriend = async (friendId) => {
  if (!currentUser.value) return
  if (!confirm('정말 친구를 삭제하시겠습니까?')) return
  
  try {
    const res = await fetch(`${API_URL}/users/remove-friend?user_id=${currentUser.value.id}&friend_id=${friendId}`, {
      method: 'POST'
    })
    if (res.ok) {
      const data = await res.json()
      alert(data.message)
      // 사용자 정보 갱신
      const userRes = await fetch(`${API_URL}/users`)
      if (userRes.ok) {
        globalUsers.value = await userRes.json()
        const updatedMe = globalUsers.value.find(u => u.id === currentUser.value.id)
        if (updatedMe) {
          currentUser.value = updatedMe
          localStorage.setItem('rundanggeun_user', JSON.stringify(updatedMe))
        }
      }
    }
  } catch (e) {
    console.error('친구 삭제 실패:', e)
  }
}

const goToRecord = () => {
  if (!isLoggedIn.value) {
    showAuthDialog.value = true
    return
  }
  currentView.value = 'record'
}

const goToCreate = () => {
  if (!isLoggedIn.value) {
    showAuthDialog.value = true
    return
  }
  currentView.value = 'create'
}
</script>

<template>
  <VApp>
    <!-- 상단 헤더 영역 -->
    <VAppBar flat border height="56">
      <VContainer class="d-flex align-center">
        <div style="width: 80px"></div> <!-- Spacer for symmetry -->
        <VAppBarTitle class="text-center font-weight-black text-primary">런릿 (Run-it)</VAppBarTitle>
        <div style="width: 80px" class="text-right">
          <VBtn
            v-if="!isLoggedIn"
            variant="text"
            color="primary"
            class="font-weight-bold"
            @click="showAuthDialog = true"
          >
            로그인
          </VBtn>
          <VAvatar
            v-else
            color="primary"
            size="32"
            class="cursor-pointer"
            @click="currentView = 'history'"
          >
            <span class="text-caption">{{ currentUser.name[0] }}</span>
          </VAvatar>
        </div>
      </VContainer>
    </VAppBar>

    <!-- 메인 컨텐츠 영역 -->
    <VMain class="app-background">
      <VContainer class="max-width-mobile">
        <div v-if="currentView === 'discover'">
          <HeroSection v-model="searchQuery" @find-me="handleFindMe" />
          
          <!-- 실시간 친구 활동 상태 바 -->
          <VExpandTransition>
            <div v-if="liveFriends.length > 0" class="live-status-bar mb-6 px-4">
              <VCard color="error" theme="dark" class="rounded-xl pa-4 d-flex align-center shadow-lg clickable-card" @click="openFriendMap(liveFriends[0])">
                <div class="live-pulse-container mr-3">
                  <div class="live-pulse-dot"></div>
                </div>
                <div class="flex-grow-1">
                  <div class="text-subtitle-2 font-weight-black">LIVE : 친구가 달리고 있어요!</div>
                  <div class="text-caption opacity-80">
                    {{ liveFriends.map(f => f.name).join(', ') }}님이 현재 러닝 중입니다.
                  </div>
                </div>
                <VBtn variant="tonal" size="small" class="rounded-lg ml-2">위치 보기</VBtn>
              </VCard>
            </div>
          </VExpandTransition>
          
          <div class="content-section">
            <div class="section-header animate-fade-in d-flex justify-space-between align-center">
              <div>
                <h2 class="text-h6 font-weight-bold">우리 동네 러닝 게시판</h2>
                <p class="text-caption text-grey">이웃들이 공유한 숨은 러닝 명소를 찾아보세요</p>
              </div>
              <VBtn 
                color="primary" 
                variant="flat" 
                prepend-icon="mdi-pencil" 
                rounded="pill" 
                @click="goToCreate"
              >
                코스 등록
              </VBtn>
            </div>

            <CourseFilters v-model="selectedDifficulty" />

            <div class="course-list">
              <CourseCard 
                v-for="course in filteredCourses" 
                :key="course.id" 
                :course="course"
                :current-user="currentUser"
                @click="openDetail(course)"
                @filter-location="handleFilterLocation"
                @toggle-like="handleToggleLike"
                @delete-course="handleDeleteCourse"
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
          <CourseCreate 
            :prefilled-data="prefilledCourseData"
            @create="handleCreateCourse" 
          />
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
            :current-user="currentUser"
            @back="currentView = 'discover'"
            @update-comments="handleUpdateComments"
            @filter-location="handleFilterLocation"
            @toggle-like="handleToggleLike"
            @delete-course="handleDeleteCourse"
          />
        </div>

        <!-- 러닝 기록 뷰 -->
        <div v-else-if="currentView === 'record'">
          <RunningRecord 
            :user-id="currentUser?.id"
            :shoes="userShoes"
            :api-url="API_URL"
            @save-record="handleSaveRecord"
            @recommend-route="handleRecommendRoute"
            @back="currentView = 'history'"
          />
        </div>

        <!-- 커뮤니티 뷰 -->
        <div v-else-if="currentView === 'community'">
          <CommunityView 
            :current-user="currentUser"
            :global-users="globalUsers"
            :global-records="globalRecords"
            :live-friends="liveFriends"
            :pending-requests="pendingRequests"
            @open-profile="openFriendProfile"
            @add-friend-by-email="handleAddFriendByEmail"
            @accept-request="handleAcceptRequest"
            @decline-request="handleDeclineRequest"
            @open-live-map="openFriendMap"
          />
        </div>

        <!-- 내 활동 뷰 (신발 관리 포함) -->
        <div v-else-if="currentView === 'history'">
          <UserHistory 
            :user="currentUser"
            :records="myRecords"
            :shoes="userShoes"
            :api-url="API_URL"
            :is-me="true"
            @logout="handleLogout"
            @refresh-shoes="fetchUserShoes"
          />
        </div>
      </VContainer>
    </VMain>

    <!-- 인증 다이얼로그 -->
    <AuthDialog 
      v-model="showAuthDialog" 
      @login="handleLogin" 
    />

    <!-- 친구 프로필 다이얼로그 -->
    <VDialog v-model="showFriendProfile" max-width="500" transition="dialog-bottom-transition">
      <VCard class="rounded-xl" v-if="selectedFriend">
        <VToolbar color="transparent" flat class="pr-2">
          <VSpacer />
          <VBtn icon="mdi-close" variant="text" @click="showFriendProfile = false" />
        </VToolbar>
        <VCardText class="pt-0 pb-6">
          <UserHistory 
            :user="selectedFriend"
            :records="globalRecords.filter(r => r.userId === selectedFriend.id)"
            :is-me="false"
            :is-friend="currentUser?.friends?.includes(selectedFriend.id)"
            @add-friend="handleAddFriend"
            @remove-friend="handleRemoveFriend"
          />
        </VCardText>
      </VCard>
    </VDialog>

    <!-- 실시간 위치 추적 다이얼로그 (앱 내부 지도) -->
    <VDialog v-model="showLiveMap" max-width="600">
      <VCard class="rounded-xl overflow-hidden">
        <VToolbar color="error" dark flat>
          <VIcon icon="mdi-map-marker-radius" class="mr-2" />
          <VToolbarTitle class="text-subtitle-1 font-weight-bold">
            {{ liveMapFriend?.name }}님의 실시간 위치
          </VToolbarTitle>
          <VSpacer />
          <VBtn icon="mdi-close" @click="showLiveMap = false" />
        </VToolbar>
        
        <VCardText class="pa-0" style="height: 400px; position: relative;">
          <!-- 실시간 이동 경로 지도 컴포넌트 -->
          <LiveMap v-if="showLiveMap && liveMapFriend" :friend="liveMapFriend" />
        </VCardText>
        
        <VCardActions class="bg-white pa-4">
          <VIcon icon="mdi-clock-outline" size="16" class="mr-1 text-grey" />
          <span class="text-caption text-grey">마지막 업데이트: 방금 전</span>
          <VSpacer />
          <VBtn color="primary" variant="tonal" rounded="lg" @click="showLiveMap = false">닫기</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- 친구 러닝 시작 알림 스낵바 -->
    <VSnackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      location="top"
      elevation="24"
      rounded="pill"
      class="mt-12"
      :timeout="5000"
    >
      <div class="d-flex align-center">
        <VIcon icon="mdi-fire" class="mr-2" color="white" />
        {{ snackbar.text }}
      </div>
      <template v-slot:actions>
        <VBtn
          variant="text"
          class="font-weight-bold"
          @click="openFriendMap(snackbar.friend)"
        >
          위치 확인
        </VBtn>
      </template>
    </VSnackbar>

    <!-- 하단 네비게이션 탭 (Glassmorphism + Centered FAB 적용) -->
    <VBottomNavigation
      v-model="currentView"
      class="glass-nav"
      mandatory
      grow
    >
      <VBtn value="discover">
        <VIcon icon="mdi-home" />
        <span>홈</span>
      </VBtn>

      <VBtn value="recommend">
        <VIcon icon="mdi-star" />
        <span>추천</span>
      </VBtn>

      <!-- 중앙 기록 버튼 (FAB) -->
      <div class="fab-container">
        <VBtn
          @click="goToRecord"
          :class="{ 'fab-active': currentView === 'record' }"
          class="main-record-fab"
        >
          <VIcon icon="mdi-run" size="32" color="white" />
          <span class="fab-label">기록</span>
        </VBtn>
      </div>

      <VBtn value="community" v-if="isLoggedIn">
        <VIcon icon="mdi-account-group" />
        <span>커뮤니티</span>
      </VBtn>

      <VBtn value="history" v-if="isLoggedIn">
        <VIcon icon="mdi-account" />
        <span>내 정보</span>
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
  /* 모바일 가로 스크롤 지원 */
  overflow-x: auto !important;
  white-space: nowrap !important;
}

.v-bottom-navigation__content {
  justify-content: flex-start !important;
  padding: 0 16px;
  min-width: max-content;
}

/* 스크롤바 숨기기 */
.glass-nav::-webkit-scrollbar {
  display: none;
}
.glass-nav {
  -ms-overflow-style: none;
  scrollbar-width: none;
  overflow: visible !important; /* FAB가 튀어나오게 설정 */
}

/* 중앙 FAB 스타일 */
.fab-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 70px;
  z-index: 10;
}

.main-record-fab {
  position: absolute !important;
  bottom: 12px !important; /* 조금 더 아래로 */
  width: 52px !important;
  height: 52px !important;
  min-width: 52px !important;
  background: linear-gradient(135deg, #ff8a3d 0%, #ff7e5f 100%) !important; /* 부드러운 그라데이션 */
  border-radius: 50% !important;
  box-shadow: 0 4px 12px rgba(255, 138, 61, 0.3) !important; /* 부드러운 그림자 */
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
  padding: 0 !important;
}

.main-record-fab:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 15px rgba(255, 138, 61, 0.4) !important;
}

.fab-label {
  position: absolute;
  bottom: -22px;
  font-size: 10px;
  font-weight: bold;
  color: #ff8a3d;
  white-space: nowrap;
}

.fab-active {
  transform: translateY(-8px) scale(1.1);
  box-shadow: 0 15px 30px rgba(255, 138, 61, 0.6) !important;
}

.v-bottom-navigation__content {
  justify-content: space-around !important;
  padding: 0 8px;
  min-width: 100%;
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

/* 실시간 상태 바 애니메이션 */
.live-status-bar {
  cursor: pointer;
}

.live-pulse-container {
  position: relative;
  width: 12px;
  height: 12px;
}

.live-pulse-dot {
  width: 12px;
  height: 12px;
  background-color: white;
  border-radius: 50%;
  position: relative;
}

.live-pulse-dot::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: white;
  border-radius: 50%;
  animation: live-pulse-anim 1.5s infinite ease-in-out;
}

@keyframes live-pulse-anim {
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(3); opacity: 0; }
}

.clickable-card {
  transition: transform 0.2s;
}

.clickable-card:active {
  transform: scale(0.98);
}
</style>




