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
              <div v-if="msg.progress" class="assistant-status-line">
                <span class="status-dot"></span>
                <span>{{ msg.progress.currentAgent || '正在思考' }}</span>
              </div>

              <!-- 高风险警告 -->
              <el-alert
                v-if="msg.isHighRisk"
                title="⚠️ 检测到高风险症状，请立即就医！"
                type="error"
                :closable="false"
                class="risk-alert"
              />

              <div v-if="msg.content" class="bubble" :class="msg.role">
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
      <div class="input-area" :class="{ completed: currentStage === 'done' }">
        <div class="disclaimer-bar" v-if="messages.length && currentStage !== 'done'">
          ⚠️ 本系统仅提供健康参考建议，不构成医疗诊断，如有急重症状请立即就医
        </div>
        <div v-if="currentStage !== 'done'" class="input-row">
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
          <el-tooltip
            :content="!voiceSupported ? '当前浏览器不支持语音识别' : (isRecording ? '停止语音输入' : '开始语音输入')"
            placement="top"
          >
            <el-button
              class="voice-btn"
              :class="{ recording: isRecording }"
              :type="isRecording ? 'danger' : 'default'"
              :disabled="isSending || currentStage === 'done' || !voiceSupported"
              :aria-label="isRecording ? '停止语音输入' : '开始语音输入'"
              @click="toggleVoiceInput"
            >
              <el-icon><Microphone /></el-icon>
            </el-button>
          </el-tooltip>
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
          <el-button
            class="upload-tongue-btn"
            :disabled="isSending || currentStage === 'done'"
            @click="showTongueDialog = true"
          >
            <el-icon><Camera /></el-icon>
            上传舌象
          </el-button>
        </div>
        <div v-if="currentStage === 'done'" class="report-confirm-card">
          <div class="confirm-copy">
            <el-icon><CircleCheckFilled /></el-icon>
            <div>
              <strong>问诊已完成</strong>
              <span>{{ reportEntryConfirmed ? '正式问诊报告已生成，可前往报告页查看或导出 PDF。' : '对话中已生成问诊报告内容，是否生成正式报告页？' }}</span>
            </div>
          </div>
          <div class="confirm-actions">
            <el-button
              v-if="!reportEntryConfirmed"
              type="primary"
              @click="confirmReportEntry"
            >
              生成正式报告
            </el-button>
            <el-button
              v-else
              type="primary"
              @click="goToReport"
            >
              查看问诊报告
            </el-button>
            <el-button @click="startNewSession">开始新问诊</el-button>
          </div>
        </div>
      </div>

      <!-- 舌象上传悬浮窗 -->
      <el-dialog
        v-model="showTongueDialog"
        title="舌象照片上传"
        width="480px"
        :close-on-click-modal="false"
        class="bento-dialog"
        align-center
      >
        <div class="tongue-bento-container">
          <!-- 拍照提示 Bento 卡片 -->
          <div class="bento-card guide-card">
            <div class="guide-icon-wrapper">
              <el-icon class="camera-icon-large"><CameraFilled /></el-icon>
            </div>
            <div class="guide-text">
              <h4>拍摄建议</h4>
              <ul>
                <li><el-icon><Check /></el-icon> 在自然光线下正对摄像头</li>
                <li><el-icon><Check /></el-icon> 保持舌面平展，舌尖向前</li>
                <li><el-icon><Check /></el-icon> 饭后30分钟以上拍摄为佳</li>
              </ul>
            </div>
          </div>

          <!-- 上传/拍照区域 Bento 卡片 -->
          <div class="bento-card upload-card" :class="{ 'has-preview': previewUrl }">
            <div v-if="!previewUrl" class="upload-actions">
              <div class="action-btn-wrapper" @click="openCamera">
                <div class="action-icon bento-hover">
                  <el-icon><VideoCamera /></el-icon>
                </div>
                <span>实时拍照</span>
              </div>
              
              <div class="action-divider"></div>

              <el-upload
                class="upload-wrapper"
                :show-file-list="false"
                :before-upload="() => false"
                :on-change="handleFileSelect"
                accept="image/*"
              >
                <div class="action-btn-wrapper">
                  <div class="action-icon bento-hover">
                    <el-icon><Picture /></el-icon>
                  </div>
                  <span>上传照片</span>
                </div>
              </el-upload>
            </div>
            
            <!-- 预览区域 -->
            <div v-else class="preview-area">
              <div class="preview-wrapper">
                <img :src="previewUrl" class="preview-image" alt="舌象预览" />
                <div class="preview-overlay">
                  <el-button
                    type="danger"
                    circle
                    class="remove-btn bento-hover"
                    @click="removeImage"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 分析状态 -->
          <div v-if="analyzing" class="bento-card status-card">
            <div class="loading-ring"></div>
            <span>正在进行智能特征提取...</span>
          </div>
        </div>

        <template #footer>
          <div class="bento-footer">
            <el-button class="pill-btn cancel-btn" @click="closeTongueDialog">取消</el-button>
            <el-button
              type="primary"
              class="pill-btn submit-btn"
              :loading="analyzing"
              :disabled="!selectedFile"
              @click="analyzeTongue"
            >
              开始分析
            </el-button>
          </div>
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
  Promotion, CircleCheckFilled, Delete, CameraFilled, Check, VideoCamera, Picture, Upload
} from '@element-plus/icons-vue'
import { consultApi, authApi, type StreamEvent } from '@/api'
import dayjs from 'dayjs'

type SpeechRecognitionLikeResult = {
  isFinal: boolean
  0?: {
    transcript?: string
  }
}

type SpeechRecognitionLikeEvent = Event & {
  resultIndex: number
  results: {
    length: number
    [index: number]: SpeechRecognitionLikeResult
  }
}

type SpeechRecognitionLikeErrorEvent = Event & {
  error?: string
  message?: string
}

type SpeechRecognitionLike = EventTarget & {
  lang: string
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number
  onresult: ((event: SpeechRecognitionLikeEvent) => void) | null
  onerror: ((event: SpeechRecognitionLikeErrorEvent) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
  abort: () => void
}

type SpeechRecognitionLikeCtor = new () => SpeechRecognitionLike

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionLikeCtor
    webkitSpeechRecognition?: SpeechRecognitionLikeCtor
  }
}

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
const isRecording = ref(false)
const voiceSupported = ref(false)
const speechRecognition = ref<SpeechRecognitionLike | null>(null)
const voiceBaseText = ref('')
const voiceFinalText = ref('')
const currentSessionId = ref('')
const currentStage = ref('intake')
const agentSteps = ref<AgentStep[]>([])
const sessionHistory = ref<SessionHistoryItem[]>([])
const isLoggedIn = ref(!!localStorage.getItem('token'))
const reportEntryConfirmed = ref(false)

const STORAGE_KEY_GUEST = 'tcm_session_history_guest'
const MESSAGES_PREFIX = 'tcm_session_msgs_'
const STAGE_PREFIX = 'tcm_session_stage_'
const REPORT_ENTRY_PREFIX = 'tcm_session_report_entry_'

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

const getReportEntryKey = (sessionId: string): string => {
  if (!isLoggedIn.value) return `${REPORT_ENTRY_PREFIX}guest_${sessionId}`
  const uid = getUserId()
  return `${REPORT_ENTRY_PREFIX}${uid || 'guest'}_${sessionId}`
}

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

const sleep = (ms: number) => new Promise<void>((resolve) => window.setTimeout(resolve, ms))

const getSpeechRecognitionCtor = (): SpeechRecognitionLikeCtor | null => {
  if (typeof window === 'undefined') return null
  return window.SpeechRecognition || window.webkitSpeechRecognition || null
}

const mergeVoiceText = (baseText: string, finalText: string, interimText: string = '') => {
  const pieces = [baseText.trim(), finalText.trim(), interimText.trim()].filter(Boolean)
  return pieces.join(' ')
}

const cleanupSpeechRecognition = () => {
  if (!speechRecognition.value) return
  speechRecognition.value.onresult = null
  speechRecognition.value.onerror = null
  speechRecognition.value.onend = null
  speechRecognition.value = null
}

const stopVoiceInput = (abort = false) => {
  const recognition = speechRecognition.value
  if (!recognition) {
    isRecording.value = false
    return
  }

  try {
    if (abort) {
      recognition.abort()
    } else {
      recognition.stop()
    }
  } catch {
    // The browser may throw if recognition already stopped.
  } finally {
    isRecording.value = false
  }
}

const startVoiceInput = () => {
  if (isSending.value || currentStage.value === 'done') return

  const RecognitionCtor = getSpeechRecognitionCtor()
  if (!RecognitionCtor) {
    voiceSupported.value = false
    ElMessage.warning('当前浏览器不支持语音识别，请使用 Chrome 或 Edge 浏览器')
    return
  }

  cleanupSpeechRecognition()
  const recognition = new RecognitionCtor()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true
  recognition.maxAlternatives = 1

  voiceBaseText.value = inputText.value.trim()
  voiceFinalText.value = ''

  recognition.onresult = (event: SpeechRecognitionLikeEvent) => {
    let finalChunk = ''
    let interimChunk = ''

    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const result = event.results[i]
      const transcript = result?.[0]?.transcript?.trim() || ''
      if (!transcript) continue

      if (result.isFinal) {
        finalChunk = `${finalChunk} ${transcript}`.trim()
      } else {
        interimChunk = `${interimChunk} ${transcript}`.trim()
      }
    }

    if (finalChunk) {
      voiceFinalText.value = `${voiceFinalText.value} ${finalChunk}`.trim()
    }

    inputText.value = mergeVoiceText(voiceBaseText.value, voiceFinalText.value, interimChunk)
  }

  recognition.onerror = (event: SpeechRecognitionLikeErrorEvent) => {
    const error = event.error || ''
    isRecording.value = false
    if (error === 'not-allowed' || error === 'service-not-allowed') {
      ElMessage.error('麦克风权限被拒绝，请允许浏览器使用麦克风后重试')
    } else if (error === 'no-speech') {
      ElMessage.warning('没有识别到语音，请靠近麦克风再试一次')
    } else {
      ElMessage.error(event.message || '语音识别失败，请稍后重试')
    }
  }

  recognition.onend = () => {
    isRecording.value = false
  }

  speechRecognition.value = recognition

  try {
    recognition.start()
    isRecording.value = true
    ElMessage.success('语音输入已开启，请开始说话')
  } catch {
    cleanupSpeechRecognition()
    isRecording.value = false
    ElMessage.error('语音输入启动失败，请稍后重试')
  }
}

const toggleVoiceInput = () => {
  if (isRecording.value) {
    stopVoiceInput()
    return
  }
  startVoiceInput()
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

const stripTransientMessageState = (items: Message[]): Message[] =>
  items.map(({ progress, ...msg }) => msg)

const hasReportLikeAnswer = (items: Message[]): boolean =>
  items.some((msg) => {
    if (msg.role !== 'assistant' || !msg.content) return false
    const content = msg.content
    return (
      content.includes('中医智能问诊报告') ||
      content.includes('中医问诊报告') ||
      (
        content.includes('辨证结论') &&
        content.includes('详细建议') &&
        content.includes('重要提示')
      )
    )
  })

const normalizeCompletedSession = (sessionId: string) => {
  if (currentStage.value === 'done') return
  if (!hasReportLikeAnswer(messages.value)) return

  currentStage.value = 'done'
  localStorage.setItem(getStageKey(sessionId), 'done')
}

const saveMessagesToStorage = (sessionId: string) => {
  localStorage.setItem(getMessagesKey(sessionId), JSON.stringify(stripTransientMessageState(messages.value)))
  localStorage.setItem(getStageKey(sessionId), currentStage.value)
  localStorage.setItem(getReportEntryKey(sessionId), reportEntryConfirmed.value ? '1' : '0')
}

const loadMessagesFromStorage = (sessionId: string): boolean => {
  try {
    const raw = localStorage.getItem(getMessagesKey(sessionId))
    const stage = localStorage.getItem(getStageKey(sessionId))
    if (raw) {
      messages.value = stripTransientMessageState(JSON.parse(raw))
      currentStage.value = stage || 'intake'
      reportEntryConfirmed.value = localStorage.getItem(getReportEntryKey(sessionId)) === '1'
      normalizeCompletedSession(sessionId)
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
  const guestReportEntryRaw = localStorage.getItem(`${REPORT_ENTRY_PREFIX}guest_${currentSessionId.value}`)
  if (guestReportEntryRaw) {
    localStorage.setItem(`${REPORT_ENTRY_PREFIX}${uid}_${currentSessionId.value}`, guestReportEntryRaw)
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
    reportEntryConfirmed.value = false

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
  localStorage.removeItem(getReportEntryKey(sessionId))
  
  // 如果删除的是当前会话，清空当前状态
  if (currentSessionId.value === sessionId) {
    currentSessionId.value = ''
    messages.value = []
    currentStage.value = 'intake'
    agentSteps.value = []
    reportEntryConfirmed.value = false
  }
  
  ElMessage.success('会话已删除')
}

const loadSession = (sessionId: string) => {
  currentSessionId.value = sessionId
  agentSteps.value = []
  inputText.value = ''
  reportEntryConfirmed.value = localStorage.getItem(getReportEntryKey(sessionId)) === '1'
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
  if (isRecording.value) {
    stopVoiceInput()
  }

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
    let renderedText = ''
    let queuedText = ''
    let isTypingAnswer = false

    // 收到第一个事件时创建回复框
    const ensureAssistantMessage = () => {
      if (assistantMsgId) return
      assistantMsgId = (Date.now() + 1).toString()
      messages.value.push({
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        time: dayjs().format('HH:mm'),
        progress: {
          currentAgent: '正在思考',
          steps: [],
          expanded: false,
        },
      })
    }

    const setAssistantContent = (content: string) => {
      if (!assistantMsgId) return
      const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
      if (msgIndex !== -1) {
        messages.value[msgIndex].content = content
      }
    }

    const runAnswerTypewriter = async () => {
      if (isTypingAnswer) return
      isTypingAnswer = true
      try {
        while (queuedText.length) {
          const take = queuedText.length > 240 ? 8 : queuedText.length > 80 ? 4 : 2
          renderedText += queuedText.slice(0, take)
          queuedText = queuedText.slice(take)
          setAssistantContent(renderedText)
          await scrollToBottom()
          await sleep(16)
        }
      } finally {
        isTypingAnswer = false
      }
    }

    const enqueueAnswerText = (content: string) => {
      if (!content) return
      queuedText += content
      void runAnswerTypewriter()
    }

    const waitForAnswerTypewriter = async () => {
      while (isTypingAnswer || queuedText.length) {
        await sleep(24)
      }
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
        // 流式生成期间仅更新轻量状态行，最终回复完成后会移除
        if (assistantMsgId) {
          const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
          if (msgIndex !== -1) {
            messages.value[msgIndex].progress = {
              currentAgent: stageMap[evt.stage] || evt.stage,
              steps: [...runningSteps.value],
              expanded: false,
            }
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
        if (assistantMsgId) {
          const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
          if (msgIndex !== -1) {
            messages.value[msgIndex].progress = {
              currentAgent: translateAgent(evt.agent),
              steps: [...runningSteps.value],
              expanded: false,
            }
          }
        }
      }

      if (evt.type === 'token' && evt.content) {
        streamedText += evt.content
        enqueueAnswerText(evt.content)
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
                if (!streamedText && finalContent) {
                  enqueueAnswerText(finalContent)
                } else if (finalContent && finalContent.startsWith(streamedText)) {
                  enqueueAnswerText(finalContent.slice(streamedText.length))
                }
                await waitForAnswerTypewriter()
                messages.value[msgIndex].content = finalContent || renderedText || '处理完成'
                messages.value[msgIndex].isHighRisk = res.is_high_risk
                delete messages.value[msgIndex].progress
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

const confirmReportEntry = () => {
  if (!currentSessionId.value) return
  reportEntryConfirmed.value = true
  localStorage.setItem(getReportEntryKey(currentSessionId.value), '1')
  ElMessage.success('正式报告入口已生成')
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
  voiceSupported.value = !!getSpeechRecognitionCtor()

  loadHistoryFromStorage()
  if (!isLoggedIn.value) {
    ElMessage.info('当前为访客模式，登录后可同步保存问诊历史到个人档案')
  }
})

onUnmounted(() => {
  stopVoiceInput(true)
  cleanupSpeechRecognition()
  window.removeEventListener('auth-changed', handleAuthChanged)
})
</script>

<style scoped lang="scss">
$sidebar-width: 280px;
$header-height: 64px;
$primary: var(--tcm-accent-color, #10B981);
$bg-main: var(--tcm-bg-color, #050505);

.consult-page {
  display: flex;
  height: 100%;
  background: $bg-main;
  background-image: 
    radial-gradient(circle at 15% 50%, rgba(var(--theme-accent-rgb, 16, 185, 129), 0.04), transparent 50%),
    radial-gradient(circle at 85% 30%, rgba(var(--theme-accent-rgb, 52, 211, 153), 0.04), transparent 50%);
  overflow: hidden;
  color: var(--tcm-text-primary);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* ─── Sidebar: Seamless & Floating ─────────────────────────────────────── */
.sidebar {
  width: $sidebar-width;
  background: transparent;
  border-right: 1px solid var(--tcm-border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  padding: 16px 0;

  .sidebar-header {
    padding: 0 24px 24px;
    .new-session-btn {
      width: 100%;
      background: var(--tcm-card-bg);
      border: 1px solid var(--tcm-border-color);
      height: 48px;
      font-size: 15px;
      font-weight: 500;
      border-radius: 24px;
      color: var(--tcm-text-primary);
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      cursor: pointer;
      
      &:hover {
        background: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.1);
        border-color: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.3);
        color: $primary;
        transform: translateY(-2px);
        box-shadow: var(--tcm-shadow);
      }
    }
  }

  .session-list {
    flex: 1;
    overflow-y: auto;
    padding: 0 16px;

    &::-webkit-scrollbar { width: 0px; }

    .session-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 16px;
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-bottom: 8px;
      background: transparent;

      &:hover { 
        background: var(--tcm-card-bg); 
      }
      &.active { 
        background: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.08);
        border: 1px solid rgba(var(--theme-accent-rgb, 16, 185, 129), 0.15);
      }

      .session-icon { font-size: 18px; color: var(--tcm-text-regular); }
      &.active .session-icon { color: $primary; }

      .session-meta {
        flex: 1;
        overflow: hidden;
        .session-title {
          font-size: 14px;
          color: var(--tcm-text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .session-time {
          font-size: 12px;
          color: var(--tcm-text-regular);
          margin-top: 4px;
        }
      }

      .delete-btn { opacity: 0; color: #ef4444; }
      &:hover .delete-btn { opacity: 1; }
    }
  }
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background: transparent;
}

/* ─── Chat area ───────────────────────────────────── */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 40px 0 200px;
  scroll-behavior: smooth;

  &::-webkit-scrollbar { width: 0px; }

  .welcome-screen {
    max-width: 700px;
    width: 100%;
    margin: 0 auto;
    text-align: center;
    animation: fadeIn 1s cubic-bezier(0.16, 1, 0.3, 1);

    .welcome-icon img {
      width: 80px;
      height: 80px;
      border-radius: 24px;
      box-shadow: var(--tcm-shadow);
      margin-bottom: 32px;
    }

    h2 {
      font-size: 36px;
      font-weight: 600;
      letter-spacing: -0.5px;
      color: var(--tcm-text-primary);
      margin-bottom: 16px;
    }

    p { color: var(--tcm-text-regular); font-size: 16px; margin-bottom: 48px; }

    .feature-cards {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 48px;

      .feature-card {
        background: var(--tcm-card-bg);
        border: 1px solid var(--tcm-border-color);
        border-radius: 24px;
        padding: 24px 16px;
        transition: all 0.4s ease;

        &:hover {
          background: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.04);
          border-color: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.2);
          transform: translateY(-4px);
        }

        .el-icon { font-size: 24px; color: $primary; margin-bottom: 12px; }
        span { display: block; font-size: 15px; font-weight: 500; color: var(--tcm-text-primary); margin-bottom: 4px; }
        small { color: var(--tcm-text-regular); font-size: 12px; }
      }
    }
    
    .start-btn {
      padding: 0 40px;
      height: 56px;
      border-radius: 28px;
      font-size: 16px;
      font-weight: 600;
      background: var(--tcm-text-primary);
      color: var(--tcm-bg-color);
      border: none;
      transition: all 0.3s ease;
      cursor: pointer;
      
      &:hover {
        transform: scale(1.05);
        background: $primary;
        color: #fff;
        box-shadow: 0 12px 24px rgba(var(--theme-accent-rgb, 16, 185, 129), 0.3);
      }
    }
  }

  .messages-list { 
    width: 100%;
    max-width: 840px; 
    padding: 0 24px;
    margin: 0 auto;
    display: flex; 
    flex-direction: column; 
    gap: 40px; 
  }

  .message-row {
    display: flex;
    align-items: flex-start;
    gap: 20px;
    animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);

    &.user { justify-content: flex-end; }

    .avatar {
      width: 36px;
      height: 36px;
      border-radius: 12px;
      object-fit: cover;
    }

    .bubble-wrap {
      max-width: 85%;
      display: flex;
      flex-direction: column;
      gap: 8px;

      .assistant-status-line {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 2px 0 2px 24px;
        width: fit-content;
        color: var(--tcm-text-regular);
        font-size: 13px;
        line-height: 1.5;

        .status-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: $primary;
          box-shadow: 0 0 0 0 rgba(var(--theme-accent-rgb, 16, 185, 129), 0.35);
          animation: statusPulse 1.4s ease-in-out infinite;
        }
      }

      .bubble {
        line-height: 1.7;
        font-size: 16px;
        letter-spacing: 0.1px;
        padding: 14px 18px;
        border: 1px solid var(--tcm-border-color);
        border-radius: 20px;
        background: var(--tcm-card-bg);
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);

        &.assistant {
          background: var(--tcm-card-bg);
          border-color: rgba(148, 163, 184, 0.28);
          color: var(--tcm-text-primary);
          border-radius: 20px 20px 20px 6px;
        }

        &.user {
          border-radius: 20px 20px 6px 20px;
          background: $primary;
          color: #fff;
          border-color: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.45);
          box-shadow: 0 12px 32px rgba(var(--theme-accent-rgb, 16, 185, 129), 0.2);
        }

        .bubble-content :deep(p) { margin: 0 0 1em; }
        .bubble-content :deep(p:last-child) { margin: 0; }
        .bubble-content :deep(strong) { color: inherit; font-weight: 600; }
        .bubble-content :deep(h3), .bubble-content :deep(h4), .bubble-content :deep(h5) {
          margin: 1.5em 0 0.5em;
          color: inherit;
        }
        .bubble-content :deep(ul) { padding-left: 20px; }
        .bubble-content :deep(li) { margin-bottom: 8px; }

        .references {
          margin-top: 16px;
          border-top: 1px solid var(--tcm-border-color);
          padding-top: 12px;

          :deep(.el-collapse) {
            border: none;
            --el-collapse-header-bg-color: transparent;
            --el-collapse-header-text-color: var(--tcm-text-regular);
            --el-collapse-content-bg-color: transparent;
            --el-collapse-content-text-color: var(--tcm-text-regular);
            --el-collapse-border-color: transparent;
          }

          .ref-item {
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin: 8px 0;
            font-size: 13px;
            background: var(--tcm-card-bg);
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid var(--tcm-border-color);
            
            .el-tag {
              background: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.1);
              border-color: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.2);
              color: $primary;
            }
          }
        }
      }

      .msg-time { font-size: 12px; color: var(--tcm-text-regular); padding: 0 8px; }
    }
    
    &.user .bubble-wrap { align-items: flex-end; }
    &.user .bubble-wrap .msg-time { text-align: right; }
  }
}

/* ─── Input area: Floating Bento Box ──────────────────────────────────── */
.input-area {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 800px;
  background: var(--theme-overlay);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border: 1px solid var(--tcm-border-color);
  border-radius: 32px;
  padding: 16px 24px;
  box-shadow: 
    var(--tcm-shadow), 
    0 0 0 1px var(--tcm-border-color) inset;
  z-index: 100;
  transition: all 0.3s ease;

  &:focus-within {
    background: var(--theme-overlay);
    border-color: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.3);
    box-shadow: var(--tcm-shadow), 0 0 0 1px rgba(var(--theme-accent-rgb, 16, 185, 129), 0.1) inset;
  }

  &.completed {
    max-width: 720px;
    padding: 14px 18px;
  }

  .disclaimer-bar {
    font-size: 12px;
    color: var(--tcm-text-regular);
    text-align: center;
    margin-bottom: 12px;
  }

  .input-row {
    display: flex;
    gap: 16px;
    align-items: flex-end;

    .el-textarea { 
      flex: 1; 
      :deep(.el-textarea__inner) {
        background: transparent !important;
        border: none !important;
        color: var(--tcm-text-primary) !important;
        padding: 12px 4px;
        font-size: 16px;
        line-height: 1.5;
        box-shadow: none !important;
        resize: none;
        
        &::placeholder { color: var(--tcm-text-regular); }
      }
    }

    .voice-btn {
      width: 48px;
      height: 48px;
      padding: 0;
      border-radius: 20px;
      background: var(--tcm-card-bg);
      border: 1px solid var(--tcm-border-color);
      color: var(--tcm-text-primary);
      font-size: 18px;
      transition: all 0.2s ease;
      cursor: pointer;
      flex: 0 0 48px;

      &:hover:not(:disabled) {
        background: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.1);
        color: $primary;
        border-color: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.3);
        transform: scale(1.02);
      }

      &.recording {
        background: #ef4444;
        border-color: #ef4444;
        color: #fff;
        box-shadow: 0 0 0 6px rgba(239, 68, 68, 0.16);
        animation: recordingPulse 1.4s ease-in-out infinite;
      }

      &:disabled {
        background: var(--tcm-card-bg);
        color: var(--tcm-text-regular);
        cursor: not-allowed;
        opacity: 0.6;
      }
    }

    .send-btn {
      height: 48px;
      padding: 0 24px;
      border-radius: 20px;
      background: var(--tcm-text-primary);
      color: var(--tcm-bg-color);
      border: none;
      font-size: 15px;
      font-weight: 600;
      transition: all 0.2s ease;
      cursor: pointer;
      
      &:hover:not(:disabled) {
        transform: scale(1.02);
        background: $primary;
        color: #fff;
      }
      
      &:disabled { background: var(--tcm-card-bg); color: var(--tcm-text-regular); cursor: not-allowed; }
    }

    .upload-tongue-btn {
      height: 48px;
      padding: 0 20px;
      border-radius: 20px;
      background: var(--tcm-card-bg);
      border: 1px solid var(--tcm-border-color);
      color: var(--tcm-text-primary);
      font-size: 15px;
      font-weight: 500;
      transition: all 0.2s ease;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      
      &:hover:not(:disabled) {
        background: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.1);
        color: $primary;
        border-color: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.3);
        transform: scale(1.02);
      }
      
      &:disabled { background: var(--tcm-card-bg); color: var(--tcm-text-regular); cursor: not-allowed; opacity: 0.7; }
    }
  }

  .report-confirm-card {
    margin-top: 16px;
    padding: 14px 16px;
    border: 1px solid var(--tcm-border-color);
    border-radius: 20px;
    background: var(--tcm-card-bg);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;

    .confirm-copy {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      min-width: 0;
      color: var(--tcm-text-primary);

      .el-icon {
        color: $primary;
        margin-top: 2px;
        flex: 0 0 auto;
      }

      strong {
        display: block;
        font-size: 14px;
        margin-bottom: 2px;
      }

      span {
        display: block;
        font-size: 13px;
        color: var(--tcm-text-regular);
        line-height: 1.5;
      }
    }

    .confirm-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 0 0 auto;

      .el-button {
        height: 38px !important;
        padding: 0 16px !important;
        border-radius: 18px !important;
      }
    }
  }

  &.completed .report-confirm-card {
    margin-top: 0;
  }
}

/* ─── Dialogs & Modals (Bento Box Redesign) ───────────────────────── */
:deep(.el-dialog) {
  background: var(--tcm-bg-color) !important;
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border: 1px solid var(--tcm-border-color);
  border-radius: 32px;
  box-shadow: 
    0 24px 48px -12px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.05) inset;
  padding: 8px;
  
  .el-dialog__header {
    border: none;
    padding: 24px 24px 16px;
    margin-right: 0;
  }
  
  .el-dialog__title {
    color: var(--tcm-text-primary) !important;
    font-weight: 600;
    font-size: 20px;
    letter-spacing: -0.02em;
  }
  
  .el-dialog__body {
    padding: 0 16px 16px;
    color: var(--tcm-text-regular);
  }

  .el-dialog__footer {
    padding: 0 16px 24px;
    border: none;
  }
  
  .el-dialog__headerbtn {
    top: 24px;
    right: 24px;
    .el-dialog__close {
      color: var(--tcm-text-regular);
      font-size: 20px;
      transition: color 0.2s ease;
      &:hover { color: var(--tcm-text-primary); }
    }
  }

  /* Bento Box Layout */
  .tongue-bento-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .bento-card {
    background: var(--tcm-card-bg);
    border: 1px solid var(--tcm-border-color);
    border-radius: 24px;
    padding: 20px;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
  }

  .bento-hover {
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
    &:hover {
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 8px 24px -8px rgba(var(--theme-accent-rgb, 16, 185, 129), 0.3);
      border-color: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.4);
      background: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.05);
    }
    &:active {
      transform: translateY(0) scale(0.98);
    }
  }

  /* Guide Card */
  .guide-card {
    display: flex;
    align-items: center;
    gap: 20px;
    background: var(--tcm-card-bg);
    
    .guide-icon-wrapper {
      width: 56px;
      height: 56px;
      border-radius: 16px;
      background: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.1);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      color: $primary;
      
      .camera-icon-large {
        font-size: 28px;
      }
    }
    
    .guide-text {
      h4 {
        margin: 0 0 8px 0;
        color: var(--tcm-text-primary);
        font-size: 16px;
        font-weight: 600;
      }
      ul {
        margin: 0;
        padding: 0;
        list-style: none;
        li {
          font-size: 13px;
          color: var(--tcm-text-regular);
          margin-bottom: 6px;
          display: flex;
          align-items: center;
          gap: 6px;
          line-height: 1.4;
          &:last-child { margin-bottom: 0; }
          .el-icon {
            color: $primary;
            font-size: 14px;
          }
        }
      }
    }
  }

  /* Upload Card */
  .upload-card {
    padding: 0; /* Remove padding to let children fill */
    border-style: dashed;
    border-width: 2px;
    
    &.has-preview {
      border-style: solid;
      border-width: 1px;
    }

    .upload-actions {
      display: flex;
      height: 160px;
      
      .action-btn-wrapper {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 12px;
        color: var(--tcm-text-primary);
        font-weight: 500;
        font-size: 15px;
        
        .action-icon {
          width: 64px;
          height: 64px;
          border-radius: 20px;
          background: var(--tcm-bg-color);
          border: 1px solid var(--tcm-border-color);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 28px;
          color: var(--tcm-text-primary);
        }
      }
      
      .upload-wrapper {
        flex: 1;
        display: flex;
        .el-upload {
          width: 100%;
          display: flex;
        }
      }
      
      .action-divider {
        width: 1px;
        background: var(--tcm-border-color);
        margin: 24px 0;
      }
    }

    .preview-area {
      padding: 12px;
      
      .preview-wrapper {
        position: relative;
        border-radius: 16px;
        overflow: hidden;
        aspect-ratio: 16 / 9;
        max-height: 240px;
        background: var(--tcm-bg-color);
        
        .preview-image {
          width: 100%;
          height: 100%;
          object-fit: contain;
          display: block;
        }
        
        .preview-overlay {
          position: absolute;
          inset: 0;
          background: rgba(0, 0, 0, 0.4);
          opacity: 0;
          transition: opacity 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        &:hover .preview-overlay {
          opacity: 1;
        }
        
        .remove-btn {
          width: 48px;
          height: 48px;
          font-size: 20px;
          background: rgba(245, 108, 108, 0.9);
          border: none;
          color: #fff;
          
          &:hover {
            background: #f56c6c;
            transform: scale(1.1);
          }
        }
      }
    }
  }

  /* Status Card */
  .status-card {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 16px;
    background: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.1);
    border-color: rgba(var(--theme-accent-rgb, 16, 185, 129), 0.3);
    color: $primary;
    font-weight: 500;
    
    .loading-ring {
      width: 20px;
      height: 20px;
      border: 2px solid rgba(var(--theme-accent-rgb, 16, 185, 129), 0.3);
      border-top-color: $primary;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
  }

  /* Footer Buttons */
  .bento-footer {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    
    .pill-btn {
      height: 44px;
      border-radius: 22px;
      padding: 0 24px;
      font-size: 15px;
      font-weight: 600;
      transition: all 0.2s ease;
      
      &.cancel-btn {
        background: transparent;
        border: 1px solid var(--tcm-border-color);
        color: var(--tcm-text-regular);
        &:hover {
          color: var(--tcm-text-primary);
          background: var(--tcm-card-bg);
        }
      }
      
      &.submit-btn {
        background: var(--tcm-text-primary);
        color: var(--tcm-bg-color);
        border: none;
        &:hover:not(:disabled) {
          background: $primary;
          color: #fff;
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(var(--theme-accent-rgb, 16, 185, 129), 0.3);
        }
        &:disabled {
          background: var(--tcm-card-bg);
          color: var(--tcm-text-regular);
          opacity: 0.5;
        }
      }
    }
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes recordingPulse {
  0%, 100% { box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.14); }
  50% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0.05); }
}

@keyframes statusPulse {
  0% { opacity: 0.45; box-shadow: 0 0 0 0 rgba(var(--theme-accent-rgb, 16, 185, 129), 0.35); }
  50% { opacity: 1; box-shadow: 0 0 0 6px rgba(var(--theme-accent-rgb, 16, 185, 129), 0.08); }
  100% { opacity: 0.45; box-shadow: 0 0 0 0 rgba(var(--theme-accent-rgb, 16, 185, 129), 0); }
}

/* ─── Animations ──────────────────────────────────── */
@keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

/* Responsive */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .chat-area { padding: 20px 0 180px; }
  .input-area { width: 92%; bottom: 20px; padding: 12px 16px; border-radius: 28px; }
  .input-area .input-row .upload-tongue-btn { height: 44px; padding: 0 16px; border-radius: 16px; font-size: 14px; }
  .input-area .input-row .voice-btn { width: 44px; height: 44px; border-radius: 16px; flex-basis: 44px; }
  .input-area .input-row .send-btn { height: 44px; border-radius: 16px; }
  .input-area .report-confirm-card { align-items: stretch; flex-direction: column; }
  .input-area .report-confirm-card .confirm-actions { width: 100%; justify-content: flex-end; flex-wrap: wrap; }
}
</style>
