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
  padding: 20px;
  height: 100vh;
  overflow: auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.model-list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>