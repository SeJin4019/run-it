<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
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

const handleUpdateUser = (updatedUser) => {
  if (currentUser.value && updatedUser.id === currentUser.value.id) {
    currentUser.value = updatedUser
    localStorage.setItem('rundanggeun_user', JSON.stringify(updatedUser))
  }
  
  // globalUsers에서도 갱신
  const index = globalUsers.value.findIndex(u => u.id === updatedUser.id)
  if (index !== -1) {
    globalUsers.value[index] = updatedUser
  }
  
  if (selectedFriend.value && selectedFriend.value.id === updatedUser.id) {
    selectedFriend.value = updatedUser
  }
}

// 화면 전환
const currentView = ref('discover') // 'discover', 'recommend', 'create', 'detail', 'record', 'history', 'shoes'
const selectedDifficulty = ref('전체')
const selectedCourse = ref(null)
const searchQuery = ref('')

// 인증 및 기록 상태 - 초기 상태 동기 로드하여 깜빡임 방지
const savedToken = localStorage.getItem('rundanggeun_token')
const savedUser = localStorage.getItem('rundanggeun_user')
const savedExpiry = localStorage.getItem('rundanggeun_expiry')

const checkIsLoggedIn = () => {
  if (!savedToken || !savedUser) return false
  if (savedExpiry) {
    const now = new Date().getTime()
    return now <= parseInt(savedExpiry)
  }
  return true
}

const isLoggedIn = ref(checkIsLoggedIn())
const currentUser = ref(isLoggedIn.value ? JSON.parse(savedUser) : null)
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
const crewLiveMembers = ref([]) // 현재 지도에서 보고 있는 크루 멤버들
const selectedCrew = ref(null) // 현재 지도로 보고 있는 크루
const crewLiveTimer = ref(null) // 크루 실시간 동기화 타이머

// 알림용 스낵바 상태
const snackbar = ref({
  show: false,
  text: '',
  color: 'primary',
  friend: null
})

const courses = ref([])

const updateCourseLikeStates = () => {
  courses.value = courses.value.map(c => {
    const likedUsers = c.liked_users || []
    return {
      ...c,
      liked_users: likedUsers,
      likes: likedUsers.length,
      isLiked: isLoggedIn.value && currentUser.value ? likedUsers.includes(currentUser.value.id) : false
    }
  })
}

// 현재 유저의 기록 계산
const myRecords = computed(() => {
  if (!currentUser.value) return []
  return globalRecords.value.filter(r => r.user_id === currentUser.value.id)
})

// 로그인 안된 상태에서 접근이 필요한 뷰 감시
watch(currentView, (newView, oldView) => {
  const protectedViews = ['community', 'history', 'record', 'create', 'crew']
  if (!isLoggedIn.value && protectedViews.includes(newView)) {
    showAuthDialog.value = true
    // 이전 뷰가 유효하면 복구, 아니면 discover로 이동
    currentView.value = protectedViews.includes(oldView) ? 'discover' : (oldView || 'discover')
  }

  // 크루 뷰나 커뮤니티 뷰 전환 시 데이터 최신화
  if (newView === 'community' && isLoggedIn.value) {
    fetchGlobalRecords()
  }
})

/**
 * 앱 초기화 시 백엔드에서 데이터를 불러옵니다.
 */
onMounted(async () => {
  // 코스, 유저 목록을 병렬로 로드
  try {
    const [coursesRes, usersRes] = await Promise.all([
      fetch(`${API_URL}/courses`),
      fetch(`${API_URL}/users`)
    ])
    
    if (coursesRes.ok) {
      courses.value = await coursesRes.json()
      updateCourseLikeStates()
    }
    
    if (usersRes.ok) {
      globalUsers.value = await usersRes.json()
    }
  } catch (e) {
    console.error('초기 데이터 로딩 실패:', e)
  }

  // 로그인 상태인 경우 유저별 데이터 로드
  if (isLoggedIn.value && currentUser.value) {
    // 최신 유저 정보 동기화
    const freshMe = globalUsers.value.find(u => u.id === currentUser.value.id)
    if (freshMe) {
      currentUser.value = freshMe
      localStorage.setItem('rundanggeun_user', JSON.stringify(freshMe))
    }
    
    // 유저별 기록 및 신발 정보 병렬 로드
    Promise.all([
      fetchUserRecords(),
      fetchUserShoes()
    ]).catch(e => console.error('유저 데이터 로딩 실패:', e))
    
    startLiveFriendsPolling()
  }

  // 온라인 상태(하트비트) 시작
  sendHeartbeat()
  heartbeatTimer = setInterval(sendHeartbeat, 60000)
})

let heartbeatTimer = null
onUnmounted(() => {
  if (heartbeatTimer) clearInterval(heartbeatTimer)
})

const sendHeartbeat = async () => {
  if (!isLoggedIn.value || !currentUser.value) return
  try {
    await fetch(`${API_URL}/users/heartbeat?user_id=${currentUser.value.id}`, { method: 'POST' })
  } catch (e) {}
}

const refreshData = async () => {
  try {
    // 모든 기본 데이터를 병렬로 로드하여 속도 개선
    const promises = [
      fetch(`${API_URL}/courses`).then(r => r.ok ? r.json() : null),
      fetch(`${API_URL}/users`).then(r => r.ok ? r.json() : null)
    ]
    
    const [coursesData, usersData] = await Promise.all(promises)
    
    if (coursesData) {
      courses.value = coursesData
      updateCourseLikeStates()
    }
    
    if (usersData) {
      globalUsers.value = usersData
      // 내 정보 동기화
      if (currentUser.value) {
        const latestMe = usersData.find(u => u.id === currentUser.value.id)
        if (latestMe) {
          handleUpdateUser(latestMe)
        }
      }
    }

    // 로그인된 경우 추가 데이터 로드
    if (isLoggedIn.value && currentUser.value) {
      await Promise.all([
        fetchUserRecords(),
        fetchUserShoes(),
        fetchLiveFriends(),
        fetchPendingRequests()
      ])
    }

    snackbar.value = {
      show: true,
      text: '데이터를 최신 상태로 새로고침했습니다.',
      color: 'success',
      friend: null
    }
  } catch (e) {
    console.error('새로고침 실패:', e)
  }
}

const fetchUserRecords = async () => {
  if (!currentUser.value) return
  try {
    // 1. 먼저 본인의 기록만 빠르게 가져옴 (히스토리 뷰용)
    const res = await fetch(`${API_URL}/records/${currentUser.value.id}`)
    if (res.ok) {
      const myData = await res.json()
      // globalRecords에 본인 기록 반영 (합치기)
      const otherRecords = globalRecords.value.filter(r => r.user_id !== currentUser.value.id)
      globalRecords.value = [...otherRecords, ...myData]
    }
    
    // 2. 전체 기록(친구용)은 백그라운드에서 비동기로 가져옴 (속도 저하 방지)
    fetchGlobalRecords()
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
  // fetchPendingRequests() // 여기서 매번 호출하지 않고 별도 폴링으로 분리
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
      
      // 열려 있는 실시간 지도가 있다면, 갱신된 새 데이터 참조로 교체해주어야 Vue가 반응하여 즉각 그려줌
      if (showLiveMap.value && liveMapFriend.value) {
        const targetId = liveMapFriend.value.user_id || liveMapFriend.value.id
        const updatedFriend = newData.find(f => (f.user_id || f.id) === targetId)
        if (updatedFriend) {
          // 객체 전체를 교체하여 모든 스탯(거리, 시간, 페이스)이 반응형으로 업데이트되도록 함
          liveMapFriend.value = { ...updatedFriend }
        } else {
          showLiveMap.value = false
          snackbar.value = {
            show: true,
            text: `🏁 ${liveMapFriend.value.name}님이 러닝을 종료했습니다.`,
            color: 'primary',
            friend: null
          }
          liveMapFriend.value = null
        }
      }
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

const fetchCrewLiveLocations = async () => {
  if (!selectedCrew.value) return
  try {
    const res = await fetch(`${API_URL}/live/crews/${selectedCrew.value.id}`)
    if (res.ok) {
      crewLiveMembers.value = await res.json()
    }
  } catch (e) {
    console.error('크루 실시간 위치 로딩 실패:', e)
  }
}

const openCrewMap = (crew) => {
  selectedCrew.value = crew
  liveMapFriend.value = null // 개별 친구 모드 비활성
  showLiveMap.value = true
  fetchCrewLiveLocations()
  
  if (crewLiveTimer.value) clearInterval(crewLiveTimer.value)
  crewLiveTimer.value = setInterval(fetchCrewLiveLocations, 5000)
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
  fetchPendingRequests()
  
  // 친구 수락 등 상태 변화를 감지하기 위해 가끔 전체 데이터도 갱신 (60초마다로 완화)
  setInterval(refreshData, 60000)
  
  if (liveFriendsTimer.value) clearInterval(liveFriendsTimer.value)
  liveFriendsTimer.value = setInterval(fetchLiveFriends, 5000) // 5초마다 갱신 (기존 2초에서 완화)
  
  // 친구 요청은 더 가끔 확인 (30초마다)
  setInterval(fetchPendingRequests, 30000)
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
const handleUpdateComments = async ({ courseId, comments }) => {
  const course = courses.value.find(c => c.id === courseId)
  if (!course) return
  
  course.comments = comments
  const newComment = comments[comments.length - 1]
  
  try {
    const res = await fetch(`${API_URL}/courses/${courseId}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newComment)
    })
    if (res.ok) {
      const updatedCourse = await res.json()
      const index = courses.value.findIndex(c => c.id === courseId)
      if (index !== -1) {
        courses.value[index] = updatedCourse
      }
    }
  } catch (e) {
    console.error('댓글 업데이트 실패:', e)
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
const handleToggleLike = async (courseId) => {
  if (!isLoggedIn.value || !currentUser.value) {
    alert("로그인이 필요한 기능입니다.")
    return
  }
  
  try {
    const res = await fetch(`${API_URL}/courses/${courseId}/like?user_id=${currentUser.value.id}`, { method: 'POST' })
    if (res.ok) {
      const data = await res.json()
      const course = courses.value.find(c => c.id === courseId)
      if (course) {
        course.liked_users = data.liked_users || []
        course.likes = course.liked_users.length
        course.isLiked = course.liked_users.includes(currentUser.value.id)
      }
    }
  } catch (e) {
    console.error('좋아요 토글 실패', e)
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
  
  updateCourseLikeStates()
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
  updateCourseLikeStates()
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

const fetchGlobalRecords = async () => {
  try {
    const res = await fetch(`${API_URL}/records`)
    if (res.ok) {
      globalRecords.value = await res.json()
    }
  } catch (e) {
    console.error('전체 기록 로딩 실패:', e)
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
      fetchUserShoes() // 신발 마일리지 즉시 갱신
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
  showFriendProfile.value = false // 다른 다이얼로그 닫기
  currentView.value = 'create'
}

const handleDeleteRecord = async (recordId) => {
  if (!isLoggedIn.value) return

  try {
    const res = await fetch(`${API_URL}/records/${recordId}?user_id=${currentUser.value.id}`, {
      method: 'DELETE'
    })
    
    if (res.ok) {
      // 전역 레코드에서 삭제
      globalRecords.value = globalRecords.value.filter(r => r.id !== recordId)
      // 신발 마일리지 갱신 (마일리지가 차감되었을 수 있음)
      fetchUserShoes()
      alert('기록이 정상적으로 삭제되었습니다.')
    } else {
      const data = await res.json()
      alert('기록 삭제 실패: ' + (data.detail || '알 수 없는 오류'))
    }
  } catch (e) {
    console.error('기록 삭제 에러:', e)
  }
}

const selectedFriendRecords = ref([])
const selectedFriendShoes = ref([])

const openFriendProfile = async (friend) => {
  selectedFriend.value = friend
  showFriendProfile.value = true
  selectedFriendRecords.value = []
  selectedFriendShoes.value = []
  
  try {
    const [recRes, shoeRes] = await Promise.all([
      fetch(`${API_URL}/records/${friend.id}`),
      fetch(`${API_URL}/shoes/${friend.id}`)
    ])
    if (recRes.ok) selectedFriendRecords.value = await recRes.json()
    if (shoeRes.ok) selectedFriendShoes.value = await shoeRes.json()
  } catch (e) {
    console.error('친구 데이터 로딩 실패:', e)
  }
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
        <div style="width: 100px" class="text-right d-flex align-center justify-end">
          <VBtn icon="mdi-refresh" variant="text" size="small" class="mr-2 text-grey-darken-1" @click="refreshData" />
          <VBtn
            v-if="!isLoggedIn"
            variant="text"
            color="primary"
            class="font-weight-bold pa-0"
            @click="showAuthDialog = true"
          >
            로그인
          </VBtn>
          <VBadge
            dot
            color="success"
            location="bottom right"
            offset-x="3"
            offset-y="3"
          >
            <!-- 사용자 프로필 (로그인 시) -->
            <VAvatar v-if="isLoggedIn && currentUser" :color="currentUser.profile_image ? 'transparent' : 'primary'" size="40" class="mr-2" style="cursor: pointer" @click="currentView = 'history'">
              <img v-if="currentUser.profile_image" :src="currentUser.profile_image" alt="Profile" style="width:100%; height:100%; object-fit:cover;">
              <span v-else class="text-subtitle-1 text-white">{{ currentUser.name[0] }}</span>
            </VAvatar>
          </VBadge>
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

          <!-- 코스 등록 플로팅 액션 버튼 (FAB) -->
          <VBtn
            class="position-fixed bg-primary"
            style="bottom: 80px; right: 16px; z-index: 100;"
            icon="mdi-pencil-plus"
            size="x-large"
            elevation="8"
            @click="goToCreate"
          />
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
            @refresh="refreshData"
          />
        </div>

        <!-- 크루 뷰 -->
        <div v-else-if="currentView === 'crew'">
          <CrewView 
            :current-user="currentUser"
            :api-url="API_URL"
            @open-crew-map="openCrewMap"
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
            @recommend-route="handleRecommendRoute"
            @delete-record="handleDeleteRecord"
            @update-user="handleUpdateUser"
            @logout="handleLogout"
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
            :records="selectedFriendRecords"
            :shoes="selectedFriendShoes"
            :is-me="false"
            :is-friend="(() => {
              if (!currentUser || !currentUser.friends || !selectedFriend) return false;
              let fIds = currentUser.friends;
              if (typeof fIds === 'string') {
                try { fIds = JSON.parse(fIds); } catch (e) { fIds = []; }
              }
              return Array.isArray(fIds) && fIds.map(Number).includes(Number(selectedFriend.id));
            })()"
            @add-friend="handleAddFriend"
            @remove-friend="handleRemoveFriend"
            @recommend-route="handleRecommendRoute"
            @delete-record="handleDeleteRecord"
            @update-user="handleUpdateUser"
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
        
        <VCardText class="pa-0" style="position: relative;">
          <!-- 실시간 스탯 바 -->
          <div class="live-stats-overlay px-2 py-3 bg-white-glass d-flex justify-space-around align-center">
            <div class="text-center flex-grow-1">
              <div class="d-flex align-center justify-center mb-1">
                <VIcon icon="mdi-map-marker-distance" size="14" color="grey" class="mr-1" />
                <span class="text-caption text-grey font-weight-bold">거리</span>
              </div>
              <div class="text-subtitle-1 font-weight-black">{{ Number(liveMapFriend?.distance || 0).toFixed(2) }}<small class="ml-1 text-grey font-weight-medium">km</small></div>
            </div>
            
            <div class="stats-divider"></div>

            <div class="text-center flex-grow-1">
              <div class="d-flex align-center justify-center mb-1">
                <VIcon icon="mdi-clock-outline" size="14" color="grey" class="mr-1" />
                <span class="text-caption text-grey font-weight-bold">시간</span>
              </div>
              <div class="text-subtitle-1 font-weight-black">{{ liveMapFriend?.time || '00:00:00' }}</div>
            </div>

            <div class="stats-divider"></div>

            <div class="text-center flex-grow-1">
              <div class="d-flex align-center justify-center mb-1">
                <VIcon icon="mdi-speedometer" size="14" color="grey" class="mr-1" />
                <span class="text-caption text-grey font-weight-bold">페이스</span>
              </div>
              <div class="text-subtitle-1 font-weight-black text-primary">{{ liveMapFriend?.pace || "0'00\"" }}</div>
            </div>
          </div>

          <div style="height: 400px; width: 100%;">
            <!-- 실시간 이동 경로 지도 컴포넌트 -->
            <LiveMap 
              v-if="showLiveMap && (liveMapFriend || crewLiveMembers.length > 0)" 
              :members="liveMapFriend ? [liveMapFriend] : crewLiveMembers" 
            />
          </div>
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

      <VBtn value="community">
        <VIcon icon="mdi-account-group" />
        <span>커뮤니티</span>
      </VBtn>

      <VBtn value="crew">
        <VIcon icon="mdi-account-multiple" />
        <span>크루</span>
      </VBtn>

      <VBtn value="history">
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
  background: rgba(255, 255, 255, 0.85) !important;
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(0, 0, 0, 0.05) !important;
  box-shadow: none !important;
  overflow: visible !important; /* FAB가 튀어나오게 설정 */
}

/* 스크롤바 숨기기 (모바일 환경 등에서) */
.glass-nav::-webkit-scrollbar {
  display: none;
}
.glass-nav {
  -ms-overflow-style: none;
  scrollbar-width: none;
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

.live-stats-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000; /* Leaflet 지도보다 위로 오도록 높임 */
  border-bottom: 1px solid rgba(0,0,0,0.05);
}
.bg-white-glass {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
}
.stats-divider {
  width: 1px;
  height: 24px;
  background: rgba(0, 0, 0, 0.05);
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




