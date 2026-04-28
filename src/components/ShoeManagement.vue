<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  userId: Number,
  apiUrl: String
})

const shoes = ref([])
const showAddDialog = ref(false)
const newShoe = ref({
  name: '',
  brand: '',
  initial_km: 0
})

const fetchShoes = async () => {
  if (!props.userId) return
  try {
    const res = await fetch(`${props.apiUrl}/shoes/${props.userId}`)
    if (res.ok) {
      shoes.value = await res.json()
    }
  } catch (e) {
    console.error('신발 정보 로딩 실패:', e)
  }
}

const handleAddShoe = async () => {
  if (!newShoe.value.name || !newShoe.value.brand) {
    alert('이름과 브랜드를 입력해주세요.')
    return
  }
  
  try {
    const res = await fetch(`${props.apiUrl}/shoes?user_id=${props.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newShoe.value)
    })
    
    if (res.ok) {
      const addedShoe = await res.json()
      shoes.value.push(addedShoe)
      showAddDialog.value = false
      newShoe.value = { name: '', brand: '', initial_km: 0 }
    }
  } catch (e) {
    console.error('신발 등록 실패:', e)
  }
}

const toggleShoeStatus = async (shoe) => {
  try {
    const res = await fetch(`${props.apiUrl}/shoes/${shoe.id}?is_active=${!shoe.is_active}`, {
      method: 'PATCH'
    })
    if (res.ok) {
      shoe.is_active = !shoe.is_active
    }
  } catch (e) {
    console.error('상태 변경 실패:', e)
  }
}

const deleteShoe = async (shoeId) => {
  if (!confirm('정말 삭제하시겠습니까?')) return
  try {
    const res = await fetch(`${props.apiUrl}/shoes/${shoeId}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      shoes.value = shoes.value.filter(s => s.id !== shoeId)
    }
  } catch (e) {
    console.error('삭제 실패:', e)
  }
}

onMounted(fetchShoes)
</script>

<template>
  <div class="shoe-management animate-fade-in">
    <div class="section-header d-flex align-center justify-space-between mb-6">
      <div>
        <h2 class="text-h6 font-weight-bold">장비 관리</h2>
        <p class="text-caption text-grey">런닝화의 마일리지를 체크하고 교체 시기를 관리하세요</p>
      </div>
      <VBtn color="primary" variant="flat" prepend-icon="mdi-plus" @click="showAddDialog = true">
        신발 등록
      </VBtn>
    </div>

    <!-- 신발 목록 -->
    <VRow v-if="shoes.length > 0">
      <VCol v-for="shoe in shoes" :key="shoe.id" cols="12" sm="6">
        <VCard border flat class="rounded-xl shoe-card" :class="{ 'inactive-shoe': !shoe.is_active }">
          <VCardText>
            <div class="d-flex justify-space-between align-start mb-4">
              <div>
                <div class="text-overline text-primary font-weight-bold">{{ shoe.brand }}</div>
                <h3 class="text-h6 font-weight-bold">{{ shoe.name }}</h3>
              </div>
              <VChip :color="shoe.is_active ? 'success' : 'grey'" size="small">
                {{ shoe.is_active ? '사용 중' : '은퇴' }}
              </VChip>
            </div>

            <div class="mb-2 d-flex justify-space-between align-end">
              <span class="text-caption text-grey">현재 마일리지</span>
              <span class="text-h6 font-weight-black">
                {{ (shoe.initial_km + shoe.total_km).toFixed(1) }} <small>km</small>
              </span>
            </div>
            
            <!-- 수명 게이지 (예: 800km 기준) -->
            <VProgressLinear
              :model-value="((shoe.initial_km + shoe.total_km) / 800) * 100"
              color="primary"
              height="8"
              rounded
              class="mb-1"
            ></VProgressLinear>
            <div class="text-right text-caption text-grey">
              권장 수명 대비 {{ Math.min(Math.round(((shoe.initial_km + shoe.total_km) / 800) * 100), 100) }}% 사용
            </div>
          </VCardText>
          
          <VDivider />
          
          <VCardActions>
            <VBtn 
              size="small" 
              variant="text" 
              :color="shoe.is_active ? 'grey' : 'primary'"
              @click="toggleShoeStatus(shoe)"
            >
              {{ shoe.is_active ? '은퇴시키기' : '다시 사용하기' }}
            </VBtn>
            <VSpacer />
            <VBtn size="small" variant="text" color="error" icon="mdi-trash-can-outline" @click="deleteShoe(shoe.id)" />
          </VCardActions>
        </VCard>
      </VCol>
    </VRow>

    <div v-else class="text-center py-12">
      <VIcon icon="mdi-shoe-run" size="64" color="grey-lighten-2" class="mb-4" />
      <p class="text-body-1 text-grey">등록된 신발이 없습니다.<br>새 신발을 등록하고 거리를 관리해보세요!</p>
    </div>

    <!-- 등록 다이얼로그 -->
    <VDialog v-model="showAddDialog" max-width="400">
      <VCard class="rounded-xl pa-4">
        <VCardTitle class="px-0 font-weight-bold">새 신발 등록</VCardTitle>
        <VCardText class="px-0">
          <VTextField
            v-model="newShoe.brand"
            label="브랜드 (예: 나이키, 아디다스)"
            variant="outlined"
            density="comfortable"
            class="mb-2"
          />
          <VTextField
            v-model="newShoe.name"
            label="모델명 (예: 페가수스 40)"
            variant="outlined"
            density="comfortable"
            class="mb-2"
          />
          <VTextField
            v-model.number="newShoe.initial_km"
            label="시작 마일리지 (km)"
            type="number"
            hint="이미 신었던 신발이라면 기존 주행 거리를 입력하세요"
            persistent-hint
            variant="outlined"
            density="comfortable"
          />
        </VCardText>
        <VCardActions class="px-0">
          <VSpacer />
          <VBtn variant="text" @click="showAddDialog = false">취소</VBtn>
          <VBtn color="primary" variant="flat" class="px-6" @click="handleAddShoe">등록 완료</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
.shoe-card {
  transition: all 0.3s ease;
}
.shoe-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
}
.inactive-shoe {
  opacity: 0.6;
  filter: grayscale(0.5);
}
</style>
