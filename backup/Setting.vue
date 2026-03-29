<template>
  <div class="application-setting">
    <h2 class="page-title">应用设置</h2>
    
    <el-card style="--el-card-padding: 0">
      <el-row>
        <!-- 左侧设置区域 - 10列 -->
        <el-col :span="10">
          <div class="p-24 mb-16" style="padding-bottom: 0">
            <h4 class="title-decoration-1">信息</h4>
          </div>
          <div class="scrollbar-height-left">
            <el-scrollbar>
              <el-form ref="formRef" :model="formData" label-width="100px" size="default" class="setting-form p-24" style="padding-top: 0">
                <!-- 基本信息 -->
                <el-form-item label="名称" prop="name" required>
                  <el-input 
                    v-model="formData.name" 
                    placeholder="请输入应用名称" 
                    maxlength="64" 
                    show-word-limit 
                  />
                </el-form-item>
                
                <el-form-item label="描述">
                  <el-input
                    v-model="formData.desc"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入应用描述"
                    maxlength="256"
                    show-word-limit
                  />
                </el-form-item>
                
                <h4 class="title-decoration-1 mt-24 mb-16">AI 模型</h4>
                
                <!-- 系统角色 -->
                <el-form-item label="系统角色">
                  <el-input
                    v-model="formData.system_prompt"
                    type="textarea"
                    :rows="4"
                    placeholder="请输入系统角色"
                    maxlength="500"
                    show-word-limit
                  />
                </el-form-item>
                
                <!-- 提示词 (无引用知识库) -->
                <el-form-item label="提示词(无引用知识库)" required>
                  <el-input
                    v-model="formData.prompt_without_knowledge"
                    placeholder="请输入无引用知识库的提示词"
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>
                
                <!-- 历史聊天记录 -->
                <el-form-item label="历史聊天记录">
                  <el-input-number
                    v-model="formData.model_config.history_count"
                    :min="1"
                    :max="20"
                    :step="1"
                    style="width: 120px"
                  />
                </el-form-item>
                
                <!-- 关联知识库 -->
                <el-form-item label="关联知识库">
                  <el-select
                    v-model="formData.knowledge_bases"
                    multiple
                    placeholder="请选择关联知识库"
                    collapse-tags
                    style="width: 100%"
                  >
                    <el-option
                      v-for="kb in knowledgeBases"
                      :key="kb.id"
                      :label="kb.name"
                      :value="kb.id"
                    />
                  </el-select>
                  <div class="knowledge-tip">关联的知识库展示在这里</div>
                </el-form-item>
                
                <!-- 提示词 (引用知识库) -->
                <el-form-item label="提示词(引用知识库)" required>
                  <el-input
                    v-model="formData.prompt_with_knowledge"
                    type="textarea"
                    :rows="4"
                    placeholder="请输入引用知识库的提示词"
                    maxlength="300"
                    show-word-limit
                  />
                </el-form-item>
                
                <!-- 开场白 -->
                <el-form-item label="开场白">
                  <el-input
                    v-model="formData.model_config.greeting"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入开场白"
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>
                
                <!-- 知识库检索设置 -->
                <h4 class="title-decoration-1 mt-24 mb-16">知识库检索设置</h4>
                
                <el-card shadow="never" class="card-never mb-16" style="--el-card-padding: 12px">
                  <!-- 检索模式 -->
                  <el-form-item label="检索模式">
                    <el-select v-model="formData.knowledge_setting.search_mode" style="width: 100%">
                      <el-option label="向量检索" value="embedding" />
                      <el-option label="关键词检索" value="keyword" />
                      <el-option label="混合检索" value="hybrid" />
                    </el-select>
                  </el-form-item>
                  
                  <!-- 相似度高于 -->
                  <el-form-item label="相似度高于">
                    <el-input-number
                      v-model="formData.knowledge_setting.similarity"
                      :min="0"
                      :max="1"
                      :step="0.001"
                      :precision="3"
                      style="width: 100%"
                    />
                  </el-form-item>
                  
                  <!-- 引用分段数 TOP -->
                  <el-form-item label="引用分段数 TOP">
                    <el-input-number
                      v-model="formData.knowledge_setting.top_n"
                      :min="1"
                      :max="20"
                      :step="1"
                      style="width: 100%"
                    />
                  </el-form-item>
                  
                  <!-- 最多引用字符数 -->
                  <el-form-item label="最多引用字符数">
                    <el-input-number
                      v-model="formData.knowledge_setting.max_paragraph_char_number"
                      :min="1000"
                      :max="20000"
                      :step="500"
                      style="width: 100%"
                    />
                  </el-form-item>
                  
                  <!-- 无引用知识库分段时 -->
                  <el-form-item label="无引用知识库分段时">
                    <el-select v-model="formData.knowledge_setting.no_references_setting.status" style="width: 100%">
                      <el-option label="直接回答" value="direct_answer" />
                      <el-option label="AI提问优化" value="ai_questioning" />
                    </el-select>
                  </el-form-item>
                  
                  <!-- 问题优化 -->
                  <el-form-item label="问题优化">
                    <el-switch v-model="formData.problem_optimization" />
                  </el-form-item>
                </el-card>
                
                <!-- 功能开关 -->
                <h4 class="title-decoration-1 mt-24 mb-16">功能设置</h4>
                
                <el-form-item label="输出思考">
                  <el-switch v-model="formData.model_config.output_thinking" />
                </el-form-item>
                
                <el-form-item label="语音输入" required>
                  <el-switch v-model="formData.model_config.voice_input" />
                </el-form-item>
                
                <el-form-item label="语音播放" required>
                  <el-switch v-model="formData.model_config.voice_output" />
                </el-form-item>
                
                <div class="form-actions mt-24">
                  <el-button @click="handleCancel" size="default">取消</el-button>
                  <el-button type="primary" @click="handleSave" size="default" :loading="loading">保存设置</el-button>
                </div>
              </el-form>
            </el-scrollbar>
          </div>
        </el-col>
        
        <!-- 右侧预览区域 - 14列 -->
        <el-col :span="14" class="p-24 border-l">
          <h4 class="title-decoration-1 mb-16">调试预览</h4>
          <div class="dialog-bg">
            <div class="scrollbar-height">
              <div class="preview-content">
                <div class="preview-title">{{ formData.name || '中医智能问诊系统' }}</div>
                
                <div class="preview-chat">
                  <div class="chat-message bot-message">
                    <div class="message-content">
                      {{ formData.model_config.greeting || '您好，我是江小智——中医智能问诊小助手，您可以向我提出问题。\n\n- 主要功能有什么？\n- 怎样预防传染病？\n- 推荐用药' }}
                    </div>
                  </div>
                  
                  <div class="chat-input-area">
                    <el-input
                      placeholder="请输入问题"
                      v-model="previewInput"
                      @keyup.enter="sendPreviewMessage"
                      style="width: 100%"
                    >
                      <template #append>
                        <el-button type="primary" @click="sendPreviewMessage">发送</el-button>
                      </template>
                    </el-input>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { applicationApi, knowledgeApi, toolsApi } from '@/api'

const formRef = ref<InstanceType<typeof ElForm>>()
const loading = ref(false)
const previewInput = ref('')

// 表单数据
const formData = reactive({
  id: '',
  name: '中医智能问诊系统',
  desc: '由江西中医药大学研发的中医智能诊疗大模型，致力于将传统中医理论与现代科技相结合，为医疗提供智能化支持。拥有已确诊疾病的临床诊疗模块、基于症状和体征的临床诊疗模块、中医养生调理模块。通过输入患者的症状、体征或已确诊的疾病信息，能够输出精准的中医辨证、治法、药方等内容。',
  icon: '',
  user_id: '',
  work_flow: {},
  model_config: {
    greeting: '您好，我是江小智——中医智能问诊小助手，您可以向我提出问题。\n\n- 主要功能有什么？\n- 怎样预防传染病？\n- 推荐用药',
    output_thinking: false,
    voice_input: false,
    voice_output: false,
    tts_type: 'browser',
    stt_model: 'default',
    tts_model: 'default',
    history_count: 1
  },
  system_prompt: '你是由江西中医药大学研发的中医智能诊疗大模型，致力于将传统中医理论与现代科技相结合，为医疗提供智能化支持。拥有已确诊疾病的临床诊疗模块、基于症状和体征的临床诊疗模块、中医养生调理模块。通过输入患者的症状、体征或已确诊的疾病信息，能够输出精准的中医辨证、治法、药方等内容。',
  prompt_without_knowledge: '{question}',
  prompt_with_knowledge: '已知信息：{data}\n用户问题：{question}\n回答要求：\n - 请使用中文回答用户问题',
  knowledge_bases: [] as string[],
  tools: [] as string[],
  prompt_template: '',
  prompt_template_type: 'DEFAULT',
  similarity_threshold: 0.5,
  top_k: 5,
  is_active: true,
  // 知识库检索设置
  knowledge_setting: {
    top_n: 3,
    similarity: 0.6,
    max_paragraph_char_number: 5000,
    search_mode: 'embedding',
    no_references_setting: {
      status: 'ai_questioning',
      value: '{question}',
    },
  },
  problem_optimization: false,
  problem_optimization_prompt: '请优化以下问题：{question}'
})

// 关联数据
const knowledgeBases = ref([])
const tools = ref([])

// 加载关联数据
const loadAssociatedData = async () => {
  try {
    // 加载知识库
    const kbs = await knowledgeApi.getKnowledgeBases()
    knowledgeBases.value = kbs
    
    // 加载工具
    const toolsList = await toolsApi.getTools()
    tools.value = toolsList
  } catch (error) {
    ElMessage.error('加载关联数据失败')
    console.error('Failed to load associated data:', error)
  }
}

// 加载应用配置
const loadApplicationConfig = async () => {
  try {
    loading.value = true
    const applications = await applicationApi.getApplications()
    if (applications.length > 0) {
      const app = applications[0]
      // 更新表单数据
      Object.assign(formData, app)
      
      // 确保prompt字段存在
      if (!formData.prompt_without_knowledge) {
        formData.prompt_without_knowledge = '{question}'
      }
      if (!formData.prompt_with_knowledge) {
        formData.prompt_with_knowledge = '已知信息：{data}\n用户问题：{question}\n回答要求：\n - 请使用中文回答用户问题'
      }
    }
  } catch (error) {
    ElMessage.error('加载应用配置失败')
    console.error('Failed to load application config:', error)
  } finally {
    loading.value = false
  }
}

// 保存设置
const handleSave = async () => {
  if (!formRef.value) return
  
  try {
    loading.value = true
    
    if (formData.id) {
      // 更新应用
      await applicationApi.updateApplication(formData.id, formData)
      ElMessage.success('保存成功')
    } else {
      // 创建应用
      await applicationApi.createApplication(formData)
      ElMessage.success('创建成功')
    }
  } catch (error) {
    ElMessage.error('保存失败')
    console.error('Failed to save application:', error)
  } finally {
    loading.value = false
  }
}

// 取消操作
const handleCancel = () => {
  ElMessage.info('操作已取消')
}

// 发送预览消息
const sendPreviewMessage = () => {
  if (!previewInput.value) return
  // 这里可以添加预览消息的处理逻辑
  ElMessage.success('预览消息已发送')
  previewInput.value = ''
}

// 初始化
onMounted(async () => {
  await Promise.all([
    loadAssociatedData(),
    loadApplicationConfig()
  ])
})
</script>

<style scoped>
.application-setting {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-title {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

/* 标题装饰样式 */
.title-decoration-1 {
  position: relative;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  padding-left: 12px;
  line-height: 1;
}

.title-decoration-1::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  background-color: #409eff;
  border-radius: 2px;
}

/* 对话框背景样式 */
.dialog-bg {
  border-radius: 8px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  overflow: hidden;
  box-sizing: border-box;
}

/* 滚动区域高度样式 */
.scrollbar-height-left {
  height: calc(100vh - 180px);
}

.scrollbar-height {
  padding-top: 16px;
  height: calc(100vh - 220px);
}

/* 设置表单样式 */
.setting-form {
  flex: 1;
}

/* 预览内容样式 */
.preview-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.preview-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  text-align: center;
}

.preview-chat {
  flex: 1;
  background-color: #fafafa;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chat-message {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
}

.bot-message {
  align-self: flex-start;
  background-color: #e6f7ff;
  color: #000;
}

.user-message {
  align-self: flex-end;
  background-color: #f0f0f0;
  color: #000;
}

.message-content {
  line-height: 1.5;
}

.chat-input-area {
  margin-top: auto;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 0;
  background-color: transparent;
  margin-top: 0;
  border-top: none;
}

/* 紧凑的表单样式 */
.setting-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.setting-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

/* 卡片样式 */
.card-never {
  border: 1px solid #ebeef5;
  background-color: #fff;
}

.knowledge-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 左侧边框样式 */
.border-l {
  border-left: 1px solid #ebeef5;
}

/* 内边距简写 */
.p-24 {
  padding: 24px;
}

.mt-24 {
  margin-top: 24px;
}

.mb-16 {
  margin-bottom: 16px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .scrollbar-height-left,
  .scrollbar-height {
    height: calc(100vh - 200px);
  }
}

@media (max-width: 992px) {
  .scrollbar-height-left,
  .scrollbar-height {
    height: auto;
    max-height: 500px;
  }
}

@media (max-width: 768px) {
  .application-setting {
    padding: 10px;
  }
  
  .p-24 {
    padding: 16px;
  }
  
  .setting-form :deep(.el-form-item__label) {
    width: 80px;
  }
}
</style>