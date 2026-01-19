<template>
  <div class="chat-pc layout-bg">
    <div class="chat-pc__header">
      <div class="flex align-center">
        <div class="mr-12 ml-24 flex">
          <el-avatar :src="appInfo.icon" :size="32" shape="square" style="background: none; flex-shrink: 0;"></el-avatar>
        </div>
        <h4>{{ appInfo.name || '中医智能问诊系统' }}</h4>
      </div>
    </div>
    <div>
      <div class="flex">
        <div class="chat-pc__left border-r">
          <div class="p-24 pb-0">
            <el-button type="primary" @click="createNewSession" style="width: 100%;" class="add-button">
              <el-icon><Plus /></el-icon>
              <span class="ml-4">新建对话</span>
            </el-button>
            <p class="mt-20 mb-8">历史记录</p>
          </div>
          <div class="left-height pt-0">
            <div class="el-scrollbar">
              <div class="el-scrollbar__wrap el-scrollbar__wrap--hidden-default">
                <div class="el-scrollbar__view" style="">
                  <div class="p-8 pt-0">
                    <div class="common-list mt-8">
                      <ul>
                        <li
                          v-for="session in sessions"
                          :key="session.id"
                          :class="{ active: currentSessionId === session.id }"
                        >
                          <div class="flex-between">
                            <div class="session-content" @click="selectSession(session.id)">
                              <div class="session-name">{{ session.session_name }}</div>
                              <div class="session-time">{{ formatTime(session.create_time) }}</div>
                             </div>
                            <div class="session-delete-wrapper">
                              <div class="el-dropdown">
                                <el-button
                                  type="text"
                                  size="small"
                                  @click.stop="deleteSession(session.id)"
                                  class="session-delete-button"
                                >
                                  <el-icon><Delete /></el-icon>
                                </el-button>
                              </div>
                            </div>
                          </div>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="content" style="padding-left: var(--padding-left); padding-right: var(--padding-left);">
          <div class="operation-button-container">
            <div class="mt-8">
              <!-- 操作按钮区域 -->
            </div>
            <div class="chat-operation-button flex-between">
              <span class="el-text el-text--info"><span class="ml-4">{{ currentSessionName }}</span></span>
              <div>
                <!-- 操作按钮 -->
              </div>
            </div>
          </div>
          <div class="chat-messages" ref="messagesRef">
        <!-- 开场白消息 -->
        <div v-if="showGreeting && appInfo.greeting" class="message-item assistant">
          <!-- AI助手头像 -->
          <img
            :src="appInfo.model_config?.assistant_avatar || '/src/assets/assistant-avatar.png'"
            alt="AI助手头像"
            class="message-avatar"
          />
          
          <div class="message-content-wrapper">
            <div class="message-content">
              <div class="message-text greeting-text">
                <div v-html="formattedGreeting"></div>
              </div>
            </div>
            <div class="message-time">{{ formatTime(new Date()) }}</div>
          </div>
        </div>
        
        <div
          v-for="message in messages"
          :key="message.id"
          class="message-item"
          :class="message.role"
        >
          <!-- 用户头像 -->
          <img
            v-if="message.role === 'user'"
            src="/src/assets/user-avatar.jpg"
            alt="用户头像"
            class="message-avatar"
          />
          
          <!-- AI助手头像 -->
          <img
            v-else
            :src="appInfo.model_config?.assistant_avatar || appInfo.icon || 'https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=40&h=40&fit=crop&crop=faces'"
            alt="AI助手头像"
            class="message-avatar"
          />
          
          <div class="message-content-wrapper">
            <!-- 思考过程显示 - 移除了重新生成回复提示 -->
            <div class="message-content">
              <div class="message-text">
                <el-icon v-if="message.thinking" class="loading-icon">
                  <Loading />
                </el-icon>
                {{ filterMessageContent(message.content) || (message.thinking ? '正在分析您的问题' : '') }}
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
              <!-- AI助手消息操作按钮 -->
              <div v-if="message.role === 'assistant' && !message.thinking" class="message-actions">
                <el-button 
                  type="text" 
                  size="small" 
                  @click="handlePlay(message)"
                  class="action-button"
                >
                  <app-icon icon-name="app-video-play" />
                </el-button>
                <el-button 
                  type="text" 
                  size="small" 
                  @click="handleCopy(message)"
                  class="action-button"
                >
                  <app-icon icon-name="app-copy" />
                </el-button>
                <el-button 
                  type="text" 
                  size="small" 
                  @click="handleRegenerate(message)"
                  class="action-button"
                >
                  <app-icon icon-name="app-sync" />
                </el-button>
                <el-button 
                  type="text" 
                  size="small" 
                  @click="handleLike(message)"
                  class="action-button"
                >
                  <app-icon icon-name="app-like" />
                </el-button>
                <el-button 
                  type="text" 
                  size="small" 
                  @click="handleDislike(message)"
                  class="action-button"
                >
                  <app-icon icon-name="app-oppose" />
                </el-button>
              </div>
            </div>
            <div class="message-time">{{ formatTime(message.create_time) }}</div>
          </div>
        </div>
      </div>
      
      <!-- 使用新的聊天输入组件 -->
      <div class="chat-input">
        <ChatInput
          @send="handleChatSend"
          :disabled="sending"
          :enable-file-upload="enableFileUpload"
        />
      </div>
    </div>
  </div>
</div>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Loading, Delete, Search } from '@element-plus/icons-vue'
import AppIcon from '@/components/app-icon/AppIcon.vue'
import ChatInput from '@/components/chat-input/ChatInput.vue'
import { applicationApi, chatApi, type Application, type ChatSession, type ChatMessage } from '@/api'
import request from '@/utils/request'
import dayjs from 'dayjs'

const route = useRoute()
const sessions = ref<ChatSession[]>([])
const messages = ref<ChatMessage[]>([])
const currentSessionId = ref('')
const currentSessionName = ref('新建对话')
const inputMessage = ref('')
const sending = ref(false)
const messagesRef = ref<HTMLElement | null>(null)

// 应用信息
const appInfo = ref({
  name: '中医智能问诊系统',
  icon: '',
  model_config: {},
  greeting: '您好，我是江小智——中医智能问诊小助手，您可以向我提出问题。\n\n- 主要功能有什么？\n- 怎样预防传染病？\n- 推荐用药'
})

// 监听appInfo变化，调试assistant_avatar
watch(() => appInfo.value.model_config, (newModelConfig) => {
  console.log('appInfo.model_config changed:', newModelConfig)
  console.log('assistant_avatar:', newModelConfig?.assistant_avatar)
}, { immediate: true })

// 开场白显示状态
const showGreeting = ref(true)

// 格式化开场白，支持可交互的示例问题
const formattedGreeting = ref('')

// 处理聊天发送
const handleChatSend = async (message: string, files: Array<any>) => {
  // 调用原来的sendMessage方法，传递消息内容
  await sendMessage(message, files)
}

// 语音输入设置
const voiceInputEnabled = ref(true) // 默认启用语音输入

// 文件上传设置
const enableFileUpload = ref(true) // 默认启用文件上传









// 格式化开场白，将示例问题转换为可点击的链接
const formatGreeting = (greeting: string) => {
  // 将开场白文本分为普通文本和预设问题两部分
  const parts = greeting.split('\n\n')
  const mainText = parts[0] || ''
  const questions = parts[1] || ''
  
  // 格式化预设问题为纵向排列的可点击标签
  let questionsHtml = ''
  if (questions) {
    const questionList = questions.match(/- (.*?)(\n|$)/g) || []
    if (questionList.length > 0) {
      questionsHtml = '<div style="margin-top: 12px;">'
      questionList.forEach(q => {
        const questionText = q.replace(/- (.*?)(\n|$)/, '$1')
        questionsHtml += `<div class="example-question" style="background-color: #f0f2f5 !important; color: #303133 !important; padding: 8px 16px !important; border-radius: 12px !important; cursor: pointer !important; font-size: 14px !important; transition: all 0.3s ease !important; user-select: none !important; display: block !important; margin: 4px 0 !important; width: fit-content !important;">${questionText}</div>`
      })
      questionsHtml += '</div>'
    }
  }
  
  // 组合最终的HTML
  return `${mainText}<br>${questionsHtml}`
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
    // 先移除旧的事件监听器，避免重复绑定
    link.removeEventListener('click', handleExampleQuestionClick)
    // 添加新的事件监听器
    link.addEventListener('click', handleExampleQuestionClick)
  })
}

// 处理播放按钮点击
const handlePlay = (message: ChatMessage) => {
  // 播放功能实现 - 使用浏览器Web Speech API
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(message.content)
    // 设置默认语音参数
    utterance.lang = 'zh-CN'
    utterance.rate = 1.0
    utterance.pitch = 1.0
    utterance.volume = 1.0
    
    // 开始播放
    speechSynthesis.speak(utterance)
    
    // 显示播放状态
    ElMessage.success('正在播放...')
  } else {
    ElMessage.error('您的浏览器不支持语音播放功能')
  }
}

// 处理复制按钮点击
const handleCopy = (message: ChatMessage) => {
  // 复制功能实现
  navigator.clipboard.writeText(message.content).then(() => {
    ElMessage.success('复制成功')
  }).catch(err => {
    console.error('复制失败:', err)
    ElMessage.error('复制失败')
  })
}

// 处理重新生成按钮点击
const handleRegenerate = async (message: ChatMessage) => {
  // 重新生成功能实现
  try {
    // 找到当前消息的索引
    const messageIndex = messages.value.findIndex(msg => msg.id === message.id)
    if (messageIndex === -1) {
      ElMessage.error('找不到对应的消息')
      return
    }
    
    // 获取该消息对应的用户消息（应该是前一条消息）
    const userMessage = messages.value[messageIndex - 1]
    if (!userMessage || userMessage.role !== 'user') {
      ElMessage.error('找不到对应的用户消息')
      return
    }
    
    // 标记消息为重新生成中
    messages.value[messageIndex] = {
      ...messages.value[messageIndex],
      thinking: true,
      content: ''
      // 移除了thought属性，不再显示重新生成提示
    } as ExtendedChatMessage
    
    await nextTick()
    scrollToBottom()
    
    // 创建新的AbortController
    currentAbortController = new AbortController()
    const { signal } = currentAbortController
    
    // 发送请求获取新的AI回复
    const token = localStorage.getItem('token')
    const response = await fetch('/api/chat/stream/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify({
        application_id: 'default',
        message: userMessage.content,
        session_id: currentSessionId.value,
        regenerate: true,
        original_message_id: message.id
      }),
      signal
    })
    
    if (!response.ok) {
      throw new Error(`Network response was not ok: ${response.statusText}`)
    }
    
    // 读取流式响应
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('Response body is not a readable stream')
    }
    
    const decoder = new TextDecoder()
    let fullResponse = ''
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        // 更新消息为完成状态
        messages.value[messageIndex] = {
          ...messages.value[messageIndex],
          thinking: false,
          thought: '',
          content: fullResponse
        } as ExtendedChatMessage
        await nextTick()
        scrollToBottom()
        currentAbortController = null
        break
      }
      
      // 解码并更新消息内容
        const chunk = decoder.decode(value, { stream: true })
        
        // 当收到第一个回复chunk时，设置thinking为false并清空内容从新开始
        if (!fullResponse) {
            fullResponse = ''
        }
        fullResponse += chunk
        
        messages.value[messageIndex] = {
          ...messages.value[messageIndex],
          thinking: false, // 开始回复时关闭思考状态
          content: fullResponse // 从空开始逐步累加回复内容
        } as ExtendedChatMessage
      
      await nextTick()
      scrollToBottom()
    }
    
    ElMessage.success('回复已重新生成')
  } catch (error) {
    console.error('重新生成失败:', error)
    ElMessage.error('重新生成失败，请稍后重试')
    
    // 恢复消息状态
    const messageIndex = messages.value.findIndex(msg => msg.id === message.id)
    if (messageIndex !== -1) {
      messages.value[messageIndex] = {
        ...messages.value[messageIndex],
        thinking: false,
        thought: ''
      } as ExtendedChatMessage
    }
  }
}

// 处理赞同按钮点击
const handleLike = async (message: ChatMessage) => {
  try {
    console.log('发送点赞请求, messageId:', message.id)
    await request.post(`/chat/message/${message.id}/rate/`, { satisfaction: 1 })
    ElMessage.success('赞同成功')
  } catch (error) {
    console.error('赞同失败:', error)
    ElMessage.error('操作失败，请重试')
  }
}

// 处理反对按钮点击
const handleDislike = async (message: ChatMessage) => {
  try {
    console.log('发送反对请求, messageId:', message.id)
    await request.post(`/chat/message/${message.id}/rate/`, { satisfaction: 0 })
    ElMessage.success('反对成功')
  } catch (error) {
    console.error('反对失败:', error)
    ElMessage.error('操作失败，请重试')
  }
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
    if (sessions.value.length > 0) {
      if (!currentSessionId.value) {
        selectSession(sessions.value[0].id)
      } else {
        // 如果已有选中的会话，更新会话名称
        const selectedSession = sessions.value.find(session => session.id === currentSessionId.value)
        if (selectedSession) {
          currentSessionName.value = selectedSession.session_name
        }
      }
    }
    
    // 加载应用信息，获取语音输入设置
    const applications = await applicationApi.getApplications()
    if (applications.length > 0) {
      const app = applications[0]
      // 更新应用信息
      appInfo.value = {
        name: app.name || '中医智能问诊',
        icon: app.icon || '',
        model_config: app.model_config || {},
        greeting: app.model_config?.greeting || '您好，我是江小智——中医智能问诊小助手，您可以向我提出问题。\n\n- 主要功能有什么？\n- 怎样预防传染病？\n- 推荐用药'
      }
      // 更新语音输入设置
      voiceInputEnabled.value = app.model_config?.voice_input || false
      // 更新文件上传设置（处理null和undefined情况）
      enableFileUpload.value = app.enable_file_upload ?? true
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
  // 更新当前会话名称
  const selectedSession = sessions.value.find(session => session.id === sessionId)
  if (selectedSession) {
    currentSessionName.value = selectedSession.session_name
  }
  loadMessages(sessionId)
}

const createNewSession = async () => {
  try {
    const session = await chatApi.createSession({
      application_id: 'default' // 使用默认应用ID，不指定会话名称，由后端生成
    })
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    currentSessionName.value = session.session_name
    messages.value = []
  } catch (error) {
    console.error('创建会话失败:', error)
    ElMessage.error('创建会话失败')
  }
}

const deleteSession = async (sessionId: string) => {
  try {
    await chatApi.deleteSession(sessionId)
    // 从会话列表中移除
    const index = sessions.value.findIndex(session => session.id === sessionId)
    if (index !== -1) {
      sessions.value.splice(index, 1)
    }
    // 如果删除的是当前会话，或者会话列表为空，创建新会话
    if (currentSessionId.value === sessionId || sessions.value.length === 0) {
      if (sessions.value.length > 0) {
        // 如果还有其他会话，切换到第一个
        currentSessionId.value = sessions.value[0].id
        await loadMessages(sessions.value[0].id)
      } else {
        // 如果没有会话，创建新会话
        await createNewSession()
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error)
    ElMessage.error('删除会话失败')
  }
}

// 用于存储当前正在进行的fetch请求控制器
let currentAbortController = null

const sendMessage = async (messageContent: string, files: Array<any> = []) => {
  console.log('sendMessage function called')
  if (!messageContent.trim() && files.length === 0) return
  
  // 如果有正在进行的请求，取消它
  if (currentAbortController) {
    currentAbortController.abort()
    currentAbortController = null
  }
  
  // 创建新的AbortController
  currentAbortController = new AbortController()
  const { signal } = currentAbortController
  
  // 记录当前会话ID，用于后续检查
  let originalSessionId = currentSessionId.value
  
  // 立即将用户消息添加到聊天记录
  const userMessage = {
    id: Date.now().toString(),
    role: 'user',
    content: messageContent,
    message_type: files.length > 0 ? 'multimodal' : 'text',
    create_time: new Date().toISOString()
  } as ExtendedChatMessage
  messages.value.push(userMessage)
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  // 添加AI回复占位符，显示"正在分析您的问题"
  const aiMessage = {
    id: (Date.now() + 1).toString(),
    role: 'assistant',
    content: '',
    message_type: 'text',
    create_time: new Date().toISOString(),
    thinking: true
    // 移除默认思考过程，只在回复框中显示"正在分析您的问题"
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
        console.log('Files:', files)
        
        // 确保session_id存在
        if (!originalSessionId) {
            console.error('No session ID found, creating new session...')
            await createNewSession()
            // 使用新创建的会话ID继续发送消息
            const newSessionId = currentSessionId.value
            if (newSessionId) {
                originalSessionId = newSessionId
            } else {
                throw new Error('Failed to create new session')
            }
        }
        
        // 准备请求数据
        const requestData = {
            application_id: 'default',
            message: messageContent,
            session_id: originalSessionId,
            files: files.map(file => ({
                file_id: file.file_id,
                name: file.name,
                type: file.type,
                url: file.url
            }))
        }
        
        const response = await fetch('/api/chat/stream/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : ''
            },
            body: JSON.stringify(requestData),
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
                // 重新加载会话列表，获取更新后的会话名称
                await loadSessions()
                currentAbortController = null
                break
            }
            
            // 解码数据
            const chunk = decoder.decode(value, { stream: true })
            console.log('Received chunk:', chunk)
            
            // 当收到第一个回复chunk时，设置thinking为false并清空内容从新开始
            if (!fullResponse) {
                fullResponse = ''
            }
            fullResponse += chunk
            
            // 使用索引更新整个消息对象，确保Vue能检测到变化
            const messageIndex = messages.value.findIndex(msg => msg.id === aiMessage.id)
            if (messageIndex !== -1) {
                messages.value[messageIndex] = {
                    ...messages.value[messageIndex],
                    thinking: false, // 开始回复时关闭思考状态
                    content: fullResponse // 从空开始逐步累加回复内容
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
        model_config: parsedModelConfig,
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
/* MaxKB风格样式 */
.chat-pc {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.chat-pc__header {
  display: flex;
  align-items: center;
  height: 64px;
  background-color: #ffffff;
  border-bottom: 1px solid #ebeef5;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.flex {
  display: flex;
}

.align-center {
  align-items: center;
}

.mr-12 {
  margin-right: 12px;
}

.ml-24 {
  margin-left: 24px;
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-pc__left {
  width: 280px;
  border-right: 1px solid #ebeef5;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
}

.p-24 {
  padding: 24px;
}

.pb-0 {
  padding-bottom: 0;
}

.add-button {
  margin-bottom: 16px;
}

.mt-20 {
  margin-top: 20px;
}

.mb-8 {
  margin-bottom: 8px;
}

.left-height {
  flex: 1;
  overflow: hidden;
}

.pt-0 {
  padding-top: 0;
}

.common-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.common-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.common-list li {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
  list-style: none;
}

.common-list li:hover {
  background-color: #f5f7fa;
}

.common-list li.active {
  background-color: #ecf5ff;
  border: 1px solid #409eff;
}

.cursor {
  cursor: pointer;
}

.session-delete-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.common-list li:hover .session-delete-wrapper {
  opacity: 1;
}

.session-delete-button {
  color: #909399;
  padding: 4px;
  min-height: 24px;
  width: 24px;
}

.session-delete-button:hover {
  color: #f56c6c;
}

.session-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-name {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-time {
  font-size: 12px;
  color: #909399;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  height: calc(100vh - 64px);
}

.operation-button-container {
  padding: 16px 24px;
  border-bottom: 1px solid #ebeef5;
}

.mt-8 {
  margin-top: 8px;
}

.chat-operation-button {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background-color: #fafafa;
}

.message-item {
  margin-bottom: 24px;
  display: flex;
  align-items: flex-start;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.assistant {
  flex-direction: row;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  margin: 0 12px;
  object-fit: cover;
  flex-shrink: 0;
}

.thought-process {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  padding-left: 52px;
  font-style: italic;
  line-height: 1.4;
}

.message-content {
  max-width: 90%;
}

.message-item.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-item.assistant .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
  position: relative;
  word-wrap: normal;
  word-break: keep-all;
  overflow-wrap: break-word;
}

.message-item.user .message-text {
  background-color: #409eff;
  color: white;
  border-bottom-right-radius: 4px;
}

.message-item.assistant .message-text {
  background-color: #ffffff;
  color: #303133; /* 确保正常消息文本是黑色 */
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.message-item.user .message-time {
  text-align: right;
  padding-right: 12px;
}

.message-item.assistant .message-time {
  text-align: left;
  padding-left: 12px;
}

.loading-icon {
  display: inline-block;
  margin-right: 8px;
  font-size: 14px;
  animation: spin 1s linear infinite;
  vertical-align: middle;
}

/* AI思考中状态样式 - 只对包含加载图标的文本应用浅灰色 */
.message-item.assistant .message-text:has(.loading-icon) {
  font-size: 12px;
  color: #909399 !important; /* 仅思考状态文本是浅灰色 */
  white-space: nowrap !important; /* 强制在一行显示 */
  min-width: fit-content;
  display: inline-block !important; /* 确保是块级元素但内容在一行 */
  align-items: center;
  width: auto !important;
  max-width: 85% !important; /* 限制最大宽度 */
  line-height: 1.2; /* 确保行高合适 */
  padding: 12px 16px; /* 确保内边距一致 */
  margin: 0; /* 移除可能的外边距 */
}

/* 确保AI思考时的文本容器不会换行 */
.message-item.assistant:has(.loading-icon) .message-content {
  max-width: 85% !important;
  width: auto !important;
  white-space: nowrap !important;
  display: inline-block !important;
}

/* 确保AI思考时的整个消息项不换行 */
.message-item.assistant:has(.loading-icon) {
  white-space: nowrap !important;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.message-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding-right: 0;
  justify-content: flex-end;
  width: 100%;
}

.action-button {
  font-size: 10px;
  color: #909399;
  transition: color 0.3s;
  background: none;
  border: none;
  padding: 2px 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
}

.action-button:hover {
  color: #409eff;
}

.chat-input {
  padding: 24px;
  border-top: 1px solid #ebeef5;
  background-color: #ffffff;
}

/* 开场白样式 */
.greeting-text {
  line-height: 1.6;
}

/* 示例问题样式 */
.example-question {
  background-color: #f5f7fa !important;
  color: #606266 !important;
  padding: 8px 16px !important;
  border-radius: 20px !important;
  cursor: pointer !important;
  margin-right: 16px !important;
  margin-bottom: 12px !important;
  display: inline-block !important;
  font-weight: 400 !important;
  font-size: 14px !important;
  transition: all 0.3s ease !important;
  text-decoration: none !important;
  border: none !important;
  line-height: 1.5 !important;
  vertical-align: middle !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

.example-question:hover {
  background-color: #e6e8eb !important;
  color: #409eff !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
}

/* 检索结果样式 */
.search-results {
  margin-top: 16px;
  padding: 16px;
  background-color: #f0f9ff;
  border: 1px solid #e0f2fe;
  border-radius: 12px;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.results-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  color: #0284c7;
  font-weight: 500;
}

.results-header el-icon {
  margin-right: 8px;
  font-size: 16px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-item {
  padding: 16px;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.result-title {
  font-weight: 500;
  margin-bottom: 8px;
  color: #1e40af;
  font-size: 14px;
}

.result-content {
  color: #334155;
  line-height: 1.5;
  margin-bottom: 8px;
  font-size: 13px;
}

.result-score {
  font-size: 12px;
  color: #64748b;
  text-align: right;
}

/* 滚动条样式 */
.el-scrollbar__wrap {
  overflow-x: hidden !important;
}

/* 动画效果 */
@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}
</style>
