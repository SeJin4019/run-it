<script setup>
import { computed } from 'vue'
import ShoeManagement from './ShoeManagement.vue'

const props = defineProps({
  user: Object,
  records: Array,
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

const emit = defineEmits(['logout', 'add-friend', 'remove-friend'])

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
      >
        <div class="d-flex justify-space-between align-center">
          <div>
            <div class="text-caption text-grey mb-1">{{ formatDate(record.date) }} 러닝</div>
            <div class="text-h6 font-weight-black">{{ record.distance }} km</div>
          </div>
          <div class="text-right">
            <div class="text-body-2 font-weight-bold text-primary">{{ record.pace }}</div>
            <div class="text-caption text-grey">{{ record.time }}</div>
          </div>
        </div>
      </VCard>
    </div>
  </div>
</template>

<style scoped>
.history-container {
  padding: 1rem 0;
}

.record-item {
  transition: transform 0.2s;
}

.record-item:active {
  transform: scale(0.98);
}
</style>
