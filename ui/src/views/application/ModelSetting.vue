<template>
  <div class="model-setting-container">
    <div class="header">
      <h2>模型设置</h2>
    </div>
    <div class="model-setting-content">
      <!-- 模型设置面板 -->
      <el-card shadow="hover" class="model-setting-card">
        <el-form :model="modelConfigForm" label-width="120px" size="default">
          <!-- 模型选择 -->
          <div class="section-header">模型选择</div>
          <el-form-item label="模型类型">
            <el-select 
              v-model="modelConfigForm.model_type" 
              placeholder="请选择模型类型"
              style="width: 100%"
              @change="handleModelTypeChange"
            >
              <el-option label="OpenAI" value="openai" />
              <el-option label="Anthropic" value="anthropic" />
              <el-option label="Google" value="google" />
              <el-option label="阿里通义千问" value="tongyi" />
              <el-option label="百度文心一言" value="wenxin" />
              <el-option label="智谱AI" value="zhipu" />
              <el-option label="字节豆包" value="doubao" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="模型名称">
            <el-select 
              v-model="modelConfigForm.model_name" 
              placeholder="请选择模型名称"
              style="width: 100%"
            >
              <el-option 
                v-for="model in availableModels" 
                :key="model.value" 
                :label="model.label" 
                :value="model.value"
              />
            </el-select>
          </el-form-item>
          
          <!-- API配置 -->
          <div class="section-header">API配置</div>
          <el-form-item label="API密钥">
            <el-input 
              v-model="modelConfigForm.api_key" 
              placeholder="请输入API密钥"
              type="password"
              show-password
              maxlength="256"
            />
          </el-form-item>
          
          <el-form-item label="API基础URL">
            <el-input 
              v-model="modelConfigForm.base_url" 
              placeholder="请输入API基础URL（可选，使用默认值请留空）"
              maxlength="256"
            />
          </el-form-item>
          
          <!-- 模型参数配置 -->
          <div class="section-header">模型参数</div>
          <el-form-item label="温度（Temperature）">
            <el-slider
              v-model="modelConfigForm.temperature"
              :min="0"
              :max="2"
              :step="0.1"
              show-input
              :input-size="'small'"
              :format-tooltip="val => val.toFixed(1)"
            />
            <div class="help-text">控制生成文本的随机性，值越大越随机，值越小越确定</div>
          </el-form-item>
          
          <el-form-item label="最大生成 tokens">
            <el-input-number
              v-model="modelConfigForm.max_tokens"
              :min="100"
              :max="32768"
              :step="100"
              placeholder="请输入最大生成 tokens"
              controls-position="right"
              size="large"
            />
            <div class="help-text">控制模型生成的最大文本长度</div>
          </el-form-item>
          
          <el-form-item label="上下文窗口 tokens">
            <el-input-number
              v-model="modelConfigForm.context_window"
              :min="1024"
              :max="200000"
              :step="1024"
              placeholder="请输入上下文窗口大小"
              controls-position="right"
              size="large"
            />
            <div class="help-text">控制模型能处理的最大上下文长度</div>
          </el-form-item>
          
          <el-form-item label="top_p">
            <el-slider
              v-model="modelConfigForm.top_p"
              :min="0"
              :max="1"
              :step="0.05"
              show-input
              :input-size="'small'"
              :format-tooltip="val => val.toFixed(2)"
            />
            <div class="help-text">控制生成时考虑的词的概率范围，值越大考虑的词越多</div>
          </el-form-item>
          
          <el-form-item label="top_k">
            <el-input-number
              v-model="modelConfigForm.top_k"
              :min="1"
              :max="100"
              :step="1"
              placeholder="请输入top_k值"
              controls-position="right"
              size="large"
            />
            <div class="help-text">控制生成时考虑的词的数量，值越大考虑的词越多</div>
          </el-form-item>
          
          <!-- 系统提示词设置 -->
          <div class="section-header">系统提示词</div>
          <el-form-item label="系统角色">
            <el-input
              v-model="modelConfigForm.system_prompt"
              type="textarea"
              :rows="4"
              placeholder="请输入系统角色描述"
              maxlength="2048"
              show-word-limit
            />
            <div class="help-text">系统角色描述将作为角色扮演的提示词融入到传递给模型的prompt中</div>
          </el-form-item>
          
          <!-- 历史记录设置 -->
          <div class="section-header">历史记录</div>
          <el-form-item label="历史聊天记录">
            <el-input-number
              v-model="modelConfigForm.history_count"
              :min="0"
              :max="20"
              :step="1"
              placeholder="请输入历史记录数量"
              controls-position="right"
              size="large"
            />
            <div class="help-text">设置传递给模型的历史聊天记录条数</div>
          </el-form-item>
          
          <!-- 开场白设置 -->
          <div class="section-header">开场白</div>
          <el-form-item label="欢迎语">
            <el-input
              v-model="modelConfigForm.greeting"
              type="textarea"
              :rows="3"
              placeholder="请输入开场白"
              maxlength="512"
              show-word-limit
            />
            <div class="help-text">开场白将显示在对话界面的欢迎消息中，支持可交互的示例问题</div>
          </el-form-item>
          
          <!-- 输出设置 -->
          <div class="section-header">输出设置</div>
          <el-form-item label="输出思考过程">
            <el-switch v-model="modelConfigForm.output_thinking" />
            <div class="help-text">开启后，模型将输出思考过程，增强对话的透明度</div>
          </el-form-item>
          
          <!-- 操作按钮 -->
          <div class="button-section">
            <el-form-item>
              <el-button type="primary" @click="saveModelConfig" class="save-button" size="large" style="width: 100%">保存设置</el-button>
            </el-form-item>
            <el-form-item>
              <el-button @click="resetModelConfig" size="large" style="width: 100%">重置</el-button>
            </el-form-item>
          </div>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { applicationApi, type Application } from '@/api'

// 可用模型列表，根据模型类型动态变化
const availableModels = ref([
  { label: 'gpt-4o', value: 'gpt-4o' },
  { label: 'gpt-4-turbo', value: 'gpt-4-turbo' },
  { label: 'gpt-3.5-turbo', value: 'gpt-3.5-turbo' }
])

// 模型配置表单数据
const modelConfigForm = ref({
  // 模型选择
  model_type: 'openai',
  model_name: 'gpt-4o',
  
  // API配置
  api_key: '',
  base_url: '',
  
  // 模型参数
  temperature: 0.7,
  max_tokens: 4096,
  context_window: 128000,
  top_p: 0.95,
  top_k: 50,
  
  // 系统提示词
  system_prompt: '',
  
  // 历史记录设置
  history_count: 10,
  
  // 开场白
  greeting: '您好，我是智能助手，有什么可以帮助您的？',
  
  // 输出设置
  output_thinking: false
})

// 模型类型变化处理
const handleModelTypeChange = (modelType: string) => {
  // 根据模型类型更新可用模型列表
  switch (modelType) {
    case 'openai':
      availableModels.value = [
        { label: 'gpt-4o', value: 'gpt-4o' },
        { label: 'gpt-4-turbo', value: 'gpt-4-turbo' },
        { label: 'gpt-3.5-turbo', value: 'gpt-3.5-turbo' }
      ]
      break
    case 'anthropic':
      availableModels.value = [
        { label: 'claude-3-opus-20240229', value: 'claude-3-opus-20240229' },
        { label: 'claude-3-sonnet-20240229', value: 'claude-3-sonnet-20240229' },
        { label: 'claude-3-haiku-20240307', value: 'claude-3-haiku-20240307' }
      ]
      break
    case 'google':
      availableModels.value = [
        { label: 'gemini-pro', value: 'gemini-pro' },
        { label: 'gemini-ultra', value: 'gemini-ultra' }
      ]
      break
    case 'tongyi':
      availableModels.value = [
        { label: 'qwen-max', value: 'qwen-max' },
        { label: 'qwen-plus', value: 'qwen-plus' },
        { label: 'qwen-turbo', value: 'qwen-turbo' }
      ]
      break
    case 'wenxin':
      availableModels.value = [
        { label: 'ERNIE-Bot-4', value: 'ERNIE-Bot-4' },
        { label: 'ERNIE-Bot-3.5', value: 'ERNIE-Bot-3.5' }
      ]
      break
    case 'zhipu':
      availableModels.value = [
        { label: 'glm-4', value: 'glm-4' },
        { label: 'glm-3-turbo', value: 'glm-3-turbo' }
      ]
      break
    case 'doubao':
      availableModels.value = [
        { label: '豆包-4', value: 'doubao-4' },
        { label: '豆包-3.5', value: 'doubao-3.5' }
      ]
      break
    default:
      availableModels.value = [
        { label: 'gpt-4o', value: 'gpt-4o' },
        { label: 'gpt-4-turbo', value: 'gpt-4-turbo' },
        { label: 'gpt-3.5-turbo', value: 'gpt-3.5-turbo' }
      ]
  }
  
  // 重置模型名称为第一个可用模型
  modelConfigForm.value.model_name = availableModels.value[0].value
}

// 保存模型配置
const saveModelConfig = async () => {
  try {
    // 加载当前应用
    const applications = await applicationApi.getApplications()
    if (applications.length === 0) {
      ElMessage.error('没有可用的应用')
      return
    }
    
    const app = applications[0]
    
    // 合并模型配置
    const updatedModelConfig = {
      ...app.model_config,
      ...modelConfigForm.value
    }
    
    // 更新应用
    await applicationApi.updateApplication(app.id, {
      ...app,
      model_config: updatedModelConfig
    })
    
    ElMessage.success('模型配置保存成功')
  } catch (error) {
    console.error('保存模型配置失败:', error)
    ElMessage.error('保存模型配置失败')
  }
}

// 重置模型配置
const resetModelConfig = () => {
  loadCurrentModelConfig()
}

// 加载当前模型配置
const loadCurrentModelConfig = async () => {
  try {
    // 加载应用列表
    const applications = await applicationApi.getApplications()
    if (applications.length > 0) {
      const app = applications[0]
      
      // 解析模型配置
      let parsedModelConfig = {}
      if (typeof app.model_config === 'string') {
        parsedModelConfig = JSON.parse(app.model_config)
      } else {
        parsedModelConfig = app.model_config || {}
      }
      
      // 合并到表单
      modelConfigForm.value = {
        // 默认值
        model_type: 'openai',
        model_name: 'gpt-4o',
        api_key: '',
        base_url: '',
        temperature: 0.7,
        max_tokens: 4096,
        context_window: 128000,
        top_p: 0.95,
        top_k: 50,
        system_prompt: '',
        history_count: 10,
        greeting: '您好，我是智能助手，有什么可以帮助您的？',
        output_thinking: false,
        
        // 合并应用的模型配置
        ...parsedModelConfig
      }
      
      // 更新可用模型列表
      handleModelTypeChange(modelConfigForm.value.model_type)
    }
  } catch (error) {
    console.error('加载模型配置失败:', error)
    ElMessage.error('加载模型配置失败')
  }
}

// 初始化
onMounted(() => {
  loadCurrentModelConfig()
})
</script>

<style scoped>
.model-setting-container {
  padding: 20px;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.header {
  margin-bottom: 20px;
}

.model-setting-content {
  flex: 1;
  overflow: hidden;
}

.model-setting-card {
  margin-bottom: 20px;
  overflow-y: auto;
  max-height: calc(100vh - 120px);
}

.section-header {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 10px 0 15px 0;
  padding-left: 5px;
  border-left: 3px solid #409eff;
}

.help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.button-section {
  margin-top: 20px;
}

.save-button {
  margin-bottom: 10px;
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