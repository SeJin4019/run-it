<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentUser: Object,
  globalUsers: Array,
  globalRecords: Array
})

const emit = defineEmits(['open-profile'])

// 내 친구 목록
const myFriends = computed(() => {
  if (!props.currentUser || !props.currentUser.friends) return []
  return props.globalUsers.filter(u => props.currentUser.friends.includes(u.id))
})

// 추천 친구 (나와 내 친구를 제외한 나머지 사용자)
const recommendedFriends = computed(() => {
  if (!props.currentUser) return props.globalUsers
  const friendIds = props.currentUser.friends || []
  return props.globalUsers.filter(u => u.id !== props.currentUser.id && !friendIds.includes(u.id))
})

const getUserLatestRecord = (userId) => {
  const userRecords = props.globalRecords.filter(r => r.userId === userId)
  if (userRecords.length === 0) return null
  // 최신 기록 하나 반환 (가정: records는 추가된 순서)
  return userRecords[userRecords.length - 1]
}

</script>

<template>
  <div class="community-container animate-fade-in py-4">
    <div class="section-header mb-6">
      <h2 class="text-h5 font-weight-black">러닝 커뮤니티</h2>
      <p class="text-caption text-grey">친구들과 러닝 기록을 공유해보세요</p>
    </div>

    <!-- 내 친구 목록 -->
    <div class="mb-8">
      <h3 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
        <VIcon icon="mdi-account-multiple" class="mr-2" color="primary" /> 내 친구 ({{ myFriends.length }})
      </h3>
      
      <div v-if="myFriends.length === 0" class="text-center py-8 bg-white rounded-xl border">
        <VIcon icon="mdi-account-search" size="32" color="grey-lighten-2" class="mb-2" />
        <p class="text-caption text-grey">아직 친구가 없습니다.<br>추천 친구를 확인해보세요!</p>
      </div>

      <VCard
        v-for="friend in myFriends"
        :key="friend.id"
        flat
        class="friend-card rounded-xl border mb-3 pa-4 cursor-pointer"
        @click="emit('open-profile', friend)"
      >
        <div class="d-flex align-center">
          <VAvatar color="primary-lighten-1" size="48" class="mr-4">
            <span class="text-h6 text-white font-weight-bold">{{ friend.name[0] }}</span>
          </VAvatar>
          <div class="flex-grow-1">
            <div class="font-weight-bold">{{ friend.name }}</div>
            <div class="text-caption text-grey">
              <span v-if="getUserLatestRecord(friend.id)">
                최근 러닝: {{ getUserLatestRecord(friend.id).distance }}km ({{ getUserLatestRecord(friend.id).pace }})
              </span>
              <span v-else>최근 러닝 기록 없음</span>
            </div>
          </div>
          <VIcon icon="mdi-chevron-right" color="grey-lighten-1" />
        </div>
      </VCard>
    </div>

    <VDivider class="mb-8" />

    <!-- 추천 친구 목록 -->
    <div>
      <h3 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
        <VIcon icon="mdi-star-circle-outline" class="mr-2" color="warning" /> 추천 친구
      </h3>

      <div class="recommended-list d-flex overflow-x-auto pb-4 hide-scrollbar">
        <VCard
          v-for="user in recommendedFriends"
          :key="user.id"
          flat
          class="recommended-card rounded-xl border pa-4 mr-3 text-center flex-shrink-0 cursor-pointer"
          width="140"
          @click="emit('open-profile', user)"
        >
          <VAvatar color="grey-lighten-3" size="64" class="mb-3">
            <span class="text-h5 text-primary font-weight-bold">{{ user.name[0] }}</span>
          </VAvatar>
          <div class="font-weight-bold text-truncate mb-1">{{ user.name }}</div>
          <VBtn 
            size="small" 
            variant="tonal" 
            color="primary" 
            class="mt-2 rounded-lg"
            @click.stop="emit('open-profile', user)"
          >
            프로필 보기
          </VBtn>
        </VCard>

        <div v-if="recommendedFriends.length === 0" class="text-center py-6 px-4 text-caption text-grey">
          더 이상 추천할 친구가 없어요.
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.friend-card, .recommended-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.friend-card:active, .recommended-card:active {
  transform: scale(0.98);
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
