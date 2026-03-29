<template>
  <div class="model-setting">
    <h2 class="page-title">模型设置</h2>
    
    <el-card class="model-setting-card">
      <el-tabs v-model="activeTab" type="card">
        <!-- 模型列表 -->
        <el-tab-pane label="模型列表" name="model-list">
          <div class="model-list-container">
            <el-button type="primary" @click="openCreateModelDialog" class="mb-16">
              <el-icon><Plus /></el-icon>
              添加模型
            </el-button>
            
            <el-row :gutter="16">
              <el-col
                v-for="model in modelList"
                :key="model.id"
                :xs="24"
                :sm="12"
                :md="8"
                :lg="6"
                :xl="6"
              >
                <el-card class="model-card" shadow="hover">
                  <template #header>
                    <div class="model-card-header">
                      <div class="model-card-title">{{ model.name }}</div>
                      <el-dropdown trigger="click">
                        <el-button text size="small">
                          <el-icon><More /></el-icon>
                        </el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="editModel(model)">
                              <el-icon><Edit /></el-icon>
                              编辑
                            </el-dropdown-item>
                            <el-dropdown-item @click="deleteModel(model)" divided>
                              <el-icon><Delete /></el-icon>
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </template>
                  
                  <div class="model-info">
                    <div class="info-item">
                      <span class="info-label">模型类型：</span>
                      <span class="info-value">{{ model.model_type }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">提供商：</span>
                      <span class="info-value">{{ model.provider }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">模型标识：</span>
                      <span class="info-value">{{ model.model_name }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">状态：</span>
                      <el-switch 
                        v-model="model.is_active" 
                        @change="toggleModelStatus(model)"
                        size="small"
                      />
                    </div>
                  </div>
                  
                  <div class="model-actions">
                    <el-button type="primary" link size="small" @click="editModel(model)">
                      参数设置
                    </el-button>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>
        <!-- Agent配置 -->
        <el-tab-pane label="Agent配置" name="agent-config">
          <div class="agent-config-container">
            <el-alert
              type="info"
              :closable="false"
              title="Agent模型分配"
              description="为每个智能体独立指定调用的模型。未指定时，系统将使用全局默认模型。配置保存在本地浏览器中。"
              class="mb-16"
            />
            <el-table :data="agentConfigList" border>
              <el-table-column prop="label" label="智能体" width="180" />
              <el-table-column prop="desc" label="职责说明" />
              <el-table-column label="分配的模型" width="260">
                <template #default="{ row }">
                  <el-select
                    v-model="agentModelMap[row.name]"
                    placeholder="使用全局默认"
                    clearable
                    style="width: 100%;"
                    @change="saveAgentConfig"
                  >
                    <el-option
                      v-for="m in modelList"
                      :key="m.id"
                      :label="m.name"
                      :value="m.id"
                    />
                  </el-select>
                  <div class="custom-model-tip">
                    若预设模型缺失，请先在“模型列表”中添加自定义模型。
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <div class="agent-config-tip">
              <el-icon><InfoFilled /></el-icon>
              Agent模型配置保存到后端后立即生效；未指定的Agent将使用系统默认激活模型。
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    
    <!-- 模型创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
    >
      <el-form ref="modelFormRef" :model="modelFormData" label-width="120px">
        <el-form-item label="模型名称" prop="name" required>
          <el-input v-model="modelFormData.name" placeholder="请输入模型名称" />
        </el-form-item>

        <el-form-item label="Base URL" required>
          <el-input v-model="modelFormData.credential.base_url" placeholder="例如：https://api.openai.com/v1" />
          <div class="custom-model-tip" v-if="modelFormData.provider === 'lmstudio'">
            LM Studio 推荐：`http://127.0.0.1:1234/v1`（不要使用 `/api/v1` 路径）。
          </div>
        </el-form-item>

        <el-form-item :label="isApiKeyOptional ? 'API Key（可选）' : 'API Key'" :required="!isApiKeyOptional">
          <el-input v-model="modelFormData.credential.api_key" type="password" show-password placeholder="请输入API Key（本提供商可留空）" />
        </el-form-item>
        
        <el-form-item label="模型类型" prop="model_type" required>
          <el-select 
            v-model="modelFormData.model_type" 
            placeholder="请选择模型类型"
            @change="handleModelTypeChange"
          >
            <el-option 
              v-for="type in modelTypes" 
              :key="type.value" 
              :label="type.key" 
              :value="type.value" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="提供商" prop="provider" required>
          <el-select 
            v-model="modelFormData.provider" 
            placeholder="请选择提供商"
            @change="handleProviderChange"
          >
            <el-option 
              v-for="provider in providers" 
              :key="provider.provider" 
              :label="provider.name" 
              :value="provider.provider" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型" prop="model_name" required>
          <el-select 
          v-model="modelFormData.model_name" 
          placeholder="请选择模型"
          filterable
          allow-create
          default-first-option
          @change="handleModelNameChange"
        >
          <el-option 
            v-for="model in availableModels" 
            :key="model.value" 
            :label="model.label" 
            :value="model.value" 
          />
        </el-select>
        <div class="custom-model-tip">如果下拉中没有目标模型，可直接输入模型标识并保存。</div>
        </el-form-item>

        <el-form-item>
          <el-button size="small" @click="testCredential">测试连接</el-button>
        </el-form-item>

        <el-alert
          v-if="modelFormData.provider === 'lmstudio'"
          type="info"
          :closable="false"
          title="LM Studio建议：请在LM Studio中先加载模型并预热；本系统默认将max_tokens限制为128以降低KV Cache压力。"
        />
        
        <!-- 动态生成的模型参数表单 -->
        <div v-if="modelParamsForm.length > 0" class="dynamic-form-section">
          <el-divider content-position="left">模型参数</el-divider>
          <el-form-item 
            v-for="field in modelParamsForm" 
            :key="field.key" 
            :label="field.label"
            :prop="`credential.${field.key}`"
            :required="field.required"
          >
            <!-- 文本输入框 -->
            <el-input 
              v-if="field.type === 'text'" 
              v-model="modelFormData.credential[field.key]" 
              :placeholder="field.placeholder"
              :show-password="field.key.toLowerCase().includes('password') || field.key.toLowerCase().includes('api_key')"
            />
            
            <!-- 数字输入框 -->
            <el-input-number 
              v-else-if="field.type === 'number'" 
              v-model="modelFormData.credential[field.key]" 
              :min="field.min" 
              :max="field.max"
              :step="field.step || 0.1"
            />
            
            <!-- 滑块 -->
            <div v-else-if="field.type === 'slider'" class="slider-container">
              <el-slider 
                v-model="modelFormData.credential[field.key]" 
                :min="field.min" 
                :max="field.max" 
                :step="field.step || 0.1"
              />
              <span class="slider-value">{{ modelFormData.credential[field.key] }}</span>
            </div>
          </el-form-item>
        </div>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveModel">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { Plus, More, Edit, Delete, InfoFilled } from '@element-plus/icons-vue'
import { modelApi, type ModelConfig } from '@/api'

// 定义类型
interface Model {
  id: string
  name: string
  model_type: string
  provider: string
  model_name: string
  credential: Record<string, any>
  is_active: boolean
  params?: Record<string, any>
}

// 提供商信息类型
interface Provider {
  provider: string
  name: string
  icon: string
}

// 模型信息类型
interface ModelInfo {
  name: string
  desc: string
  model_type: string
}

// 模型列表项类型
interface ModelListItem {
  value: string
  label: string
}

// 参数表单字段类型
interface ParamField {
  key: string
  label: string
  type: 'text' | 'number' | 'slider' | 'select' | 'boolean'
  value: any
  required: boolean
  placeholder?: string
  min?: number
  max?: number
  step?: number
  options?: Array<{label: string; value: any}>
}

const PROVIDER_PRESET_MODELS: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini', 'o3-mini'],
  anthropic: ['claude-3-7-sonnet-latest', 'claude-3-5-sonnet-latest', 'claude-3-5-haiku-latest'],
  gemini: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'],
  deepseek: ['deepseek-chat', 'deepseek-reasoner'],
  qwen: ['qwen-max', 'qwen-plus', 'qwen-turbo'],
  kimi: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
  ollama: ['qwen2.5:7b', 'llama3.1:8b', 'deepseek-r1:7b'],
  zhipu: ['glm-4-plus', 'glm-4-air', 'glm-4-flash'],
  siliconflow: ['Qwen/Qwen2.5-72B-Instruct', 'deepseek-ai/DeepSeek-R1', 'THUDM/glm-4-9b-chat'],
  azure_openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1'],
  lmstudio: ['qwen2.5-7b-instruct', 'llama-3.1-8b-instruct', 'mistral-7b-instruct'],
}

const PROVIDER_BASE_URL: Record<string, string> = {
  openai: 'https://api.openai.com/v1',
  deepseek: 'https://api.deepseek.com/v1',
  qwen: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  kimi: 'https://api.moonshot.cn/v1',
  zhipu: 'https://open.bigmodel.cn/api/paas/v4',
  siliconflow: 'https://api.siliconflow.cn/v1',
  ollama: 'http://localhost:11434',
  vllm: 'http://localhost:8000/v1',
  xorbits: 'http://localhost:9997/v1',
  lmstudio: 'http://localhost:1234/v1',
}

const NO_API_KEY_PROVIDERS = ['ollama', 'vllm', 'xorbits', 'lmstudio']
const isApiKeyOptional = computed(() => NO_API_KEY_PROVIDERS.includes(modelFormData.provider))

const LMSTUDIO_SAFE_DEFAULTS = {
  timeout: 60,
  max_tokens: 128,
}

const agentConfigList = [
  { name: 'IntakeAgent',          label: '接诊分诊 Agent',   desc: '收集主诉、病程、伴随症状及既往史' },
  { name: 'InquiryAgent',         label: '追问引导 Agent',   desc: '按"十问"策略动态追问以补全信息' },
  { name: 'ObservationAgent',     label: '望诊融合 Agent',   desc: '分析舌象/面色图片，提取视觉诊断特征' },
  { name: 'SyndromeAgent',        label: '辨证分型 Agent',   desc: '综合症状输出候选证型与置信度' },
  { name: 'RecommendationAgent',  label: '调理建议 Agent',   desc: '生成饮食/作息/情志/穴位等个性化建议' },
  { name: 'SafetyGuardAgent',     label: '安全审查 Agent',   desc: '识别高危症状并拦截不当建议' },
  { name: 'ReportAgent',          label: '报告生成 Agent',   desc: '汇总生成结构化问诊报告' },
]

const agentModelMap = reactive<Record<string, string>>({})

const loadAgentConfig = () => {
  modelApi.getAgentConfig().then((rows) => {
    Object.keys(agentModelMap).forEach((k) => delete agentModelMap[k])
    rows.forEach((row) => {
      if (row.model) {
        agentModelMap[row.agent_name] = row.model
      }
    })
  }).catch(() => {
    ElMessage.error('加载Agent配置失败')
  })
}

const saveAgentConfig = () => {
  const payload = agentConfigList.map((agent) => ({
    agent_name: agent.name,
    model: agentModelMap[agent.name] || null
  }))
  modelApi.saveAgentConfig(payload).then(() => {
    ElMessage.success('Agent配置已保存并生效')
  }).catch(() => {
    ElMessage.error('保存Agent配置失败')
  })
}

// 页面状态
const activeTab = ref('model-list')
const modelList = ref<Model[]>([])
const dialogVisible = ref(false)
const dialogTitle = ref('添加模型')

// 表单引用
const modelFormRef = ref<InstanceType<typeof ElForm>>()

// 提供商、模型类型、可用模型数据
const providers = ref<Provider[]>([])
const modelTypes = ref<Array<{key: string; value: string}>>([])
// 将availableModels的类型从ModelInfo[]改为ModelListItem[]
const availableModels = ref<ModelListItem[]>([])
const modelParamsForm = ref<ParamField[]>([])

// 加载状态
const loadingProviders = ref(false)
const loadingModelTypes = ref(false)
const loadingModels = ref(false)
const loadingParamsForm = ref(false)

// 模型表单数据
const modelFormData = reactive<Model>({
  id: '',
  name: '',
  model_type: 'LLM',
  provider: '',
  model_name: '',
  credential: {},
  is_active: true
})



// 加载提供商列表
const loadProviders = async () => {
  try {
    loadingProviders.value = true
    providers.value = await modelApi.getProviders()
  } catch (error) {
    ElMessage.error('加载提供商列表失败')
    console.error('Failed to load providers:', error)
  } finally {
    loadingProviders.value = false
  }
}

// 加载模型类型列表
const loadModelTypes = async () => {
  try {
    loadingModelTypes.value = true
    modelTypes.value = await modelApi.getModelTypes()
  } catch (error) {
    ElMessage.error('加载模型类型列表失败')
    console.error('Failed to load model types:', error)
  } finally {
    loadingModelTypes.value = false
  }
}

// 加载可用模型列表
const loadAvailableModels = async () => {
  if (!modelFormData.provider || !modelFormData.model_type) return
  
  try {
    loadingModels.value = true
    const baseUrl = modelFormData.credential?.base_url
    const serverModels = await modelApi.getModelList(modelFormData.provider, modelFormData.model_type, baseUrl)
    const preset = (PROVIDER_PRESET_MODELS[modelFormData.provider] || []).map((v) => ({ value: v, label: v }))
    const mergedMap = new Map<string, ModelListItem>()
    ;[...serverModels, ...preset].forEach((item) => {
      if (item?.value) {
        mergedMap.set(item.value, item)
      }
    })
    availableModels.value = Array.from(mergedMap.values())
  } catch (error) {
    ElMessage.error('加载可用模型列表失败')
    console.error('Failed to load available models:', error)
  } finally {
    loadingModels.value = false
  }
}

// 加载模型参数表单
const loadModelParamsForm = async () => {
  if (!modelFormData.provider || !modelFormData.model_name) return
  
  try {
    loadingParamsForm.value = true
    const formConfig = await modelApi.getModelParamsForm(modelFormData.provider, modelFormData.model_name)
    modelParamsForm.value = formConfig
    
    // 初始化表单数据
    formConfig.forEach(field => {
      if (!(field.key in modelFormData.credential)) {
        modelFormData.credential[field.key] = field.value || ''
      }
    })
  } catch (error) {
    ElMessage.error('加载模型参数表单失败')
    console.error('Failed to load model params form:', error)
  } finally {
    loadingParamsForm.value = false
  }
}

// 处理模型类型变化
const handleModelTypeChange = () => {
  modelFormData.model_name = ''
  availableModels.value = []
  modelParamsForm.value = []
  // 重置凭证
  modelFormData.credential = {
    base_url: modelFormData.credential?.base_url || PROVIDER_BASE_URL[modelFormData.provider] || '',
    api_key: modelFormData.credential?.api_key || ''
  }
  // 重新加载可用模型
  loadAvailableModels()
}

// 处理提供商变化
const handleProviderChange = () => {
  modelFormData.model_name = ''
  availableModels.value = []
  modelParamsForm.value = []
  // 重置凭证
  modelFormData.credential = {
    base_url: PROVIDER_BASE_URL[modelFormData.provider] || '',
    api_key: ''
  }
  // 重新加载可用模型
  loadAvailableModels()
}

// 处理模型名称变化
const handleModelNameChange = () => {
  modelParamsForm.value = []
  // 重置凭证
  const keep = {
    base_url: modelFormData.credential?.base_url || '',
    api_key: modelFormData.credential?.api_key || ''
  }
  modelFormData.credential = keep
  // 加载模型参数表单
  loadModelParamsForm()
}

// 加载模型列表
const loadModelList = async () => {
  try {
    modelList.value = await modelApi.getModels()
  } catch (error) {
    ElMessage.error('加载模型列表失败')
    console.error('Failed to load model list:', error)
  }
}

// 打开创建模型对话框
const openCreateModelDialog = () => {
  // 重置表单
  Object.assign(modelFormData, {
    id: '',
    name: '',
    model_type: 'LLM',
    provider: '',
    model_name: '',
    credential: {
      base_url: '',
      api_key: ''
    },
    is_active: true
  })
  
  // 重置动态数据
  availableModels.value = []
  modelParamsForm.value = []
  
  // 确保加载了提供商和模型类型
  if (providers.value.length === 0) {
    loadProviders()
  }
  if (modelTypes.value.length === 0) {
    loadModelTypes()
  }
  
  dialogTitle.value = '添加模型'
  dialogVisible.value = true
}

// 编辑模型
const editModel = (model: Model) => {
  // 复制数据到表单
  modelFormData.id = model.id
  modelFormData.name = model.name
  modelFormData.model_type = model.model_type
  modelFormData.provider = model.provider
  modelFormData.model_name = model.model_name
  modelFormData.credential = { ...model.credential, ...(model.params || {}) }
  if (!modelFormData.credential.base_url) {
    modelFormData.credential.base_url = PROVIDER_BASE_URL[model.provider] || ''
  }
  if (!modelFormData.credential.api_key) {
    modelFormData.credential.api_key = ''
  }
  modelFormData.is_active = model.is_active
  
  // 确保加载了提供商和模型类型
  if (providers.value.length === 0) {
    loadProviders()
  }
  if (modelTypes.value.length === 0) {
    loadModelTypes()
  }
  
  // 加载可用模型和参数表单
  loadAvailableModels().then(() => {
    loadModelParamsForm()
  })
  
  dialogTitle.value = '编辑模型'
  dialogVisible.value = true
}

// 保存模型
const saveModel = async () => {
  if (!modelFormRef.value) return
  
  await modelFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (modelFormData.provider === 'lmstudio') {
          modelFormData.credential.base_url = (modelFormData.credential.base_url || '')
            .replace('/api/v1/', '/v1/')
            .replace('/api/v1', '/v1')
        }

        if (!modelFormData.credential?.base_url) {
          ElMessage.warning('请先填写Base URL')
          return
        }
        if (!isApiKeyOptional.value && !modelFormData.credential?.api_key) {
          ElMessage.warning('请先填写API Key')
          return
        }

        const params: Record<string, any> = {}
        Object.entries(modelFormData.credential || {}).forEach(([key, value]) => {
          if (key !== 'api_key' && key !== 'base_url') {
            params[key] = value
          }
        })

        if (modelFormData.provider === 'lmstudio') {
          if (!params.timeout) params.timeout = LMSTUDIO_SAFE_DEFAULTS.timeout
          if (!params.max_tokens) params.max_tokens = LMSTUDIO_SAFE_DEFAULTS.max_tokens
        }

        // 转换模型数据为API所需格式
        const modelData: any = {
          name: modelFormData.name,
          model_type: modelFormData.model_type,
          provider: modelFormData.provider,
          model_name: modelFormData.model_name,
          credential: {
            api_key: modelFormData.credential.api_key,
            base_url: modelFormData.credential.base_url,
            model: modelFormData.model_name,
          },
          params,
          is_active: modelFormData.is_active
        }
        
        if (modelFormData.id) {
          // 更新模型
          modelData.id = modelFormData.id
          await modelApi.updateModel(modelData as ModelConfig)
          ElMessage.success('模型更新成功')
        } else {
          // 创建模型
          await modelApi.createModel(modelData as Partial<ModelConfig>)
          ElMessage.success('模型创建成功')
        }
        
        dialogVisible.value = false
        loadModelList()
      } catch (error) {
        ElMessage.error('保存模型失败：' + (((error as any)?.response?.data?.error) || ((error as any)?.response?.data?.detail) || '请检查参数'))
        console.error('Failed to save model:', error)
      }
    }
  })
}

const testCredential = async () => {
  if (!modelFormData.provider || !modelFormData.model_name) {
    ElMessage.warning('请先选择提供商和模型')
    return
  }
  if (!modelFormData.credential?.base_url) {
    ElMessage.warning('请先填写Base URL')
    return
  }
  if (!isApiKeyOptional.value && !modelFormData.credential?.api_key) {
    ElMessage.warning('请先填写API Key')
    return
  }
  if (modelFormData.provider === 'lmstudio') {
    modelFormData.credential.base_url = (modelFormData.credential.base_url || '')
      .replace('/api/v1/', '/v1/')
      .replace('/api/v1', '/v1')
  }

  const modelName = (modelFormData.model_name || '').trim()
  if (!modelName) {
    ElMessage.warning('模型名称不能为空，请先选择或输入模型名称')
    return
  }

  const res = await modelApi.validateCredential(
    modelFormData.provider,
    modelFormData.model_type,
    modelName,
    {
      api_key: modelFormData.credential.api_key,
      base_url: modelFormData.credential.base_url,
      model: modelName,
    }
  )
  if (res?.is_valid) {
    ElMessage.success('连接测试通过')
  } else {
    ElMessage.error('连接测试失败：' + (res?.error || '请确认LM Studio本地服务已启动且模型已加载'))
  }
}

// 删除模型
const deleteModel = (model: Model) => {
  ElMessageBox.confirm(
    `确定要删除模型 "${model.name}" 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await modelApi.deleteModel(model.id)
      ElMessage.success('模型删除成功')
      loadModelList()
    } catch (error) {
      ElMessage.error('删除模型失败')
      console.error('Failed to delete model:', error)
    }
  }).catch(() => {
    // 取消删除
  })
}



// 切换模型状态
const toggleModelStatus = async (model: Model) => {
  try {
    // 先更新模型对象
    const updatedModel = { ...model, is_active: model.is_active };
    await modelApi.updateModel(updatedModel as ModelConfig);
    ElMessage.success('模型状态更新成功')
  } catch (error) {
    model.is_active = !model.is_active // 恢复原状态
    ElMessage.error('模型状态更新失败')
    console.error('Failed to toggle model status:', error)
  }
}

// 初始化
onMounted(() => {
  loadModelList()
  loadProviders()
  loadModelTypes()
  loadAgentConfig()
})
</script>

<style scoped>
.model-setting {
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

.model-setting-card {
  background-color: #fff;
}

.model-list-container {
  padding: 20px;
}

.model-card {
  margin-bottom: 16px;
}

.model-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.model-info {
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-label {
  color: #606266;
}

.info-value {
  color: #303133;
  font-weight: 500;
}

.model-actions {
  display: flex;
  justify-content: flex-end;
}

.param-setting-container {
  padding: 20px;
}

.slider-value {
  margin-left: 10px;
  font-size: 14px;
  color: #606266;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

/* 动态表单样式 */
.dynamic-form-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.slider-value {
  min-width: 60px;
  text-align: left;
  font-size: 14px;
  color: #606266;
}

.agent-config-container {
  padding: 20px;
}

.agent-config-tip {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 16px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}

.mb-16 { margin-bottom: 16px; }

.custom-model-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #7b8f84;
}
</style>
