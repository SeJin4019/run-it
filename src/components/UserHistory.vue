<script setup>
import { computed, ref } from 'vue'
import ShoeManagement from './ShoeManagement.vue'
import MapRoutePicker from './MapRoutePicker.vue'

const props = defineProps({
  user: Object,
  records: Array,
  shoes: {
    type: Array,
    default: () => []
  },
  isMe: {
    type: Boolean,
    default: true
  },
  isFriend: {
    type: Boolean,
    default: false
  },
  apiUrl: String
})

const emit = defineEmits(['logout', 'add-friend', 'remove-friend', 'recommend-route', 'delete-record'])

const stats = computed(() => {
  const totalKm = props.records.reduce((acc, rec) => acc + parseFloat(rec.distance), 0)
  const totalRuns = props.records.length
  return {
    totalKm: totalKm.toFixed(1),
    totalRuns,
    avgKm: totalRuns ? (totalKm / totalRuns).toFixed(1) : 0
  }
})

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}월 ${date.getDate()}일`
}

const selectedRecord = ref(null)
const showDetailDialog = ref(false)

const openRecordDetail = (record) => {
  selectedRecord.value = record
  showDetailDialog.value = true
}

const handleShareCourse = () => {
  if (selectedRecord.value && selectedRecord.value.path) {
    emit('recommend-route', {
      path: selectedRecord.value.path,
      distance: selectedRecord.value.distance
    })
    showDetailDialog.value = false
  }
}

const handleDeleteRecord = () => {
  if (confirm('정말로 이 기록을 삭제하시겠습니까? (관련 신발 마일리지도 함께 차감됩니다)')) {
    emit('delete-record', selectedRecord.value.id)
    showDetailDialog.value = false
  }
}

const getShoeName = (shoeId) => {
  if (!shoeId || !props.shoes) return '선택 안 함'
  const shoe = props.shoes.find(s => s.id === shoeId)
  return shoe ? `${shoe.brand} ${shoe.name}` : '알 수 없음'
}
</script>

<template>
  <div class="history-container animate-fade-in">
    <!-- 유저 프로필 섹션 -->
    <div class="profile-section d-flex align-center mb-8 pa-4 rounded-xl bg-white border">
      <VAvatar color="primary" size="64" class="mr-4">
        <span class="text-h5">{{ user.name[0] }}</span>
      </VAvatar>
      <div>
        <h3 class="text-h6 font-weight-black">{{ user.name }}님</h3>
        <p class="text-caption text-grey">{{ user.email }}</p>
      </div>
      <VSpacer />
      <VBtn v-if="isMe" variant="text" color="grey" icon="mdi-logout" @click="emit('logout')" />
      <template v-else>
        <VBtn 
          v-if="isFriend" 
          color="error" 
          variant="tonal" 
          size="small"
          @click="emit('remove-friend', user.id)"
        >친구 삭제</VBtn>
        <VBtn 
          v-else 
          color="primary" 
          variant="elevated" 
          size="small"
          @click="emit('add-friend', user.id)"
        >친구 추가</VBtn>
      </template>
    </div>

    <!-- 통계 요약 섹션 -->
    <VRow class="mb-8">
      <VCol cols="4">
        <VCard flat class="rounded-xl border text-center pa-4">
          <div class="text-caption text-grey mb-1">총 거리</div>
          <div class="text-h6 font-weight-black text-primary">{{ stats.totalKm }}km</div>
        </VCard>
      </VCol>
      <VCol cols="4">
        <VCard flat class="rounded-xl border text-center pa-4">
          <div class="text-caption text-grey mb-1">러닝 횟수</div>
          <div class="text-h6 font-weight-black text-primary">{{ stats.totalRuns }}회</div>
        </VCard>
      </VCol>
      <VCol cols="4">
        <VCard flat class="rounded-xl border text-center pa-4">
          <div class="text-caption text-grey mb-1">평균 거리</div>
          <div class="text-h6 font-weight-black text-primary">{{ stats.avgKm }}km</div>
        </VCard>
      </VCol>
    </VRow>

    <!-- 신발 관리 섹션 (내 정보 탭에 통합) -->
    <div v-if="isMe" class="shoes-section mb-8">
      <ShoeManagement 
        :user-id="user.id" 
        :api-url="apiUrl" 
      />
    </div>

    <!-- 활동 기록 리스트 -->
    <div class="section-header mb-4">
      <h3 class="text-h6 font-weight-bold">활동 기록</h3>
    </div>

    <div v-if="records.length === 0" class="text-center py-12 bg-white rounded-xl border">
      <VIcon icon="mdi-run" size="48" color="grey-lighten-2" class="mb-4" />
      <p class="text-body-2 text-grey">아직 기록된 러닝이 없습니다.<br>첫 번째 러닝을 시작해보세요!</p>
    </div>

    <div v-else class="record-list">
      <VCard
        v-for="record in records.slice().reverse()"
        :key="record.id"
        flat
        class="record-item rounded-xl border mb-3 pa-4"
        @click="openRecordDetail(record)"
      >
        <div class="d-flex justify-space-between align-center">
          <div>
            <div class="text-caption text-grey mb-1">{{ formatDate(record.date) }} 러닝</div>
            <div class="text-h6 font-weight-black">{{ Number(record.distance).toFixed(2) }} km</div>
          </div>
          <div class="text-right d-flex flex-column align-end">
            <div class="text-body-2 font-weight-bold text-primary mb-1">{{ record.pace }} / km</div>
            <VChip size="x-small" color="grey-lighten-3" class="text-grey-darken-2 px-2">상세보기 <VIcon icon="mdi-chevron-right" size="small" /></VChip>
          </div>
        </div>
      </VCard>
    </div>

    <!-- 상세 기록 팝업 다이얼로그 -->
    <VDialog v-model="showDetailDialog" max-width="500" v-if="selectedRecord">
      <VCard class="rounded-xl overflow-hidden bg-grey-lighten-4">
        <!-- 상단 헤더 영역 -->
        <VCardItem class="bg-primary text-white pa-4 pb-6">
          <div class="d-flex justify-space-between align-start mb-2">
            <div>
              <div class="text-caption opacity-80">{{ formatDate(selectedRecord.date) }} 러닝</div>
              <div class="text-h4 font-weight-black">{{ Number(selectedRecord.distance).toFixed(2) }} <span class="text-h6">km</span></div>
            </div>
            <VBtn icon="mdi-close" variant="text" color="white" @click="showDetailDialog = false" />
          </div>
        </VCardItem>

        <!-- 지도 영역 -->
        <div v-if="selectedRecord.path && selectedRecord.path.length > 0" class="map-container-wrapper bg-white">
          <MapRoutePicker :model-value="selectedRecord.path" :read-only="true" />
        </div>
        <div v-else class="pa-8 text-center bg-white text-grey">
          <VIcon icon="mdi-map-marker-off" size="48" class="mb-2 opacity-50" />
          <div class="text-caption">경로 데이터가 없는 기록입니다.</div>
        </div>

        <!-- 세부 정보 영역 -->
        <VCardText class="pa-4">
          <VRow>
            <VCol cols="6">
              <VCard flat class="pa-3 rounded-lg text-center bg-white">
                <div class="text-caption text-grey mb-1">시간</div>
                <div class="text-h6 font-weight-bold">{{ selectedRecord.time }}</div>
              </VCard>
            </VCol>
            <VCol cols="6">
              <VCard flat class="pa-3 rounded-lg text-center bg-white">
                <div class="text-caption text-grey mb-1">평균 페이스</div>
                <div class="text-h6 font-weight-bold">{{ selectedRecord.pace }}</div>
              </VCard>
            </VCol>
            <VCol cols="6">
              <VCard flat class="pa-3 rounded-lg text-center bg-white">
                <div class="text-caption text-grey mb-1">소모 칼로리</div>
                <div class="text-h6 font-weight-bold">{{ selectedRecord.calories || 0 }} kcal</div>
              </VCard>
            </VCol>
            <VCol cols="6">
              <VCard flat class="pa-3 rounded-lg text-center bg-white">
                <div class="text-caption text-grey mb-1">케이던스</div>
                <div class="text-h6 font-weight-bold">{{ selectedRecord.cadence || 0 }} spm</div>
              </VCard>
            </VCol>
            
            <VCol cols="12" class="pt-0">
              <VCard flat class="pa-3 rounded-lg bg-white d-flex align-center">
                <VAvatar color="primary-lighten-4" size="36" class="mr-3">
                  <VIcon icon="mdi-shoe-run" color="primary" />
                </VAvatar>
                <div>
                  <div class="text-caption text-grey">함께한 러닝화</div>
                  <div class="text-body-2 font-weight-bold">{{ getShoeName(selectedRecord.shoe_id) }}</div>
                </div>
              </VCard>
            </VCol>
          </VRow>

          <!-- 구간별 기록 표시 -->
          <div v-if="selectedRecord.splits && selectedRecord.splits.length > 0" class="mt-6 mb-2">
            <h4 class="text-subtitle-2 font-weight-bold mb-2">구간 페이스</h4>
            <VCard variant="outlined" class="rounded-lg bg-white overflow-hidden">
              <VTable density="compact">
                <thead>
                  <tr>
                    <th class="text-left text-caption font-weight-bold">구간</th>
                    <th class="text-left text-caption font-weight-bold">시간</th>
                    <th class="text-left text-caption font-weight-bold">페이스</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(split, idx) in selectedRecord.splits" :key="idx">
                    <td class="text-caption font-weight-bold">{{ split.km }} km</td>
                    <td class="text-caption text-grey-darken-1">{{ split.time }}</td>
                    <td class="text-caption font-weight-bold text-primary">{{ split.pace }}</td>
                  </tr>
                </tbody>
              </VTable>
            </VCard>
          </div>

          <!-- 공유 버튼 -->
          <VBtn 
            v-if="selectedRecord.path && selectedRecord.path.length > 0"
            color="primary" 
            variant="elevated" 
            block 
            class="mt-6 rounded-lg font-weight-bold" 
            size="large"
            prepend-icon="mdi-share-variant"
            @click="handleShareCourse"
          >
            이 기록을 추천 코스로 공유하기
          </VBtn>

          <!-- 삭제 버튼 -->
          <VBtn 
            v-if="isMe"
            color="error" 
            variant="text" 
            block 
            class="mt-2 rounded-lg font-weight-bold" 
            prepend-icon="mdi-delete"
            @click="handleDeleteRecord"
          >
            기록 삭제하기
          </VBtn>
        </VCardText>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
.history-container {
  padding: 1rem 0;
}

.record-item {
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.record-item:hover {
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}

.record-item:active {
  transform: scale(0.98);
}

.map-container-wrapper {
  height: 250px;
  width: 100%;
  position: relative;
  z-index: 1;
}
</style>
