<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'

const props = defineProps({
  currentUser: Object,
  apiUrl: String
})

const emit = defineEmits(['back'])

const messages = ref([
  {
    id: 1,
    text: `안녕하세요 ${props.currentUser?.name || '러너'}님! 무엇을 도와드릴까요?`,
    sender: 'bot',
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
])

const newMessage = ref('')
const isLoading = ref(false)
const chatContainer = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!newMessage.value.trim() || isLoading.value) return

  const userMsg = {
    id: Date.now(),
    text: newMessage.value,
    sender: 'user',
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  messages.value.push(userMsg)
  const query = newMessage.value
  newMessage.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    const res = await fetch(`${props.apiUrl}/chatbot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: query,
        user_id: props.currentUser?.id
      })
    })

    if (res.ok) {
      const data = await res.json()
      messages.value.push({
        id: Date.now() + 1,
        text: data.response,
        sender: 'bot',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      })
    } else {
      throw new Error('Server error')
    }
  } catch (e) {
    messages.value.push({
      id: Date.now() + 1,
      text: '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
      sender: 'bot',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  scrollToBottom()
})

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

</script>

<template>
  <div class="chatbot-view animate-fade-in">
    <VToolbar color="white" flat border class="sticky-header">
      <VBtn icon="mdi-chevron-left" @click="$emit('back')" />
      <VToolbarTitle class="font-weight-black text-primary">AI 러닝 코치</VToolbarTitle>
      <VSpacer />
      <VBtn icon="mdi-dots-vertical" variant="text" />
    </VToolbar>

    <div class="chat-content" ref="chatContainer">
      <div v-for="msg in messages" :key="msg.id" :class="['message-wrapper', msg.sender]">
        <VAvatar v-if="msg.sender === 'bot'" size="36" color="primary" class="mr-2 bot-avatar">
          <VIcon icon="mdi-robot" color="white" />
        </VAvatar>
        
        <div class="message-bubble-container">
          <div :class="['message-bubble', msg.sender]">
            {{ msg.text }}
          </div>
          <span class="message-time">{{ msg.time }}</span>
        </div>
      </div>

      <div v-if="isLoading" class="message-wrapper bot">
        <VAvatar size="36" color="primary" class="mr-2">
          <VIcon icon="mdi-robot" color="white" />
        </VAvatar>
        <div class="message-bubble bot typing">
          <div class="dot"></div>
          <div class="dot"></div>
          <div class="dot"></div>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <VContainer class="pa-2">
        <div class="input-container glass-effect">
          <VTextField
            v-model="newMessage"
            placeholder="메시지를 입력하세요..."
            variant="plain"
            hide-details
            class="chat-input px-4"
            @keyup.enter="sendMessage"
            :disabled="isLoading"
          />
          <VBtn
            icon="mdi-send"
            color="primary"
            variant="flat"
            class="send-btn ml-2"
            @click="sendMessage"
            :loading="isLoading"
            :disabled="!newMessage.trim()"
          />
        </div>
      </VContainer>
    </div>
  </div>
</template>

<style scoped>
.chatbot-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px - 64px); /* AppBar - BottomNav height */
  background: #f8f9fa;
  position: relative;
}

.sticky-header {
  position: sticky;
  top: 0;
  z-index: 10;
}

.chat-content {
  flex-grow: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  scroll-behavior: smooth;
}

/* Hide scrollbar */
.chat-content::-webkit-scrollbar {
  display: none;
}
.chat-content {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.message-wrapper {
  display: flex;
  max-width: 85%;
}

.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.bot {
  align-self: flex-start;
}

.message-bubble-container {
  display: flex;
  flex-direction: column;
}

.user .message-bubble-container {
  align-items: flex-end;
}

.message-bubble {
  padding: 0.85rem 1.1rem;
  border-radius: 1.25rem;
  font-size: 0.95rem;
  line-height: 1.4;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}

.bot .message-bubble {
  background: white;
  color: #333;
  border-bottom-left-radius: 0.25rem;
}

.user .message-bubble {
  background: linear-gradient(135deg, #ff8a3d 0%, #ff7e5f 100%);
  color: white;
  border-bottom-right-radius: 0.25rem;
}

.message-time {
  font-size: 0.7rem;
  color: #999;
  margin-top: 0.3rem;
  margin-left: 0.5rem;
  margin-right: 0.5rem;
}

.chat-input-area {
  background: white;
  border-top: 1px solid rgba(0,0,0,0.05);
  padding-bottom: env(safe-area-inset-bottom);
}

.input-container {
  display: flex;
  align-items: center;
  background: #f1f3f5;
  border-radius: 2rem;
  padding: 0.25rem;
  transition: all 0.2s;
}

.input-container:focus-within {
  background: white;
  box-shadow: 0 0 0 2px rgba(255, 138, 61, 0.2);
}

.chat-input :deep(input) {
  padding: 12px 0;
}

.send-btn {
  width: 40px !important;
  height: 40px !important;
  border-radius: 50% !important;
}

/* Typing indicator */
.typing {
  display: flex;
  gap: 4px;
  padding: 12px 16px !important;
}

.dot {
  width: 6px;
  height: 6px;
  background: #ccc;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
