<script setup>
import { onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

/**
 * 🗺️ 리플렛(Leaflet) 기반 지도 컴포넌트
 * 별도의 API 키 없이 100% 무료로 사용할 수 있는 오픈소스 지도를 사용합니다.
 * 한국 사용자에게 친숙한 VWorld(브이월드) 타일을 적용했습니다.
 */

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'update:distance'])

const mapContainer = ref(null)
const isLoadingLocation = ref(false)
let map = null
let polyline = null
let markers = []
let userLocationMarker = null

/**
 * 지도 초기화
 */
const initMap = () => {
  if (!mapContainer.value) return

  // 기본 위치 설정 (서울시청 또는 첫 번째 좌표)
  const center = props.modelValue.length > 0 ? props.modelValue[0] : [37.5665, 126.9780]
  
  map = L.map(mapContainer.value, {
    zoomControl: !props.readOnly,
    attributionControl: false
  }).setView(center, 14)

  // 한국 국토교통부 제공 VWorld 타일 (한국 정서에 맞는 지도 스타일)
  // 별도 키 없이 개발용으로 사용 가능하며 한국어 라벨이 명확합니다.
  L.tileLayer('https://xdworld.vworld.kr/2d/Base/service/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 6,
    errorTileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png' // 실패 시 OSM으로 백업
  }).addTo(map)

  polyline = L.polyline(props.modelValue, { color: '#ff8a3d', weight: 5, opacity: 0.8 }).addTo(map)

  if (!props.readOnly) {
    map.on('click', (e) => {
      const newPath = [...props.modelValue, [e.latlng.lat, e.latlng.lng]]
      emit('update:modelValue', newPath)
      calculateDistance(newPath)
    })
    
    findMyLocation()
  }

  if (props.modelValue.length > 0) {
    updatePath(props.modelValue)
    if (props.readOnly) {
      setTimeout(fitFullCourse, 300)
    }
  }

  // 컴포넌트 렌더링/애니메이션 완료 후 지도 크기 재계산 (회색 타일 방지)
  setTimeout(() => {
    if (map) map.invalidateSize()
  }, 300)
}

/**
 * GPS 기능을 통한 현재 위치 탐색
 */
const findMyLocation = () => {
  if (!navigator.geolocation) return
  
  isLoadingLocation.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords
      const latlng = [latitude, longitude]
      
      if (map) {
        map.setView(latlng, 16)
        
        if (userLocationMarker) map.removeLayer(userLocationMarker)
        
        const userIcon = L.divIcon({ 
          className: 'user-location-dot', 
          html: '<div class="pulse"></div>' 
        })
        userLocationMarker = L.marker(latlng, { icon: userIcon }).addTo(map)
      }
      isLoadingLocation.value = false
    },
    (error) => {
      console.error('위치 권한 에러:', error)
      isLoadingLocation.value = false
    }
  )
}

/**
 * 경로 및 마커 업데이트
 */
const updatePath = (path) => {
  if (!polyline || !map) return
  
  polyline.setLatLngs(path)
  
  markers.forEach(m => map.removeLayer(m))
  markers = []

  if (path.length > 0) {
    const startIcon = L.divIcon({ className: 'map-dot start', html: '<div></div>' })
    markers.push(L.marker(path[0], { icon: startIcon }).addTo(map))

    if (path.length > 1) {
      const endIcon = L.divIcon({ className: 'map-dot end', html: '<div></div>' })
      markers.push(L.marker(path[path.length - 1], { icon: endIcon }).addTo(map))
    }
  }
}

/**
 * 경로 총 거리 계산
 */
const calculateDistance = (path) => {
  let distance = 0
  for (let i = 0; i < path.length - 1; i++) {
    const p1 = L.latLng(path[i])
    const p2 = L.latLng(path[i+1])
    distance += p1.distanceTo(p2)
  }
  emit('update:distance', (distance / 1000).toFixed(2))
}

/**
 * 초기화
 */
const clearPath = () => {
  emit('update:modelValue', [])
  emit('update:distance', 0)
}

/**
 * 코스 전체 보기
 */
const fitFullCourse = () => {
  if (polyline && polyline.getBounds().isValid()) {
    map.fitBounds(polyline.getBounds(), { padding: [40, 40] })
  }
}

watch(() => props.modelValue, (newPath) => {
  if (map) updatePath(newPath)
}, { deep: true })

onMounted(() => {
  initMap()
})
</script>

<template>
  <div class="map-wrapper">
    <div ref="mapContainer" class="map-container"></div>
    
    <div v-if="!readOnly" class="map-controls-bar d-flex align-center pa-2">
      <VBtn
        size="small"
        color="primary"
        variant="elevated"
        prepend-icon="mdi-map-marker"
        :loading="isLoadingLocation"
        @click="findMyLocation"
        class="mr-2"
        rounded="lg"
      >
        내 위치
      </VBtn>
      <VBtn
        size="small"
        color="error"
        variant="tonal"
        icon="mdi-trash-can-outline"
        @click="clearPath"
        rounded="lg"
      />
      <div class="ml-3 text-caption text-grey-darken-1 font-weight-bold">
        지도를 클릭해 경로를 그려보세요
      </div>
    </div>

    <div v-else-if="modelValue.length > 0" class="map-detail-controls">
      <VBtn
        size="small"
        color="white"
        variant="elevated"
        prepend-icon="mdi-arrow-expand-all"
        @click="fitFullCourse"
        class="font-weight-bold"
        rounded="lg"
      >
        전체 코스 보기
      </VBtn>
    </div>
  </div>
</template>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.map-container {
  width: 100%;
  height: 100%;
  z-index: 1;
  background: #f8f9fa;
}

.map-controls-bar {
  position: absolute;
  bottom: 12px;
  left: 12px;
  right: 12px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  border: 1px solid rgba(0,0,0,0.05);
}

.map-detail-controls {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 1000;
}

:deep(.map-dot) {
  width: 12px !important;
  height: 12px !important;
  margin-left: -6px !important;
  margin-top: -6px !important;
}

:deep(.map-dot div) {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

:deep(.map-dot.start div) { background: #4dabf7; }
:deep(.map-dot.end div) { background: #ff8a3d; }

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
  animation: pulse-animation 2s infinite;
}

@keyframes pulse-animation {
  0% { box-shadow: 0 0 0 0 rgba(34, 139, 230, 0.7); }
  70% { box-shadow: 0 0 0 15px rgba(34, 139, 230, 0); }
  100% { box-shadow: 0 0 0 0 rgba(34, 139, 230, 0); }
}
</style>
