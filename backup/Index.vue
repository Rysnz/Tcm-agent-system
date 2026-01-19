<template>
  <div class="chat-container">
    <div class="chat-sidebar">
      <h3>会话管理</h3>
      
      <div class="session-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: currentSessionId === session.id }"
        >
          <div class="session-content" @click="selectSession(session.id)">
            <div class="session-name">{{ session.session_name }}</div>
            <div class="session-time">{{ formatTime(session.create_time) }}</div>
          </div>
          <el-button 
            type="text" 
            @click.stop="deleteSession(session.id)"
            size="small"
            class="delete-session-btn"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
      
      <el-button type="primary" @click="createNewSession" style="width: 100%">
        <el-icon><Plus /></el-icon>
        新建会话
      </el-button>
    </div>
    
    <div class="chat-main">
      <!-- 聊天头部，显示应用名称和图标 -->
      <div class="chat-header">
        <div class="app-info">
          <img v-if="appInfo.icon" :src="appInfo.icon" class="app-icon" />
          <h3 class="app-name">{{ appInfo.name || '中医智能问诊' }}</h3>
        </div>
      </div>
      
      <div class="chat-messages" ref="messagesRef">
        <!-- 开场白消息 -->
        <div v-if="showGreeting && appInfo.greeting" class="message-item assistant">
          <div class="message-content">
            <div class="message-role">中医助手</div>
            <div class="message-text greeting-text">
              <div v-html="formattedGreeting"></div>
            </div>
          </div>
          <div class="message-time">{{ formatTime(new Date()) }}</div>
        </div>
        
        <div
          v-for="message in messages"
          :key="message.id"
          class="message-item"
          :class="message.role"
        >
          <!-- 思考过程显示 -->
          <div v-if="message.thought" class="thought-process">
            {{ message.thought }}
          </div>
          <div class="message-content">
            <div class="message-role">
              {{ message.role === 'user' ? '我' : '中医助手' }}
            </div>
            <div class="message-text">
              {{ filterMessageContent(message.content) || (message.thinking ? '思考中...' : '') }}
              <el-icon v-if="message.thinking" class="loading-icon">
                <Loading />
              </el-icon>
            </div>
            <!-- 检索结果显示区域 -->
            <div v-if="message.search_results && message.search_results.length > 0" class="search-results">
              <div class="results-header">
                <el-icon><Search /></el-icon>
                <span>相关文档内容 ({{ message.search_results.length }}条)</span>
              </div>
              <div class="results-list">
                <div v-for="(result, index) in message.search_results" :key="result.id" class="result-item">
                  <div class="result-title">{{ result.title || `相关内容${index + 1}` }}</div>
                  <div class="result-content">{{ result.content }}</div>
                  <div class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</div>
                </div>
              </div>
            </div>
          </div>
          <div class="message-time">{{ formatTime(message.create_time) }}</div>
        </div>
      </div>
      
      <div class="chat-input">
        <div class="input-wrapper">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="请描述您的症状或问题..."
            @keydown.ctrl.enter="sendMessage"
          >
            <template #append>
              <el-button
                type="text"
                @click="handleVoiceInput"
                :disabled="isRecording"
                class="voice-input-button"
              >
                <el-icon :class="{ 'recording': isRecording }">
                  <Microphone />
                </el-icon>
              </el-button>
            </template>
          </el-input>
        </div>
        <div class="input-actions">
          <div class="satisfaction-feedback" v-if="messages.length > 0 && messages[messages.length - 1].role === 'assistant'">
            <span class="feedback-text">满意吗？</span>
            <el-button type="text" @click="handleSatisfaction('like')">
              <el-icon><ThumbsUp /></el-icon>
            </el-button>
            <el-button type="text" @click="handleSatisfaction('dislike')">
              <el-icon><ThumbsDown /></el-icon>
            </el-button>
          </div>
          <el-button type="primary" @click="sendMessage" :loading="sending">
            发送 (Ctrl+Enter)
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Loading, Microphone, Delete } from '@element-plus/icons-vue'
import { applicationApi, chatApi, type Application, type ChatSession, type ChatMessage } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const sessions = ref<ChatSession[]>([])
const messages = ref<ChatMessage[]>([])
const currentSessionId = ref('')
const inputMessage = ref('')
const sending = ref(false)
const messagesRef = ref<HTMLElement | null>(null)

// 应用信息
const appInfo = ref({
  name: '中医智能问诊系统',
  icon: '',
  greeting: '您好，我是江小智——中医智能问诊小助手，您可以向我提出问题。\n\n- 主要功能有什么？\n- 怎样预防传染病？\n- 推荐用药'
})

// 开场白显示状态
const showGreeting = ref(true)

// 格式化开场白，支持可交互的示例问题
const formattedGreeting = ref('')

// 语音输入状态
const voiceInputEnabled = ref(false)
const isRecording = ref(false)

// 处理语音输入
const handleVoiceInput = () => {
  // 语音输入功能实现
  ElMessage.info('语音输入功能开发中')
}

// 格式化开场白，将示例问题转换为可点击的链接
  const formatGreeting = (greeting: string) => {
    let formatted = greeting.replace(/\n/g, '<br>')
    // 将示例问题转换为可点击的链接
    formatted = formatted.replace(/- (.*?)(<br>|$)/g, '<br><a href="javascript:void(0);" class="example-question">$1</a>$2')
    return formatted
  }

  // 处理示例问题点击
  const handleExampleQuestionClick = (event: MouseEvent) => {
    const target = event.target as HTMLElement
    if (target.classList.contains('example-question')) {
      const question = target.textContent || ''
      inputMessage.value = question
      sendMessage()
    }
  }

  // 监听示例问题点击事件
  const addExampleQuestionListeners = () => {
    const questionLinks = document.querySelectorAll('.example-question')
    questionLinks.forEach(link => {
      link.addEventListener('click', handleExampleQuestionClick)
    })
  }

// 处理满意度反馈
const handleSatisfaction = (type: 'like' | 'dislike') => {
  // 满意度反馈功能实现
  ElMessage.success(`已${type === 'like' ? '点赞' : '点踩'}`)
  // TODO: 将反馈发送到后端
}

// 简化的消息类型，支持思考过程和检索结果
interface SearchResult {
  id: string
  content: string
  title: string
  score: number
}

interface ExtendedChatMessage extends ChatMessage {
  thinking?: boolean
  thought?: string
  search_results?: SearchResult[]
}

const loadSessions = async () => {
  try {
    // 使用默认应用ID或空字符串，让后端处理
    sessions.value = await chatApi.getSessions('default')
    // 如果有会话且当前没有选中会话，自动选择第一个会话
    if (sessions.value.length > 0 && !currentSessionId.value) {
      selectSession(sessions.value[0].id)
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
    ElMessage.error('加载会话列表失败')
  }
}

const loadMessages = async (sessionId: string) => {
  try {
    messages.value = await chatApi.getMessages(sessionId)
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('加载消息失败:', error)
    ElMessage.error('加载消息失败')
  }
}

const selectSession = (sessionId: string) => {
  currentSessionId.value = sessionId
  loadMessages(sessionId)
}

const createNewSession = async () => {
  try {
    const session = await chatApi.createSession({
      application_id: 'default', // 使用默认应用ID
      session_name: `会话${sessions.value.length + 1}`
    })
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    messages.value = []
  } catch (error) {
    console.error('创建会话失败:', error)
    ElMessage.error('创建会话失败')
  }
}

// 删除会话
const deleteSession = async (sessionId: string) => {
  try {
    const isCurrentSession = currentSessionId.value === sessionId
    await chatApi.deleteSession(sessionId)
    sessions.value = sessions.value.filter(session => session.id !== sessionId)
    if (isCurrentSession) {
      await createNewSession()
    }
  } catch (error) {
    ElMessage.error('删除会话失败')
  }
}

// 用于存储当前正在进行的fetch请求控制器
let currentAbortController = null

const sendMessage = async () => {
  console.log('sendMessage function called')
  if (!inputMessage.value.trim()) return
  
  // 如果有正在进行的请求，取消它
  if (currentAbortController) {
    currentAbortController.abort()
    currentAbortController = null
  }
  
  // 创建新的AbortController
  currentAbortController = new AbortController()
  const { signal } = currentAbortController
  
  // 记录当前会话ID，用于后续检查
  const originalSessionId = currentSessionId.value
  
  // 立即将用户消息添加到聊天记录
  const userMessage = {
    id: Date.now().toString(),
    role: 'user',
    content: inputMessage.value,
    message_type: 'text',
    create_time: new Date().toISOString()
  } as ExtendedChatMessage
  messages.value.push(userMessage)
  
  // 清空输入框
  const messageContent = inputMessage.value
  inputMessage.value = ''
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  // 添加AI回复占位符，显示"思考中..."
  const aiMessage = {
    id: (Date.now() + 1).toString(),
    role: 'assistant',
    content: '',
    message_type: 'text',
    create_time: new Date().toISOString(),
    thinking: true,
    thought: '正在分析您的问题...' // 默认思考过程
  } as ExtendedChatMessage
  messages.value.push(aiMessage)
  await nextTick()
  scrollToBottom()
  
  // 发送请求获取AI回复
    try {
        // 使用fetch API实现流式响应
        console.log('Sending message with streaming response...')
        const token = localStorage.getItem('token')
        console.log('Token:', token)
        console.log('Message content:', messageContent)
        console.log('Session ID:', originalSessionId)
        
        // 确保session_id存在
        if (!originalSessionId) {
            console.error('No session ID found, creating new session...')
            await createNewSession()
            return
        }
        
        const response = await fetch('/api/chat/stream/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : ''
            },
            body: JSON.stringify({
                application_id: 'default',
                message: messageContent,
                session_id: originalSessionId
            }),
            signal // 添加AbortSignal，用于取消请求
        })
        console.log('Streaming response received:', response)
        console.log('Response status:', response.status)
        console.log('Response headers:', response.headers)
        
        if (!response.ok) {
            const errorText = await response.text()
            throw new Error(`Network response was not ok: ${response.statusText}, ${errorText}`)
        }
        
        // 获取可读流
        const reader = response.body?.getReader()
        if (!reader) {
            throw new Error('Response body is not a readable stream')
        }
        
        const decoder = new TextDecoder()
        let fullResponse = ''
        
        // 逐块读取响应
        while (true) {
            const { done, value } = await reader.read()
            console.log('Reader read result:', { done, value: value ? value.length : 0 })
            
            // 检查是否已切换会话，如果是则取消读取
            if (currentSessionId.value !== originalSessionId) {
                console.log('Session changed, aborting reading...')
                await reader.cancel()
                currentAbortController = null
                break
            }
            
            if (done) {
                console.log('Streaming response done')
                // 确保思考中状态被关闭 - 使用Vue.set或直接替换对象确保响应式更新
                const messageIndex = messages.value.findIndex(msg => msg.id === aiMessage.id)
                if (messageIndex !== -1) {
                    messages.value[messageIndex] = {
                        ...messages.value[messageIndex],
                        thinking: false,
                        thought: ''
                    }
                }
                await nextTick()
                scrollToBottom()
                currentAbortController = null
                break
            }
            
            // 解码数据
            const chunk = decoder.decode(value, { stream: true })
            console.log('Received chunk:', chunk)
            fullResponse += chunk
            
            // 使用索引更新整个消息对象，确保Vue能检测到变化
            const messageIndex = messages.value.findIndex(msg => msg.id === aiMessage.id)
            if (messageIndex !== -1) {
                messages.value[messageIndex] = {
                    ...messages.value[messageIndex],
                    content: fullResponse
                }
            }
            
            // 使用nextTick确保UI更新
            await nextTick()
            scrollToBottom()
        }
    } catch (error) {
      // 检查是否是用户主动取消的请求
      if (error.name === 'AbortError') {
        console.log('Fetch request aborted')
        return
      }
      
      console.error('发送消息失败:', error)
      ElMessage.error('发送消息失败')
      
      // 只有在当前会话没有切换时，才更新AI回复
      if (currentSessionId.value === originalSessionId) {
        // 更新AI回复为错误信息 - 使用索引更新确保响应式
        const messageIndex = messages.value.findIndex(msg => msg.id === aiMessage.id)
        if (messageIndex !== -1) {
          messages.value[messageIndex] = {
            ...messages.value[messageIndex],
            content: '抱歉，处理您的请求时出现错误，请稍后重试',
            thinking: false,
            thought: ''
          }
        }
        await nextTick()
        scrollToBottom()
      }
      
      currentAbortController = null
    }
}

const scrollToBottom = () => {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

// 过滤消息内容，移除Markdown格式的**符号
const filterMessageContent = (content: string) => {
  if (!content) return ''
  // 移除**符号（用于粗体的Markdown语法）
  return content.replace(/\*\*/g, '')
}

onMounted(async () => {
  try {
    // 从API获取应用信息
    const applications = await applicationApi.getApplications()
    if (applications.length > 0) {
      const app = applications[0]
      
      // 解析model_config字符串为对象
      let parsedModelConfig = {};
      try {
        if (typeof app.model_config === 'string') {
          parsedModelConfig = JSON.parse(app.model_config);
        } else {
          parsedModelConfig = app.model_config || {};
        }
      } catch (error) {
        console.error('解析model_config失败:', error);
        parsedModelConfig = {};
      }
      
      appInfo.value = {
        name: app.name,
        icon: app.icon,
        greeting: parsedModelConfig.greeting || appInfo.value.greeting
      }
    }
    
    // 格式化开场白
    formattedGreeting.value = formatGreeting(appInfo.value.greeting)
    
    // 加载会话列表
    loadSessions()
    
    // 添加示例问题点击事件监听器
    nextTick(() => {
      addExampleQuestionListeners()
    })
  } catch (error) {
    console.error('加载应用信息失败:', error)
    ElMessage.error('加载应用信息失败')
    
    // 格式化开场白
    formattedGreeting.value = formatGreeting(appInfo.value.greeting)
    
    // 加载会话列表
    loadSessions()
    
    // 添加示例问题点击事件监听器
    nextTick(() => {
      addExampleQuestionListeners()
    })
  }
})

watch(() => route.path, (newPath) => {
  if (newPath === '/chat') {
    loadSessions()
    // 格式化开场白
    formattedGreeting.value = formatGreeting(appInfo.value.greeting)
    
    // 添加示例问题点击事件监听器
    nextTick(() => {
      addExampleQuestionListeners()
    })
  }
})

// 监听会话变化，加载消息
watch(() => currentSessionId.value, (newSessionId) => {
  if (newSessionId) {
    loadMessages(newSessionId)
    // 切换会话时显示开场白
    showGreeting.value = true
    formattedGreeting.value = formatGreeting(appInfo.value.greeting)
    
    // 重新添加示例问题点击事件监听器
    nextTick(() => {
      addExampleQuestionListeners()
    })
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 60px);
}

.chat-sidebar {
  width: 300px;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.chat-sidebar h3 {
  margin: 0 0 20px 0;
}

.loading-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #909399;
}

.empty-tip {
  padding: 20px;
}

/* 聊天头部样式 */
.chat-header {
  padding: 15px 20px;
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
}

.app-info {
  display: flex;
  align-items: center;
}

.app-icon {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  margin-right: 10px;
  object-fit: cover;
}

.app-name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

/* 开场白样式 */
.greeting-text {
  line-height: 1.6;
}

.example-question {
  color: #409eff;
  text-decoration: none;
  cursor: pointer;
  margin-right: 15px;
  font-weight: 500;
  transition: color 0.3s;
}

.example-question:hover {
  color: #66b1ff;
  text-decoration: underline;
}

/* 输入区域样式 */
.input-wrapper {
  position: relative;
}

.voice-input-button {
  font-size: 18px;
  color: #909399;
  transition: color 0.3s;
}

.voice-input-button:hover {
  color: #409eff;
}

.voice-input-button .el-icon {
  transition: transform 0.3s;
}

.voice-input-button .el-icon.recording {
  color: #f56c6c;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

/* 满意度反馈样式 */
.satisfaction-feedback {
  display: flex;
  align-items: center;
  margin-right: 15px;
}

.feedback-text {
  margin-right: 10px;
  color: #909399;
  font-size: 14px;
}

.satisfaction-feedback .el-button {
  padding: 0;
  margin: 0 5px;
}

.satisfaction-feedback .el-icon {
  font-size: 18px;
  color: #909399;
  transition: color 0.3s;
}

.satisfaction-feedback .el-button:hover .el-icon {
  color: #409eff;
}

/* 输入操作区样式 */
.input-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 10px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
}

.session-item {
  padding: 12px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 8px;
}

.session-item:hover {
  background: #f5f7fa;
}

.session-item.active {
  background: #ecf5ff;
  border: 1px solid #409eff;
}

.session-name {
  font-weight: bold;
  margin-bottom: 4px;
}

.session-time {
  font-size: 12px;
  color: #909399;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message-item {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.message-item.user {
  align-items: flex-end;
}

.message-item.assistant {
  align-items: flex-start;
}

/* 思考过程样式 - MaxKB风格 */
.thought-process {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  padding-left: 40px;
  font-style: italic;
  line-height: 1.4;
}

.message-content {
  max-width: 70%;
}

.message-role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.message-text {
  padding: 12px;
  border-radius: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
  position: relative;
}

.loading-icon {
  display: inline-block;
  margin-left: 8px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.message-item.user .message-text {
  background: #409eff;
  color: #fff;
}

.message-item.assistant .message-text {
  background: #f5f7fa;
  color: #303133;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 检索结果样式 */
.search-results {
  margin-top: 12px;
  padding: 12px;
  background-color: #f0f9ff;
  border: 1px solid #e0f2fe;
  border-radius: 8px;
  font-size: 14px;
}

.results-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: #0284c7;
  font-weight: bold;
}

.results-header el-icon {
  margin-right: 6px;
  font-size: 16px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  padding: 10px;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}

.result-title {
  font-weight: bold;
  margin-bottom: 6px;
  color: #1e40af;
  font-size: 14px;
}

.result-content {
  color: #334155;
  line-height: 1.5;
  margin-bottom: 6px;
  font-size: 13px;
}

.result-score {
  font-size: 12px;
  color: #64748b;
  text-align: right;
}

.chat-input {
  padding: 20px;
  border-top: 1px solid #ebeef5;
}

.input-actions {
  margin-top: 10px;
  text-align: right;
}
</style>
