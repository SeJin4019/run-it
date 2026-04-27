<script setup>
import { ref } from 'vue'
import MapRoutePicker from './MapRoutePicker.vue'

/**
 * 📝 코스 등록 컴포넌트
 * 새로운 러닝 코스를 생성하기 위한 입력 폼을 제공합니다.
 * .skills/file-upload 표준을 준수하며, 이미지를 Base64로 인코딩하여 저장합니다.
 */

const emit = defineEmits(['create'])

const previewImage = ref(null)
const selectedFile = ref(null)
const loading = ref(false)

const newCourse = ref({
  name: '',
  location: '',
  distance: 0,
  elevation: '',
  difficulty: '보통',
  parking: '정보 없음',
  description: '',
  path: [],
  image: 'https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=800&q=80'
})

/**
 * 시/도 및 시/군/구 데이터
 */
const CITY_DATA = {
  '서울특별시': ['강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구', '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구'],
  '울산광역시': ['중구', '남구', '동구', '북구', '울주군'],
  '경기도': ['수원시', '성남시', '고양시', '용인시', '부천시', '안산시', '안양시', '남양주시', '화성시', '평택시', '의정부시', '파주시', '시흥시', '김포시', '광명시', '광주시', '군포시', '이천시', '오산시', '하남시', '양주시', '구리시', '안성시', '포천시', '의왕시', '양평군', '여주시', '동두천시', '가평군', '과천시', '연천군'],
  '부산광역시': ['중구', '서구', '동구', '영도구', '부산진구', '동래구', '남구', '북구', '해운대구', '사하구', '금정구', '강서구', '연제구', '수영구', '사상구', '기장군'],
  '인천광역시': ['중구', '동구', '미추홀구', '연수구', '남동구', '부평구', '계양구', '서구', '강화군', '옹진군'],
  '대구광역시': ['중구', '동구', '서구', '남구', '북구', '수성구', '달서구', '달성군', '군위군'],
  '대전광역시': ['동구', '중구', '서구', '유성구', '대덕구'],
  '광주광역시': ['동구', '서구', '남구', '북구', '광산구'],
  '세종특별자치시': ['세종시'],
  '강원특별자치도': ['춘천시', '원주시', '강릉시', '동해시', '태백시', '속초시', '삼척시', '홍천군', '횡성군', '영월군', '평창군', '정선군', '철원군', '화천군', '양구군', '인제군', '고성군', '양양군']
}

const selectedCity = ref('')
const selectedDistrict = ref('')

/**
 * 시/도 선택 변경 시 시/군/구 초기화
 */
const onCityChange = () => {
  selectedDistrict.value = ''
  updateLocation()
}

/**
 * 최종 위치 문자열 업데이트
 */
const updateLocation = () => {
  if (selectedCity.value && selectedDistrict.value) {
    newCourse.value.location = `${selectedCity.value} ${selectedDistrict.value}`
  } else {
    newCourse.value.location = ''
  }
}

/**
 * 파일 선택 시 이미지 프리뷰 및 Base64 변환
 */
const onFileChange = (e) => {
  const file = e.target.files[0]
  if (file) {
    selectedFile.value = file
    const reader = new FileReader()
    reader.onload = (event) => {
      previewImage.value = event.target.result
      newCourse.value.image = event.target.result
    }
    reader.readAsDataURL(file)
  }
}

/**
 * 폼 제출 처리
 */
const handleSubmit = async () => {
  if (!newCourse.value.name || !newCourse.value.location) {
    alert('코스 이름과 동네 이름을 입력해주세요!')
    return
  }

  loading.value = true
  
  // 시뮬레이션된 로딩 시간
  await new Promise(resolve => setTimeout(resolve, 500))

  emit('create', {
    ...newCourse.value,
    id: Date.now(),
    distance: parseFloat(newCourse.value.distance),
    elevation: parseInt(newCourse.value.elevation) || 0
  })
  
  // 폼 초기화
  resetForm()
  loading.value = false
}

const resetForm = () => {
  newCourse.value = {
    name: '',
    location: '',
    distance: 0,
    elevation: '',
    difficulty: '보통',
    parking: '정보 없음',
    description: '',
    path: [],
    image: 'https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=800&q=80'
  }
  previewImage.value = null
  selectedFile.value = null
  selectedCity.value = ''
  selectedDistrict.value = ''
}
</script>

<template>
  <VCard class="pa-6 animate-fade-in" elevation="0" border rounded="xl">
    <div class="text-center mb-8">
      <h2 class="text-h5 font-weight-black text-primary">동네 러닝 코스 만들기</h2>
      <p class="text-body-2 text-grey">우리 동네 최고의 러닝 코스를 이웃들에게 공유해보세요!</p>
    </div>

    <VForm @submit.prevent="handleSubmit">
      <VRow>
        <!-- 사진 업로드 영역 -->
        <VCol cols="12" class="d-flex justify-center mb-4">
          <div 
            class="image-upload-box" 
            :style="{ backgroundImage: `url(${previewImage})` }"
            @click="$refs.fileInput.click()"
          >
            <input 
              ref="fileInput"
              type="file" 
              accept="image/*" 
              @change="onFileChange" 
              hidden
            >
            <div v-if="!previewImage" class="d-flex flex-column align-center text-grey">
              <VIcon icon="mdi-camera" size="32" class="mb-1" />
              <span class="text-caption font-weight-bold">사진 올리기</span>
            </div>
          </div>
        </VCol>

        <VCol cols="12">
          <VTextField
            v-model="newCourse.name"
            label="코스 이름"
            placeholder="예: 불광천 새벽 조깅 코스"
            variant="outlined"
            density="comfortable"
            color="primary"
            required
          />
        </VCol>

        <VCol cols="12" sm="6">
          <VSelect
            v-model="selectedCity"
            :items="Object.keys(CITY_DATA)"
            label="시/도 선택"
            variant="outlined"
            density="comfortable"
            color="primary"
            @update:model-value="onCityChange"
            required
          />
        </VCol>

        <VCol cols="12" sm="6">
          <VSelect
            v-model="selectedDistrict"
            :items="selectedCity ? CITY_DATA[selectedCity] : []"
            label="동네(시/군/구) 선택"
            variant="outlined"
            density="comfortable"
            color="primary"
            :disabled="!selectedCity"
            @update:model-value="updateLocation"
            required
          />
        </VCol>

        <VCol cols="12" sm="6">
          <VSelect
            v-model="newCourse.difficulty"
            :items="['쉬움', '보통', '어려움']"
            label="난이도"
            variant="outlined"
            density="comfortable"
            color="primary"
          />
        </VCol>

        <VCol cols="12" sm="6">
          <VSelect
            v-model="newCourse.parking"
            :items="['주차 가능', '주차 협소', '주차 불가', '정보 없음']"
            label="주차 여부"
            variant="outlined"
            density="comfortable"
            color="primary"
          />
        </VCol>

        <VCol cols="12">
          <VTextarea
            v-model="newCourse.description"
            label="코스 후기 및 꿀팁"
            placeholder="이 코스의 매력 포인트나 주의할 점을 적어주세요 (예: 야경이 예뻐요, 오르막이 힘들어요)"
            variant="outlined"
            density="comfortable"
            color="primary"
            rows="3"
            auto-grow
          />
        </VCol>

        <VCol cols="12">
          <div class="text-subtitle-2 font-weight-bold mb-2">코스 그리기 (지도를 클릭하세요)</div>
          <div class="map-picker-wrapper">
            <MapRoutePicker 
              v-model="newCourse.path" 
              @update:distance="newCourse.distance = $event"
            />
          </div>
        </VCol>

        <VCol cols="6">
          <VTextField
            v-model="newCourse.distance"
            label="총 거리 (km)"
            type="number"
            step="0.01"
            variant="outlined"
            density="comfortable"
            color="primary"
            required
          />
        </VCol>

        <VCol cols="6">
          <VTextField
            v-model="newCourse.elevation"
            label="상승 고도 (m)"
            type="number"
            variant="outlined"
            density="comfortable"
            color="primary"
          />
        </VCol>

        <VCol cols="12" class="mt-4">
          <VBtn 
            type="submit" 
            color="primary" 
            size="large" 
            block 
            rounded="lg"
            :loading="loading"
          >
            코스 등록하기
          </VBtn>
        </VCol>
      </VRow>
    </VForm>
  </VCard>
</template>

<style scoped>
.image-upload-box {
  width: 120px;
  height: 120px;
  border: 2px dashed #e9ecef;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background-size: cover;
  background-position: center;
  background-color: #f8f9fa;
  transition: all 0.2s;
}

.image-upload-box:hover {
  border-color: var(--v-theme-primary);
  background-color: #fffaf7;
}

.map-picker-wrapper {
  height: 300px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}
</style>
