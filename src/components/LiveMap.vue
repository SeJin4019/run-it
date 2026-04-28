<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  friend: {
    type: Object,
    required: true
  }
})

const mapContainer = ref(null)
let map = null
let polyline = null
let marker = null

const initMap = () => {
  if (!mapContainer.value || map) return

  const initialPos = props.friend.path && props.friend.path.length > 0 
    ? props.friend.path[props.friend.path.length - 1] 
    : [props.friend.latitude, props.friend.longitude]

  map = L.map(mapContainer.value, {
    zoomControl: false,
    attributionControl: false
  }).setView(initialPos, 15)

  L.tileLayer('https://xdworld.vworld.kr/2d/Base/service/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 6,
  }).addTo(map)

  const path = props.friend.path || [[props.friend.latitude, props.friend.longitude]]
  polyline = L.polyline(path, { color: '#ff4b2b', weight: 5, opacity: 0.8 }).addTo(map)

  const userIcon = L.divIcon({ 
    className: 'live-location-dot', 
    html: '<div class="pulse"></div>' 
  })
  marker = L.marker(initialPos, { icon: userIcon }).addTo(map)
}

const updateMap = () => {
  if (!map || !props.friend) return
  
  const path = props.friend.path || [[props.friend.latitude, props.friend.longitude]]
  const currentPos = [props.friend.latitude, props.friend.longitude]

  if (polyline) polyline.setLatLngs(path)
  if (marker) marker.setLatLng(currentPos)
  
  map.panTo(currentPos)
}

watch(() => props.friend, () => {
  updateMap()
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
  height: 400px;
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

@keyframes live-pulse {
  0% { box-shadow: 0 0 0 0 rgba(255, 75, 43, 0.7); }
  70% { box-shadow: 0 0 0 15px rgba(255, 75, 43, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 75, 43, 0); }
}
</style>
