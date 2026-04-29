<script setup>
import { ref, onUnmounted, computed, onMounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'


const props = defineProps({
  userId: Number,
  shoes: Array,
  apiUrl: String
})

const emit = defineEmits(['save-record', 'back', 'recommend-route'])

const selectedShoe = ref(null)

const isRunning = ref(false)
const elapsedTime = ref(0) // seconds
const distance = ref(0.0) // km
const timer = ref(null)
const liveUpdateTimer = ref(null) // 실시간 위치 공유용 타이머 추가

// Map & GPS related
const mapContainer = ref(null)
let map = null
let polyline = null
let userMarker = null
const currentPath = ref([])
const startPosition = ref([37.5665, 126.9780]) // Default Seoul City Hall
let watchId = null
let lastUpdateTime = 0
const cadence = ref(0) // steps per minute
const cadenceDistanceHistory = ref([]) // 5-second window history for real-time cadence
const splits = ref([])
const lastSplitDistance = ref(0)
const lastSplitTime = ref(0)
const accumulatedTime = ref(0) // 이전 세션까지의 누적 시간 (초)
const lastStartTime = ref(0) // 마지막으로 '시작/재개' 버튼을 누른 시점 (ms)

// 주머니 모드 및 Wake Lock 관련
const isPocketMode = ref(false)
const unlockValue = ref(0)
let wakeLock = null

const requestWakeLock = async () => {
  if ('wakeLock' in navigator) {
    try {
      wakeLock = await navigator.wakeLock.request('screen')
      console.log('Wake Lock 활성화')
    } catch (err) {
      console.warn('Wake Lock 요청 실패:', err)
    }
  }
}

const releaseWakeLock = () => {
  if (wakeLock) {
    wakeLock.release()
    wakeLock = null
    console.log('Wake Lock 해제')
  }
}

const togglePocketMode = async () => {
  if (!isPocketMode.value) {
    await requestWakeLock()
    isPocketMode.value = true
    unlockValue.value = 0
  } else {
    isPocketMode.value = false
    releaseWakeLock()
  }
}

const handleUnlock = () => {
  if (unlockValue.value > 80) {
    isPocketMode.value = false
    releaseWakeLock()
    unlockValue.value = 0
  } else {
    unlockValue.value = 0
  }
}

const formatTimeFromSeconds = (secs) => {
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const formatPaceFromSeconds = (secs, dist) => {
  if (dist <= 0) return "0'00\""
  const paceSecs = secs / dist
  const paceM = Math.floor(paceSecs / 60)
  const paceS = Math.floor(paceSecs % 60)
  return `${paceM}'${paceS.toString().padStart(2, '0')}"`
}
const isManualMode = ref(false)
const manualDistance = ref(0)
const manualTime = ref('00:00:00')
const showRecommendDialog = ref(false)
const lastSavedPath = ref([])
const lastSavedDistance = ref(0)

const formattedTime = computed(() => {
  const hrs = Math.floor(elapsedTime.value / 3600)
  const mins = Math.floor((elapsedTime.value % 3600) / 60)
  const secs = elapsedTime.value % 60
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})

const pace = computed(() => {
  if (distance.value === 0) return "0'00\""
  const totalMins = elapsedTime.value / 60
  const pacePerKm = totalMins / distance.value
  const mins = Math.floor(pacePerKm)
  const secs = Math.round((pacePerKm - mins) * 60)
  return `${mins}'${secs.toString().padStart(2, '0')}"`
})

const calories = computed(() => {
  // 간단한 칼로리 계산 공식 (몸무게 70kg 기준 소모 칼로리)
  return Math.round(distance.value * 70)
})

const startRunning = () => {
  if (elapsedTime.value === 0 && currentPath.value.length === 0) {
    splits.value = []
    lastSplitDistance.value = 0
    lastSplitTime.value = 0
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        startPosition.value = [pos.coords.latitude, pos.coords.longitude]
        currentPath.value = [startPosition.value]
        initMap()
        requestWakeLock() // 시작 시 Wake Lock 요청
      }, (error) => {
        console.error('초기 위치 획득 실패:', error)
        if (error.code === 1) alert('GPS 권한이 거부되었습니다. 기기 설정에서 Safari(또는 사용 중인 브라우저)의 위치 권한을 허용해주세요.')
        else if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
          alert('아이폰 등 스마트폰 환경에서는 HTTPS 접속 시에만 GPS가 동작합니다.')
        }
        currentPath.value = [startPosition.value]
        initMap()
      }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 })
    } else {
      alert('이 기기는 GPS를 지원하지 않습니다.')
      currentPath.value = [startPosition.value]
      initMap()
    }
  }

  isRunning.value = true
  lastStartTime.value = Date.now() // 시작 시각 기록
  cadenceDistanceHistory.value = [] // Reset cadence history when starting/resuming
  
  // 1. 시간 측정용 타이머 및 실시간 케이던스 계산
  timer.value = setInterval(() => {
    // 현재 시간과 시작 시각의 차이를 계산하여 '경과 시간' 업데이트 (브라우저 절전 모드 대응)
    const now = Date.now()
    const sessionElapsed = Math.floor((now - lastStartTime.value) / 1000)
    elapsedTime.value = accumulatedTime.value + sessionElapsed

    if (isRunning.value) {
      cadenceDistanceHistory.value.push({ t: elapsedTime.value, d: distance.value })
      if (cadenceDistanceHistory.value.length > 5) {
        cadenceDistanceHistory.value.shift()
      }

      if (cadenceDistanceHistory.value.length >= 2) {
        const first = cadenceDistanceHistory.value[0]
        const last = cadenceDistanceHistory.value[cadenceDistanceHistory.value.length - 1]
        const timeDeltaMin = (last.t - first.t) / 60
        const distDeltaMeters = (last.d - first.d) * 1000

        if (timeDeltaMin > 0) {
          const speedMetersPerMin = distDeltaMeters / timeDeltaMin
          const speedMetersPerSec = speedMetersPerMin / 60
          
          // 러닝 케이던스 계산 (속도 기반 추정)
          // 속도가 너무 낮으면(걷기 이하) 0으로 처리
          let calcCadence = 0
          if (speedMetersPerSec > 1.5) { // 약 5.4km/h 이상일 때만 러닝으로 간주
            // 속도에 따른 가변 보폭 가정 (속도가 빠를수록 보폭이 커짐)
            // 보통 160~190 spm 사이가 일반적
            const estimatedStride = 0.7 + (speedMetersPerSec * 0.1) // 속도에 따라 0.8m ~ 1.2m 가변
            calcCadence = Math.round(speedMetersPerMin / estimatedStride)
          }
          
          if (calcCadence < 120) calcCadence = 0 // 최소 케이던스 제한
          if (calcCadence > 210) calcCadence = 210 // 최대 케이던스 제한

          if (cadence.value === 0 || calcCadence === 0) {
            cadence.value = calcCadence
          } else {
            // 부드러운 전환을 위한 보간 (필터링 강화)
            cadence.value = Math.round((cadence.value * 0.8) + (calcCadence * 0.2))
          }
        }
      } else {
        cadence.value = 0
      }
    }
  }, 1000)

  // 1.5 실시간 위치 공유 타이머 (5초마다 서버 전송으로 실시간성 강화)
  liveUpdateTimer.value = setInterval(() => {
    sendLiveLocation(true)
  }, 5000)

  // 2. 실제 GPS 위치 추적 및 거리 계산
  if (navigator.geolocation) {
    watchId = navigator.geolocation.watchPosition(
      (position) => {
        if (!isRunning.value) return // 일시정지 상태면 무시

        const { latitude, longitude, accuracy } = position.coords

        // GPS 정확도 필터링 강화 (30m 이상은 무시, 초기 50m 허용)
        const accuracyThreshold = currentPath.value.length < 5 ? 50 : 30
        if (accuracy && accuracy > accuracyThreshold) return

        const newPos = [latitude, longitude]

        if (currentPath.value.length > 0) {
          const lastPos = currentPath.value[currentPath.value.length - 1]
          
          // Leaflet의 distanceTo를 사용하여 실제 두 좌표 간의 거리(미터) 계산
          const p1 = L.latLng(lastPos[0], lastPos[1])
          const p2 = L.latLng(newPos[0], newPos[1])
          const distMeters = p1.distanceTo(p2)

          // 비정상적인 도약 방지 (GPS 튐 현상 제어)
          // 시간 간격(초) 계산
          const now = Date.now()
          const timeDelta = lastUpdateTime ? (now - lastUpdateTime) / 1000 : 1
          lastUpdateTime = now

          // 초당 12m(시속 43.2km) 이상 이동은 비정상으로 간주하여 무시
          if (timeDelta > 0 && distMeters > 12 * timeDelta) return 

          // 너무 작은 움직임(GPS 오차, 예: 3m 이하)은 무시
          if (distMeters > 3) {
            distance.value += distMeters / 1000 // km로 변환하여 누적
            currentPath.value.push(newPos)
            updateMap()

            // 구간 페이스 체크 (1km 마다)
            const currentKm = Math.floor(distance.value)
            if (currentKm > Math.floor(lastSplitDistance.value)) {
              const splitTimeSecs = elapsedTime.value - lastSplitTime.value
              const splitDist = distance.value - lastSplitDistance.value
              splits.value.push({
                km: currentKm, // 1, 2, 3...
                time: formatTimeFromSeconds(splitTimeSecs),
                pace: formatPaceFromSeconds(splitTimeSecs, splitDist)
              })
              lastSplitDistance.value = distance.value
              lastSplitTime.value = elapsedTime.value
            }
          }
        } else {
          currentPath.value.push(newPos)
          updateMap()
        }
      },
      (error) => {
        console.error('GPS 추적 에러:', error)
        if (error.code === 1) { // PERMISSION_DENIED
          alert('GPS 권한이 차단되었습니다. 아이폰 [설정] - [개인정보 보호] - [위치 서비스]에서 브라우저의 위치 권한을 허용해주세요.')
          pauseRunning()
        } else if (error.code === 3) { // TIMEOUT
          console.warn('GPS 신호가 약해 위치를 가져오는데 시간이 걸리고 있습니다.')
        }
      },
      {
        enableHighAccuracy: true, // 고정밀 GPS 사용
        maximumAge: 1000, // 캐시된 위치는 1초만 허용하여 최신 위치 강제
        timeout: 20000 // 타임아웃 20초로 넉넉하게
      }
    )
  }
}

const sendLiveLocation = async (isActive) => {
  if (!props.userId || !props.apiUrl || currentPath.value.length === 0) return
  
  const lastPos = currentPath.value[currentPath.value.length - 1]
  try {
    await fetch(`${props.apiUrl}/live/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: props.userId,
        latitude: lastPos[0],
        longitude: lastPos[1],
        distance: distance.value,
        pace: pace.value,
        time: formattedTime.value,
        path: currentPath.value,
        is_active: isActive
      })
    })
  } catch (e) {
    console.error('실시간 위치 전송 실패:', e)
  }
}

// 개발/테스트용 시뮬레이션 버튼 (선택사항)
const simulateRun = () => {
  if (!isRunning.value) startRunning()
  
  // 시뮬레이터: 강제로 5~10m씩 이동시킴
  if (currentPath.value.length > 0) {
    const lastPos = currentPath.value[currentPath.value.length - 1]
    const latOffset = (Math.random() - 0.2) * 0.0001
    const lngOffset = (Math.random() - 0.5) * 0.0001
    const newPos = [lastPos[0] + latOffset, lastPos[1] + lngOffset]
    
    const p1 = L.latLng(lastPos[0], lastPos[1])
    const p2 = L.latLng(newPos[0], newPos[1])
    distance.value += p1.distanceTo(p2) / 1000
    
    currentPath.value.push(newPos)
    updateMap()
  }
}

const updateMap = () => {
  if (!map || !polyline) return
  polyline.setLatLngs(currentPath.value)
  
  const currentPos = currentPath.value[currentPath.value.length - 1]
  if (userMarker) {
    userMarker.setLatLng(currentPos)
  }
  map.panTo(currentPos)
}

const initMap = () => {
  if (!mapContainer.value || map) return

  map = L.map(mapContainer.value, {
    zoomControl: false,
    attributionControl: false
  }).setView(startPosition.value, 16)

  L.tileLayer('https://xdworld.vworld.kr/2d/Base/service/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 6,
  }).addTo(map)

  polyline = L.polyline(currentPath.value, { color: '#ff8a3d', weight: 5, opacity: 0.8 }).addTo(map)

  const userIcon = L.divIcon({ 
    className: 'user-location-dot', 
    html: '<div class="pulse"></div>' 
  })
  userMarker = L.marker(startPosition.value, { icon: userIcon }).addTo(map)
  
  setTimeout(() => {
    if (map) map.invalidateSize()
  }, 300)
}

const pauseRunning = () => {
  if (isRunning.value) {
    const now = Date.now()
    accumulatedTime.value += Math.floor((now - lastStartTime.value) / 1000)
  }
  isRunning.value = false
  cadence.value = 0
  cadenceDistanceHistory.value = []
  if (timer.value) clearInterval(timer.value)
  if (watchId) {
    navigator.geolocation.clearWatch(watchId)
    watchId = null
  }
  if (liveUpdateTimer.value) {
    clearInterval(liveUpdateTimer.value)
    liveUpdateTimer.value = null
  }
}

const stopRunning = async () => {
  if (isRunning.value) {
    const now = Date.now()
    accumulatedTime.value += Math.floor((now - lastStartTime.value) / 1000)
    elapsedTime.value = accumulatedTime.value
  }
  isRunning.value = false
  cadenceDistanceHistory.value = []
  if (timer.value) {
    clearInterval(timer.value)
    timer.value = null
  }
  if (watchId) {
    navigator.geolocation.clearWatch(watchId)
    watchId = null
  }
  if (liveUpdateTimer.value) {
    clearInterval(liveUpdateTimer.value)
    liveUpdateTimer.value = null
  }
  
  // 실시간 공유 종료 서버 알림
  try {
    await sendLiveLocation(false)
  } catch (e) {
    console.error('공유 종료 알림 실패:', e)
  }
}

const saveRecord = async () => {
  if (isManualMode.value) {
    const record = {
      distance: Number(manualDistance.value).toFixed(2),
      time: manualTime.value,
      pace: calculatePace(manualDistance.value, manualTime.value),
      calories: Math.floor(manualDistance.value * 60), // 대략적 계산
      shoe_id: selectedShoe.value
    }
    emit('save-record', record)
    emit('back') // 직접 입력은 경로가 없으므로 바로 돌아감
    return
  }

  await stopRunning()
  
  if (currentPath.value.length > 0) {
    // 남은 거리가 있으면 마지막 구간도 추가
    const remainingDist = distance.value - lastSplitDistance.value
    if (remainingDist > 0.05) { // 50m 이상일 때만
      const splitTimeSecs = elapsedTime.value - lastSplitTime.value
      splits.value.push({
        km: Number(distance.value).toFixed(2), // 마지막 구간은 총 거리 표시 (e.g. 2.45)
        time: formatTimeFromSeconds(splitTimeSecs),
        pace: formatPaceFromSeconds(splitTimeSecs, remainingDist)
      })
    }

    const record = {
      distance: Number(distance.value.toFixed(2)),
      time: formattedTime.value,
      pace: pace.value,
      calories: calories.value,
      shoe_id: selectedShoe.value,
      cadence: cadence.value,
      splits: splits.value, // 구간 기록 포함
      path: currentPath.value // 경로 데이터 포함
    }
    
    // 추천 경로용 데이터 저장
    lastSavedPath.value = [...currentPath.value]
    lastSavedDistance.value = distance.value
    
    emit('save-record', record)
    
    // 기록 저장 후 추천 다이얼로그 표시 (움직임이 아주 조금이라도 있을 때)
    console.log('기록 저장 완료, 추천 다이얼로그 체크:', distance.value)
    if (distance.value > 0.01 || currentPath.value.length > 1) {
      showRecommendDialog.value = true
    } else {
      console.log('거리 부족으로 추천 건너뜀')
      emit('back')
    }
  } else {
    emit('back')
  }
}

const calculatePace = (dist, timeStr) => {
  if (!dist || dist <= 0) return "0'00\""
  const parts = timeStr.split(':').map(Number)
  const seconds = (parts[0] * 3600) + (parts[1] * 60) + parts[2]
  const paceSec = seconds / dist
  const min = Math.floor(paceSec / 60)
  const sec = Math.floor(paceSec % 60)
  return `${min}'${sec.toString().padStart(2, '0')}"`
}

const handleRecommendConfirm = (confirm) => {
  showRecommendDialog.value = false
  if (confirm) {
    emit('recommend-route', {
      path: lastSavedPath.value,
      distance: lastSavedDistance.value
    })
  } else {
    emit('back')
  }
}

onMounted(() => {
  // 마운트 시 바로 GPS 위치 시도
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition((pos) => {
      startPosition.value = [pos.coords.latitude, pos.coords.longitude]
      if (!map) initMap()
    }, (error) => {
      console.warn('마운트 시 초기 위치 획득 실패:', error)
    }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 })
  }
})


onUnmounted(() => {
  if (timer.value) clearInterval(timer.value)
  if (watchId) navigator.geolocation.clearWatch(watchId)
  if (map) {
    map.remove()
    map = null
  }
  releaseWakeLock()
})
</script>

<template>
  <div class="record-container animate-fade-in d-flex flex-column h-100">
    <div class="header d-flex align-center mb-4 shrink-0">
      <VBtn icon="mdi-chevron-left" variant="text" @click="emit('back')" />
      <h2 class="text-h6 font-weight-black ml-2">오늘의 러닝</h2>
    </div>

    <!-- Map or Manual Input section -->
    <div class="map-section rounded-xl overflow-hidden mb-4 border flex-grow-1" style="min-height: 250px; position: relative;">
      <template v-if="!isManualMode">
        <!-- Actual Leaflet Map -->
        <div ref="mapContainer" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 0;"></div>
      </template>
      
      <template v-else>
        <div class="manual-input-form fill-height pa-4 bg-grey-lighten-4 d-flex flex-column justify-center">
          <h3 class="text-subtitle-1 font-weight-bold mb-4 text-center">러닝 정보 직접 입력</h3>
          <VTextField
            v-model.number="manualDistance"
            label="러닝 거리 (km)"
            type="number"
            variant="outlined"
            rounded="xl"
            bg-color="white"
            class="mb-3"
            density="comfortable"
            prepend-inner-icon="mdi-map-marker-distance"
          />
          <VTextField
            v-model="manualTime"
            label="러닝 시간 (HH:MM:SS)"
            placeholder="00:00:00"
            variant="outlined"
            rounded="xl"
            bg-color="white"
            class="mb-3"
            density="comfortable"
            prepend-inner-icon="mdi-clock-outline"
          />
          <div class="text-center text-caption text-grey">
            입력하신 정보를 바탕으로 페이스와 칼로리가 계산됩니다.
          </div>
        </div>
      </template>
    </div>

    <div class="stats-card pa-4 rounded-xl text-center mb-4 shrink-0">
      <div class="text-caption text-grey-lighten-1 mb-2">총 주행 거리</div>
      <div class="text-h1 font-weight-black text-white mb-6">
        {{ distance.toFixed(2) }} <span class="text-h4">km</span>
      </div>

      <VRow>
        <VCol cols="4">
          <div class="text-caption text-grey-lighten-1">시간</div>
          <div class="text-h5 font-weight-bold text-white">{{ formattedTime }}</div>
        </VCol>
        <VCol cols="4">
          <div class="text-caption text-grey-lighten-1">페이스</div>
          <div class="text-h5 font-weight-bold text-white">{{ pace }}</div>
        </VCol>
        <VCol cols="4">
          <div class="text-caption text-grey-lighten-1">케이던스</div>
          <div class="text-h5 font-weight-bold text-white">{{ cadence }}</div>
        </VCol>
      </VRow>

      <!-- 주머니 모드 진입 버튼 -->
      <VBtn
        v-if="isRunning"
        variant="tonal"
        color="white"
        size="small"
        rounded="pill"
        class="mt-6 px-6"
        prepend-icon="mdi-lock-outline"
        @click="togglePocketMode"
      >
        주머니 모드 (화면 잠금)
      </VBtn>
    </div>

    <div class="controls d-flex flex-column align-center justify-center shrink-0 mb-6 mt-2">
      <!-- 1. 시작 전 상태 -->
      <template v-if="!isRunning && elapsedTime === 0">
        <VBtn
          color="primary"
          size="x-large"
          class="action-btn-large rounded-circle mb-2"
          icon="mdi-play"
          style="width: 80px; height: 80px; box-shadow: 0 10px 20px rgba(0,0,0,0.2) !important;"
          @click="isManualMode ? saveRecord() : startRunning()"
        />
        <VBtn
          variant="text"
          :color="isManualMode ? 'primary' : 'grey'"
          size="small"
          class="font-weight-bold"
          @click="isManualMode = !isManualMode"
        >
          <VIcon :icon="isManualMode ? 'mdi-run' : 'mdi-pencil-box-outline'" class="mr-1" />
          {{ isManualMode ? '실시간 트래킹 모드' : '기록 직접 입력하기' }}
        </VBtn>
      </template>
      
      <!-- 2. 실행 중 상태 (커다란 빨간색 일시정지 버튼) -->
      <VBtn
        v-else-if="isRunning"
        color="error"
        size="x-large"
        class="action-btn-large rounded-circle shadow-lg mb-2"
        icon="mdi-pause"
        style="box-shadow: 0 10px 20px rgba(231,76,60,0.4) !important;"
        @click="pauseRunning"
      />

      <!-- 3. 일시정지 상태 (다시 시작 및 최종 종료) -->
      <div v-else class="d-flex align-center gap-6 mb-2">
        <VBtn
          color="success"
          size="x-large"
          class="action-btn rounded-circle"
          icon="mdi-play"
          style="box-shadow: 0 10px 20px rgba(46,204,113,0.3) !important;"
          @click="startRunning"
        />
        <VBtn
          color="orange-darken-2"
          size="x-large"
          class="rounded-xl px-8"
          style="height: 64px; min-width: 140px; box-shadow: 0 10px 20px rgba(245,124,0,0.3) !important;"
          prepend-icon="mdi-stop"
          @click="saveRecord"
        >
          기록 종료
        </VBtn>
      </div>
    </div>

    <div class="additional-info mb-12">
      <VRow>
        <VCol cols="12">
          <VCard variant="tonal" class="rounded-lg pa-4 d-flex align-center">
            <VIcon icon="mdi-fire" color="orange" size="large" class="mr-4" />
            <div>
              <div class="text-caption text-grey">소모 칼로리</div>
              <div class="text-h6 font-weight-bold">{{ calories }} kcal</div>
            </div>
          </VCard>
        </VCol>
        <VCol cols="12">
          <VSelect
            v-model="selectedShoe"
            :items="shoes.filter(s => s.is_active)"
            item-title="name"
            item-value="id"
            label="신발 선택"
            placeholder="오늘 신은 신발을 골라주세요"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-shoe-run"
            class="rounded-lg"
            clearable
            :disabled="isRunning"
          >
            <template v-slot:item="{ props, item }">
              <VListItem v-bind="props" :subtitle="item.raw.brand + ' - ' + (item.raw.initial_km + item.raw.total_km).toFixed(1) + 'km'"></VListItem>
            </template>
          </VSelect>
        </VCol>
      </VRow>
    </div>
    
    <div class="text-center mt-6" v-if="isRunning">
      <p class="text-caption text-primary animate-pulse mb-2">실제 GPS를 기반으로 거리를 측정 중입니다!</p>
      
      <!-- 테스트 환경용 버튼: PC에서는 GPS 이동이 잡히지 않으므로 시뮬레이션용 버튼 제공 -->
      <VBtn 
        size="x-small" 
        variant="tonal" 
        color="grey" 
        @click="simulateRun"
      >
        [테스트] 강제 이동 (GPS 모의 테스트)
      </VBtn>
    </div>

    <!-- 추천 경로 추가 다이얼로그 -->
    <VDialog v-model="showRecommendDialog" max-width="400" persistent>
      <VCard class="rounded-xl pa-4">
        <VCardTitle class="text-h6 font-weight-black text-center">오늘 달린 코스가 좋았나요?</VCardTitle>
        <VCardText class="text-body-2 text-center text-grey">
          방금 달린 따끈따끈한 경로를<br>
          우리 동네 추천 코스 게시판에 공유할까요?
        </VCardText>
        <VCardActions class="justify-center mt-4">
          <VBtn color="grey" variant="text" @click="handleRecommendConfirm(false)">아니요</VBtn>
          <VBtn color="primary" variant="elevated" rounded="lg" class="px-6" @click="handleRecommendConfirm(true)">네, 공유할게요!</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- 주머니 모드 오버레이 (화면 동결 방지) -->
    <VOverlay
      v-model="isPocketMode"
      persistent
      class="align-center justify-center"
      scrim="#000"
      :opacity="1"
      style="z-index: 9999;"
    >
      <div class="pocket-mode-content text-center px-10" style="width: 100vw;">
        <div class="mb-8">
          <VIcon icon="mdi-lock" size="80" color="white" class="mb-4 opacity-20" />
          <h2 class="text-h4 text-white font-weight-black mb-2">주머니 모드</h2>
          <p class="text-body-2 text-grey-lighten-1">
            화면이 켜진 상태로 유지되어<br>
            기록 중단 없이 안전하게 추적합니다.
          </p>
        </div>

        <div class="stats-mini mb-12 py-4 border-y border-grey-darken-3">
          <div class="text-h3 text-white font-weight-black mb-1">{{ distance.toFixed(2) }} km</div>
          <div class="text-h6 text-primary">{{ formattedTime }}</div>
        </div>
        
        <div class="unlock-area">
          <p class="text-caption text-grey mb-4">해제하려면 오른쪽으로 끝까지 미세요</p>
          <div class="slider-wrapper bg-grey-darken-4 rounded-pill pa-2 d-flex align-center">
            <VSlider
              v-model="unlockValue"
              min="0"
              max="100"
              hide-details
              color="primary"
              track-color="transparent"
              class="unlock-slider flex-grow-1"
              @end="handleUnlock"
            >
              <template v-slot:prepend>
                <VAvatar color="primary" size="48">
                  <VIcon icon="mdi-chevron-right" color="white" />
                </VAvatar>
              </template>
            </VSlider>
          </div>
        </div>
      </div>
    </VOverlay>
  </div>
</template>

<style scoped>
.record-container {
  padding: 1.5rem;
  min-height: 100vh;
}
.unlock-slider :deep(.v-slider-thumb) {
  width: 56px;
  height: 56px;
}
.opacity-20 { opacity: 0.2; }
.border-y {
  border-top: 1px solid rgba(255,255,255,0.1);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.stats-card {
  background: linear-gradient(135deg, #1867c0 0%, #5CBBF6 100%);
  box-shadow: 0 15px 35px rgba(24, 103, 192, 0.3);
}

.action-btn {
  width: 64px !important;
  height: 64px !important;
}

.action-btn-large {
  width: 90px !important;
  height: 90px !important;
}

.gap-6 {
  gap: 24px;
}

.shadow-lg {
  box-shadow: 0 10px 25px rgba(231, 76, 60, 0.4) !important;
}

.animate-pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 0.5; }
  50% { opacity: 1; }
  100% { opacity: 0.5; }
}

:deep(.user-location-dot) {
  width: 20px !important;
  height: 20px !important;
  margin-left: -10px !important;
  margin-top: -10px !important;
}

:deep(.user-location-dot .pulse) {
  width: 14px;
  height: 14px;
  background: #228be6;
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 0 0 rgba(34, 139, 230, 0.4);
  animation: map-pulse 2s infinite;
}

@keyframes map-pulse {
  0% { box-shadow: 0 0 0 0 rgba(34, 139, 230, 0.7); }
  70% { box-shadow: 0 0 0 15px rgba(34, 139, 230, 0); }
  100% { box-shadow: 0 0 0 0 rgba(34, 139, 230, 0); }
}


</style>
