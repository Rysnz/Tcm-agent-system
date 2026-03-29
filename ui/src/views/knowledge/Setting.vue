<template>
  <div class="knowledge-setting">
    <h2>知识库设置</h2>
    <el-form :model="formData" label-width="150px" @submit.prevent="saveSettings">
      <!-- 基本信息 -->
      <el-card shadow="hover" class="setting-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>
        <el-form-item label="知识库名称">
          <el-input v-model="formData.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="formData.desc"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
      </el-card>

      <!-- 检索设置 -->
      <el-card shadow="hover" class="setting-card mt-20">
        <template #header>
          <div class="card-header">
            <span>检索设置</span>
          </div>
        </template>
        <el-form-item label="嵌入模型">
          <el-select v-model="formData.embedding_model" placeholder="请选择嵌入模型">
            <el-option label="text2vec-base-Chinese (推荐)" value="text2vec-base-Chinese" />
            <el-option label="BAAI/bge-large-zh-v1.5" value="BAAI/bge-large-zh-v1.5" />
            <el-option label="BAAI/bge-small-zh-v1.5" value="BAAI/bge-small-zh-v1.5" />
            <el-option label="m3e-base" value="m3e-base" />
            <el-option label="m3e-small" value="m3e-small" />
          </el-select>
        </el-form-item>
        <el-form-item label="向量维度" help="根据选择的嵌入模型自动设置，无需手动修改">
          <el-input-number v-model="formData.embedding_dimension" :disabled="true" />
        </el-form-item>
        <el-form-item label="搜索模式">
          <el-radio-group v-model="formData.search_type">
            <el-radio-button label="embedding">向量搜索</el-radio-button>
            <el-radio-button label="keywords">关键词搜索</el-radio-button>
            <el-radio-button label="blend">混合搜索 (推荐)</el-radio-button>
          </el-radio-group>
          <div class="help-text">设置该知识库的默认搜索模式</div>
        </el-form-item>
      </el-card>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { knowledgeApi, type KnowledgeBase } from '@/api'

const route = useRoute()
const router = useRouter()
const knowledgeBaseId = computed(() => route.params.id as string)

const formData = ref<Partial<KnowledgeBase>>({
  name: '',
  desc: '',
  embedding_model: 'text2vec-base-Chinese',
  embedding_dimension: 768,
  similarity_threshold: 0.5,
  search_type: 'blend',
  top_k: 5
})

// 模型维度映射
const modelDimensions: Record<string, number> = {
  'text2vec-base-Chinese': 768,
  'BAAI/bge-large-zh-v1.5': 1024,
  'BAAI/bge-small-zh-v1.5': 384,
  'm3e-base': 768,
  'm3e-small': 384
}

// 监听模型变化，自动更新维度
watch(() => formData.value.embedding_model, (newModel) => {
  if (newModel && modelDimensions[newModel]) {
    formData.value.embedding_dimension = modelDimensions[newModel]
  }
})

const loadSettings = async () => {
  try {
    const knowledgeBase = await knowledgeApi.getKnowledgeBase(knowledgeBaseId.value)
    formData.value = { ...knowledgeBase }
    // 确保模型维度正确
    if (knowledgeBase.embedding_model && modelDimensions[knowledgeBase.embedding_model]) {
      formData.value.embedding_dimension = modelDimensions[knowledgeBase.embedding_model]
    }
  } catch (error) {
    ElMessage.error('加载设置失败')
  }
}

const saveSettings = async () => {
  try {
    await knowledgeApi.updateKnowledgeBase(knowledgeBaseId.value, formData.value)
    ElMessage.success('保存成功')
    router.push('/knowledge')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const goBack = () => {
  router.push('/knowledge')
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.knowledge-setting {
  padding: 20px;
}

.setting-card {
  margin-bottom: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-actions {
  margin-top: 30px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>