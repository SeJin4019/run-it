<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  currentUser: Object,
  apiUrl: String
})

const emit = defineEmits(['open-crew-map', 'refresh'])

const crews = ref([])
const myCrews = computed(() => {
  if (!props.currentUser) return []
  return crews.value.filter(c => c.members.some(m => m.user_id === props.currentUser.id))
})

const otherCrews = computed(() => {
  if (!props.currentUser) return crews.value
  return crews.value.filter(c => !c.members.some(m => m.user_id === props.currentUser.id))
})

const fetchCrews = async () => {
  try {
    const res = await fetch(`${props.apiUrl}/crews`)
    if (res.ok) {
      crews.value = await res.json()
    }
  } catch (e) {
    console.error('크루 목록 로딩 실패:', e)
  }
}

const joinCrew = async (crewId) => {
  if (!props.currentUser) return
  try {
    const res = await fetch(`${props.apiUrl}/crews/${crewId}/join?user_id=${props.currentUser.id}`, {
      method: 'POST'
    })
    if (res.ok) {
      alert('크루에 가입되었습니다!')
      fetchCrews()
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
      alert('크루에서 탈퇴되었습니다.')
      fetchCrews()
    }
  } catch (e) {
    console.error('크루 탈퇴 실패:', e)
  }
}

const showCreateDialog = ref(false)
const newCrew = ref({
  name: '',
  description: ''
})

const createCrew = async () => {
  if (!newCrew.value.name) return
  try {
    const res = await fetch(`${props.apiUrl}/crews?user_id=${props.currentUser.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newCrew.value)
    })
    if (res.ok) {
      alert('크루가 생성되었습니다!')
      showCreateDialog.value = false
      newCrew.value = { name: '', description: '' }
      fetchCrews()
    }
  } catch (e) {
    console.error('크루 생성 실패:', e)
  }
}

onMounted(fetchCrews)

</script>

<template>
  <div class="crew-container animate-fade-in py-4">
    <div class="d-flex align-center justify-space-between mb-6">
      <h2 class="text-h5 font-weight-black text-primary">러닝 크루 🤝</h2>
      <VBtn 
        color="primary" 
        prepend-icon="mdi-plus" 
        rounded="xl" 
        variant="flat"
        @click="showCreateDialog = true"
      >크루 만들기</VBtn>
    </div>

    <!-- 내 크루 섹션 -->
    <div class="mb-8" v-if="myCrews.length > 0">
      <h3 class="text-subtitle-1 font-weight-bold mb-4 d-flex align-center">
        <VIcon icon="mdi-account-group" class="mr-2" color="primary" /> 내 크루
      </h3>
      <VCard v-for="crew in myCrews" :key="crew.id" flat class="crew-card rounded-xl border mb-4 pa-4 overflow-hidden">
        <div class="d-flex align-start">
          <VAvatar color="primary-lighten-4" size="64" rounded="lg" class="mr-4">
            <VIcon icon="mdi-account-group" color="primary" size="32" />
          </VAvatar>
          <div class="flex-grow-1">
            <div class="d-flex align-center justify-space-between">
              <h4 class="text-h6 font-weight-bold">{{ crew.name }}</h4>
              <VChip size="x-small" color="primary" variant="flat">{{ crew.member_count }}명 참여 중</VChip>
            </div>
            <p class="text-body-2 text-grey mb-3">{{ crew.description }}</p>
            <div class="d-flex gap-2">
              <VBtn 
                color="error" 
                variant="flat" 
                rounded="lg" 
                size="small" 
                prepend-icon="mdi-map-marker-radius"
                @click="emit('open-crew-map', crew)"
              >크루 위치 확인</VBtn>
              <VBtn 
                color="grey" 
                variant="tonal" 
                rounded="lg" 
                size="small"
                @click="leaveCrew(crew.id)"
              >탈퇴</VBtn>
            </div>
          </div>
        </div>
      </VCard>
    </div>

    <VDivider class="mb-8" />

    <!-- 전체 크루 섹션 -->
    <div>
      <h3 class="text-subtitle-1 font-weight-bold mb-4">새로운 크루 탐색</h3>
      <VRow>
        <VCol v-for="crew in otherCrews" :key="crew.id" cols="12" sm="6">
          <VCard flat class="rounded-xl border pa-4 h-100">
            <div class="d-flex align-center mb-2">
              <VAvatar color="grey-lighten-4" size="48" rounded="lg" class="mr-3">
                <VIcon icon="mdi-account-group-outline" color="grey" />
              </VAvatar>
              <div>
                <div class="font-weight-bold">{{ crew.name }}</div>
                <div class="text-caption text-grey">{{ crew.member_count }}명의 멤버</div>
              </div>
            </div>
            <p class="text-caption text-grey mb-4 line-clamp-2">{{ crew.description }}</p>
            <VBtn 
              block 
              color="primary" 
              variant="tonal" 
              rounded="lg" 
              size="small"
              @click="joinCrew(crew.id)"
            >가입하기</VBtn>
          </VCard>
        </VCol>
      </VRow>
      <div v-if="otherCrews.length === 0 && myCrews.length === 0" class="text-center py-12">
        <VIcon icon="mdi-account-group-outline" size="48" color="grey-lighten-2" class="mb-2" />
        <p class="text-grey">아직 생성된 크루가 없습니다.<br>첫 번째 크루를 만들어보세요!</p>
      </div>
    </div>

    <!-- 크루 생성 다이얼로그 -->
    <VDialog v-model="showCreateDialog" max-width="400">
      <VCard class="rounded-xl pa-4">
        <VCardTitle class="text-h6 font-weight-black">새로운 크루 만들기</VCardTitle>
        <VCardText class="pa-0 pt-4">
          <VTextField
            v-model="newCrew.name"
            label="크루 이름"
            variant="outlined"
            rounded="lg"
            class="mb-4"
            hide-details
          />
          <VTextarea
            v-model="newCrew.description"
            label="크루 설명"
            variant="outlined"
            rounded="lg"
            rows="3"
            hide-details
          />
        </VCardText>
        <VCardActions class="px-0 pt-6">
          <VSpacer />
          <VBtn variant="text" color="grey" @click="showCreateDialog = false">취소</VBtn>
          <VBtn color="primary" variant="flat" rounded="lg" class="px-6" @click="createCrew">생성하기</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
.crew-card {
  transition: transform 0.2s;
}
.crew-card:hover {
  transform: translateY(-2px);
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
