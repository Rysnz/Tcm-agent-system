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

      <!-- Agent 执行步骤时间线 -->
      <transition name="slide-down">
        <div v-if="agentSteps.length" class="agent-timeline">
          <div class="timeline-title">
            <el-icon><Operation /></el-icon>
            <span>智能体执行轨迹</span>
          </div>
          <el-scrollbar class="timeline-scroll">
            <div class="timeline-steps">
              <div
                v-for="(step, idx) in agentSteps"
                :key="idx"
                class="step-item"
                :class="{ 'step-active': idx === agentSteps.length - 1, 'step-error': !step.success }"
              >
                <el-icon class="step-icon">
                  <component :is="getStepIcon(step.agent)" />
                </el-icon>
                <span class="step-name">{{ translateAgent(step.agent) }}</span>
                <el-tag size="small" :type="step.success ? 'success' : 'danger'" effect="light">
                  {{ step.success ? '✓' : '✗' }}
                </el-tag>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </transition>

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

          <!-- 打字动画 -->
          <div v-if="isThinking" class="message-row assistant">
            <img src="@/assets/assistant-avatar.png" class="avatar" alt="助手" />
            <div class="bubble-wrap">
              <div class="bubble assistant thinking">
                <span class="dot" /><span class="dot" /><span class="dot" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <div class="disclaimer-bar" v-if="messages.length">
          ⚠️ 本系统仅提供健康参考建议，不构成医疗诊断，如有急重症状请立即就医
        </div>
        <div class="input-row">
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus, ChatDotRound, Document, Camera, Operation,
  View, Microphone, QuestionFilled, FirstAidKit,
  Promotion, CircleCheckFilled
} from '@element-plus/icons-vue'
import { consultApi } from '@/api'
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
}

interface AgentStep {
  agent: string
  stage: string
  success: boolean
  retry_count: number
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

const STORAGE_KEY = 'tcm_session_history'
const MESSAGES_PREFIX = 'tcm_session_msgs_'
const STAGE_PREFIX = 'tcm_session_stage_'

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

const getStepIcon = (_name: string) => 'Operation'

const scrollToBottom = async () => {
  await nextTick()
  if (chatAreaRef.value) {
    chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
  }
}

const loadHistoryFromStorage = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) sessionHistory.value = JSON.parse(raw)
  } catch {
    sessionHistory.value = []
  }
}

const saveHistoryToStorage = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionHistory.value))
}

const saveMessagesToStorage = (sessionId: string) => {
  localStorage.setItem(MESSAGES_PREFIX + sessionId, JSON.stringify(messages.value))
  localStorage.setItem(STAGE_PREFIX + sessionId, currentStage.value)
}

const loadMessagesFromStorage = (sessionId: string): boolean => {
  try {
    const raw = localStorage.getItem(MESSAGES_PREFIX + sessionId)
    const stage = localStorage.getItem(STAGE_PREFIX + sessionId)
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

const startNewSession = async () => {
  try {
    messages.value = []
    agentSteps.value = []
    currentStage.value = 'intake'
    inputText.value = ''

    const res = await consultApi.createSession()
    currentSessionId.value = res.session_id

    if (res.message) {
      messages.value.push({
        id: Date.now().toString(),
        role: 'assistant',
        content: res.message,
        time: dayjs().format('HH:mm'),
      })
      saveMessagesToStorage(currentSessionId.value)
      await scrollToBottom()
    }
  } catch (err) {
    ElMessage.error('创建会话失败，请检查后端服务是否启动')
    console.error(err)
  }
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
    const res = await consultApi.sendMessage(currentSessionId.value, text)
    isThinking.value = false
    currentStage.value = res.stage

    // Update agent steps
    if (res.agent_steps?.length) {
      agentSteps.value = [...agentSteps.value, ...res.agent_steps].slice(-10)
    }

    // Build references from report if available
    const refs = res.report?.references || []

    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: res.assistant_message,
      time: dayjs().format('HH:mm'),
      isHighRisk: res.is_high_risk,
      references: refs,
    })

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

onMounted(() => {
  loadHistoryFromStorage()
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
  background: $bg-main;
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
    }
  }
}

/* ─── Main content ────────────────────────────────── */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .content-header {
    height: $header-height;
    background: #fff;
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
    gap: 6px;
    font-size: 12px;
    color: #666;
    margin-bottom: 6px;
  }

  .timeline-scroll { max-height: 48px; }

  .timeline-steps {
    display: flex;
    gap: 8px;

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

    &.user { flex-direction: row-reverse; }

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

      .risk-alert { margin-bottom: 8px; }

      .bubble {
        padding: 12px 16px;
        border-radius: 12px;
        line-height: 1.7;
        font-size: 14px;

        &.assistant {
          background: #fff;
          border: 1px solid $border-color;
          border-radius: 2px 12px 12px 12px;
          color: #1a1a2e;
        }

        &.user {
          background: $primary;
          color: #fff;
          border-radius: 12px 2px 12px 12px;
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
