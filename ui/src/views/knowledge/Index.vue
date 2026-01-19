<template>
  <div class="knowledge-container">
    <div class="header">
      <h2>知识库管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建知识库
      </el-button>
    </div>
    
    <el-table :data="knowledgeBases" stripe>
      <el-table-column prop="name" label="知识库名称" width="200" />
      <el-table-column prop="desc" label="描述" show-overflow-tooltip />
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '激活' : '未激活' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="180" />
      <el-table-column label="操作" width="350" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewDocuments(row)">文档</el-button>
          <el-button link type="success" @click="searchKnowledge(row)">检索</el-button>
          <el-button link type="warning" @click="editKnowledgeBase(row)">设置</el-button>
          <el-button link type="danger" @click="deleteKnowledgeBase(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog v-model="showCreateDialog" title="创建知识库" width="600px">
      <el-form :model="formData" label-width="100px">
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
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveKnowledgeBase">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showDocumentsDialog" title="文档管理" width="80%">
      <div class="upload-area">
        <el-upload
          :auto-upload="false"
          :on-change="handleFileChange"
          :show-file-list="false"
        >
          <el-button type="primary">
            <el-icon><Upload /></el-icon>
            上传文档
          </el-button>
        </el-upload>
      </div>
      <el-table :data="documents" stripe>
        <el-table-column prop="name" label="文档名称" />
        <el-table-column prop="file_type" label="文件类型" width="100" />
        <el-table-column prop="char_count" label="字符数" width="100" />
        <el-table-column prop="paragraph_count" label="段落数" width="100" />
        <el-table-column prop="status" label="状态" width="150">
          <template #default="{ row }">
            <div>
              <el-tag :type="getStatusType(row.status)" style="margin-bottom: 5px;">
                {{ getStatusText(row.status) }}
              </el-tag>
              <div v-if="row.status === 'processing' || row.status === 'partially_completed'" style="margin-top: 5px;">
                <el-progress 
                  :percentage="row.progress || 0" 
                  size="small"
                  text-inside
                  stroke-width="8"
                />
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="deleteDocument(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    
    <el-dialog v-model="showSearchDialog" title="知识检索" width="80%">
      <el-input
        v-model="searchQuery"
        placeholder="请输入检索关键词"
        @keyup.enter="doSearch"
      >
        <template #append>
          <el-button icon="Search" @click="doSearch" />
        </template>
      </el-input>
      <div class="search-results">
        <div v-for="(item, index) in searchResults" :key="index" class="result-item">
          <div class="result-title">{{ item.title }}</div>
          <div class="result-content">{{ item.content }}</div>
          <div class="result-score">相似度: {{ (item.score * 100).toFixed(2) }}%</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Search } from '@element-plus/icons-vue'
import { knowledgeApi, type KnowledgeBase, type Document } from '@/api'

const route = useRoute()
const router = useRouter()

const knowledgeBases = ref<KnowledgeBase[]>([])
const documents = ref<Document[]>([])
const searchResults = ref<any[]>([])
const showCreateDialog = ref(false)
const showDocumentsDialog = ref(false)
const showSearchDialog = ref(false)
const searchQuery = ref('')
const currentKnowledgeBase = ref<KnowledgeBase | null>(null)
const formData = ref<Partial<KnowledgeBase>>({
  name: '',
  desc: ''
})

// 进度更新相关
let progressUpdateTimer: any = null
const updateInterval = 3000 // 3秒更新一次

const loadKnowledgeBases = async () => {
  try {
    knowledgeBases.value = await knowledgeApi.getKnowledgeBases()
  } catch (error) {
    ElMessage.error('加载知识库列表失败')
  }
}

const saveKnowledgeBase = async () => {
  try {
    await knowledgeApi.createKnowledgeBase(formData.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    loadKnowledgeBases()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

const viewDocuments = async (row: KnowledgeBase) => {
  currentKnowledgeBase.value = row
  documents.value = await knowledgeApi.getDocuments(row.id)
  showDocumentsDialog.value = true
}

// 启动进度更新定时器
const startProgressUpdate = () => {
  if (progressUpdateTimer) {
    clearInterval(progressUpdateTimer)
  }
  
  progressUpdateTimer = setInterval(async () => {
    if (currentKnowledgeBase.value && showDocumentsDialog.value) {
      // 检查是否有处理中的文档
      const hasProcessing = documents.value.some(doc => doc.status === 'processing')
      if (hasProcessing) {
        // 只有当有处理中的文档时才刷新
        const updatedDocs = await knowledgeApi.getDocuments(currentKnowledgeBase.value.id)
        documents.value = updatedDocs
      } else {
        // 没有处理中的文档，停止定时器
        stopProgressUpdate()
      }
    }
  }, updateInterval)
}

// 停止进度更新定时器
const stopProgressUpdate = () => {
  if (progressUpdateTimer) {
    clearInterval(progressUpdateTimer)
    progressUpdateTimer = null
  }
}

// 监听文档对话框的显示状态，自动启动/停止进度更新
watch(showDocumentsDialog, (newVal) => {
  if (newVal) {
    startProgressUpdate()
  } else {
    stopProgressUpdate()
  }
})

const handleFileChange = async (file: any) => {
  if (!currentKnowledgeBase.value) return
  
  const formData = new FormData()
  formData.append('file', file.raw)
  formData.append('knowledge_base_id', currentKnowledgeBase.value.id)
  
  try {
    await knowledgeApi.uploadDocument(formData)
    ElMessage.success('上传成功')
    documents.value = await knowledgeApi.getDocuments(currentKnowledgeBase.value.id)
  } catch (error) {
    ElMessage.error('上传失败')
  }
}

const searchKnowledge = (row: KnowledgeBase) => {
  currentKnowledgeBase.value = row
  showSearchDialog.value = true
}

const doSearch = async () => {
  if (!currentKnowledgeBase.value || !searchQuery.value) return
  
  try {
    const result = await knowledgeApi.searchKnowledge({
      knowledge_base_id: currentKnowledgeBase.value.id,
      query: searchQuery.value,
      top_k: 5
    })
    searchResults.value = result.results
  } catch (error) {
    ElMessage.error('检索失败')
  }
}

const deleteKnowledgeBase = async (row: KnowledgeBase) => {
  try {
    await ElMessageBox.confirm('确定要删除该知识库吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await knowledgeApi.deleteKnowledgeBase(row.id)
    ElMessage.success('删除成功')
    loadKnowledgeBases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const editKnowledgeBase = (row: KnowledgeBase) => {
  // 跳转到设置页面
  router.push(`/knowledge/${row.id}/setting`)
}

const deleteDocument = async (row: Document) => {
  try {
    await ElMessageBox.confirm(`确定要删除文档"${row.name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await knowledgeApi.deleteDocument(row.id)
    ElMessage.success('删除成功')
    // 刷新文档列表
    if (currentKnowledgeBase.value) {
      documents.value = await knowledgeApi.getDocuments(currentKnowledgeBase.value.id)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    processing: 'warning',
    completed: 'success',
    partially_completed: 'info',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    processing: '处理中',
    completed: '已完成',
    partially_completed: '部分完成',
    failed: '失败'
  }
  return textMap[status] || status
}

onMounted(() => {
  loadKnowledgeBases()
})

watch(() => route.path, (newPath) => {
  if (newPath === '/knowledge') {
    loadKnowledgeBases()
  }
}, { immediate: true })
</script>

<style scoped>
.knowledge-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.upload-area {
  margin-bottom: 20px;
}

.search-results {
  max-height: 500px;
  overflow-y: auto;
  margin-top: 20px;
}

.result-item {
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 10px;
}

.result-title {
  font-weight: bold;
  margin-bottom: 8px;
  color: #303133;
}

.result-content {
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.6;
}

.result-score {
  color: #409eff;
  font-size: 12px;
}
</style>
