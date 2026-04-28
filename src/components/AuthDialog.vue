<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'login'])

const tab = ref('login')
const loginData = ref({ email: '', password: '' })
const signupData = ref({ name: '', email: '', password: '', confirmPassword: '', region: '' })
const loading = ref(false)
const locationLoading = ref(false)

const API_URL = import.meta.env.VITE_API_URL || `http://127.0.0.1:8000/api`

const handleLogin = async () => {
  if (!loginData.value.email || !loginData.value.password) {
    alert('이메일과 비밀번호를 입력해주세요.')
    return
  }

  loading.value = true
  try {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginData.value)
    })
    
    if (res.ok) {
      const data = await res.json()
      emit('login', data)
      emit('update:modelValue', false)
    } else {
      const err = await res.json()
      alert(err.detail || '로그인에 실패했습니다.')
    }
  } catch (e) {
    alert('서버 연결에 실패했습니다.')
  } finally {
    loading.value = false
  }
}

const handleSignup = async () => {
  if (signupData.value.password !== signupData.value.confirmPassword) {
    alert('비밀번호가 일치하지 않습니다.')
    return
  }

  loading.value = true
  try {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: signupData.value.email,
        password: signupData.value.password,
        name: signupData.value.name,
        region: signupData.value.region
      })
    })

    if (res.ok) {
      alert('회원가입이 완료되었습니다! 로그인해주세요.')
      tab.value = 'login'
    } else {
      const err = await res.json()
      alert(err.detail || '회원가입에 실패했습니다.')
    }
  } catch (e) {
    alert('서버 연결에 실패했습니다.')
  } finally {
    loading.value = false
  }
}

const autoFillLocation = () => {
  if (!navigator.geolocation) {
    alert('브라우저가 위치 정보를 지원하지 않습니다.')
    return
  }

  locationLoading.value = true
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        const { latitude, longitude } = position.coords
        // Nominatim API 호출 (한국어 응답)
        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1&accept-language=ko`)
        if (res.ok) {
          const data = await res.json()
          if (data.address) {
            const addr = data.address
            const sido = addr.city || addr.province || addr.state || ''
            const sigungu = addr.borough || addr.county || addr.town || ''
            const dong = addr.suburb || addr.village || addr.neighbourhood || addr.quarter || ''
            
            signupData.value.region = `${sido} ${sigungu} ${dong}`.replace(/\s+/g, ' ').trim()
          } else {
            alert('주소 정보를 가져올 수 없습니다.')
          }
        }
      } catch (e) {
        console.error(e)
        alert('위치 정보를 변환하는 중 오류가 발생했습니다.')
      } finally {
        locationLoading.value = false
      }
    },
    (err) => {
      console.error(err)
      alert('위치 정보를 가져올 수 없습니다. 권한을 확인해주세요.')
      locationLoading.value = false
    },
    { enableHighAccuracy: true, timeout: 10000 }
  )
}
</script>

<template>
  <VDialog
    :model-value="modelValue"
    @update:model-value="val => emit('update:modelValue', val)"
    max-width="450"
    transition="dialog-bottom-transition"
  >
    <VCard class="rounded-xl overflow-hidden auth-card">
      <VCardText class="pa-0">
        <VTabs
          v-model="tab"
          grow
          color="primary"
          class="auth-tabs"
        >
          <VTab value="login">로그인</VTab>
          <VTab value="signup">회원가입</VTab>
        </VTabs>

        <VWindow v-model="tab" class="pa-6">
          <!-- 로그인 섹션 -->
          <VWindowItem value="login">
            <div class="text-center mb-6">
              <h3 class="text-h5 font-weight-black mb-1">다시 만나서 반가워요!</h3>
              <p class="text-caption text-grey">런릿과 함께 오늘도 건강하게 뛰어볼까요?</p>
            </div>

            <VForm @submit.prevent="handleLogin">
              <VTextField
                v-model="loginData.email"
                label="이메일"
                variant="outlined"
                prepend-inner-icon="mdi-email-outline"
                class="mb-3"
                density="comfortable"
                hide-details
              />
              <VTextField
                v-model="loginData.password"
                label="비밀번호"
                type="password"
                variant="outlined"
                prepend-inner-icon="mdi-lock-outline"
                class="mb-6"
                density="comfortable"
                hide-details
              />
              <VBtn
                block
                color="primary"
                size="large"
                elevation="0"
                class="rounded-lg font-weight-bold"
                type="submit"
                :loading="loading"
              >
                로그인하기
              </VBtn>
            </VForm>
          </VWindowItem>

          <!-- 회원가입 섹션 -->
          <VWindowItem value="signup">
            <div class="text-center mb-6">
              <h3 class="text-h5 font-weight-black mb-1">함께 시작해요!</h3>
              <p class="text-caption text-grey">가입하고 나만의 러닝 기록을 관리해보세요.</p>
            </div>

            <VForm @submit.prevent="handleSignup">
              <VTextField
                v-model="signupData.name"
                label="이름"
                variant="outlined"
                prepend-inner-icon="mdi-account-outline"
                class="mb-3"
                density="comfortable"
                hide-details
              />
              <VTextField
                v-model="signupData.email"
                label="이메일"
                variant="outlined"
                prepend-inner-icon="mdi-email-outline"
                class="mb-3"
                density="comfortable"
                hide-details
              />
              <VTextField
                v-model="signupData.region"
                label="지역 (시/도 군/구 동)"
                variant="outlined"
                prepend-inner-icon="mdi-map-marker-outline"
                class="mb-3"
                density="comfortable"
                hide-details
              >
                <template v-slot:append-inner>
                  <VBtn
                    icon="mdi-crosshairs-gps"
                    variant="text"
                    size="small"
                    color="primary"
                    @click="autoFillLocation"
                    :loading="locationLoading"
                    title="현재 위치로 채우기"
                  />
                </template>
              </VTextField>
              <VTextField
                v-model="signupData.password"
                label="비밀번호"
                type="password"
                variant="outlined"
                prepend-inner-icon="mdi-lock-outline"
                class="mb-3"
                density="comfortable"
                hide-details
              />
              <VTextField
                v-model="signupData.confirmPassword"
                label="비밀번호 확인"
                type="password"
                variant="outlined"
                prepend-inner-icon="mdi-lock-check-outline"
                class="mb-6"
                density="comfortable"
                hide-details
              />
              <VBtn
                block
                color="primary"
                size="large"
                elevation="0"
                class="rounded-lg font-weight-bold"
                type="submit"
                :loading="loading"
              >
                시작하기
              </VBtn>
            </VForm>
          </VWindowItem>
        </VWindow>
      </VCardText>
    </VCard>
  </VDialog>
</template>

<style scoped>
.auth-card {
  box-shadow: 0 20px 40px rgba(0,0,0,0.1) !important;
}

.auth-tabs {
  border-bottom: 1px solid #f0f0f0;
}

:deep(.v-field--variant-outlined) {
  border-radius: 12px !important;
}

:deep(.v-field--focused) {
  background: #f8faff;
}
</style>
