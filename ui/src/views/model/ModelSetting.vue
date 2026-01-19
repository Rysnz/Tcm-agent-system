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
          @change="handleModelNameChange"
        >
          <el-option 
            v-for="model in availableModels" 
            :key="model.value" 
            :label="model.label" 
            :value="model.value" 
          />
        </el-select>
        </el-form-item>
        
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { Plus, More, Edit, Delete } from '@element-plus/icons-vue'
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
    availableModels.value = await modelApi.getModelList(modelFormData.provider, modelFormData.model_type)
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
  modelFormData.credential = {}
  // 重新加载可用模型
  loadAvailableModels()
}

// 处理提供商变化
const handleProviderChange = () => {
  modelFormData.model_name = ''
  availableModels.value = []
  modelParamsForm.value = []
  // 重置凭证
  modelFormData.credential = {}
  // 重新加载可用模型
  loadAvailableModels()
}

// 处理模型名称变化
const handleModelNameChange = () => {
  modelParamsForm.value = []
  // 重置凭证
  modelFormData.credential = {}
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
    credential: {},
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
  modelFormData.credential = { ...model.credential }
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
        // 转换模型数据为API所需格式
        const modelData: any = {
          name: modelFormData.name,
          model_type: modelFormData.model_type,
          provider: modelFormData.provider,
          model_name: modelFormData.model_name,
          credential: modelFormData.credential,
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
        ElMessage.error('保存模型失败')
        console.error('Failed to save model:', error)
      }
    }
  })
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
</style>
