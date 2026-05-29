<template>
  <div class="knowledge-setting awwwards-theme">
    <div class="ambient-bg">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="noise-overlay"></div>
    </div>
    <div class="main-content">
      <h2 class="page-title gradient-text">知识库设置</h2>
      <el-form :model="formData" label-width="150px" @submit.prevent="saveSettings">
        <!-- 基本信息 -->
        <div class="setting-card glass-panel">
          <div class="card-header">
            <span>基本信息</span>
          </div>
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
        </div>

        <!-- 检索设置 -->
        <div class="setting-card glass-panel mt-20">
          <div class="card-header">
            <span>检索设置</span>
          </div>
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
              <el-radio-button value="embedding">向量搜索</el-radio-button>
              <el-radio-button value="keywords">关键词搜索</el-radio-button>
              <el-radio-button value="blend">混合搜索 (推荐)</el-radio-button>
            </el-radio-group>
            <div class="help-text">设置该知识库的默认搜索模式</div>
          </el-form-item>
        </div>

        <!-- 操作按钮 -->
        <div class="form-actions">
          <button type="button" class="btn-outline" @click="goBack">返回</button>
          <button type="button" class="btn-glow" @click="saveSettings">保存设置</button>
        </div>
      </el-form>
    </div>
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

<style scoped lang="scss">
:root {
  --abyss: var(--tcm-bg-color);
  --surface: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent);
  --border: var(--tcm-border-color);
}

.awwwards-theme {
  position: relative;
  width: 100%;
  min-height: 100vh;
  background-color: var(--tcm-bg-color);
  color: var(--tcm-text-primary);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  overflow-x: hidden;
  padding: 0;
  box-sizing: border-box;
}

/* 沉浸式背景 */
.ambient-bg {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.3;
  animation: float 20s infinite ease-in-out alternate;
}
.orb-1 { top: -10%; left: -10%; width: 50vw; height: 50vw; background: radial-gradient(circle, color-mix(in srgb, var(--tcm-accent-color) 30%, transparent) 0%, transparent 70%); }
.orb-2 { bottom: -20%; right: -10%; width: 60vw; height: 60vw; background: radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 70%); animation-delay: -5s; }

.noise-overlay {
  position: absolute; inset: 0;
  background: url('data:image/svg+xml;utf8,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)" opacity="0.05"/%3E%3C/svg%3E');
  mix-blend-mode: overlay;
}

@keyframes float {
  0% { transform: scale(1) translate(0, 0); }
  50% { transform: scale(1.1) translate(2%, 2%); }
  100% { transform: scale(0.9) translate(-2%, -2%); }
}

.main-content {
  position: relative;
  z-index: 10;
  padding: 40px;
  max-width: 1000px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 32px;
}

.gradient-text {
  background: linear-gradient(to right, var(--tcm-text-primary), var(--tcm-accent-color), #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.glass-panel {
  background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent);
  border: 1px solid var(--tcm-border-color);
  border-radius: 24px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 32px;
}

.setting-card {
  margin-bottom: 24px;
}

.mt-20 {
  margin-top: 24px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
  color: var(--tcm-text-primary);
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--tcm-border-color);
}

.help-text {
  font-size: 12px;
  color: var(--tcm-text-regular);
  margin-top: 8px;
}

.form-actions {
  margin-top: 40px;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
}

/* 按钮样式 */
.btn-glow {
  padding: 12px 24px; background: linear-gradient(135deg, color-mix(in srgb, var(--tcm-accent-color) 20%, transparent), rgba(139,92,246,0.2));
  border: 1px solid var(--tcm-border-color); border-radius: 100px; color: var(--tcm-text-primary); font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.4s;
}
.btn-glow:hover { transform: translateY(-2px); box-shadow: 0 10px 30px color-mix(in srgb, var(--tcm-accent-color) 30%, transparent); border-color: color-mix(in srgb, var(--tcm-border-color) 30%, transparent); }

.btn-outline {
  padding: 12px 24px; border: 1px solid var(--tcm-border-color); border-radius: 100px; color: var(--tcm-text-primary); font-size: 14px; background: transparent; cursor: pointer; transition: all 0.3s;
}
.btn-outline:hover { background: color-mix(in srgb, var(--tcm-card-bg) 50%, transparent); border-color: var(--tcm-text-primary); }

/* 覆盖 Element Plus 表单样式 */
:deep(.el-form-item__label) {
  color: var(--tcm-text-regular) !important;
}

:deep(.el-input__wrapper), :deep(.el-textarea__inner) {
  background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent) !important;
  border: 1px solid var(--tcm-border-color) !important;
  box-shadow: none !important;
  color: var(--tcm-text-primary);
}
:deep(.el-input__inner) { color: var(--tcm-text-primary); }

:deep(.el-select-dropdown) {
  background: color-mix(in srgb, var(--tcm-bg-color) 90%, transparent) !important;
  border: 1px solid var(--tcm-border-color);
  backdrop-filter: blur(20px);
}
:deep(.el-select-dropdown__item) { color: var(--tcm-text-regular); }
:deep(.el-select-dropdown__item.hover), :deep(.el-select-dropdown__item:hover) {
  background: var(--tcm-border-color); color: var(--tcm-text-primary);
}

:deep(.el-radio-button__inner) {
  background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent);
  border: 1px solid var(--tcm-border-color);
  color: var(--tcm-text-regular);
}
:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: color-mix(in srgb, var(--tcm-accent-color) 20%, transparent);
  border-color: var(--tcm-accent-color);
  color: var(--tcm-text-primary);
  box-shadow: -1px 0 0 0 var(--tcm-accent-color);
}

:deep(.el-input-number__decrease), :deep(.el-input-number__increase) {
  background: color-mix(in srgb, var(--tcm-card-bg) 50%, transparent);
  border-color: var(--tcm-border-color);
  color: var(--tcm-text-primary);
}
</style>
