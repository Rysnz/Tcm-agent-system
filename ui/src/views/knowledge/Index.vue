<template>
  <div class="knowledge-page awwwards-theme">
    <!-- 动态背景 -->
    <div class="ambient-bg">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="noise-overlay"></div>
    </div>

    <div class="main-content">
      <!-- 页面头部 -->
      <div class="page-header glass-panel">
        <div class="header-left">
          <h2 class="page-title">
            <el-icon class="glow-icon"><DataAnalysis /></el-icon>
            <span class="gradient-text">知识库管理</span>
          </h2>
          <div class="header-desc">管理您的知识库和文档，支持向量检索和智能问答</div>
        </div>
        <div class="header-right">
          <button class="btn-glow" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建知识库
          </button>
        </div>
      </div>

    <!-- 知识库列表 -->
    <div v-if="knowledgeBases.length" class="kb-grid">
      <div 
        v-for="kb in knowledgeBases" 
        :key="kb.id"
        class="kb-card"
        @click="openKnowledgeBase(kb)"
      >
        <div class="kb-header">
          <div class="kb-icon">📚</div>
          <div class="kb-status">
            <el-tag :type="kb.is_active ? 'success' : 'info'" size="small">
              {{ kb.is_active ? '已激活' : '未激活' }}
            </el-tag>
          </div>
        </div>
        <div class="kb-body">
          <div class="kb-name">{{ kb.name || '未命名知识库' }}</div>
          <div class="kb-desc">{{ kb.desc || '暂无描述' }}</div>
        </div>
        <div class="kb-footer">
          <div class="kb-stats">
            <div class="stat-item">
              <span class="stat-value">{{ getDocCount(kb.id) }}</span>
              <span class="stat-label">文档</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ getVectorCount(kb.id) }}</span>
              <span class="stat-label">向量</span>
            </div>
          </div>
          <div class="kb-actions" @click.stop>
            <el-dropdown trigger="click">
              <el-button type="primary" text>
                <el-icon><More /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="openDocuments(kb)">
                    <el-icon><Document /></el-icon>
                    文档管理
                  </el-dropdown-item>
                  <el-dropdown-item @click="openSearch(kb)">
                    <el-icon><Search /></el-icon>
                    知识检索
                  </el-dropdown-item>
                  <el-dropdown-item @click="editKnowledgeBase(kb)">
                    <el-icon><Setting /></el-icon>
                    知识库设置
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="deleteKnowledgeBase(kb)">
                    <el-icon><Delete /></el-icon>
                    <span style="color: #f56c6c;">删除知识库</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无知识库" :image-size="120">
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建第一个知识库
      </el-button>
    </el-empty>

    <!-- 创建知识库对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建知识库" width="500px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="知识库名称">
          <el-input v-model="formData.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="formData.desc" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入知识库描述（选填）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createKnowledgeBase">创建</el-button>
      </template>
    </el-dialog>

    <!-- 知识库详情对话框 -->
    <el-dialog v-model="showDocumentDialog" title="知识库详情" width="1100px">
      <div class="knowledge-detail">
        <!-- 知识库信息 -->
        <div v-if="currentKB" class="kb-info-bar">
          <div class="kb-info">
            <div class="kb-icon">📚</div>
            <div class="kb-details">
              <div class="kb-name">{{ currentKB.name }}</div>
              <div class="kb-desc">{{ currentKB.desc || '暂无描述' }}</div>
            </div>
          </div>
          <div class="kb-stats">
            <div class="stat-item">
              <span class="stat-value">{{ documents.length }}</span>
              <span class="stat-label">文档</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ totalParagraphs }}</span>
              <span class="stat-label">段落</span>
            </div>
          </div>
        </div>

        <!-- 左右布局 -->
        <div class="detail-layout">
          <!-- 左侧：文档列表和上传 -->
          <div class="detail-left">
            <div class="panel-header">
              <span class="panel-title">📁 文档管理</span>
              <el-button type="primary" size="small" @click="refreshDocuments">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>

            <!-- 上传区域 -->
            <div class="upload-area">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :on-change="handleFileChange"
                :show-file-list="false"
                :limit="10"
                accept=".pdf,.doc,.docx,.txt,.md,.xlsx,.xls"
              >
                <el-button type="primary" style="width: 100%;">
                  <el-icon><Upload /></el-icon>
                  上传文档
                </el-button>
              </el-upload>
              <div class="upload-hint">支持 PDF、Word、TXT、Markdown、Excel</div>
            </div>

            <!-- 文档列表 -->
            <div class="doc-list">
              <div 
                v-for="doc in documents" 
                :key="doc.id" 
                class="doc-item"
                :class="{ selected: selectedDoc?.id === doc.id }"
                @click="selectDocument(doc)"
              >
                <div class="doc-icon">{{ getFileIcon(doc.file_type) }}</div>
                <div class="doc-content">
                  <div class="doc-name">{{ doc.name }}</div>
                  <div class="doc-meta">
                    <el-tag :type="getStatusType(doc.status)" size="small">
                      {{ getStatusText(doc.status) }}
                    </el-tag>
                    <span class="meta-text">{{ doc.paragraph_count || 0 }}段落</span>
                  </div>
                </div>
                <el-button 
                  type="danger" 
                  text 
                  size="small"
                  @click.stop="deleteDocument(doc)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-empty v-if="!documents.length" description="暂无文档" :image-size="60" />
            </div>
          </div>

          <!-- 右侧：文档内容 -->
          <div class="detail-right">
            <div class="panel-header">
              <span class="panel-title">
                {{ selectedDoc ? selectedDoc.name : '📋 文档内容' }}
              </span>
              <span v-if="paragraphs.length" class="paragraph-count">共 {{ paragraphs.length }} 个段落</span>
            </div>

            <div v-if="selectedDoc && paragraphs.length" class="content-view">
              <div 
                v-for="(para, idx) in paragraphs" 
                :key="para.id" 
                class="paragraph-card"
              >
                <div class="para-header">
                  <span class="para-index">段落 {{ idx + 1 }}</span>
                  <span v-if="para.page_number" class="para-page">第{{ para.page_number }}页</span>
                </div>
                <div class="para-content">{{ para.content }}</div>
              </div>
            </div>

            <div v-else-if="loadingParagraphs" class="loading-state">
              <el-icon class="is-loading" style="font-size: 32px;"><Loading /></el-icon>
              <p>加载中...</p>
            </div>

            <el-empty 
              v-else 
              description="请在左侧选择一个文档查看内容" 
              :image-size="80"
            />
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 知识检索对话框 -->
    <el-dialog v-model="showSearchDialog" title="知识检索" width="700px">
      <div class="search-manager">
        <div class="search-input">
          <el-input
            v-model="searchQuery"
            placeholder="输入问题进行知识检索..."
            size="large"
            @keyup.enter="performSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #append>
              <el-button type="primary" @click="performSearch" :loading="searching">
                检索
              </el-button>
            </template>
          </el-input>
        </div>
        
        <div class="search-options">
          <el-select v-model="searchType" size="small" style="width: 120px;">
            <el-option label="混合检索" value="blend" />
            <el-option label="向量检索" value="embedding" />
            <el-option label="关键词检索" value="keywords" />
          </el-select>
          <el-input-number 
            v-model="topK" 
            :min="1" 
            :max="20" 
            size="small"
            style="width: 100px; margin-left: 12px;"
          />
          <span style="margin-left: 8px; color: #909399;">返回数量</span>
        </div>

        <div v-if="searching" class="search-loading">
          <el-icon class="is-loading" style="font-size: 32px;"><Loading /></el-icon>
          <p>正在检索中...</p>
        </div>
        
        <div v-else-if="searchResults.length" class="search-results">
          <div 
            v-for="(result, idx) in searchResults" 
            :key="idx" 
            class="result-card"
          >
            <div class="result-header">
              <span class="result-rank">#{{ idx + 1 }}</span>
              <el-tag size="small" :type="getSearchTypeTag(result.search_type)">
                {{ getSearchTypeText(result.search_type) }}
              </el-tag>
              <span class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</span>
            </div>
            <div class="result-title">{{ result.title || '未知来源' }}</div>
            <div class="result-content">{{ result.content }}</div>
          </div>
        </div>
        
        <el-empty v-else-if="hasSearched" description="未找到相关内容" :image-size="80" />
      </div>
    </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  DataAnalysis, Plus, Document, Search, Setting, Delete, Upload,
  More, Refresh, Loading
} from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api'
import dayjs from 'dayjs'

// 路由
const router = useRouter()

// 数据
const knowledgeBases = ref<any[]>([])
const documents = ref<any[]>([])
const kbStats = ref<Record<string, { doc_count: number; vector_count: number }>>({})
const paragraphs = ref<any[]>([])
const selectedDoc = ref<any>(null)

// 对话框
const showCreateDialog = ref(false)
const showDocumentDialog = ref(false)
const showSearchDialog = ref(false)
const loadingParagraphs = ref(false)

// 计算段落总数
const totalParagraphs = computed(() => {
  return documents.value.reduce((sum, doc) => sum + (doc.paragraph_count || 0), 0)
})

// 当前选中的知识库
const currentKB = ref<any>(null)

// 表单数据
const formData = ref({
  name: '',
  desc: ''
})

// 检索相关
const searchQuery = ref('')
const searchType = ref('blend')
const topK = ref(5)
const searchResults = ref<any[]>([])
const searching = ref(false)
const hasSearched = ref(false)

// 定时器
let progressTimer: any = null

// 加载知识库列表
const loadKnowledgeBases = async () => {
  try {
    const res = await knowledgeApi.getKnowledgeBases()
    knowledgeBases.value = res.results || res || []
    // 加载统计信息
    for (const kb of knowledgeBases.value) {
      loadKBStats(kb.id)
    }
  } catch (error) {
    console.error('加载知识库失败:', error)
  }
}

// 加载知识库统计
const loadKBStats = async (kbId: string) => {
  try {
    const res = await knowledgeApi.getKnowledgeBaseStats(kbId)
    kbStats.value[kbId] = {
      doc_count: res.document_count || 0,
      vector_count: res.vector_count || 0
    }
    console.log(`Stats loaded for ${kbId}:`, res)
  } catch (error) {
    console.error(`Failed to load stats for ${kbId}:`, error)
    kbStats.value[kbId] = { doc_count: 0, vector_count: 0 }
  }
}

// 获取文档数量
const getDocCount = (kbId: string) => {
  return kbStats.value[kbId]?.doc_count || 0
}

// 获取向量数量
const getVectorCount = (kbId: string) => {
  return kbStats.value[kbId]?.vector_count || 0
}

// 创建知识库
const createKnowledgeBase = async () => {
  if (!formData.value.name) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  try {
    await knowledgeApi.createKnowledgeBase(formData.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    formData.value = { name: '', desc: '' }
    loadKnowledgeBases()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

// 打开知识库
const openKnowledgeBase = (kb: any) => {
  currentKB.value = kb
  openDocuments(kb)
}

// 打开文档管理
const openDocuments = async (kb: any) => {
  currentKB.value = kb
  showDocumentDialog.value = true
  await refreshDocuments()
  startProgressTimer()
}

// 刷新文档列表
const refreshDocuments = async () => {
  if (!currentKB.value) return
  try {
    const res = await knowledgeApi.getDocuments(currentKB.value.id)
    documents.value = res.results || res || []
  } catch (error) {
    console.error('加载文档失败:', error)
  }
}

// 选择文档并加载段落
const selectDocument = async (doc: any) => {
  selectedDoc.value = doc
  loadingParagraphs.value = true
  paragraphs.value = []
  
  try {
    const res = await knowledgeApi.getDocumentParagraphs(doc.id)
    paragraphs.value = res.paragraphs || []
  } catch (error) {
    console.error('加载段落失败:', error)
    paragraphs.value = []
  } finally {
    loadingParagraphs.value = false
  }
}

// 处理文件上传
const handleFileChange = async (file: any) => {
  if (!currentKB.value) return
  
  const formData = new FormData()
  formData.append('file', file.raw)
  formData.append('knowledge_base_id', currentKB.value.id)
  
  try {
    await knowledgeApi.uploadDocument(formData)
    ElMessage.success('文档上传成功，正在处理...')
    await refreshDocuments()
    startProgressTimer()
  } catch (error) {
    ElMessage.error('上传失败')
  }
}

// 重新处理文档
const reprocessDocument = async (doc: any) => {
  try {
    await knowledgeApi.reprocessDocument(doc.id)
    ElMessage.success('重新处理已开始')
    await refreshDocuments()
  } catch (error) {
    ElMessage.error('重新处理失败')
  }
}

// 删除文档
const deleteDocument = async (doc: any) => {
  try {
    await ElMessageBox.confirm(`确定删除文档"${doc.name}"吗？`, '确认删除')
    await knowledgeApi.deleteDocument(doc.id)
    ElMessage.success('删除成功')
    await refreshDocuments()
    loadKBStats(currentKB.value.id)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 打开知识检索
const openSearch = (kb: any) => {
  currentKB.value = kb
  searchQuery.value = ''
  searchResults.value = []
  hasSearched.value = false
  showSearchDialog.value = true
}

// 执行检索
const performSearch = async () => {
  if (!currentKB.value || !searchQuery.value) return
  
  searching.value = true
  hasSearched.value = true
  try {
    const res = await knowledgeApi.searchKnowledge({
      knowledge_base_id: currentKB.value.id,
      query: searchQuery.value,
      search_type: searchType.value,
      top_k: topK.value
    })
    searchResults.value = res.results || []
  } catch (error) {
    ElMessage.error('检索失败')
  } finally {
    searching.value = false
  }
}

// 编辑知识库
const editKnowledgeBase = (kb: any) => {
  router.push(`/knowledge/${kb.id}/setting`)
}

// 删除知识库
const deleteKnowledgeBase = async (kb: any) => {
  try {
    await ElMessageBox.confirm(`确定删除知识库"${kb.name}"吗？此操作不可恢复。`, '确认删除')
    await knowledgeApi.deleteKnowledgeBase(kb.id)
    ElMessage.success('删除成功')
    loadKnowledgeBases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 启动进度定时器
const startProgressTimer = () => {
  stopProgressTimer()
  progressTimer = setInterval(async () => {
    const hasProcessing = documents.value.some(d => d.status === 'processing')
    if (hasProcessing) {
      await refreshDocuments()
    } else {
      stopProgressTimer()
    }
  }, 3000)
}

// 停止进度定时器
const stopProgressTimer = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

// 工具函数
const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}

const getFileIcon = (type: string) => {
  const icons: Record<string, string> = {
    pdf: '📄',
    doc: '📝',
    docx: '📝',
    txt: '📃',
    md: '📑',
    xlsx: '📊',
    xls: '📊'
  }
  return icons[type] || '📄'
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    processing: 'warning',
    completed: 'success',
    partially_completed: 'info',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    processing: '处理中',
    completed: '已完成',
    partially_completed: '部分完成',
    failed: '失败'
  }
  return texts[status] || status
}

const getSearchTypeTag = (type: string) => {
  const tags: Record<string, string> = {
    blend_rrf: 'primary',
    embedding: 'success',
    keywords: 'warning'
  }
  return tags[type] || 'info'
}

const getSearchTypeText = (type: string) => {
  const texts: Record<string, string> = {
    blend_rrf: '混合检索',
    embedding: '向量检索',
    keywords: '关键词检索'
  }
  return texts[type] || type
}

// 生命周期
onMounted(() => {
  loadKnowledgeBases()
})

onUnmounted(() => {
  stopProgressTimer()
})
</script>

<style scoped lang="scss">
:root {
  --abyss: var(--tcm-bg-color);
  --surface: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent);
  --surface-hover: var(--tcm-border-color);
  --border: var(--tcm-border-color);
  --border-light: var(--tcm-border-color);
  --text-main: var(--tcm-text-primary);
  --text-muted: var(--tcm-text-regular);
  
  --emerald: #10b981;
  --teal: var(--tcm-accent-color);
  --purple: #8b5cf6;
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

/* 沉浸式流体背景 */
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
  opacity: 0.4;
  animation: float 20s infinite ease-in-out alternate;
}

.orb-1 { top: -10%; left: -10%; width: 50vw; height: 50vw; background: radial-gradient(circle, color-mix(in srgb, var(--tcm-accent-color) 30%, transparent) 0%, transparent 70%); }
.orb-2 { bottom: -20%; right: -10%; width: 60vw; height: 60vw; background: radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 70%); animation-delay: -5s; }
.orb-3 { top: 40%; left: 40%; width: 40vw; height: 40vw; background: radial-gradient(circle, rgba(16,185,129,0.15) 0%, transparent 70%); animation-delay: -10s; }

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

/* 主体内容区 */
.main-content {
  position: relative;
  z-index: 10;
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.glass-panel {
  background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent);
  border: 1px solid var(--tcm-border-color);
  border-radius: 24px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 24px 32px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  color: var(--tcm-text-primary);
}

.glow-icon {
  color: var(--tcm-accent-color);
  filter: drop-shadow(0 0 8px color-mix(in srgb, var(--tcm-accent-color) 60%, transparent));
}

.gradient-text {
  background: linear-gradient(to right, var(--tcm-text-primary), var(--tcm-accent-color), #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-desc {
  font-size: 14px;
  color: var(--tcm-text-regular);
}

/* 发光按钮 */
.btn-glow {
  position: relative; display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 24px; background: linear-gradient(135deg, color-mix(in srgb, var(--tcm-accent-color) 20%, transparent), rgba(139,92,246,0.2));
  border: 1px solid var(--tcm-border-color); border-radius: 100px; color: var(--tcm-text-primary); font-size: 14px; font-weight: 600; cursor: pointer; overflow: hidden; transition: all 0.4s;
}
.btn-glow:hover { transform: translateY(-2px); box-shadow: 0 10px 30px color-mix(in srgb, var(--tcm-accent-color) 30%, transparent); border-color: color-mix(in srgb, var(--tcm-border-color) 30%, transparent); }

/* 知识库卡片网格 */
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.kb-card {
  background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent);
  border: 1px solid var(--tcm-border-color);
  border-radius: 24px;
  padding: 24px;
  backdrop-filter: blur(20px);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.kb-card::after {
  content: ''; position: absolute; inset: 0; background: radial-gradient(circle at center, color-mix(in srgb, var(--tcm-card-bg) 50%, transparent) 0%, transparent 60%); opacity: 0; transition: opacity 0.4s;
}

.kb-card:hover {
  transform: translateY(-5px);
  border-color: var(--tcm-border-color);
  box-shadow: 0 20px 40px color-mix(in srgb, var(--tcm-border-color) 50%, transparent), 0 0 20px color-mix(in srgb, var(--tcm-accent-color) 10%, transparent);
}
.kb-card:hover::after { opacity: 1; }

.kb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  position: relative; z-index: 2;
}

.kb-icon {
  font-size: 32px;
  filter: drop-shadow(0 0 10px var(--tcm-border-color));
}

.kb-body {
  flex: 1;
  position: relative; z-index: 2;
}

.kb-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--tcm-text-primary);
  margin-bottom: 8px;
}

.kb-desc {
  font-size: 13px;
  color: var(--tcm-text-regular);
  line-height: 1.6;
}

.kb-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--tcm-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative; z-index: 2;
}

.kb-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--tcm-accent-color);
  text-shadow: 0 0 10px color-mix(in srgb, var(--tcm-accent-color) 40%, transparent);
}

.stat-label {
  font-size: 12px;
  color: var(--tcm-text-regular);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.kb-actions :deep(.el-button) {
  color: var(--tcm-text-primary);
}
.kb-actions :deep(.el-button:hover) {
  color: var(--tcm-accent-color);
}

/* 覆盖 Element Plus 样式 */
:deep(.el-dialog) {
  background: color-mix(in srgb, var(--tcm-bg-color) 85%, transparent) !important;
  backdrop-filter: blur(30px);
  border: 1px solid var(--tcm-border-color);
  border-radius: 24px;
  box-shadow: 0 24px 48px color-mix(in srgb, var(--tcm-border-color) 50%, transparent);
}

:deep(.el-dialog__title) {
  color: var(--tcm-text-primary);
  font-weight: 600;
}

:deep(.el-dialog__body) {
  color: var(--tcm-text-regular);
}

:deep(.el-form-item__label) {
  color: var(--tcm-text-regular);
}

:deep(.el-input__wrapper), :deep(.el-textarea__inner) {
  background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent) !important;
  border: 1px solid var(--tcm-border-color) !important;
  box-shadow: none !important;
  color: var(--tcm-text-primary);
}
:deep(.el-input__inner) { color: var(--tcm-text-primary); }

:deep(.el-dropdown-menu) {
  background: color-mix(in srgb, var(--tcm-bg-color) 90%, transparent) !important;
  border: 1px solid var(--tcm-border-color);
  backdrop-filter: blur(20px);
}
:deep(.el-dropdown-menu__item) {
  color: var(--tcm-text-regular) !important;
}
:deep(.el-dropdown-menu__item:hover) {
  background: var(--tcm-border-color) !important;
  color: var(--tcm-text-primary) !important;
}

:deep(.el-button) {
  background: transparent;
  border-color: var(--tcm-border-color);
  color: var(--tcm-text-primary);
}
:deep(.el-button--primary) {
  background: linear-gradient(135deg, color-mix(in srgb, var(--tcm-accent-color) 80%, transparent), rgba(139,92,246,0.8));
  border: none;
  color: var(--tcm-text-primary);
}
:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, var(--tcm-accent-color), rgba(139,92,246,1));
  box-shadow: 0 0 15px color-mix(in srgb, var(--tcm-accent-color) 40%, transparent);
}

/* 知识库详情内页重构 */
.knowledge-detail {
  .kb-info-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent);
    border: 1px solid var(--tcm-border-color);
    border-radius: 16px;
    margin-bottom: 24px;
  }

  .kb-name { font-size: 18px; font-weight: 600; color: var(--tcm-text-primary); }
  .kb-desc { font-size: 13px; color: var(--tcm-text-regular); }
  .stat-value { font-size: 24px; font-weight: 700; color: var(--tcm-accent-color); }

  .detail-layout {
    display: flex;
    gap: 20px;
    height: 550px;
  }

  .detail-left, .detail-right {
    background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent);
    border: 1px solid color-mix(in srgb, var(--tcm-card-bg) 50%, transparent);
    border-radius: 16px;
    padding: 20px;
    display: flex;
    flex-direction: column;
  }
  
  .detail-left { width: 340px; flex-shrink: 0; }
  .detail-right { flex: 1; }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 16px;
    margin-bottom: 16px;
    border-bottom: 1px solid var(--tcm-border-color);
  }

  .panel-title { font-size: 16px; font-weight: 600; color: var(--tcm-text-primary); }
  
  .doc-list {
    flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px;
    &::-webkit-scrollbar { width: 6px; }
    &::-webkit-scrollbar-thumb { background: var(--tcm-border-color); border-radius: 3px; }
  }

  .doc-item {
    display: flex; align-items: center; gap: 12px; padding: 12px;
    background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent); border-radius: 12px; border: 1px solid transparent;
    cursor: pointer; transition: all 0.3s;
  }
  .doc-item:hover { background: color-mix(in srgb, var(--tcm-card-bg) 60%, transparent); }
  .doc-item.selected {
    background: color-mix(in srgb, var(--tcm-accent-color) 10%, transparent); border-color: color-mix(in srgb, var(--tcm-accent-color) 30%, transparent);
  }
  
  .doc-name { font-size: 13px; font-weight: 500; color: var(--tcm-text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .meta-text { font-size: 11px; color: var(--tcm-text-regular); }

  .content-view {
    flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; padding-right: 8px;
    &::-webkit-scrollbar { width: 6px; }
    &::-webkit-scrollbar-thumb { background: var(--tcm-border-color); border-radius: 3px; }
  }

  .paragraph-card {
    padding: 16px; background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent); border-radius: 12px;
    border-left: 4px solid #8b5cf6;
  }

  .para-index { font-weight: 600; color: #8b5cf6; font-size: 13px; }
  .para-content { font-size: 14px; color: var(--tcm-text-primary); line-height: 1.7; margin-top: 8px; }
}

/* 检索界面重构 */
.search-manager {
  .search-input { margin-bottom: 20px; }
  
  .search-options { margin-bottom: 24px; color: var(--tcm-text-regular); }

  .search-results {
    max-height: 450px; overflow-y: auto; padding-right: 8px;
    &::-webkit-scrollbar { width: 6px; }
    &::-webkit-scrollbar-thumb { background: var(--tcm-border-color); border-radius: 3px; }
  }

  .result-card {
    padding: 20px; background: color-mix(in srgb, var(--tcm-card-bg) 80%, transparent);
    border: 1px solid var(--tcm-border-color); border-radius: 16px; margin-bottom: 16px;
    transition: transform 0.3s;
  }
  .result-card:hover { transform: translateX(4px); border-color: color-mix(in srgb, var(--tcm-accent-color) 30%, transparent); }

  .result-rank { font-weight: 700; color: var(--tcm-accent-color); }
  .result-score { font-size: 12px; color: #8b5cf6; }
  .result-title { font-size: 15px; font-weight: 500; color: var(--tcm-text-primary); margin-bottom: 12px; }
  .result-content { font-size: 14px; color: var(--tcm-text-regular); line-height: 1.6; }
}

:deep(.el-empty__description) {
  color: var(--tcm-text-regular);
}
:deep(.el-upload) {
  width: 100%;
}
:deep(.el-upload .el-button) {
  width: 100%;
  background: color-mix(in srgb, var(--tcm-card-bg) 50%, transparent);
  border: 1px dashed var(--tcm-border-color);
}
:deep(.el-upload .el-button:hover) {
  border-color: var(--tcm-accent-color); color: var(--tcm-accent-color);
}
</style>
