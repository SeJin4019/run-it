<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  currentUser: Object,
  globalUsers: Array,
  globalRecords: Array,
  liveFriends: Array,
  pendingRequests: Array
})

const emit = defineEmits(['open-profile', 'add-friend-by-email', 'accept-request', 'decline-request', 'open-live-map'])

const searchEmail = ref('')
const isAdding = ref(false)

const handleAddFriend = () => {
  if (!searchEmail.value) return
  emit('add-friend-by-email', searchEmail.value)
  searchEmail.value = ''
}

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
  return userRecords[userRecords.length - 1]
}

const getLiveStatus = (userId) => {
  return props.liveFriends.find(f => f.user_id === userId)
}

const isOnline = (user) => {
  if (!user.last_seen) return false
  const lastSeenStr = user.last_seen.endsWith('Z') ? user.last_seen : user.last_seen + 'Z'
  const lastSeen = new Date(lastSeenStr)
  const now = new Date()
  return (now - lastSeen) < 3 * 60 * 1000 // 3분 이내 접속
}

const openMap = (friend) => {
  const status = getLiveStatus(friend.id)
  if (status) {
    emit('open-live-map', status)
  }
}

</script>

<template>
  <div class="community-container animate-fade-in py-4">
    <div class="section-header mb-6">
      <h2 class="text-h5 font-weight-black">러닝 커뮤니티</h2>
      <p class="text-caption text-grey">친구들과 러닝 기록을 공유해보세요</p>
    </div>

    <!-- 친구 추가 검색창 -->
    <div class="mb-8">
      <VTextField
        v-model="searchEmail"
        label="친구 이메일로 찾기"
        placeholder="friend@example.com"
        variant="outlined"
        rounded="xl"
        density="comfortable"
        hide-details
        prepend-inner-icon="mdi-account-search"
        @keyup.enter="handleAddFriend"
      >
        <template v-slot:append-inner>
          <VBtn 
            color="primary" 
            variant="flat" 
            size="small" 
            rounded="lg" 
            class="px-4"
            @click="handleAddFriend"
          >
            추가
          </VBtn>
        </template>
      </VTextField>
    </div>

    <!-- 친구 요청 목록 (받은 요청이 있을 때만 표시) -->
    <div v-if="pendingRequests && pendingRequests.length > 0" class="mb-8">
      <h3 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center text-primary">
        <VIcon icon="mdi-account-alert" class="mr-2" /> 받은 친구 요청 ({{ pendingRequests.length }})
      </h3>
      <VCard
        v-for="req in pendingRequests"
        :key="req.request_id"
        flat
        class="rounded-xl border pa-4 mb-3"
      >
        <div class="d-flex align-center">
          <VAvatar :color="req.from_user_profile_image ? 'transparent' : 'primary-lighten-4'" size="40" class="mr-3">
            <img v-if="req.from_user_profile_image" :src="req.from_user_profile_image" alt="Profile" style="width:100%; height:100%; object-fit:cover;">
            <span v-else class="text-caption font-weight-bold">{{ req.from_user_name[0] }}</span>
          </VAvatar>
          <div class="flex-grow-1">
            <div class="font-weight-bold">{{ req.from_user_name }}</div>
            <div class="text-caption text-grey">{{ req.from_user_email }}</div>
          </div>
          <div class="d-flex gap-2">
            <VBtn 
              size="small" 
              color="primary" 
              variant="flat" 
              rounded="lg"
              @click="emit('accept-request', req.request_id)"
            >
              수락
            </VBtn>
            <VBtn 
              size="small" 
              color="grey" 
              variant="tonal" 
              rounded="lg"
              @click="emit('decline-request', req.request_id)"
            >
              거절
            </VBtn>
          </div>
        </div>
      </VCard>
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
          <VBadge
            :model-value="isOnline(friend)"
            dot
            color="success"
            location="bottom right"
            offset-x="2"
            offset-y="2"
          >
            <VAvatar :color="friend.profile_image ? 'transparent' : 'primary-lighten-1'" size="48" class="mr-4">
              <img v-if="friend.profile_image" :src="friend.profile_image" alt="Profile" style="width:100%; height:100%; object-fit:cover;">
              <span v-else class="text-h6 text-white font-weight-bold">{{ friend.name[0] }}</span>
            </VAvatar>
          </VBadge>
          <div class="flex-grow-1">
            <div class="d-flex align-center">
              <div class="font-weight-bold">{{ friend.name }}</div>
              <VChip v-if="getLiveStatus(friend.id)" color="error" size="x-small" class="ml-2 animate-pulse" variant="flat">
                LIVE
              </VChip>
            </div>
            <div class="text-caption text-grey">
              <span v-if="getLiveStatus(friend.id)" class="text-error font-weight-bold">
                🔥 지금 달리는 중!
              </span>
              <span v-else-if="getUserLatestRecord(friend.id)">
                최근 러닝: {{ getUserLatestRecord(friend.id).distance }}km ({{ getUserLatestRecord(friend.id).pace }})
              </span>
              <span v-else>최근 러닝 기록 없음</span>
            </div>
          </div>
          <VBtn 
            v-if="getLiveStatus(friend.id)" 
            icon="mdi-map-marker" 
            variant="text" 
            color="error" 
            size="small" 
            @click.stop="openMap(friend)" 
          />
          <VIcon v-else icon="mdi-chevron-right" color="grey-lighten-1" />
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
          <VBadge
            :model-value="isOnline(user)"
            dot
            color="success"
            location="bottom right"
            offset-x="4"
            offset-y="4"
          >
            <VAvatar :color="user.profile_image ? 'transparent' : 'grey-lighten-3'" size="64" class="mb-3">
              <img v-if="user.profile_image" :src="user.profile_image" alt="Profile" style="width:100%; height:100%; object-fit:cover;">
              <span v-else class="text-h5 text-primary font-weight-bold">{{ user.name[0] }}</span>
            </VAvatar>
          </VBadge>
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
.animate-pulse {
  animation: pulse-red 1.5s infinite;
}

@keyframes pulse-red {
  0% { opacity: 0.7; transform: scale(0.95); }
  50% { opacity: 1; transform: scale(1); }
  100% { opacity: 0.7; transform: scale(0.95); }
}
</style>
