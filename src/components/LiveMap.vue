<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  members: {
    type: Array,
    default: () => []
  }
})

const mapContainer = ref(null)
let map = null
const memberLayers = {} // { userId: { marker, polyline } }

const initMap = () => {
  if (!mapContainer.value || map) return

  // 기본 위치 (첫 번째 멤버 혹은 서울)
  const initialPos = props.members.length > 0 
    ? [props.members[0].latitude, props.members[0].longitude]
    : [37.5665, 126.9780]

  map = L.map(mapContainer.value, {
    zoomControl: false,
    attributionControl: false
  }).setView(initialPos, 16)

  L.tileLayer('https://xdworld.vworld.kr/2d/Base/service/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 6,
  }).addTo(map)

  updateMarkers()
  
  setTimeout(() => {
    if (map) map.invalidateSize()
  }, 300)
}

const updateMarkers = () => {
  if (!map) return

  // 현재 활성화된 멤버 ID 목록
  const activeIds = new Set(props.members.map(m => m.user_id))

  // 사라진 멤버 레이어 제거
  Object.keys(memberLayers).forEach(userId => {
    if (!activeIds.has(Number(userId))) {
      map.removeLayer(memberLayers[userId].marker)
      map.removeLayer(memberLayers[userId].polyline)
      delete memberLayers[userId]
    }
  })

  // 멤버별 마커 및 경로 업데이트
  props.members.forEach(member => {
    const userId = member.user_id
    const currentPos = [member.latitude, member.longitude]
    const path = member.path || [currentPos]

    if (memberLayers[userId]) {
      // 기존 레이어 업데이트
      memberLayers[userId].marker.setLatLng(currentPos)
      memberLayers[userId].polyline.setLatLngs(path)
    } else {
      // 새 레이어 생성
      const poly = L.polyline(path, { color: '#ff4b2b', weight: 4, opacity: 0.6 }).addTo(map)
      
      const userIcon = L.divIcon({ 
        className: 'live-location-dot', 
        html: `<div class="pulse"></div><div class="member-name">${member.name}</div>` 
      })
      const mark = L.marker(currentPos, { icon: userIcon }).addTo(map)
      
      memberLayers[userId] = { marker: mark, polyline: poly }
    }
  })

  // 위치가 하나만 있으면 거기로 팬, 여러 명이면 범위 맞추기
  if (props.members.length === 1) {
    map.panTo([props.members[0].latitude, props.members[0].longitude])
  } else if (props.members.length > 1) {
    const bounds = L.latLngBounds(props.members.map(m => [m.latitude, m.longitude]))
    map.fitBounds(bounds, { padding: [50, 50] })
  }
}

watch(() => props.members, () => {
  updateMarkers()
}, { deep: true })

onMounted(() => {
  initMap()
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div class="live-map-wrapper">
    <div ref="mapContainer" class="map-view"></div>
  </div>
</template>

<style scoped>
.live-map-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.map-view {
  width: 100%;
  height: 100%;
}

:deep(.live-location-dot) {
  width: 20px !important;
  height: 20px !important;
  margin-left: -10px !important;
  margin-top: -10px !important;
}

:deep(.live-location-dot .pulse) {
  width: 14px;
  height: 14px;
  background: #ff4b2b;
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 0 0 rgba(255, 75, 43, 0.4);
  animation: live-pulse 2s infinite;
}

:deep(.member-name) {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: bold;
  white-space: nowrap;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  border: 1px solid #ff4b2b;
  color: #ff4b2b;
}

@keyframes live-pulse {
  0% { box-shadow: 0 0 0 0 rgba(255, 75, 43, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(255, 75, 43, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 75, 43, 0); }
}
</style>
