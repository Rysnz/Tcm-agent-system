<template>
  <div class="model-management-container">
    <div class="header">
      <h2>模型管理</h2>
    </div>
    
    <!-- 模型列表 -->
    <el-card shadow="hover" class="model-list-card">
      <template #header>
        <div class="card-header">
          <span>模型列表</span>
        </div>
      </template>
      
      <el-table v-loading="loading" :data="modelList" border style="width: 100%">
        <el-table-column prop="name" label="模型名称" min-width="150" />
        <el-table-column prop="provider" label="提供商" width="120" />
        <el-table-column prop="model_type" label="模型类型" width="120" />
        <el-table-column prop="model_name" label="模型名称" min-width="150" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="scope">
            <el-switch v-model="scope.row.is_active" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { modelApi, type ModelConfig } from '@/api'

// 组件挂载状态标志
const isMounted = ref(true)

// 模型列表数据
const modelList = ref<ModelConfig[]>([])
const loading = ref(false)

// 加载模型列表
const loadModelList = async () => {
  if (!isMounted.value) return
  
  loading.value = true
  try {
    const response = await modelApi.getModels()
    if (isMounted.value) {
      modelList.value = response
    }
  } catch (error) {
    if (isMounted.value) {
      console.error('加载模型列表失败:', error)
      ElMessage.error('加载模型列表失败')
    }
  } finally {
    if (isMounted.value) {
      loading.value = false
    }
  }
}

// 初始化
onMounted(() => {
  console.log('ModelManagement component mounted')
  loadModelList()
})

// 组件卸载时清理资源
onUnmounted(() => {
  console.log('ModelManagement component unmounted')
  // 设置组件卸载状态
  isMounted.value = false
  
  // 重置所有响应式数据
  modelList.value = []
})
</script>

<style scoped>
.model-management-container {
  padding: 30px;
  min-height: calc(100vh - 70px);
  background: transparent;
  color: var(--tcm-text-primary);
  overflow: auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  background: linear-gradient(to right, var(--tcm-text-primary), var(--tcm-accent-color));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 0.5px;
}

.model-list-card {
  background: color-mix(in srgb, var(--tcm-card-bg) 60%, transparent) !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--tcm-border-color) !important;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  margin-bottom: 20px;
}

:deep(.el-card__header) {
  border-bottom: 1px solid var(--tcm-border-color);
  background: color-mix(in srgb, var(--tcm-text-primary) 2%, transparent);
  padding: 20px 24px;
}

.card-header span {
  font-size: 16px;
  font-weight: 500;
  color: var(--tcm-text-primary);
  letter-spacing: 0.5px;
}

/* Table dark theme overrides */
:deep(.el-table) {
  background-color: transparent !important;
  --el-table-border-color: var(--tcm-border-color);
  --el-table-header-bg-color: color-mix(in srgb, var(--tcm-text-primary) 3%, transparent);
  --el-table-header-text-color: var(--tcm-text-regular);
  --el-table-row-hover-bg-color: color-mix(in srgb, var(--tcm-accent-color) 8%, transparent);
}

:deep(.el-table th.el-table__cell),
:deep(.el-table tr),
:deep(.el-table td.el-table__cell) {
  background-color: transparent !important;
  border-bottom: 1px solid var(--tcm-border-color) !important;
  color: var(--tcm-text-primary);
}

:deep(.el-table::before) {
  display: none;
}

:deep(.el-table__empty-block) {
  background-color: transparent !important;
}

:deep(.el-switch__core) {
  border-color: var(--tcm-border-color);
  background-color: var(--tcm-border-color);
}

:deep(.el-switch.is-checked .el-switch__core) {
  border-color: var(--tcm-accent-color);
  background-color: var(--tcm-accent-color);
  box-shadow: 0 0 10px color-mix(in srgb, var(--tcm-accent-color) 40%, transparent);
}
</style>