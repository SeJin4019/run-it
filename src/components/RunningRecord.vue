<script setup>
import { ref, onUnmounted, computed, onMounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'


const props = defineProps({
  userId: Number,
  shoes: Array,
  apiUrl: String
})

const emit = defineEmits(['save-record', 'back'])

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
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        startPosition.value = [pos.coords.latitude, pos.coords.longitude]
        currentPath.value = [startPosition.value]
        initMap()
      }, () => {
        currentPath.value = [startPosition.value]
        initMap()
      })
    } else {
      currentPath.value = [startPosition.value]
      initMap()
    }
  }

  isRunning.value = true
  
  // 1. 시간 측정용 타이머
  timer.value = setInterval(() => {
    elapsedTime.value++
  }, 1000)

  // 1.5 실시간 위치 공유 타이머 (10초마다 서버 전송)
  liveUpdateTimer.value = setInterval(() => {
    sendLiveLocation(true)
  }, 10000)

  // 2. 실제 GPS 위치 추적 및 거리 계산
  if (navigator.geolocation) {
    watchId = navigator.geolocation.watchPosition(
      (position) => {
        if (!isRunning.value) return // 일시정지 상태면 무시

        const { latitude, longitude } = position.coords
        const newPos = [latitude, longitude]

        if (currentPath.value.length > 0) {
          const lastPos = currentPath.value[currentPath.value.length - 1]
          
          // Leaflet의 distanceTo를 사용하여 실제 두 좌표 간의 거리(미터) 계산
          const p1 = L.latLng(lastPos[0], lastPos[1])
          const p2 = L.latLng(newPos[0], newPos[1])
          const distMeters = p1.distanceTo(p2)

          // 너무 작은 움직임(GPS 오차, 예: 2m 이하)은 무시
          if (distMeters > 2) {
            distance.value += distMeters / 1000 // km로 변환하여 누적
            currentPath.value.push(newPos)
            updateMap()
          }
        } else {
          currentPath.value.push(newPos)
          updateMap()
        }
      },
      (error) => {
        console.error('GPS 추적 에러:', error)
      },
      {
        enableHighAccuracy: true, // 고정밀 GPS 사용
        maximumAge: 0,
        timeout: 5000
      }
    )
  }
}

const sendLiveLocation = async (isActive) => {
  if (!props.userId || !props.apiUrl || currentPath.value.length === 0) return
  
  const lastPos = currentPath.value[currentPath.value.length - 1]
  try {
    await fetch(`${props.apiUrl}/live/update?user_id=${props.userId}&lat=${lastPos[0]}&lng=${lastPos[1]}&is_active=${isActive}`, {
      method: 'POST'
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
}

const pauseRunning = () => {
  isRunning.value = false
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
  isRunning.value = false
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
  await stopRunning()
  
  if (currentPath.value.length > 0) {
    const record = {
      distance: distance.value,
      time: formattedTime.value,
      pace: pace.value,
      calories: calories.value,
      shoe_id: selectedShoe.value
    }
    emit('save-record', record)
    alert('러닝이 기록되었습니다!')
  }
  emit('back')
}


onUnmounted(() => {
  if (timer.value) clearInterval(timer.value)
  if (watchId) navigator.geolocation.clearWatch(watchId)
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div class="record-container animate-fade-in d-flex flex-column h-100">
    <div class="header d-flex align-center mb-4 shrink-0">
      <VBtn icon="mdi-chevron-left" variant="text" @click="emit('back')" />
      <h2 class="text-h6 font-weight-black ml-2">오늘의 러닝</h2>
    </div>

    <!-- Map container -->
    <div class="map-section rounded-xl overflow-hidden mb-4 border flex-grow-1" style="min-height: 250px; position: relative;">
      <!-- Placeholder -->
      <div v-if="!map && elapsedTime === 0" class="d-flex align-center justify-center bg-grey-lighten-3" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 1;">
        <div class="text-center text-grey">
          <VIcon icon="mdi-map-marker-radius" size="48" class="mb-2" />
          <p class="text-caption">시작 버튼을 누르면 지도가 표시됩니다.</p>
        </div>
      </div>
      <!-- Actual Leaflet Map -->
      <div ref="mapContainer" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 0;" v-show="map || elapsedTime > 0"></div>
    </div>

    <div class="stats-card pa-6 rounded-xl text-center mb-4 shrink-0">
      <div class="text-caption text-grey-lighten-1 mb-2">총 주행 거리</div>
      <div class="text-h1 font-weight-black text-white mb-6">
        {{ distance.toFixed(2) }} <span class="text-h4">km</span>
      </div>

      <VRow>
        <VCol cols="6">
          <div class="text-caption text-grey-lighten-1">시간</div>
          <div class="text-h5 font-weight-bold text-white">{{ formattedTime }}</div>
        </VCol>
        <VCol cols="6">
          <div class="text-caption text-grey-lighten-1">평균 페이스</div>
          <div class="text-h5 font-weight-bold text-white">{{ pace }}</div>
        </VCol>
      </VRow>
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

    <div class="controls d-flex justify-center align-center">
      <!-- 1. 시작 전 상태 -->
      <VBtn
        v-if="!isRunning && elapsedTime === 0"
        color="primary"
        size="x-large"
        class="action-btn-large rounded-circle"
        icon="mdi-play"
        @click="startRunning"
      />
      
      <!-- 2. 실행 중 상태 (커다란 빨간색 일시정지 버튼) -->
      <VBtn
        v-else-if="isRunning"
        color="error"
        size="x-large"
        class="action-btn-large rounded-circle shadow-lg"
        icon="mdi-pause"
        @click="pauseRunning"
      />

      <!-- 3. 일시정지 상태 (다시 시작 및 최종 종료) -->
      <div v-else class="d-flex align-center gap-6">
        <VBtn
          color="success"
          size="x-large"
          class="action-btn rounded-circle"
          icon="mdi-play"
          @click="startRunning"
        />
        <VBtn
          color="orange-darken-2"
          size="x-large"
          class="action-btn rounded-xl px-8"
          prepend-icon="mdi-stop"
          @click="saveRecord"
        >
          기록 종료
        </VBtn>
      </div>
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
  </div>
</template>

<style scoped>
.record-container {
  padding: 1.5rem;
  min-height: 80vh;
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
