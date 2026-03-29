<template>
  <div class="consult-page">
    <!-- 左侧边栏：历史会话 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <el-button type="primary" class="new-session-btn" @click="startNewSession">
          <el-icon><Plus /></el-icon>
          新建问诊
        </el-button>
      </div>
      <div class="session-list">
        <div
          v-for="s in sessionHistory"
          :key="s.session_id"
          class="session-item"
          :class="{ active: currentSessionId === s.session_id }"
          @click="loadSession(s.session_id)"
        >
          <el-icon class="session-icon"><ChatDotRound /></el-icon>
          <div class="session-meta">
            <span class="session-title">{{ s.title }}</span>
            <span class="session-time">{{ s.time }}</span>
          </div>
          <el-popconfirm
            title="确定要删除这个会话吗？删除后无法恢复。"
            confirm-button-text="确认删除"
            cancel-button-text="取消"
            @confirm="deleteSession(s.session_id, $event)"
          >
            <template #reference>
              <el-button
                type="danger"
                text
                size="small"
                class="delete-btn"
                @click.stop
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-popconfirm>
        </div>
        <el-empty v-if="!sessionHistory.length" description="暂无历史记录" :image-size="60" />
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 顶部导航栏 -->
      <div class="content-header">
        <div class="header-left">
          <el-tag type="info" size="small" effect="plain">
            <el-icon><Stethoscope /></el-icon>
            多智能体协同问诊
          </el-tag>
          <span class="stage-badge" :class="stageBadgeClass">
            {{ stageName }}
          </span>
        </div>
        <div class="header-right">
          <el-button
            v-if="currentSessionId && currentStage === 'done'"
            type="success"
            size="small"
            @click="goToReport"
          >
            <el-icon><Document /></el-icon>
            查看报告
          </el-button>
          <el-button
            type="default"
            size="small"
            @click="goToTongue"
          >
            <el-icon><Camera /></el-icon>
            上传舌象
          </el-button>
        </div>
      </div>

      <!-- 对话区 -->
      <div class="chat-area" ref="chatAreaRef">
        <!-- 欢迎屏 -->
        <div v-if="!messages.length" class="welcome-screen">
          <div class="welcome-icon">
            <img src="@/assets/assistant-avatar.png" alt="中医助手" />
          </div>
          <h2>中医智能问诊助手</h2>
          <p>基于多智能体协同架构，模拟中医"望闻问切"全流程</p>
          <div class="feature-cards">
            <div class="feature-card">
              <el-icon><View /></el-icon>
              <span>望诊</span>
              <small>舌象/面色分析</small>
            </div>
            <div class="feature-card">
              <el-icon><Microphone /></el-icon>
              <span>闻诊</span>
              <small>语音/文字描述</small>
            </div>
            <div class="feature-card">
              <el-icon><QuestionFilled /></el-icon>
              <span>问诊</span>
              <small>十问动态追问</small>
            </div>
            <div class="feature-card">
              <el-icon><FirstAidKit /></el-icon>
              <span>辨证</span>
              <small>证型分析推理</small>
            </div>
          </div>
          <el-button type="primary" size="large" @click="startNewSession" class="start-btn">
            开始问诊
          </el-button>
        </div>

        <!-- 消息列表 -->
        <div v-else class="messages-list">
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="message-row"
            :class="msg.role"
          >
            <!-- 助手头像 -->
            <img
              v-if="msg.role === 'assistant'"
              src="@/assets/assistant-avatar.png"
              class="avatar"
              alt="助手"
            />

            <div class="bubble-wrap">
              <div v-if="msg.progress" class="assistant-progress-head">
                <span class="tiny-status">正在调用：{{ msg.progress.currentAgent || '智能体' }}</span>
                <el-button text size="small" @click="msg.progress.expanded = !msg.progress.expanded">
                  {{ msg.progress.expanded ? '收起' : '展开' }}
                </el-button>
              </div>

              <div v-if="msg.progress?.expanded" class="assistant-progress-body">
                <div class="progress-step" v-for="(s, i) in (msg.progress.steps || [])" :key="i">
                  <span class="s-name">{{ translateAgent(s.agent) }}</span>
                  <span class="s-stage">{{ s.stage }}</span>
                  <span class="s-ok" :class="{ bad: !s.success }">{{ s.success ? '✓' : '✗' }}</span>
                </div>
              </div>

              <!-- 高风险警告 -->
              <el-alert
                v-if="msg.isHighRisk"
                title="⚠️ 检测到高风险症状，请立即就医！"
                type="error"
                :closable="false"
                class="risk-alert"
              />

              <div class="bubble" :class="msg.role">
                <div class="bubble-content" v-html="renderMarkdown(msg.content)" />
                <!-- 参考依据 -->
                <div v-if="msg.references && msg.references.length" class="references">
                  <el-collapse>
                    <el-collapse-item title="📚 参考依据" name="refs">
                      <div
                        v-for="(ref, i) in msg.references"
                        :key="i"
                        class="ref-item"
                      >
                        <el-tag size="small" type="info">{{ ref.source || '知识库' }}</el-tag>
                        <span class="ref-content">{{ ref.content }}</span>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
              <div class="msg-time">{{ msg.time }}</div>
            </div>

            <!-- 用户头像 -->
            <img
              v-if="msg.role === 'user'"
              src="@/assets/user-avatar.jpg"
              class="avatar"
              alt="用户"
            />
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <div class="disclaimer-bar" v-if="messages.length">
          ⚠️ 本系统仅提供健康参考建议，不构成医疗诊断，如有急重症状请立即就医
        </div>
        <div class="input-row">
          <!-- 舌象上传按钮 -->
          <el-tooltip content="上传舌象照片" placement="top">
            <el-button
              class="tongue-btn"
              :disabled="isSending || currentStage === 'done'"
              @click="showTongueDialog = true"
            >
              <el-icon><Camera /></el-icon>
            </el-button>
          </el-tooltip>
          
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            :autosize="{ minRows: 2, maxRows: 5 }"
            placeholder="描述您的症状或回答问题…（Enter发送，Shift+Enter换行）"
            @keydown.enter.exact.prevent="handleSend"
            :disabled="isSending || currentStage === 'done'"
            resize="none"
          />
          <el-button
            type="primary"
            class="send-btn"
            :loading="isSending"
            :disabled="!inputText.trim() || currentStage === 'done'"
            @click="handleSend"
          >
            <el-icon v-if="!isSending"><Promotion /></el-icon>
            发送
          </el-button>
        </div>
        <div v-if="currentStage === 'done'" class="done-hint">
          <el-icon><CircleCheckFilled /></el-icon>
          问诊已完成，
          <el-link type="primary" @click="goToReport">查看完整报告</el-link>
          或
          <el-link type="success" @click="startNewSession">开始新问诊</el-link>
        </div>
      </div>

      <!-- 舌象上传悬浮窗 -->
      <el-dialog
        v-model="showTongueDialog"
        title="舌象照片上传"
        width="480px"
        :close-on-click-modal="false"
      >
        <div class="tongue-dialog-content">
          <!-- 拍照提示 -->
          <el-card class="guide-card" shadow="never">
            <div class="guide-content">
              <div class="guide-icon">📷</div>
              <div>
                <h4>拍摄建议</h4>
                <ul>
                  <li>在自然光线下伸出舌头正对摄像头</li>
                  <li>保持舌面平展，舌尖向前</li>
                  <li>避免饮食后立即拍摄（建议饭后30分钟以上）</li>
                </ul>
              </div>
            </div>
          </el-card>

          <!-- 上传/拍照区域 -->
          <div class="upload-area">
            <div v-if="!previewUrl" class="upload-buttons">
              <el-button
                type="primary"
                size="large"
                @click="openCamera"
                class="upload-option"
              >
                <el-icon><Camera /></el-icon>
                拍照
              </el-button>
              <el-upload
                :show-file-list="false"
                :before-upload="() => false"
                :on-change="handleFileSelect"
                accept="image/*"
              >
                <el-button
                  type="default"
                  size="large"
                  class="upload-option"
                >
                  <el-icon><Upload /></el-icon>
                  上传照片
                </el-button>
              </el-upload>
            </div>
            
            <!-- 预览区域 -->
            <div v-else class="preview-area">
              <img :src="previewUrl" class="preview-image" alt="舌象预览" />
              <el-button
                type="danger"
                circle
                class="remove-btn"
                @click="removeImage"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>

          <!-- 分析状态 -->
          <div v-if="analyzing" class="analyzing-status">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>正在分析舌象...</span>
          </div>
        </div>

        <template #footer>
          <el-button @click="closeTongueDialog">取消</el-button>
          <el-button
            type="primary"
            :loading="analyzing"
            :disabled="!selectedFile"
            @click="analyzeTongue"
          >
            开始分析
          </el-button>
        </template>
      </el-dialog>

      <!-- 摄像头对话框 -->
      <el-dialog
        v-model="showCameraDialog"
        title="拍照"
        width="640px"
        :close-on-click-modal="false"
        @close="closeCamera"
      >
        <div class="camera-container">
          <video
            ref="videoRef"
            autoplay
            playsinline
            class="camera-video"
          ></video>
          <canvas ref="canvasRef" style="display: none;"></canvas>
        </div>
        <template #footer>
          <el-button @click="closeCamera">取消</el-button>
          <el-button type="primary" @click="capturePhoto">
            <el-icon><Camera /></el-icon>
            拍照
          </el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus, ChatDotRound, Document, Camera, Operation,
  View, Microphone, QuestionFilled, FirstAidKit,
  Promotion, CircleCheckFilled, Delete
} from '@element-plus/icons-vue'
import { consultApi, authApi, type StreamEvent } from '@/api'
import dayjs from 'dayjs'

// Minimal markdown renderer (no external dep needed beyond what's installed)
const escapeHtml = (raw: string): string =>
  raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')

const renderMarkdown = (text: string): string => {
  if (!text) return ''
  // Sanitize HTML first, then apply safe markdown transformations
  const safe = escapeHtml(text)
  return safe
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')
    .replace(/^###\s(.+)$/gm, '<h5>$1</h5>')
    .replace(/^##\s(.+)$/gm, '<h4>$1</h4>')
    .replace(/^#\s(.+)$/gm, '<h3>$1</h3>')
    .replace(/^[-*]\s(.+)$/gm, '<li>$1</li>')
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  time: string
  isHighRisk?: boolean
  references?: Array<{ content: string; source: string }>
  progress?: {
    currentAgent?: string
    steps?: AgentStep[]
    expanded?: boolean
  }
}

interface AgentStep {
  agent: string
  stage: string
  success: boolean
  retry_count: number
  step_note?: string
}

interface SessionHistoryItem {
  session_id: string
  title: string
  time: string
}

const router = useRouter()
const chatAreaRef = ref<HTMLElement | null>(null)

const messages = ref<Message[]>([])
const inputText = ref('')
const isSending = ref(false)
const isThinking = ref(false)
const currentSessionId = ref('')
const currentStage = ref('intake')
const agentSteps = ref<AgentStep[]>([])
const sessionHistory = ref<SessionHistoryItem[]>([])
const isLoggedIn = ref(!!localStorage.getItem('token'))

const STORAGE_KEY_GUEST = 'tcm_session_history_guest'
const MESSAGES_PREFIX = 'tcm_session_msgs_'
const STAGE_PREFIX = 'tcm_session_stage_'

const getUserId = (): string => {
  try {
    const raw = localStorage.getItem('user')
    const user = raw ? JSON.parse(raw) : null
    return user?.id ? String(user.id) : ''
  } catch {
    return ''
  }
}

const getHistoryKey = (): string => {
  if (!isLoggedIn.value) return STORAGE_KEY_GUEST
  const uid = getUserId()
  return uid ? `tcm_session_history_user_${uid}` : STORAGE_KEY_GUEST
}

const getMessagesKey = (sessionId: string): string => {
  if (!isLoggedIn.value) return `${MESSAGES_PREFIX}guest_${sessionId}`
  const uid = getUserId()
  return `${MESSAGES_PREFIX}${uid || 'guest'}_${sessionId}`
}

const getStageKey = (sessionId: string): string => {
  if (!isLoggedIn.value) return `${STAGE_PREFIX}guest_${sessionId}`
  const uid = getUserId()
  return `${STAGE_PREFIX}${uid || 'guest'}_${sessionId}`
}

const stageName = computed(() => {
  const map: Record<string, string> = {
    intake: '接诊中',
    inquiry: '追问中',
    observation: '望诊中',
    syndrome: '辨证中',
    recommendation: '给出建议',
    safety_check: '安全审查',
    report: '生成报告',
    done: '问诊完成',
  }
  return map[currentStage.value] || currentStage.value
})

const stageBadgeClass = computed(() => {
  if (currentStage.value === 'done') return 'badge-done'
  if (['syndrome', 'recommendation'].includes(currentStage.value)) return 'badge-active'
  return 'badge-default'
})

const translateAgent = (name: string) => {
  const map: Record<string, string> = {
    IntakeAgent: '接诊分诊',
    InquiryAgent: '追问引导',
    ObservationAgent: '望诊融合',
    SyndromeAgent: '辨证分型',
    RecommendationAgent: '调理建议',
    SafetyGuardAgent: '安全审查',
    ReportAgent: '报告生成',
  }
  return map[name] || name
}

const runningSteps = ref<AgentStep[]>([])

const resetRunningSteps = () => {
  runningSteps.value = []
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatAreaRef.value) {
    chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
  }
}

const loadHistoryFromStorage = () => {
  try {
    const raw = localStorage.getItem(getHistoryKey())
    if (raw) sessionHistory.value = JSON.parse(raw)
  } catch {
    sessionHistory.value = []
  }
}

const saveHistoryToStorage = () => {
  localStorage.setItem(getHistoryKey(), JSON.stringify(sessionHistory.value))
}

const saveMessagesToStorage = (sessionId: string) => {
  localStorage.setItem(getMessagesKey(sessionId), JSON.stringify(messages.value))
  localStorage.setItem(getStageKey(sessionId), currentStage.value)
}

const loadMessagesFromStorage = (sessionId: string): boolean => {
  try {
    const raw = localStorage.getItem(getMessagesKey(sessionId))
    const stage = localStorage.getItem(getStageKey(sessionId))
    if (raw) {
      messages.value = JSON.parse(raw)
      currentStage.value = stage || 'intake'
      return true
    }
  } catch {
    /* ignore */
  }
  return false
}

const addToHistory = (sessionId: string, firstMsg: string) => {
  const existing = sessionHistory.value.findIndex(s => s.session_id === sessionId)
  const item: SessionHistoryItem = {
    session_id: sessionId,
    title: firstMsg.length > 20 ? firstMsg.slice(0, 20) + '…' : firstMsg,
    time: dayjs().format('MM-DD HH:mm'),
  }
  if (existing >= 0) {
    sessionHistory.value[existing] = item
  } else {
    sessionHistory.value.unshift(item)
    if (sessionHistory.value.length > 20) sessionHistory.value.pop()
  }
  saveHistoryToStorage()
}

const bindGuestCurrentSessionToAccount = () => {
  const uid = getUserId()
  if (!uid || !currentSessionId.value) return

  const guestHistoryRaw = localStorage.getItem(STORAGE_KEY_GUEST)
  const guestHistory: SessionHistoryItem[] = guestHistoryRaw ? JSON.parse(guestHistoryRaw) : []
  const current = guestHistory.find((x) => x.session_id === currentSessionId.value)

  // 将当前访客会话迁移到账户空间
  const guestMsgsRaw = localStorage.getItem(`${MESSAGES_PREFIX}guest_${currentSessionId.value}`)
  const guestStageRaw = localStorage.getItem(`${STAGE_PREFIX}guest_${currentSessionId.value}`)
  if (guestMsgsRaw) {
    localStorage.setItem(`${MESSAGES_PREFIX}${uid}_${currentSessionId.value}`, guestMsgsRaw)
  }
  if (guestStageRaw) {
    localStorage.setItem(`${STAGE_PREFIX}${uid}_${currentSessionId.value}`, guestStageRaw)
  }

  // 更新用户会话历史，仅注入当前会话
  const userHistoryKey = `tcm_session_history_user_${uid}`
  const userHistoryRaw = localStorage.getItem(userHistoryKey)
  const userHistory: SessionHistoryItem[] = userHistoryRaw ? JSON.parse(userHistoryRaw) : []
  if (current && !userHistory.find((x) => x.session_id === current.session_id)) {
    userHistory.unshift(current)
    localStorage.setItem(userHistoryKey, JSON.stringify(userHistory.slice(0, 20)))
  }
}

const startNewSession = async () => {
  try {
    messages.value = []
    agentSteps.value = []
    currentStage.value = 'intake'
    inputText.value = ''

    const res = await consultApi.createSession()
    currentSessionId.value = res.session_id

    // 添加欢迎消息
    const welcomeMsg = '您好！我是中医智能问诊助手。请描述您目前的主要不适或症状，我将通过系统化的问诊帮您进行中医辨证分析，提供健康建议参考。\n\n⚠️ 温馨提示：本系统提供的是健康参考建议，不构成医疗诊断，如有急重症状请立即就医。'
    messages.value.push({
      id: Date.now().toString(),
      role: 'assistant',
      content: welcomeMsg,
      time: dayjs().format('HH:mm'),
    })
    
    // 保存会话ID到历史
    addToHistory(currentSessionId.value, '新会话')
    saveMessagesToStorage(currentSessionId.value)
    await scrollToBottom()
  } catch (err) {
    ElMessage.error('创建会话失败，请检查后端服务是否启动')
    console.error(err)
  }
}

const deleteSession = async (sessionId: string, event?: Event) => {
  // 先尝试调用API删除（如果存在的话）
  try {
    await consultApi.deleteSession(sessionId)
  } catch (err: any) {
    // 如果是404错误，说明会话只存在于本地，继续删除本地数据
    if (err?.response?.status !== 404) {
      ElMessage.error('删除失败：' + (err?.message || '未知错误'))
      return
    }
  }
  
  // 从本地历史中移除
  const idx = sessionHistory.value.findIndex(s => s.session_id === sessionId)
  if (idx >= 0) {
    sessionHistory.value.splice(idx, 1)
    saveHistoryToStorage()
  }
  
  // 清除本地存储的会话数据
  localStorage.removeItem(getMessagesKey(sessionId))
  localStorage.removeItem(getStageKey(sessionId))
  
  // 如果删除的是当前会话，清空当前状态
  if (currentSessionId.value === sessionId) {
    currentSessionId.value = ''
    messages.value = []
    currentStage.value = 'intake'
    agentSteps.value = []
  }
  
  ElMessage.success('会话已删除')
}

const loadSession = (sessionId: string) => {
  currentSessionId.value = sessionId
  agentSteps.value = []
  inputText.value = ''
  const restored = loadMessagesFromStorage(sessionId)
  if (!restored) {
    messages.value = []
    currentStage.value = 'intake'
    ElMessage.info('未找到该会话的本地记录，已切换到该会话ID')
  } else {
    ElMessage.success('历史会话已恢复')
    nextTick(() => scrollToBottom())
  }
}

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || isSending.value) return

  if (!currentSessionId.value) {
    await startNewSession()
  }

  // Push user message
  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: text,
    time: dayjs().format('HH:mm'),
  })
  inputText.value = ''
  isSending.value = true
  isThinking.value = true
  await scrollToBottom()

  // Update history title from first user message
  addToHistory(currentSessionId.value, text)

  try {
    resetRunningSteps()

    let finalRes: any = null
    let streamedText = ''
    let assistantMsgId: string | null = null

    // 收到第一个事件时创建回复框
    const ensureAssistantMessage = () => {
      if (assistantMsgId) return
      assistantMsgId = (Date.now() + 1).toString()
      messages.value.push({
        id: assistantMsgId,
        role: 'assistant',
        content: '处理中...',
        time: dayjs().format('HH:mm'),
      })
    }

    const onStreamEvent = (evt: StreamEvent) => {
      ensureAssistantMessage()

      if (evt.type === 'stage' && evt.stage) {
        const stageMap: Record<string, string> = {
          intake: '接诊分诊',
          inquiry: '追问引导',
          observation: '望诊分析',
          syndrome: '辨证分型',
          recommendation: '调理建议',
          safety_check: '安全审查',
          report: '报告生成',
        }
        // 更新回复框内容为当前阶段
        if (assistantMsgId) {
          const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
          if (msgIndex !== -1) {
            messages.value[msgIndex].content = `正在处理：${stageMap[evt.stage] || evt.stage}...`
          }
        }
      }

      if (evt.type === 'agent_step' && evt.agent) {
        runningSteps.value = [...runningSteps.value, {
          agent: evt.agent,
          stage: evt.stage,
          success: evt.success ?? true,
          retry_count: evt.retry_count ?? 0,
          step_note: evt.step_note,
        }].slice(-10)
      }

      if (evt.type === 'token' && evt.content) {
        streamedText += evt.content
        // 流式输出时更新回复框内容
        if (assistantMsgId && streamedText) {
          const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
          if (msgIndex !== -1) {
            messages.value[msgIndex].content = streamedText
          }
        }
      }

      if (evt.type === 'done') {
        finalRes = {
          session_id: evt.session_id || currentSessionId.value,
          stage: evt.stage || currentStage.value,
          is_high_risk: evt.is_high_risk || false,
          assistant_message: String(evt.assistant_message || streamedText || '').trim(),
          pending_questions: evt.pending_questions || [],
          primary_syndrome: evt.primary_syndrome || null,
          model_error: evt.model_error || false,
          agent_steps: evt.agent_steps?.length ? evt.agent_steps : [...runningSteps.value],
        }
      }

      if (evt.type === 'error') {
        throw new Error(evt.message || '流式问诊失败')
      }
    }

    await consultApi.sendMessageStream(currentSessionId.value, text, onStreamEvent)
    
    const res = finalRes || {
      session_id: currentSessionId.value,
      stage: currentStage.value,
      is_high_risk: false,
      assistant_message: streamedText || '本轮流式响应未完整返回，请重试。',
      pending_questions: [],
      primary_syndrome: null,
      model_error: !streamedText,
      agent_steps: [...runningSteps.value],
    }
    
    isThinking.value = false
    currentStage.value = res.stage

    if (res.model_error) {
      ElMessage.error(String(res.assistant_message || '当前模型调用失败，请在后台修复模型配置后重试'))
    }

    // Update agent steps
    if (res.agent_steps?.length) {
      agentSteps.value = [...agentSteps.value, ...res.agent_steps].slice(-10)
    }

    // 更新可变消息为最终回复
    if (assistantMsgId) {
      const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
      if (msgIndex !== -1) {
                // 使用 assistant_message 作为最终内容（后端已统一生成本轮回复）
                const finalContent = String(res.assistant_message || '').trim()
                messages.value[msgIndex].content = finalContent || '处理完成'
                messages.value[msgIndex].isHighRisk = res.is_high_risk
                const finalSteps = (res.agent_steps?.length ? res.agent_steps : runningSteps.value) as AgentStep[]
                messages.value[msgIndex].progress = {
                  currentAgent: finalSteps.length
                    ? translateAgent(finalSteps[finalSteps.length - 1].agent)
                    : '',
                  steps: [...finalSteps],
                  expanded: false,
                }
              }
            }

    if (isLoggedIn.value) {
      try {
        await authApi.saveConsultArchive({
          session_id: currentSessionId.value,
          title: text.length > 20 ? text.slice(0, 20) + '…' : text,
          current_stage: res.stage,
          latest_question: res.pending_questions?.[0] || '',
          latest_answer: text,
          is_high_risk: res.is_high_risk,
        })
      } catch {
        // ignore archive save failure
      }
    }

    saveMessagesToStorage(currentSessionId.value)
    await scrollToBottom()
  } catch (err: any) {
    isThinking.value = false
    ElMessage.error('发送失败：' + (err?.message || '未知错误'))
  } finally {
    isSending.value = false
  }
}

const goToReport = () => {
  if (currentSessionId.value) {
    router.push({ path: '/consult/report', query: { session_id: currentSessionId.value } })
  }
}

const goToTongue = () => {
  router.push({ path: '/consult/tongue', query: { session_id: currentSessionId.value || '' } })
}

// ─── 舌象上传相关 ───────────────────────────────────

const showTongueDialog = ref(false)
const showCameraDialog = ref(false)
const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const analyzing = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let mediaStream: MediaStream | null = null

// 处理文件选择
const handleFileSelect = (file: any) => {
  const raw: File = file.raw
  if (!raw) return

  // 检查文件大小（最大10MB）
  if (raw.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过10MB')
    return
  }

  selectedFile.value = raw
  previewUrl.value = URL.createObjectURL(raw)
}

// 移除图片
const removeImage = () => {
  selectedFile.value = null
  previewUrl.value = ''
}

// 打开摄像头
const openCamera = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: 1280, height: 720 }
    })
    showCameraDialog.value = true
    await nextTick()
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
    }
  } catch (err: any) {
    ElMessage.error('无法访问摄像头：' + (err?.message || '请检查权限设置'))
  }
}

// 拍照
const capturePhoto = () => {
  if (!videoRef.value || !canvasRef.value) return

  const video = videoRef.value
  const canvas = canvasRef.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.drawImage(video, 0, 0)
  canvas.toBlob((blob) => {
    if (blob) {
      const file = new File([blob], 'tongue_photo.jpg', { type: 'image/jpeg' })
      selectedFile.value = file
      previewUrl.value = URL.createObjectURL(file)
      closeCamera()
    }
  }, 'image/jpeg', 0.9)
}

// 关闭摄像头
const closeCamera = () => {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  showCameraDialog.value = false
}

// 关闭舌象对话框
const closeTongueDialog = () => {
  showTongueDialog.value = false
  removeImage()
}

// 分析舌象
const analyzeTongue = async () => {
  if (!selectedFile.value) return

  analyzing.value = true

  try {
    const res = await consultApi.uploadTongueImage(currentSessionId.value, selectedFile.value)
    
    // 显示分析结果
    const obs = res.observation
    let resultText = '舌象分析完成：\n'
    
    if (obs.tongue_color) resultText += `• 舌色：${obs.tongue_color}\n`
    if (obs.tongue_coating) resultText += `• 苔色：${obs.tongue_coating}\n`
    if (obs.coating_thickness) resultText += `• 苔厚薄：${obs.coating_thickness}\n`
    if (obs.coating_texture) resultText += `• 苔质：${obs.coating_texture}\n`
    if (obs.tongue_shape) resultText += `• 舌形：${obs.tongue_shape}\n`
    
    // 添加诊断信息
    if (obs.diagnosis?.summary) {
      resultText += `\n【诊断结论】\n${obs.diagnosis.summary}\n`
    }
    if (obs.diagnosis?.indications?.length) {
      resultText += `\n【可能提示】\n${obs.diagnosis.indications.map((i: string) => `• ${i}`).join('\n')}\n`
    }
    if (obs.diagnosis?.suggestions?.length) {
      resultText += `\n【调理建议】\n${obs.diagnosis.suggestions.map((s: string) => `• ${s}`).join('\n')}\n`
    }

    // 添加到对话中
    messages.value.push({
      id: Date.now().toString(),
      role: 'assistant',
      content: resultText,
      time: dayjs().format('HH:mm'),
    })

    // 【修复】舌象分析完成后，将问诊状态设为"inquiry"继续问诊流程
    // 而不是重置状态
    currentStage.value = 'inquiry'  // 保持在问诊阶段，继续收集信息
    
    // 保存会话状态
    saveMessagesToStorage(currentSessionId.value)
    await scrollToBottom()

    ElMessage.success('舌象分析完成，请继续描述其他症状或回答问题')
    closeTongueDialog()
  } catch (err: any) {
    ElMessage.error('舌象分析失败：' + (err?.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
}

const handleAuthChanged = () => {
  const prevLoggedIn = isLoggedIn.value
  isLoggedIn.value = !!localStorage.getItem('token')
  if (!prevLoggedIn && isLoggedIn.value) {
    bindGuestCurrentSessionToAccount()
  }
  sessionHistory.value = []
  loadHistoryFromStorage()
  if (currentSessionId.value) {
    loadMessagesFromStorage(currentSessionId.value)
  }
}

onMounted(() => {
  window.addEventListener('auth-changed', handleAuthChanged)

  loadHistoryFromStorage()
  if (!isLoggedIn.value) {
    ElMessage.info('当前为访客模式，登录后可同步保存问诊历史到个人档案')
  }
})

onUnmounted(() => {
  window.removeEventListener('auth-changed', handleAuthChanged)
})
</script>

<style scoped lang="scss">
$sidebar-width: 220px;
$header-height: 56px;
$border-color: #e8eaf0;
$primary: #1677ff;
$bg-main: #f5f7fb;

.consult-page {
  display: flex;
  height: 100vh;
  background: linear-gradient(180deg, #f7fcff 0%, #f2f8f3 100%);
  overflow: hidden;
}

/* ─── Sidebar ─────────────────────────────────────── */
.sidebar {
  width: $sidebar-width;
  background: #fff;
  border-right: 1px solid $border-color;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;

  .sidebar-header {
    padding: 16px;
    border-bottom: 1px solid $border-color;

    .new-session-btn {
      width: 100%;
    }
  }

  .session-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;

    .session-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border-radius: 8px;
      cursor: pointer;
      transition: background 0.2s;

      &:hover { background: #f0f4ff; }
      &.active { background: #e6efff; color: $primary; }

      .session-icon { font-size: 16px; flex-shrink: 0; }

      .session-meta {
        flex: 1;
        overflow: hidden;

        .session-title {
          display: block;
          font-size: 13px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .session-time {
          font-size: 11px;
          color: #999;
        }
      }

      .delete-btn {
        opacity: 0;
        transition: opacity 0.2s;
      }

      &:hover .delete-btn {
        opacity: 1;
      }
    }
  }
}
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .content-header {
    height: $header-height;
    background: rgba(255, 255, 255, 0.88);
    border-bottom: 1px solid $border-color;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    flex-shrink: 0;

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .stage-badge {
      font-size: 12px;
      padding: 2px 10px;
      border-radius: 99px;

      &.badge-default { background: #f0f0f0; color: #666; }
      &.badge-active { background: #e6f7ff; color: #1677ff; }
      &.badge-done { background: #f6ffed; color: #52c41a; }
    }
  }
}

/* ─── Agent timeline ──────────────────────────────── */
.agent-timeline {
  background: #fff;
  border-bottom: 1px solid $border-color;
  padding: 8px 20px;
  flex-shrink: 0;

  .timeline-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    font-size: 12px;
    color: #666;
    margin-bottom: 6px;

    .timeline-left {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .now-calling {
      color: #5c7f6f;
      opacity: 0.8;
      font-size: 11px;
    }
  }

  .timeline-scroll { max-height: 48px; }

  .timeline-steps {
    display: flex;
    gap: 8px;

    &.compact {
      .step-item {
        opacity: 0.78;
      }
    }

    .step-item {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 3px 10px;
      border-radius: 99px;
      background: #f5f5f5;
      font-size: 12px;
      white-space: nowrap;
      transition: all 0.3s;

      &.step-active {
        background: #e6f7ff;
        color: $primary;
      }

      &.step-error { background: #fff2f0; color: #ff4d4f; }

      .step-name { font-size: 12px; }
      .step-stage { font-size: 11px; color: #7b9386; }
    }
  }
}

/* ─── Chat area ───────────────────────────────────── */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;

  .welcome-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;

    .welcome-icon img {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      border: 3px solid #e6efff;
      margin-bottom: 16px;
    }

    h2 {
      font-size: 24px;
      color: #1a1a2e;
      margin: 0 0 8px;
    }

    p { color: #666; margin: 0 0 24px; }

    .feature-cards {
      display: flex;
      gap: 16px;
      margin-bottom: 32px;

      .feature-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        background: #fff;
        border: 1px solid $border-color;
        border-radius: 12px;
        padding: 16px 20px;
        min-width: 90px;
        transition: all 0.3s;

        &:hover {
          border-color: $primary;
          box-shadow: 0 4px 12px rgba(22, 119, 255, 0.12);
          transform: translateY(-2px);
        }

        .el-icon { font-size: 24px; color: $primary; }

        span { font-size: 14px; font-weight: 600; }
        small { font-size: 11px; color: #999; }
      }
    }

    .start-btn { padding: 12px 40px; font-size: 16px; }
  }

  .messages-list { display: flex; flex-direction: column; gap: 20px; }

  .message-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;

    &.user { justify-content: flex-end; }

    .avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      flex-shrink: 0;
      object-fit: cover;
    }

    .bubble-wrap {
      max-width: 68%;
      display: flex;
      flex-direction: column;
      gap: 4px;

      .assistant-progress-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2px;

        .tiny-status {
          font-size: 11px;
          color: #6f8478;
          opacity: 0.82;
        }
      }

      .assistant-progress-body {
        margin-bottom: 6px;
        border-left: 2px solid #dbe8df;
        padding-left: 8px;

        .progress-step {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 11px;
          color: #6a7f73;
          margin: 2px 0;

          .s-name { min-width: 84px; }
          .s-stage { opacity: 0.75; }
          .s-ok.bad { color: #d03050; }
        }
      }

      .risk-alert { margin-bottom: 8px; }

      .bubble {
        padding: 12px 16px;
        border-radius: 12px;
        line-height: 1.7;
        font-size: 14px;

        &.assistant {
          background: #ffffff;
          border: 1px solid $border-color;
          border-radius: 2px 12px 12px 12px;
          color: #1a1a2e;
          box-shadow: 0 8px 20px rgba(31, 77, 53, 0.06);
        }

        &.user {
          background: linear-gradient(135deg, #2f9776 0%, #338db0 100%);
          color: #fff;
          border-radius: 12px 2px 12px 12px;
          box-shadow: 0 10px 24px rgba(37, 132, 104, 0.28);
        }

        &.thinking {
          padding: 14px 20px;

          .dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #bbb;
            border-radius: 50%;
            margin: 0 2px;
            animation: bounce 1.2s infinite;

            &:nth-child(2) { animation-delay: 0.2s; }
            &:nth-child(3) { animation-delay: 0.4s; }
          }
        }

        .bubble-content :deep(h3), .bubble-content :deep(h4), .bubble-content :deep(h5) {
          margin: 8px 0 4px;
        }
        .bubble-content :deep(li) { margin-left: 16px; }
        .bubble-content :deep(code) {
          background: #f5f5f5;
          padding: 1px 4px;
          border-radius: 3px;
        }

        .references {
          margin-top: 10px;
          border-top: 1px solid #eee;
          padding-top: 8px;

          .ref-item {
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin: 4px 0;
            font-size: 12px;
            color: #555;
          }
        }
      }

      .msg-time {
        font-size: 11px;
        color: #bbb;
        padding: 0 4px;
      }
    }
  }
}

/* ─── Input area ──────────────────────────────────── */
.input-area {
  background: #fff;
  border-top: 1px solid $border-color;
  padding: 12px 20px 16px;
  flex-shrink: 0;

  .disclaimer-bar {
    font-size: 11px;
    color: #f5a623;
    margin-bottom: 8px;
    text-align: center;
  }

  .input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;

    .tongue-btn {
      height: 64px;
      width: 48px;
      flex-shrink: 0;
    }

    .el-textarea { flex: 1; }

    .send-btn {
      height: 64px;
      padding: 0 20px;
      flex-shrink: 0;
    }
  }

  .done-hint {
    text-align: center;
    font-size: 13px;
    color: #666;
    margin-top: 8px;
  }
}

/* ─── 舌象上传对话框 ──────────────────────────────────── */
.tongue-dialog-content {
  .guide-card {
    margin-bottom: 16px;
    border-radius: 8px;

    .guide-content {
      display: flex;
      gap: 12px;
      align-items: flex-start;

      .guide-icon { font-size: 32px; }

      h4 { margin: 0 0 8px; font-size: 14px; }
      ul {
        margin: 0;
        padding-left: 16px;
        li {
          margin: 4px 0;
          font-size: 12px;
          color: #666;
        }
      }
    }
  }

  .upload-area {
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #dcdfe6;
    border-radius: 8px;
    background: #fafafa;

    .upload-buttons {
      display: flex;
      gap: 16px;

      .upload-option {
        width: 140px;
        height: 100px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        font-size: 14px;
      }
    }

    .preview-area {
      position: relative;
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;

      .preview-image {
        max-width: 100%;
        max-height: 300px;
        border-radius: 8px;
      }

      .remove-btn {
        position: absolute;
        top: 8px;
        right: 8px;
      }
    }
  }

  .analyzing-status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 16px;
    color: #409eff;
    font-size: 14px;
  }
}

/* ─── 摄像头对话框 ──────────────────────────────────── */
.camera-container {
  display: flex;
  justify-content: center;
  background: #000;
  border-radius: 8px;
  overflow: hidden;

  .camera-video {
    max-width: 100%;
    max-height: 400px;
  }
}

/* ─── Animations ──────────────────────────────────── */
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

.slide-down-enter-active, .slide-down-leave-active { transition: all 0.3s ease; }
.slide-down-enter-from, .slide-down-leave-to { transform: translateY(-10px); opacity: 0; }

/* ─── Responsive ──────────────────────────────────── */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .chat-area { padding: 12px 16px; }
  .message-row .bubble-wrap { max-width: 85%; }
}
</style>
