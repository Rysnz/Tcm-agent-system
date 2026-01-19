<template>
  <div class="setting-container">
    <div class="header">
      <h2>设置</h2>
    </div>
    <div class="setting-content">
      <!-- 左侧设置面板 -->
      <div class="setting-panel">
        <el-card shadow="hover" class="setting-card">
          <el-form :model="settingForm" label-width="120px" size="default">
            <!-- 基本设置 -->
            <div class="section-header">基本设置</div>
            <el-form-item label="名称">
              <el-input v-model="settingForm.name" placeholder="请输入名称" maxlength="64" show-word-limit />
            </el-form-item>
            <el-form-item label="图标">
              <div class="icon-upload-section">
                <el-upload
                  action="#"
                  :show-file-list="false"
                  :before-upload="handleIconUpload"
                  accept="image/*"
                >
                  <img v-if="settingForm.icon" :src="settingForm.icon" class="avatar" />
                  <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
                </el-upload>
                <div class="upload-tips">点击上传图标，支持 JPG、PNG 等格式</div>
              </div>
            </el-form-item>
            <el-form-item label="描述">
              <el-input
                v-model="settingForm.desc"
                type="textarea"
                :rows="3"
                placeholder="请输入描述"
                maxlength="256"
                show-word-limit
              />
            </el-form-item>

            <el-divider />

            <!-- AI 模型 -->
            <div class="section-header">AI 模型</div>
            <el-form-item label="模型选择">
              <el-select v-model="settingForm.model_config.model" placeholder="请选择AI模型" style="width: 100%">
                <el-option
                  v-for="model in availableModels"
                  :key="model.id"
                  :label="model.name"
                  :value="model.id"
                >
                  {{ model.name }} ({{ model.provider }})
                </el-option>
              </el-select>
              <div class="help-text">选择用于对话的AI模型</div>
            </el-form-item>
            <el-form-item label="系统角色">
              <el-input
                v-model="settingForm.system_prompt"
                type="textarea"
                :rows="4"
                placeholder="请输入系统角色描述"
              />
            </el-form-item>
            <el-form-item label="历史聊天记录">
              <el-input-number
                v-model="settingForm.model_config.history_count"
                :min="0"
                :max="10"
                :step="1"
                placeholder="请输入历史记录数量"
                controls-position="right"
                size="large"
              />
              <div class="help-text">设置传递给模型的历史聊天记录条数</div>
            </el-form-item>

            <el-divider />

            <!-- 提示词设置 -->
            <div class="section-header">提示词设置</div>
            <el-form-item label="提示词模板">
              <el-input
                v-model="settingForm.prompt_template"
                type="textarea"
                :rows="4"
                placeholder="请输入提示词模板"
              />
              <div class="help-text">提示词模板用于生成传递给模型的完整prompt，支持{system_prompt}、{history}、{context}、{question}等变量</div>
            </el-form-item>
            <el-form-item label="开场白">
              <el-input
                v-model="settingForm.model_config.greeting"
                type="textarea"
                :rows="3"
                placeholder="请输入开场白"
              />
              <div class="help-text">开场白将显示在对话界面的欢迎消息中，支持可交互的示例问题</div>
            </el-form-item>
            <el-form-item label="输出思考">
              <el-switch v-model="settingForm.model_config.output_thinking" />
              <div class="help-text">开启后，模型将输出思考过程，增强对话的透明度</div>
            </el-form-item>

            <el-divider />

            <!-- 文件上传设置 -->
            <div class="section-header">文件上传设置</div>
            <el-form-item label="文件上传">
              <el-switch v-model="settingForm.enable_file_upload" />
              <div class="help-text">开启后，用户可以在对话中上传文件</div>
            </el-form-item>

            <el-divider />

            <!-- 语音设置 -->
            <div class="section-header">语音设置</div>
            <el-form-item label="语音输入">
              <el-switch v-model="settingForm.model_config.voice_input" />
            </el-form-item>
            <el-form-item v-if="settingForm.model_config.voice_input" label="语音转文字模型">
              <el-select v-model="settingForm.model_config.stt_model" placeholder="请选择语音转文字模型" style="width: 100%">
                <el-option
                  v-for="model in voiceModels"
                  :key="model.id"
                  :label="model.name"
                  :value="model.id"
                >
                  {{ model.name }} ({{ model.provider }})
                </el-option>
              </el-select>
              <div class="help-text">选择用于语音转文字的模型</div>
            </el-form-item>
            <el-form-item label="语音播放">
              <el-switch v-model="settingForm.model_config.voice_output" />
            </el-form-item>
            <el-form-item v-if="settingForm.model_config.voice_output" label="语音播放方式">
              <el-select v-model="settingForm.model_config.tts_type" placeholder="请选择语音播放方式" style="width: 100%" @change="handleTtsTypeChange">
                <el-option label="浏览器播放" value="browser" />
                <el-option label="语音合成模型" value="model" />
              </el-select>
              <div class="help-text">选择语音播放的方式</div>
            </el-form-item>
            <el-form-item v-if="settingForm.model_config.voice_output && settingForm.model_config.tts_type === 'model'" label="语音合成模型">
              <el-select v-model="settingForm.model_config.tts_model" placeholder="请选择语音合成模型" style="width: 100%">
                <el-option
                  v-for="model in voiceModels"
                  :key="model.id"
                  :label="model.name"
                  :value="model.id"
                >
                  {{ model.name }} ({{ model.provider }})
                </el-option>
              </el-select>
              <div class="help-text">选择用于语音合成的模型</div>
            </el-form-item>

            <el-divider />

            <!-- 知识库设置 -->
            <div class="section-header">知识库设置</div>
            <el-form-item label="关联知识库">
              <el-select
                v-model="settingForm.knowledge_bases"
                placeholder="请选择关联的知识库"
                style="width: 100%"
              >
                <el-option
                  v-for="kb in knowledgeBases"
                  :key="kb.id"
                  :label="kb.name"
                  :value="kb.id"
                >
                  {{ kb.name }}
                </el-option>
              </el-select>
              <div class="help-text">选择要关联的知识库，对话时将检索这些知识库</div>
            </el-form-item>
            <el-form-item label="相似度阈值">
              <el-slider
                v-model="settingForm.similarity_threshold"
                :min="0"
                :max="1"
                :step="0.05"
                show-input
                :input-size="'small'"
                :format-tooltip="val => `${(val * 100).toFixed(0)}%`"
              />
              <div class="help-text">相似度分数大于该阈值时，使用检索到的文档进行增强生成</div>
            </el-form-item>
            <el-form-item label="引用分段数(top)">
              <el-input-number
                v-model="settingForm.top_k"
                :min="1"
                :max="20"
                :step="1"
                placeholder="请输入引用分段数"
                controls-position="right"
                size="large"
              />
              <div class="help-text">设置将多少段相似度大于阈值的文档传递给模型用于增强生成</div>
            </el-form-item>

            <el-divider />

            <!-- 操作按钮 -->
            <div class="button-section">
              <el-form-item>
                <el-button type="primary" @click="saveSetting" class="save-button" size="large" style="width: 100%">保存设置</el-button>
              </el-form-item>
              <el-form-item>
                <el-button @click="resetSetting" size="large" style="width: 100%">重置</el-button>
              </el-form-item>
            </div>
          </el-form>
        </el-card>
      </div>

      <!-- 右侧聊天调试界面 -->
      <div class="chat-panel">
        <el-card shadow="hover" class="chat-card">
          <template #header>
            <div class="card-header">
              <span>调试聊天</span>
            </div>
          </template>
          <div class="chat-container">
            <!-- 开场白 -->
            <div v-if="showGreeting && appGreeting" class="message-item assistant-message">
              <div class="message-avatar assistant-avatar">
                <img src="/src/assets/assistant-avatar.png" alt="AI助手头像" />
              </div>
              <div class="message-content-wrapper">
                <div class="message-header">
                  <span class="message-role">AI助手</span>
                  <span class="message-time">{{ formatTime(new Date()) }}</span>
                </div>
                <div class="message-content">
                  <div class="greeting-message" v-html="formattedGreeting"></div>
                </div>
              </div>
            </div>
            
            <!-- 消息展示区 -->
            <div class="message-list" ref="messageList">
              <div
                v-for="(message, index) in debugMessages"
                :key="index"
                class="message-item"
                :class="{
                  'user-message': message.role === 'user',
                  'assistant-message': message.role === 'assistant'
                }"
              >
                <div class="message-avatar"
                     :class="{
                       'user-avatar': message.role === 'user',
                       'assistant-avatar': message.role === 'assistant'
                     }">
                  <img v-if="message.role === 'assistant'" src="/src/assets/assistant-avatar.png" alt="AI助手头像" />
                  <div v-else-if="message.role === 'assistant'" class="avatar-placeholder">AI</div>
                  <div v-else class="avatar-placeholder">我</div>
                </div>
                <div class="message-content-wrapper">
                  <div class="message-header">
                    <span class="message-role">{{ message.role === 'user' ? '我' : 'AI助手' }}</span>
                    <span class="message-time">{{ formatTime(message.create_time) }}</span>
                  </div>
                  <div class="message-content">
                    <div v-if="message.thought" class="thinking-message">
                      <el-icon class="thinking-icon"><Loading /></el-icon>
                      <span>{{ message.thought }}</span>
                    </div>
                    <div v-if="message.content" class="text-message">
                    {{ message.content }}
                  </div>
                  <!-- 检索结果显示区域 -->
                  <div v-if="message.search_results && message.search_results.length > 0" class="search-results">
                    <div class="results-header">
                      <el-icon><Search /></el-icon>
                      <span>相关文档内容 ({{ message.search_results.length }}条)</span>
                    </div>
                    <div class="results-list">
                      <div v-for="(result, idx) in message.search_results" :key="result.id || idx" class="result-item">
                        <div class="result-title">{{ result.title || `相关内容${idx + 1}` }}</div>
                        <div class="result-content">{{ result.content }}</div>
                        <div class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              </div>
            </div>

            <!-- 输入区域 -->
            <div class="input-area">
              <el-input
                v-model="inputMessage"
                type="textarea"
                placeholder="请输入消息，按 Ctrl+Enter 发送"
                :rows="3"
                resize="none"
                @keydown.enter.exact="handleSendMessage"
                @keydown.ctrl.enter="handleSendMessage"
                :disabled="isSending"
              >
                <template #append>
                  <el-button
                    type="text"
                    @click="handleDebugVoiceInput"
                    :disabled="isSending"
                    class="voice-input-button"
                  >
                    <el-icon><Microphone /></el-icon>
                  </el-button>
                </template>
              </el-input>
              <div class="input-footer">
                <div class="send-info">
                  <span v-if="isSending" class="sending-text">
                    <el-icon class="loading-icon"><Loading /></el-icon>
                    发送中...
                  </span>
                </div>
                <el-button
                  type="primary"
                  @click="handleSendMessage"
                  :disabled="!inputMessage.trim() || isSending"
                  :loading="isSending"
                  class="send-button"
                >
                  发送
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Search, Plus } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import router from '@/router'
import { applicationApi, chatApi, knowledgeApi, modelApi, type Application } from '@/api'

// 格式化时间
const formatTime = (time: string | Date) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

// 知识库列表
const knowledgeBases = ref<Array<{id: string; name: string}>>([])

// 可用模型列表
const availableModels = ref<Array<{id: string; name: string; provider: string}>>([])

// 可用语音模型列表
const voiceModels = ref<Array<{id: string; name: string; provider: string}>>([])

// 设置表单数据
const settingForm = ref<Partial<Application>>({
  name: '',
  desc: '',
  icon: '',
  system_prompt: '',
  prompt_template_type: 'DEFAULT',
  similarity_threshold: 0.5,
  top_k: 5,
  enable_file_upload: true, // 默认启用文件上传
  model_config: {
    greeting: '您好，我是江小智——中医智能问诊小助手，您可以向我提出问题。\n\n- 主要功能有什么？\n- 怎样预防传染病？\n- 推荐用药',
    output_thinking: false,
    voice_input: false,
    voice_output: false,
    tts_type: 'browser',
    stt_model: 'default',
    tts_model: 'default',
    history_count: 5, // 默认保存5条历史聊天记录
    model: ''
  },
  knowledge_bases: ''
})

// 调试消息列表
const debugMessages = ref<Array<{
  role: 'user' | 'assistant'
  content?: string
  thought?: string
  search_results?: Array<{
    id?: string
    title?: string
    content: string
    score: number
  }>
  create_time: Date
}>>([])

// 输入消息
const inputMessage = ref('')
// 发送状态
const isSending = ref(false)
// 消息列表引用
const messageList = ref<HTMLElement | null>(null)

// 开场白相关
const appGreeting = ref('')
const showGreeting = ref(true)
const formattedGreeting = ref('')

// 监听开场白变化，实时更新调试界面
watch(
  () => settingForm.value.model_config?.greeting,
  (newGreeting) => {
    appGreeting.value = newGreeting || ''
    formattedGreeting.value = formatGreeting(appGreeting.value)
    
    // 重新添加示例问题点击事件监听器
    nextTick(() => {
      // 先移除旧的事件监听器，避免重复绑定
      const oldLinks = document.querySelectorAll('.example-question')
      oldLinks.forEach(link => {
        link.removeEventListener('click', handleExampleQuestionClick)
      })
      
      // 添加新的事件监听器
      const newLinks = document.querySelectorAll('.example-question')
      newLinks.forEach(link => {
        link.addEventListener('click', handleExampleQuestionClick)
      })
    })
  },
  { deep: true }
)

// 格式化开场白，将示例问题转换为可点击的链接
const formatGreeting = (greeting: string) => {
  // 将开场白文本分为普通文本和预设问题两部分
  const parts = greeting.split('\n\n')
  const mainText = parts[0] || ''
  const questions = parts[1] || ''
  
  // 格式化预设问题为纵向排列的可点击标签，每个问题独占一行
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
    handleSendMessage()
  }
}

// 保存设置
const saveSetting = async () => {
  if (!settingForm.value.id) {
    ElMessage.error('应用ID不存在，无法保存设置')
    return
  }
  
  try {
    // 创建一个副本，用于处理保存的数据
    const saveData = { ...settingForm.value };
    
    // 将知识库字段转换为数组格式
    if (saveData.knowledge_bases) {
      if (typeof saveData.knowledge_bases === 'string') {
        // 如果是字符串，转换为单元素数组
        saveData.knowledge_bases = [saveData.knowledge_bases];
      } else if (!Array.isArray(saveData.knowledge_bases)) {
        // 如果既不是字符串也不是数组，转换为数组
        saveData.knowledge_bases = [saveData.knowledge_bases];
      }
    } else {
      // 如果为空，设置为空数组
      saveData.knowledge_bases = [];
    }
    
    console.log('保存的数据:', saveData);
    
    await applicationApi.updateApplication(settingForm.value.id, saveData)
    ElMessage.success('设置保存成功')
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存设置失败')
  }
}

// 重置设置
const resetSetting = () => {
  loadCurrentApplication()
}

// 加载当前应用
const loadCurrentApplication = async () => {
  try {
    // 加载应用列表
    const applications = await applicationApi.getApplications()
    console.log('加载应用列表结果:', applications)
    
    if (applications.length > 0) {
      // 假设使用第一个应用作为当前设置的应用
      const app = applications[0]
      console.log('当前应用数据:', app)
      
      // 确保model_config对象存在，并且包含所有必要字段
      const modelConfig = {
        greeting: '您好，我是江小智——中医智能问诊小助手，您可以向我提出问题。\n\n- 主要功能有什么？\n- 怎样预防传染病？\n- 推荐用药',
        output_thinking: false,
        voice_input: false,
        voice_output: false,
        tts_type: 'browser',
        stt_model: 'default',
        tts_model: 'default',
        history_count: 1,
        model: '',
        ...(app.model_config || {})
      };
      
      // 删除model_config中的top_k，因为它现在是根级别字段
      if (modelConfig.top_k) {
        delete modelConfig.top_k;
      }
      
      // 处理知识库字段，转换为数组格式
      let knowledgeBasesArray = [];
      if (app.knowledge_bases) {
        if (Array.isArray(app.knowledge_bases)) {
          knowledgeBasesArray = app.knowledge_bases;
        } else if (typeof app.knowledge_bases === 'string') {
          try {
            // 尝试解析JSON字符串
            knowledgeBasesArray = JSON.parse(app.knowledge_bases);
            if (!Array.isArray(knowledgeBasesArray)) {
              knowledgeBasesArray = [app.knowledge_bases];
            }
          } catch (e) {
            // 如果解析失败，将其作为单个元素放入数组
            knowledgeBasesArray = [app.knowledge_bases];
          }
        } else {
          knowledgeBasesArray = [app.knowledge_bases];
        }
      }
      
      // 将数组转换为字符串，用于单选选择框
      const knowledgeBase = knowledgeBasesArray.length > 0 ? knowledgeBasesArray[0] : '';
      
      // 从应用配置中获取top_k参数，默认为5
      const topK = app.top_k || 5;
      console.log('topK:', topK);
      
      // 合并应用数据
    settingForm.value = {
      ...settingForm.value,
      ...app,
      // 确保model_config始终是对象，不会被覆盖为undefined或null
      model_config: modelConfig,
      knowledge_bases: knowledgeBase,
      top_k: topK,
      // 确保enable_file_upload字段存在（处理null和undefined情况）
      enable_file_upload: app.enable_file_upload ?? true
    };
    console.log('设置当前应用:', settingForm.value);
    
    // 初始化开场白
    appGreeting.value = modelConfig.greeting || ''
    showGreeting.value = true
    formattedGreeting.value = formatGreeting(appGreeting.value)
    } else {
      // 如果没有应用，确保settingForm仍然有model_config
      console.log('没有应用，初始化settingForm.model_config');
      settingForm.value.model_config = settingForm.value.model_config || {
        greeting: '您好，我是江小智——中医智能问诊小助手，您可以向我提出问题。\n\n- 主要功能有什么？\n- 怎样预防传染病？\n- 推荐用药',
        output_thinking: false,
        voice_input: false,
        voice_output: false,
        tts_type: 'browser',
        stt_model: 'default',
        tts_model: 'default',
        history_count: 1
      };
    }
    
    // 加载知识库列表
    const knowledgeBasesList = await knowledgeApi.getKnowledgeBases()
    console.log('加载知识库列表结果:', knowledgeBasesList)
    knowledgeBases.value = knowledgeBasesList
    
    // 加载可用模型列表
    try {
      const modelsList = await modelApi.getModels()
      console.log('加载可用模型列表结果:', modelsList)
      
      // 筛选大语言模型作为对话模型
      availableModels.value = modelsList.filter(model => 
        model.model_type === 'LLM' || 
        model.model_type === '大语言模型' ||
        (model.name && model.name.toLowerCase().includes('llm')) ||
        (model.name && model.name.toLowerCase().includes('大语言模型'))
      )
      
      // 筛选语音相关模型
      voiceModels.value = modelsList.filter(model => 
        model.model_type === 'STT' || 
        model.model_type === 'TTS' || 
        model.model_type === '语音转文字' || 
        model.model_type === '语音合成' ||
        model.name.toLowerCase().includes('voice') || 
        model.name.toLowerCase().includes('stt') || 
        model.name.toLowerCase().includes('tts') ||
        model.provider.toLowerCase().includes('voice')
      )
      console.log('筛选后的语音模型:', voiceModels.value)
    } catch (error) {
      console.error('加载可用模型列表失败:', error)
      ElMessage.error('加载可用模型列表失败')
    }
    
    ElMessage.success('加载应用和知识库成功')
    
    // 添加示例问题点击事件监听器
    nextTick(() => {
      const questionLinks = document.querySelectorAll('.example-question')
      questionLinks.forEach(link => {
        link.addEventListener('click', handleExampleQuestionClick)
      })
    })
  } catch (error) {
    console.error('加载应用或知识库失败:', error)
    // 更详细的错误信息
    const errorMessage = error instanceof Error ? error.message : String(error)
    ElMessage.error(`加载应用或知识库失败: ${errorMessage}`)
    
    // 即使加载失败，也初始化知识库列表为数组
    knowledgeBases.value = []
    // 确保settingForm仍然有model_config
    if (!settingForm.value.model_config) {
      settingForm.value.model_config = {
        greeting: '您好，我是江小智——中医智能问诊小助手，您可以向我提出问题。\n\n- 主要功能有什么？\n- 怎样预防传染病？\n- 推荐用药',
        output_thinking: false,
        voice_input: false,
        voice_output: false,
        tts_type: 'browser',
        stt_model: 'default',
        tts_model: 'default',
        history_count: 1
      }
    }
    
    // 初始化开场白
    appGreeting.value = settingForm.value.model_config.greeting || ''
    showGreeting.value = true
    formattedGreeting.value = formatGreeting(appGreeting.value)
    
    // 添加示例问题点击事件监听器
    nextTick(() => {
      const questionLinks = document.querySelectorAll('.example-question')
      questionLinks.forEach(link => {
        link.addEventListener('click', handleExampleQuestionClick)
      })
    })
  }
}

// 发送消息
const handleSendMessage = async () => {
  if (!inputMessage.value.trim() || isSending.value) return

  const message = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息
  const userMsg = {
    role: 'user' as const,
    content: message,
    create_time: new Date()
  }
  debugMessages.value.push(userMsg)
  scrollToBottom()

  isSending.value = true

  // 添加AI思考消息
  const assistantMsg = {
    role: 'assistant' as const,
    thought: '正在思考...',
    create_time: new Date(),
    search_results: []
  }
  debugMessages.value.push(assistantMsg)
  scrollToBottom()

  try {
    // 调用聊天API
    const response = await fetch('/api/chat/stream/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        application_id: settingForm.value.id || 'default',
        message: message
      })
    })

    if (!response.ok) {
      throw new Error('Network response was not ok')
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No reader available')
    }

    const decoder = new TextDecoder()
    let assistantContent = ''

    // 处理流式响应
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      assistantContent += chunk

      // 更新AI消息内容
      debugMessages.value[debugMessages.value.length - 1] = {
        ...assistantMsg,
        content: assistantContent
      }
      scrollToBottom()
    }

    // 移除思考状态
    debugMessages.value[debugMessages.value.length - 1] = {
      ...assistantMsg,
      content: assistantContent,
      thought: undefined
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    // 更新错误消息
    debugMessages.value[debugMessages.value.length - 1] = {
      ...assistantMsg,
      content: `抱歉，处理您的请求时出现错误：${error instanceof Error ? error.message : '未知错误'}`,
      thought: undefined
    }
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messageList.value) {
      messageList.value.scrollTop = messageList.value.scrollHeight
    }
  })
}

// 处理图标上传
const handleIconUpload = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    settingForm.value.icon = e.target?.result as string
  }
  reader.readAsDataURL(file)
  // 返回false阻止默认上传行为
  return false
}

// 处理AI助手头像上传
const handleAssistantAvatarUpload = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    if (!settingForm.value.model_config) {
      settingForm.value.model_config = {}
    }
    settingForm.value.model_config.assistant_avatar = e.target?.result as string
  }
  reader.readAsDataURL(file)
  // 返回false阻止默认上传行为
  return false
}

// 处理语音播放方式变化
const handleTtsTypeChange = () => {
  // 当切换到浏览器播放时，清空语音合成模型选择
  if (settingForm.value.model_config?.tts_type === 'browser') {
    settingForm.value.model_config.tts_model = ''
  }
}

// 调试聊天界面的语音输入处理
const handleDebugVoiceInput = () => {
  // 模拟语音输入功能
  ElMessage.info('开始录音')
  // 这里应该调用浏览器的语音识别API或后端服务
  setTimeout(() => {
    ElMessage.info('录音结束')
    // 模拟语音识别结果
    inputMessage.value = '我有点咳嗽，应该吃什么药？'
  }, 3000)
}

// 初始化
onMounted(() => {
  loadCurrentApplication()
})
</script>

<style scoped>
.setting-container {
  padding: 20px;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-tabs {
  margin-left: 20px;
  flex: 1;
}

.setting-content {
  display: flex;
  gap: 20px;
  flex: 1;
  overflow: hidden;
}

/* 左侧设置面板 */
.setting-panel {
  width: 400px;
  overflow-y: auto;
  padding-right: 10px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.setting-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.save-button {
  margin-top: 10px;
}

/* 右侧聊天调试界面 */
.chat-panel {
  flex: 1;
  overflow: hidden;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 20px;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.message-item {
  display: flex;
  flex-direction: row;
  gap: 10px;
  align-items: flex-start;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  font-size: 14px;
}

.message-content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.message-item.user-message {
  flex-direction: row-reverse;
}

.message-item.assistant-message {
  flex-direction: row;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #909399;
}

.message-role {
  font-weight: 500;
  color: #606266;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  background-color: #f5f7fa;
  position: relative;
  word-wrap: break-word;
}

.user-message .message-content-wrapper {
  align-items: flex-end;
}

.assistant-message .message-content-wrapper {
  align-items: flex-start;
}

.user-message .message-content {
  background-color: #409eff;
  color: white;
  border-bottom-right-radius: 0;
}

.assistant-message .message-content {
  background-color: #f5f7fa;
  color: #303133;
  border-bottom-left-radius: 0;
}

.thinking-message {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #909399;
  font-style: italic;
}

.thinking-icon {
  animation: spin 1s linear infinite;
}

.search-results {
  margin-top: 15px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.results-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-weight: 500;
  color: #606266;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-item {
  padding: 10px;
  background-color: white;
  border-radius: 6px;
  border: 1px solid #ebeef5;
  font-size: 13px;
}

.result-title {
  font-weight: 500;
  margin-bottom: 5px;
  color: #303133;
}

.result-content {
  margin-bottom: 5px;
  color: #606266;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.result-score {
  font-size: 11px;
  color: #909399;
}

/* 输入区域 */
.input-area {
  padding: 10px;
  border-top: 1px solid #ebeef5;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.send-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sending-text {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #909399;
  font-size: 13px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

.send-button {
  min-width: 80px;
}

/* 动画 */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 区域标题样式 */
.section-header {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 10px 0 15px 0;
  padding-left: 5px;
  border-left: 3px solid #409eff;
}

/* 强制样式：开场白示例问题 */
/* 全局样式，确保所有.example-question都应用此样式 */
:root {
  --example-question-bg: #f5f7fa;
  --example-question-color: #606266;
  --example-question-hover-bg: #e6e8eb;
  --example-question-hover-color: #409eff;
}

/* 所有.example-question元素都应用此样式 */
* .example-question {
  background-color: var(--example-question-bg) !important;
  color: var(--example-question-color) !important;
  padding: 4px 12px !important;
  border-radius: 16px !important;
  cursor: pointer !important;
  margin-right: 15px !important;
  margin-bottom: 8px !important;
  display: inline-block !important;
  font-weight: 400 !important;
  font-size: 14px !important;
  transition: all 0.3s !important;
  text-decoration: none !important;
  border: none !important;
  line-height: 1.5 !important;
  vertical-align: middle !important;
}

* .example-question:hover {
  background-color: var(--example-question-hover-bg) !important;
  color: var(--example-question-hover-color) !important;
  text-decoration: none !important;
}

/* 悬停样式 */
* .example-question:hover {
  background-color: #dde0e4 !important;
  color: #409eff !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

/* 覆盖Element Plus的a标签样式 */
* .example-question {
  --el-link-color: var(--example-question-color) !important;
  --el-link-hover-color: var(--example-question-hover-color) !important;
  --el-link-active-color: var(--example-question-hover-color) !important;
  --el-link-font-weight: 400 !important;
  --el-link-decoration: none !important;
  text-decoration: none !important;
}

/* 图标上传样式 */
.icon-upload-section {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.avatar-uploader {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 4px;
  object-fit: cover;
  cursor: pointer;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100px;
  height: 100px;
  line-height: 100px;
  text-align: center;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.avatar-uploader-icon:hover {
  border-color: #409eff;
  color: #409eff;
}

.upload-tips {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

/* 按钮区域样式 */
.button-section {
  margin-top: 10px;
}

/* 关联知识库样式 */
.knowledge-bases {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 5px;
}

.knowledge-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.no-knowledge {
  color: #909399;
  font-style: italic;
  margin-top: 5px;
}

/* 头像设置弹窗样式 */
.avatar-dialog-content {
  text-align: center;
}

.current-avatar, .avatar-upload-section {
  margin-bottom: 20px;
}

.avatar-preview {
  width: 120px;
  height: 120px;
  margin: 10px auto;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #ebeef5;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder-large {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  font-weight: 600;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>