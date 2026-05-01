<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  currentUser: Object,
  apiUrl: String
})

const emit = defineEmits(['open-crew-map', 'refresh'])

const crews = ref([])
const searchQuery = ref('')
const selectedCrew = ref(null)
const showDetailDialog = ref(false)
const showCreateDialog = ref(false)

const filteredCrews = computed(() => {
  if (!searchQuery.value) return crews.value
  const q = searchQuery.value.toLowerCase()
  return crews.value.filter(c => 
    c.name.toLowerCase().includes(q) || 
    c.description.toLowerCase().includes(q)
  )
})

const myCrews = computed(() => {
  if (!props.currentUser) return []
  return filteredCrews.value.filter(c => c.members.some(m => m.user_id === props.currentUser.id))
})

const otherCrews = computed(() => {
  if (!props.currentUser) return filteredCrews.value
  return filteredCrews.value.filter(c => !c.members.some(m => m.user_id === props.currentUser.id))
})

const fetchCrews = async () => {
  try {
    const res = await fetch(`${props.apiUrl}/crews`)
    if (res.ok) {
      crews.value = await res.json()
      // 만약 상세 다이얼로그가 열려있다면 데이터 갱신
      if (selectedCrew.value) {
        const updated = crews.value.find(c => c.id === selectedCrew.value.id)
        if (updated) selectedCrew.value = updated
      }
    }
  } catch (e) {
    console.error('크루 목록 로딩 실패:', e)
  }
}

const openCrewDetail = (crew) => {
  selectedCrew.value = crew
  showDetailDialog.value = true
}

const isMember = (crew) => {
  if (!props.currentUser || !crew) return false
  return crew.members.some(m => m.user_id === props.currentUser.id)
}

const joinCrew = async (crewId) => {
  if (!props.currentUser) return
  try {
    const res = await fetch(`${props.apiUrl}/crews/${crewId}/join?user_id=${props.currentUser.id}`, {
      method: 'POST'
    })
    if (res.ok) {
      const data = await res.json()
      alert(data.message)
      fetchCrews()
    } else {
      const data = await res.json()
      alert(data.detail || '가입 실패')
    }
  } catch (e) {
    console.error('크루 가입 실패:', e)
  }
}

const leaveCrew = async (crewId) => {
  if (!props.currentUser) return
  if (!confirm('정말 크루에서 탈퇴하시겠습니까?')) return
  try {
    const res = await fetch(`${props.apiUrl}/crews/${crewId}/leave?user_id=${props.currentUser.id}`, {
      method: 'POST'
    })
    if (res.ok) {
      showDetailDialog.value = false
      fetchCrews()
    }
  } catch (e) {
    console.error('크루 탈퇴 실패:', e)
  }
}

const approveMember = async (crewId, memberId) => {
  try {
    const res = await fetch(`${props.apiUrl}/crews/${crewId}/approve/${memberId}?leader_id=${props.currentUser.id}`, {
      method: 'POST'
    })
    if (res.ok) {
      fetchCrews()
    }
  } catch (e) {
    console.error('가입 승인 실패:', e)
  }
}

const kickMember = async (crewId, memberId) => {
  if (!confirm('정말 이 멤버를 내보내시겠습니까?')) return
  try {
    const res = await fetch(`${props.apiUrl}/crews/${crewId}/kick/${memberId}?leader_id=${props.currentUser.id}`, {
      method: 'POST'
    })
    if (res.ok) {
      fetchCrews()
    }
  } catch (e) {
    console.error('멤버 추방 실패:', e)
  }
}

const newCrew = ref({
  name: '',
  description: ''
})

const preset_images = [
  "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?w=500&q=80",
  "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?w=500&q=80",
  "https://images.unsplash.com/photo-1447452030438-65c287a73e4b?w=500&q=80",
  "https://images.unsplash.com/photo-1513594335400-9482457ad9aa?w=500&q=80",
  "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=500&q=80"
]

const createCrew = async () => {
  if (!newCrew.value.name) return
  try {
    const res = await fetch(`${props.apiUrl}/crews?user_id=${props.currentUser.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newCrew.value)
    })
    if (res.ok) {
      showCreateDialog.value = false
      newCrew.value = { name: '', description: '', image: preset_images[0] }
      fetchCrews()
    }
  } catch (e) {
    console.error('크루 생성 실패:', e)
  }
}

const deleteCrew = async (crewId) => {
  if (!confirm('정말 크루를 삭제하시겠습니까? 모든 정보와 멤버 기록이 사라집니다.')) return
  try {
    const res = await fetch(`${props.apiUrl}/crews/${crewId}?user_id=${props.currentUser.id}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      showDetailDialog.value = false
      fetchCrews()
    }
  } catch (e) {
    console.error('크루 삭제 실패:', e)
  }
}
const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getFullYear()}.${date.getMonth() + 1}.${date.getDate()}`
}

onMounted(fetchCrews)

</script>

<template>
  <div class="crew-container animate-fade-in py-4">
    <!-- 헤더 섹션 -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h2 class="text-h5 font-weight-black text-primary">러닝 크루 🤝</h2>
        <p class="text-caption text-grey">함께 달리면 즐거움이 두 배가 됩니다</p>
      </div>
      <VBtn 
        color="primary" 
        prepend-icon="mdi-plus" 
        rounded="xl" 
        variant="elevated"
        elevation="4"
        @click="showCreateDialog = true"
      >크루 만들기</VBtn>
    </div>

    <!-- 검색 바 -->
    <VTextField
      v-model="searchQuery"
      placeholder="크루 이름 또는 설명으로 검색"
      variant="outlined"
      rounded="xl"
      density="comfortable"
      hide-details
      prepend-inner-icon="mdi-magnify"
      class="mb-8 bg-white"
    />

    <!-- 내 크루 섹션 -->
    <div class="mb-10" v-if="myCrews.length > 0">
      <h3 class="text-subtitle-1 font-weight-bold mb-4 d-flex align-center">
        <VIcon icon="mdi-star" class="mr-2" color="warning" /> 내가 활동 중인 크루
      </h3>
      <VRow>
        <VCol v-for="crew in myCrews" :key="crew.id" cols="12" sm="6">
          <VCard flat class="crew-card active-crew rounded-xl border pa-4 overflow-hidden shadow-sm" @click="openCrewDetail(crew)">
            <div class="d-flex align-start">
              <VAvatar color="primary-lighten-5" size="64" rounded="lg" class="mr-4 border">
                <VIcon icon="mdi-account-group" color="primary" size="32" />
              </VAvatar>
              <div class="flex-grow-1">
                <div class="d-flex align-center justify-space-between mb-1">
                  <h4 class="text-h6 font-weight-bold text-truncate">{{ crew.name }}</h4>
                  <VChip size="x-small" color="primary" variant="flat" class="font-weight-bold">{{ crew.member_count }}명</VChip>
                </div>
                <p class="text-caption text-grey line-clamp-1 mb-3">{{ crew.description }}</p>
                <VBtn 
                  block
                  color="error" 
                  variant="flat" 
                  rounded="lg" 
                  size="small" 
                  prepend-icon="mdi-map-marker-radius"
                  class="font-weight-bold"
                  @click.stop="emit('open-crew-map', crew)"
                >실시간 위치 보기</VBtn>
              </div>
            </div>
          </VCard>
        </VCol>
      </VRow>
    </div>

    <VDivider class="mb-10" v-if="myCrews.length > 0" />

    <!-- 탐색 섹션 -->
    <div class="exploration-section px-1">
      <div class="exploration-header pa-4 rounded-xl mb-6 text-white position-relative overflow-hidden">
        <div class="header-overlay-dark"></div>
        <div class="position-relative d-flex align-center" style="z-index: 1;">
          <div class="exploration-icon-box mr-4">
            <VIcon icon="mdi-compass-outline" color="white" size="24" />
          </div>
          <div>
            <h3 class="text-h6 font-weight-black">지구촌 러닝 크루 탐색 🌍</h3>
            <p class="text-caption opacity-90">당신에게 딱 맞는 러닝 메이트와 함께 달리세요</p>
          </div>
        </div>
      </div>
      <VRow>
        <VCol v-for="crew in otherCrews" :key="crew.id" cols="12" sm="6" md="4">
          <VCard flat class="crew-card rounded-xl border pa-4 h-100 shadow-sm" @click="openCrewDetail(crew)">
            <div class="d-flex align-center mb-3">
              <VAvatar color="grey-lighten-4" size="52" rounded="lg" class="mr-3 overflow-hidden">
                <img v-if="crew.image" :src="crew.image" alt="Crew" style="width:100%; height:100%; object-fit:cover;">
                <VIcon v-else icon="mdi-account-group-outline" color="grey" />
              </VAvatar>
              <div class="overflow-hidden">
                <div class="font-weight-bold text-truncate">{{ crew.name }}</div>
                <div class="text-caption text-grey">{{ crew.member_count }}명의 멤버</div>
              </div>
            </div>
            <p class="text-body-2 text-grey mb-4 line-clamp-2 h-40">{{ crew.description }}</p>
            <VBtn 
              block 
              color="primary" 
              variant="tonal" 
              rounded="lg" 
              size="small"
              class="font-weight-bold"
            >상세보기</VBtn>
          </VCard>
        </VCol>
      </VRow>
      
      <div v-if="filteredCrews.length === 0" class="text-center py-16 bg-grey-lighten-5 rounded-xl border-dashed">
        <VIcon icon="mdi-account-group-outline" size="64" color="grey-lighten-2" class="mb-4" />
        <p class="text-body-1 text-grey-darken-1 font-weight-bold">찾으시는 크루가 없나요?</p>
        <p class="text-caption text-grey mb-6">직접 새로운 크루를 만들어 멤버를 모집해보세요!</p>
        <VBtn color="primary" variant="flat" rounded="xl" @click="showCreateDialog = true">첫 크루 만들기</VBtn>
      </div>
    </div>

    <!-- 크루 상세 다이얼로그 -->
    <VDialog v-model="showDetailDialog" max-width="500" scrollable transition="dialog-bottom-transition">
      <VCard class="rounded-xl" v-if="selectedCrew" style="max-height: 90vh; display: flex; flex-direction: column;">
        <div class="crew-detail-header pa-6 bg-primary text-white position-relative overflow-hidden shrink-0">
          <!-- 헤더 배경 이미지 (있을 경우) -->
          <div v-if="selectedCrew.image" class="header-bg-image" :style="{ backgroundImage: `url(${selectedCrew.image})` }"></div>
          <div class="header-overlay"></div>

          <VBtn icon="mdi-close" variant="text" color="white" class="position-absolute" style="top: 10px; right: 10px; z-index: 2;" @click="showDetailDialog = false" />
          
          <div class="position-relative" style="z-index: 1;">
            <div class="d-flex align-center mb-4">
              <VAvatar color="white" size="72" rounded="lg" class="mr-4 shadow-lg overflow-hidden">
                <img v-if="selectedCrew.image" :src="selectedCrew.image" alt="Crew" style="width:100%; height:100%; object-fit:cover;">
                <VIcon v-else icon="mdi-account-group" color="primary" size="40" />
              </VAvatar>
              <div>
                <h3 class="text-h5 font-weight-black">{{ selectedCrew.name }}</h3>
                <div class="text-caption opacity-90">생성일: {{ formatDate(selectedCrew.created_at) }}</div>
              </div>
            </div>
            <div class="d-flex gap-2">
              <VChip size="small" color="white" variant="flat" class="text-primary font-weight-bold">{{ selectedCrew.member_count }}명 참여 중</VChip>
            </div>
          </div>
        </div>


        <VCardText class="pa-6">
          <!-- 가입 신청 대기 목록 (리더 전용) -->
          <div v-if="selectedCrew.leader_id === currentUser?.id && selectedCrew.pending_members?.length > 0" class="mb-8">
            <h4 class="text-subtitle-1 font-weight-bold mb-4 d-flex align-center text-primary">
              <VIcon icon="mdi-account-clock" class="mr-2" /> 가입 신청 대기 ({{ selectedCrew.pending_members.length }})
            </h4>
            <div v-for="pending in selectedCrew.pending_members" :key="pending.user_id" class="d-flex align-center mb-3 pa-3 rounded-xl bg-primary-lighten-5 border">
              <VAvatar size="36" class="mr-3">
                <img v-if="pending.profile_image" :src="pending.profile_image" style="width:100%; height:100%; object-fit:cover;">
                <VIcon v-else icon="mdi-account" color="primary" />
              </VAvatar>
              <div class="flex-grow-1 overflow-hidden">
                <div class="text-body-2 font-weight-bold text-truncate">{{ pending.name }}</div>
              </div>
              <div class="d-flex gap-1">
                <VBtn size="x-small" color="primary" variant="flat" rounded="lg" @click="approveMember(selectedCrew.id, pending.user_id)">승인</VBtn>
                <VBtn size="x-small" color="grey" variant="tonal" rounded="lg" @click="kickMember(selectedCrew.id, pending.user_id)">거절</VBtn>
              </div>
            </div>
            <VDivider class="mt-4" />
          </div>

          <div class="mb-8">
            <h4 class="text-subtitle-1 font-weight-bold mb-2">크루 소개</h4>
            <p class="text-body-2 text-grey-darken-2" style="line-height: 1.6">{{ selectedCrew.description }}</p>
          </div>

          <div>
            <h4 class="text-subtitle-1 font-weight-bold mb-4 d-flex align-center justify-space-between">
              멤버 목록
              <span class="text-caption text-grey font-weight-medium">최근 가입순</span>
            </h4>
            <div class="member-list">
              <div v-for="member in selectedCrew.members" :key="member.user_id" class="d-flex align-center mb-3 pa-2 rounded-lg bg-grey-lighten-5">
                <VAvatar :color="member.profile_image ? 'transparent' : 'primary-lighten-4'" size="40" class="mr-3">
                  <img v-if="member.profile_image" :src="member.profile_image" alt="Member" style="width:100%; height:100%; object-fit:cover;">
                  <span v-else class="text-caption font-weight-bold">{{ member.name[0] }}</span>
                </VAvatar>
                <div class="flex-grow-1">
                  <div class="d-flex align-center">
                    <div class="text-body-2 font-weight-bold">{{ member.name }}</div>
                    <VChip v-if="member.user_id === selectedCrew.leader_id" size="x-small" color="warning" class="ml-2 px-2" variant="flat">
                      <VIcon icon="mdi-crown" size="10" class="mr-1" /> 크루장
                    </VChip>
                  </div>
                  <div class="text-caption text-grey">{{ formatDate(member.joined_at) }} 가입</div>
                </div>
                <div class="d-flex align-center">
                  <VIcon v-if="member.user_id === currentUser?.id" icon="mdi-check-circle" color="primary" size="20" class="mr-1" />
                  <VBtn 
                    v-if="selectedCrew.leader_id === currentUser?.id && member.user_id !== currentUser?.id" 
                    icon="mdi-account-remove" 
                    variant="text" 
                    color="grey-lighten-1" 
                    size="x-small" 
                    @click.stop="kickMember(selectedCrew.id, member.user_id)" 
                  />
                </div>
              </div>
            </div>
          </div>
        </VCardText>

        <VCardActions class="pa-6 pt-0 d-flex flex-column gap-2 shrink-0">
          <template v-if="isMember(selectedCrew)">
            <VBtn 
              block 
              color="error" 
              variant="flat" 
              rounded="xl" 
              size="large" 
              prepend-icon="mdi-map-marker-radius"
              class="font-weight-bold mb-2"
              @click="emit('open-crew-map', selectedCrew); showDetailDialog = false"
            >실시간 크루 위치 보기</VBtn>
            
            <VBtn 
              v-if="selectedCrew.leader_id === currentUser?.id"
              block 
              color="error" 
              variant="tonal" 
              rounded="xl"
              class="font-weight-bold"
              @click="deleteCrew(selectedCrew.id)"
            >크루 삭제하기 (크루장)</VBtn>
            
            <VBtn 
              v-else
              block 
              color="grey" 
              variant="tonal" 
              rounded="xl"
              class="font-weight-bold"
              @click="leaveCrew(selectedCrew.id)"
            >크루 탈퇴하기</VBtn>
          </template>
          
          <VBtn 
            v-else
            block 
            color="primary" 
            variant="flat" 
            rounded="xl" 
            size="large"
            class="font-weight-bold"
            @click="joinCrew(selectedCrew.id)"
          >크루 가입하기</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- 크루 생성 다이얼로그 -->
    <VDialog v-model="showCreateDialog" max-width="450">
      <VCard class="rounded-xl overflow-hidden">
        <VToolbar color="primary" flat>
          <VToolbarTitle class="text-h6 font-weight-black text-white">새로운 크루 만들기</VToolbarTitle>
          <VBtn icon="mdi-close" color="white" @click="showCreateDialog = false" />
        </VToolbar>
        <VCardText class="pa-6">
          <div class="mb-6">
            <label class="text-subtitle-2 font-weight-bold mb-2 d-block">크루 이름</label>
            <VTextField
              v-model="newCrew.name"
              placeholder="예: 강남 새벽 러닝 크루"
              variant="outlined"
              rounded="lg"
              hide-details
              color="primary"
            />
          </div>
          <div class="mb-6">
            <label class="text-subtitle-2 font-weight-bold mb-2 d-block">크루 이미지 선택</label>
            <div class="d-flex overflow-x-auto gap-2 pb-2">
              <VAvatar 
                v-for="img in preset_images" 
                :key="img" 
                size="60" 
                rounded="lg" 
                class="cursor-pointer border-2"
                :class="newCrew.image === img ? 'border-primary' : 'border-transparent'"
                @click="newCrew.image = img"
              >
                <img :src="img" style="width:100%; height:100%; object-fit:cover;">
              </VAvatar>
            </div>
          </div>
          <div class="mb-2">
            <label class="text-subtitle-2 font-weight-bold mb-2 d-block">크루 소개</label>
            <VTextarea
              v-model="newCrew.description"
              placeholder="크루의 활동 시간, 장소, 목표 등을 자유롭게 적어주세요!"
              variant="outlined"
              rounded="lg"
              rows="4"
              hide-details
              color="primary"
            />
          </div>
          <p class="text-caption text-grey mt-2">
            <VIcon icon="mdi-information-outline" size="14" class="mr-1" />
            크루를 생성하면 자동으로 첫 번째 멤버로 등록됩니다.
          </p>
        </VCardText>
        <VCardActions class="pa-6 pt-0">
          <VBtn 
            block 
            color="primary" 
            variant="flat" 
            rounded="xl" 
            size="large" 
            class="font-weight-bold"
            :disabled="!newCrew.name"
            @click="createCrew"
          >크루 생성 완료</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
.crew-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}
.crew-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.1) !important;
}
.active-crew {
  background: linear-gradient(to bottom right, #ffffff, #f9f9ff);
}
.exploration-icon-box {
  background: linear-gradient(135deg, #ff4b2b, #ff8a3d);
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  box-shadow: 0 4px 10px rgba(255, 75, 43, 0.3);
}
.exploration-header {
  background: linear-gradient(135deg, #2c3e50, #4ca1af);
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.header-overlay-dark {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.1);
  z-index: 0;
}
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.h-40 {
  height: 40px;
}
.border-dashed {
  border: 2px dashed #e0e0e0 !important;
}
.member-list {
  max-height: 250px;
  overflow-y: auto;
}
.gap-2 {
  gap: 8px;
}
.header-bg-image {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-size: cover;
  background-position: center;
  filter: blur(5px) brightness(0.7);
  transform: scale(1.1);
}
.header-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, rgba(255, 75, 43, 0.4), rgba(255, 75, 43, 0.8));
  z-index: 1;
}
</style>
