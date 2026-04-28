<script setup>
import { ref, computed, onMounted } from 'vue'

import MapRoutePicker from './MapRoutePicker.vue'

/**
 * 📝 코스 등록 컴포넌트
 * 새로운 러닝 코스를 생성하기 위한 입력 폼을 제공합니다.
 * .skills/file-upload 표준을 준수하며, 이미지를 Base64로 인코딩하여 저장합니다.
 */

const props = defineProps({
  prefilledData: {
    type: Object,
    default: null
  }
})

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
const selectedDong = ref('')

/**
 * 구/군 → 동 데이터 (대표 동만 포함)
 */
const DISTRICT_DONG_DATA = {
  // 서울
  '강남구': ['개포동', '논현동', '대치동', '도곡동', '삼성동', '세곡동', '수서동', '압구정동', '역삼동', '일원동', '자곡동', '청담동'],
  '서초구': ['내곡동', '반포동', '방배동', '서초동', '신원동', '양재동', '우면동', '잠원동'],
  '마포구': ['공덕동', '대흥동', '망원동', '서교동', '성산동', '신수동', '아현동', '연남동', '용강동', '합정동', '홍익동'],
  '송파구': ['가락동', '거여동', '문정동', '방이동', '석촌동', '송파동', '오금동', '잠실동', '장지동', '풍납동'],
  '강서구': ['가양동', '개화동', '공항동', '내발산동', '마곡동', '방화동', '화곡동'],
  '강동구': ['강일동', '고덕동', '길동', '둔촌동', '명일동', '상일동', '성내동', '암사동', '천호동'],
  '영등포구': ['당산동', '대림동', '도림동', '문래동', '신길동', '여의도동', '영등포동', '양평동'],
  '은평구': ['갈현동', '녹번동', '대조동', '불광동', '수색동', '신사동', '역촌동', '응암동', '진관동'],
  '노원구': ['공릉동', '월계동', '중계동', '하계동', '상계동'],
  '성동구': ['금호동', '도선동', '마장동', '사근동', '성수동', '송정동', '옥수동', '왕십리동', '응봉동'],
  '관악구': ['남현동', '봉천동', '신림동'],
  '동작구': ['노량진동', '대방동', '동작동', '사당동', '상도동', '신대방동'],
  '중구': ['광희동', '남대문로', '명동', '무교동', '신당동', '을지로', '정동', '충무로', '황학동', '회현동'],
  '종로구': ['가회동', '계동', '궁정동', '내수동', '누상동', '삼청동', '서촌', '숭인동', '이화동', '인사동', '창신동', '통의동', '혜화동'],
  '용산구': ['갈월동', '동자동', '문배동', '보광동', '서계동', '이촌동', '이태원동', '청암동', '한강로동', '한남동'],
  '성북구': ['길음동', '돈암동', '동소문동', '보문동', '삼선동', '성북동', '안암동', '장위동', '정릉동', '종암동'],
  '도봉구': ['도봉동', '방학동', '쌍문동', '창동'],
  '강북구': ['미아동', '번동', '수유동', '우이동'],
  '구로구': ['개봉동', '고척동', '구로동', '신도림동', '오류동', '온수동', '항동'],
  '금천구': ['가산동', '독산동', '시흥동'],
  '광진구': ['광장동', '구의동', '군자동', '능동', '자양동', '중곡동', '화양동'],
  '중랑구': ['면목동', '망우동', '묵동', '상봉동', '신내동', '중화동'],
  '동대문구': ['답십리동', '신설동', '이문동', '장안동', '전농동', '제기동', '청량리동', '휘경동'],
  '서대문구': ['남가좌동', '냉천동', '대신동', '대현동', '북가좌동', '북아현동', '연희동', '창천동', '천연동', '충현동', '홍제동', '홍은동'],
  '양천구': ['목동', '신월동', '신정동'],
  // 경기
  '수원시': ['인계동', '팔달동', '권선동', '연무동', '우만동', '지동', '장안동', '정자동', '조원동', '천천동'],
  '성남시': ['분당동', '수내동', '야탑동', '이매동', '정자동', '판교동'],
  '고양시': ['일산동', '백석동', '주엽동', '덕이동', '화정동', '행신동'],
  '용인시': ['기흥동', '수지동', '처인동'],
  // 부산
  '해운대구': ['반여동', '반송동', '우동', '우2동', '좌동', '중동', '청사포동'],
  '부산진구': ['개금동', '당감동', '범천동', '부전동', '양정동', '전포동'],
  // 인천
  '연수구': ['동춘동', '선학동', '송도동', '연수동', '청학동'],
  // 대전
  '유성구': ['관저동', '노은동', '봉명동', '지족동', '하기동'],
  // 광주
  '북구': ['각화동', '문흥동', '삼각동', '신안동', '용봉동', '운암동', '일곡동'],
  // 대구
  '수성구': ['고산동', '대흥동', '만촌동', '범어동', '수성동', '시지동'],
}

/**
 * 시/도 선택 변경 시 시/군/구 및 동 초기화
 */
const onCityChange = () => {
  selectedDistrict.value = ''
  selectedDong.value = ''
  updateLocation()
}

/**
 * 시/군/구 선택 변경 시 동 초기화
 */
const onDistrictChange = () => {
  selectedDong.value = ''
  updateLocation()
}

/**
 * 현재 구에 해당하는 동 목록 (없으면 직접 입력)
 */
const availableDongs = computed(() => {
  return DISTRICT_DONG_DATA[selectedDistrict.value] || []
})

/**
 * 최종 위치 문자열 업데이트
 */
const updateLocation = () => {
  const parts = [selectedCity.value, selectedDistrict.value, selectedDong.value].filter(Boolean)
  newCourse.value.location = parts.join(' ')
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
  
  emit('create', {
    ...newCourse.value,
    distance: parseFloat(newCourse.value.distance),
    elevation: parseInt(newCourse.value.elevation) || 0
  })
  
  loading.value = false
}

onMounted(() => {
  if (props.prefilledData) {
    newCourse.value.path = props.prefilledData.path
    newCourse.value.distance = props.prefilledData.distance
    // 경로가 있으면 지도에 맞춰서 거리 등이 자동 계산될 수 있도록 함
  }
})

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
  selectedDong.value = ''
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
            :style="previewImage ? { backgroundImage: `url(${previewImage})` } : {}"
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
            @update:model-value="onDistrictChange"
            required
          />
        </VCol>

        <VCol cols="12" sm="6">
          <template v-if="availableDongs.length > 0">
            <VSelect
              v-model="selectedDong"
              :items="availableDongs"
              label="동 선택 (선택)"
              variant="outlined"
              density="comfortable"
              color="primary"
              :disabled="!selectedDistrict"
              clearable
              @update:model-value="updateLocation"
            />
          </template>
          <template v-else>
            <VTextField
              v-model="selectedDong"
              label="동 직접 입력 (선택)"
              placeholder="예: 서교동, 역삼동"
              variant="outlined"
              density="comfortable"
              color="primary"
              :disabled="!selectedDistrict"
              @input="updateLocation"
            />
          </template>
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
