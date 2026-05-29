<template>
  <div class="profile-page bento-layout">
    <!-- 页面头部 -->
    <div class="page-header bento-header">
      <h2 class="page-title gradient-text">
        <el-icon><User /></el-icon>
        个人档案
      </h2>
      <div class="header-desc">管理您的健康数据与养生记录</div>
    </div>

    <div class="bento-grid">
      <!-- 健康概览卡片 (span 2 if space permits) -->
      <div class="bento-card overview-bento">
        <el-card shadow="never">
          <div class="overview-header">
            <div class="overview-icon">📊</div>
            <div class="overview-title">健康概览</div>
          </div>
          <div class="overview-stats">
            <div class="stat-item">
              <div class="stat-value gradient-value">{{ checkinStats.total_days }}</div>
              <div class="stat-label">打卡天数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value gradient-value">{{ checkinStats.streak }}</div>
              <div class="stat-label">连续打卡</div>
            </div>
            <div class="stat-item">
              <div class="stat-value gradient-value">{{ checkinStats.avg_completion }}%</div>
              <div class="stat-label">平均完成率</div>
            </div>
            <div class="stat-item">
              <div class="stat-value gradient-value">{{ checkinStats.this_week }}</div>
              <div class="stat-label">本周打卡</div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 左侧：问诊记录 -->
      <div class="bento-card section-card">
        <el-card shadow="never">
          <template #header>
            <div class="section-header">
              <span class="section-title">🩺 问诊记录</span>
              <span class="section-count">共 {{ consultRecords.length }} 次</span>
            </div>
          </template>
          
          <div v-if="consultRecords.length" class="records-list">
            <div 
              v-for="record in consultRecords.slice(0, 10)" 
              :key="record.session_id"
              class="record-item"
              @click="viewConsultDetail(record)"
            >
              <div class="record-main">
                <div class="record-complaint">{{ record.chief_complaint || record.primary_syndrome || record.symptoms?.[0] || '问诊记录' }}</div>
                <div class="record-time">{{ formatDate(record.create_time || record.created_at) }}</div>
              </div>
              <div class="record-tags">
                <el-tag v-if="record.has_report" type="success" size="small">
                  已生成报告
                </el-tag>
                <el-tag v-if="record.primary_syndrome" type="primary" size="small">
                  {{ record.primary_syndrome }}
                </el-tag>
                <el-button
                  v-if="record.has_report"
                  size="small"
                  type="primary"
                  plain
                  @click.stop="goToConsultReport(record)"
                >
                  查看报告
                </el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无问诊记录" :image-size="60">
            <el-button type="primary" @click="$router.push('/consult')">开始问诊</el-button>
          </el-empty>
        </el-card>
      </div>

      <!-- 右侧：舌象档案 -->
      <div class="bento-card section-card">
        <el-card shadow="never">
          <template #header>
            <div class="section-header">
              <span class="section-title">👅 舌象档案</span>
              <span class="section-count">共 {{ tongueRecords.length }} 次</span>
            </div>
          </template>
          
          <div v-if="tongueRecords.length" class="tongue-list">
            <div 
              v-for="tongue in tongueRecords.slice(0, 6)" 
              :key="tongue.session_id"
              class="tongue-item"
              @click="toggleTongueExpand(tongue.session_id)"
            >
              <div class="tongue-header">
                <div class="tongue-features">
                  <el-tag v-if="tongue.tongue_color" type="danger" size="small">{{ tongue.tongue_color }}</el-tag>
                  <el-tag v-if="tongue.tongue_coating" type="warning" size="small">{{ tongue.tongue_coating }}苔</el-tag>
                  <el-tag v-if="tongue.tongue_shape" type="success" size="small">{{ tongue.tongue_shape }}</el-tag>
                </div>
                <div class="tongue-time">{{ formatDate(tongue.created_at) }}</div>
              </div>
              <div v-if="expandedTongue === tongue.session_id && tongue.diagnosis?.summary" class="tongue-detail">
                <div class="diagnosis-summary">{{ tongue.diagnosis.summary }}</div>
                <div v-if="tongue.diagnosis.suggestions?.length" class="diagnosis-suggestions">
                  <div class="suggestions-title">调理建议：</div>
                  <ul>
                    <li v-for="(s, idx) in tongue.diagnosis.suggestions" :key="idx">{{ s }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无舌象分析记录" :image-size="60">
            <el-button type="primary" @click="$router.push('/consult/tongue')">舌象分析</el-button>
          </el-empty>
        </el-card>
      </div>

      <!-- 养生计划记录 -->
      <div class="bento-card section-card span-2">
        <el-card shadow="never">
          <template #header>
            <div class="section-header">
              <span class="section-title">🌿 养生计划</span>
              <el-button type="primary" size="small" @click="$router.push('/wellness')">生成新计划</el-button>
            </div>
          </template>
          
          <div v-if="wellnessPlans.length" class="wellness-list">
            <div 
              v-for="plan in wellnessPlans.slice(0, 5)" 
              :key="plan.id"
              class="wellness-item"
              @click="toggleWellnessExpand(plan.id)"
            >
              <div class="wellness-header">
                <div class="wellness-main">
                  <el-tag type="success" size="small">{{ plan.constitution }}</el-tag>
                  <span v-if="plan.source_syndrome" class="wellness-source">基于：{{ plan.source_syndrome }}</span>
                </div>
                <div class="wellness-time">{{ formatDate(plan.create_time) }}</div>
              </div>
              <div v-if="expandedWellness === plan.id && plan.plan_json" class="wellness-detail">
                <div v-if="plan.plan_json.theme" class="plan-theme">
                  <span class="theme-label">主题：</span>{{ plan.plan_json.theme }}
                </div>
                <div v-if="plan.plan_json.key_principles?.length" class="plan-principles">
                  <span class="principles-label">核心原则：</span>
                  <div class="principles-tags">
                    <el-tag v-for="p in plan.plan_json.key_principles" :key="p" type="success" effect="light" size="small">
                      {{ p }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无养生计划" :image-size="60">
            <el-button type="primary" @click="$router.push('/wellness')">制定养生计划</el-button>
          </el-empty>
        </el-card>
      </div>

      <!-- 快捷操作 -->
      <div class="bento-card section-card span-2">
        <el-card shadow="never">
          <template #header>
            <span class="section-title">⚡ 快捷操作</span>
          </template>
          <div class="quick-actions">
            <div class="action-item" @click="$router.push('/consult')">
              <div class="action-icon">🩺</div>
              <div class="action-label">开始问诊</div>
            </div>
            <div class="action-item" @click="$router.push('/consult/tongue')">
              <div class="action-icon">👅</div>
              <div class="action-label">舌象分析</div>
            </div>
            <div class="action-item" @click="$router.push('/wellness')">
              <div class="action-icon">🌿</div>
              <div class="action-label">养生计划</div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 问诊详情对话框 -->
    <el-dialog v-model="consultDialogVisible" title="问诊详情" width="600px">
      <div v-if="selectedConsult" class="detail-content">
        <div class="detail-section">
          <div class="section-label">主诉</div>
          <div class="section-value">{{ selectedConsult.chief_complaint || '未记录' }}</div>
        </div>
        <div class="detail-section">
          <div class="section-label">辨证结果</div>
          <el-tag type="primary" size="large">{{ selectedConsult.primary_syndrome || '未完成' }}</el-tag>
        </div>
        <div v-if="selectedConsult.symptoms?.length" class="detail-section">
          <div class="section-label">症状</div>
          <div class="symptom-tags">
            <el-tag v-for="s in selectedConsult.symptoms" :key="s" type="info" effect="light">{{ s }}</el-tag>
          </div>
        </div>
        <div class="detail-section">
          <div class="section-label">问诊时间</div>
          <div class="section-value">{{ formatDate(selectedConsult.create_time || selectedConsult.created_at) }}</div>
        </div>
        <div v-if="selectedConsult.has_report" class="detail-actions">
          <el-button type="primary" @click="goToConsultReport(selectedConsult)">
            查看问诊报告
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 舌象详情对话框 -->
    <el-dialog v-model="tongueDialogVisible" title="舌象分析详情" width="500px">
      <div v-if="selectedTongue" class="detail-content">
        <div class="detail-section">
          <div class="section-label">舌象特征</div>
          <div class="feature-grid">
            <div class="feature-item">
              <span class="feature-label">舌色</span>
              <el-tag :type="selectedTongue.tongue_color ? 'danger' : 'info'" size="small">
                {{ selectedTongue.tongue_color || '未检测' }}
              </el-tag>
            </div>
            <div class="feature-item">
              <span class="feature-label">苔色</span>
              <el-tag :type="selectedTongue.tongue_coating ? 'warning' : 'info'" size="small">
                {{ selectedTongue.tongue_coating || '未检测' }}
              </el-tag>
            </div>
            <div class="feature-item">
              <span class="feature-label">苔厚薄</span>
              <el-tag type="info" size="small">{{ selectedTongue.coating_thickness || '未检测' }}</el-tag>
            </div>
            <div class="feature-item">
              <span class="feature-label">舌形</span>
              <el-tag type="success" size="small">{{ selectedTongue.tongue_shape || '未检测' }}</el-tag>
            </div>
          </div>
        </div>
        <div class="detail-section">
          <div class="section-label">分析时间</div>
          <div class="section-value">{{ formatDate(selectedTongue.created_at) }}</div>
        </div>
      </div>
    </el-dialog>

    <!-- 养生计划详情对话框 -->
    <el-dialog v-model="wellnessDialogVisible" title="养生计划详情" width="600px">
      <div v-if="selectedWellness" class="detail-content">
        <div class="detail-section">
          <div class="section-label">体质类型</div>
          <el-tag type="success" size="large">{{ selectedWellness.constitution }}</el-tag>
        </div>
        <div v-if="selectedWellness.source_syndrome" class="detail-section">
          <div class="section-label">参考证型</div>
          <div class="section-value">{{ selectedWellness.source_syndrome }}</div>
        </div>
        <div class="detail-section">
          <div class="section-label">创建时间</div>
          <div class="section-value">{{ formatDate(selectedWellness.create_time) }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { authApi } from '@/api'
import dayjs from 'dayjs'

const router = useRouter()

// 数据
const consultRecords = ref<any[]>([])
const tongueRecords = ref<any[]>([])
const wellnessPlans = ref<any[]>([])
const checkinStats = ref({
  total_days: 0,
  streak: 0,
  avg_completion: 0,
  this_week: 0,
})

// 对话框
const consultDialogVisible = ref(false)
const tongueDialogVisible = ref(false)
const wellnessDialogVisible = ref(false)

// 展开状态
const expandedTongue = ref<string | null>(null)
const expandedWellness = ref<string | null>(null)

// 选中的记录
const selectedConsult = ref<any>(null)
const selectedTongue = ref<any>(null)
const selectedWellness = ref<any>(null)

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

// 加载数据 - 使用综合档案API
const loadData = async () => {
  try {
    // 使用统一的档案API
    const res = await authApi.getArchives()
    // 处理问诊记录
    consultRecords.value = res.consult_records || []
    
    // 处理舌象档案（需要解析analysis_json中的observation）
    tongueRecords.value = (res.tongue_archives || []).map((archive: any) => {
      try {
        // 解析analysis_json（它应该是uploadTongueImage返回的完整对象）
        const analysis = typeof archive.analysis_json === 'string' 
          ? JSON.parse(archive.analysis_json) 
          : archive.analysis_json || {}
        
        // 从analysis中提取observation（这是实际的舌象数据）
        const observation = analysis.observation || {}
        
        return {
          session_id: archive.session_id,
          tongue_color: observation.tongue_color || '',
          tongue_coating: observation.tongue_coating || '',
          coating_thickness: observation.coating_thickness || '',
          tongue_shape: observation.tongue_shape || '',
          diagnosis: observation.diagnosis || null,
          image_features: observation.image_features || [],
          created_at: archive.create_time,
        }
      } catch (e) {
        console.warn('解析舌象档案失败:', e, archive)
        // 返回基本信息，避免整个数组因单条记录失败而为空
        return {
          session_id: archive.session_id || '',
          tongue_color: '',
          tongue_coating: '',
          coating_thickness: '',
          tongue_shape: '',
          diagnosis: null,
          image_features: [],
          created_at: archive.create_time || '',
        }
      }
    })
    
    // 处理养生计划档案
    wellnessPlans.value = res.wellness_archives || []
    
    // 计算打卡统计（从本地存储）
    calculateCheckinStats()
    
  } catch (err) {
    console.error('加档案数据失败:', err)
    // 即使API失败，也尝试从本地存储加载养生计划
    try {
      const planData = localStorage.getItem('tcm_wellness_plan')
      if (planData) {
        const plan = JSON.parse(planData)
        wellnessPlans.value = [{
          id: 'local',
          constitution: plan.constitution,
          source_syndrome: '',
          create_time: new Date().toISOString(),
          plan_json: plan,
        }]
      }
    } catch {
      wellnessPlans.value = []
    }
    consultRecords.value = []
    tongueRecords.value = []
    calculateCheckinStats()
  }
}

// 计算打卡统计 - 同时检查访客和用户的打卡记录
const calculateCheckinStats = () => {
  try {
    // 获取当前用户ID - 使用与 wellness/Index.vue 相同的逻辑
    let userId = 'anonymous'
    
    // 从JWT token中解析用户ID
    const token = localStorage.getItem('token')
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        userId = String(payload.user_id || payload.sub || 'anonymous')
      } catch {
        // ignore
      }
    }
    
    // 合并访客和用户的打卡记录
    const allRecords: Record<string, any> = {}
    
    // 1. 先加载访客的打卡记录（匿名）
    try {
      const guestData = localStorage.getItem('tcm_checkin_records_anonymous')
      if (guestData) {
        const guestRecords = JSON.parse(guestData)
        Object.assign(allRecords, guestRecords)
      }
    } catch {
      // ignore
    }
    
    // 2. 再加载当前用户的打卡记录（可能会覆盖访客记录中的同一天）
    if (userId !== 'anonymous') {
      const CHECKIN_STORAGE_KEY = `tcm_checkin_records_${userId}`
      const checkinData = localStorage.getItem(CHECKIN_STORAGE_KEY)
      if (checkinData) {
        const userRecords = JSON.parse(checkinData)
        Object.assign(allRecords, userRecords)
      }
    }
    
    // 3. 计算统计数据
    const dates = Object.keys(allRecords)
    
    checkinStats.value.total_days = dates.length
    
    // 计算连续打卡天数
    let streak = 0
    const today = dayjs().format('YYYY-MM-DD')
    let currentDate = today
    while (dates.includes(currentDate)) {
      streak++
      currentDate = dayjs(currentDate).subtract(1, 'day').format('YYYY-MM-DD')
    }
    checkinStats.value.streak = streak
    
    // 计算平均完成率（completion_rate 已经是百分比 0-100）
    const completionRates = Object.values(allRecords).map((r: any) => r.completion_rate || 0)
    checkinStats.value.avg_completion = completionRates.length 
      ? Math.round(completionRates.reduce((a: number, b: number) => a + b, 0) / completionRates.length)
      : 0
    
    // 计算本周打卡数
    const weekStart = dayjs().startOf('week').format('YYYY-MM-DD')
    checkinStats.value.this_week = dates.filter(d => d >= weekStart).length
  } catch {
    // ignore
  }
}

// 查看问诊详情
const viewConsultDetail = (record: any) => {
  if (record.has_report) {
    goToConsultReport(record)
    return
  }
  selectedConsult.value = record
  consultDialogVisible.value = true
}

const goToConsultReport = (record: any) => {
  if (!record?.session_id) {
    ElMessage.warning('该问诊记录缺少会话ID，无法查看报告')
    return
  }
  consultDialogVisible.value = false
  router.push({ path: '/consult/report', query: { session_id: record.session_id } })
}

// 切换舌象展开状态
const toggleTongueExpand = (sessionId: string) => {
  expandedTongue.value = expandedTongue.value === sessionId ? null : sessionId
}

// 切换养生计划展开状态
const toggleWellnessExpand = (id: string) => {
  expandedWellness.value = expandedWellness.value === id ? null : id
}

// 查看舌象详情
const viewTongueDetail = (tongue: any) => {
  selectedTongue.value = tongue
  tongueDialogVisible.value = true
}

// 查看养生计划详情
const viewWellnessDetail = (plan: any) => {
  selectedWellness.value = plan
  wellnessDialogVisible.value = true
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.profile-page {
  min-height: 100vh;
  background-color: var(--tcm-bg-color, #f4f6f8);
  color: var(--tcm-text-primary, #333);
  padding: 32px;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

.bento-header {
  margin-bottom: 32px;
}

.gradient-text {
  margin: 0 0 12px;
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--tcm-accent-color, #4facfe) 0%, #00f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-desc {
  font-size: 16px;
  color: var(--tcm-text-regular, #666);
  font-weight: 500;
}

.bento-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

@media (max-width: 1024px) {
  .bento-grid {
    grid-template-columns: 1fr;
  }
}

.span-2 {
  grid-column: span 2;
}

@media (max-width: 1024px) {
  .span-2 {
    grid-column: span 1;
  }
}

.overview-bento {
  grid-column: 1 / -1;
}

.bento-card {
  border-radius: 32px;
  transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease;
}

.bento-card:hover {
  transform: translateY(-4px) scale(1.01);
}

.bento-card:hover :deep(.el-card) {
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.08) !important;
}

:deep(.el-card) {
  border-radius: 32px !important;
  border: none !important;
  background: var(--tcm-card-bg, #ffffff) !important;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04) !important;
  height: 100%;
}

:deep(.el-card__body) {
  padding: 32px !important;
}

:deep(.el-card__header) {
  border-bottom: none !important;
  padding: 32px 32px 0 32px !important;
}

.overview-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  .overview-icon { font-size: 32px; }
  .overview-title { font-size: 20px; font-weight: 700; color: var(--tcm-accent-color, #4facfe); }
}

.overview-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 24px;
}

.stat-item {
  text-align: center;
  padding: 32px;
  background: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.1) 100%);
  border-radius: 24px;
  backdrop-filter: blur(10px);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.2), 0 4px 20px rgba(0,0,0,0.02);
}

.gradient-value {
  font-size: 3rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--tcm-text-primary, #111) 0%, #555 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 12px;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--tcm-text-regular, #666);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 600;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .section-title {
    font-size: 20px;
    font-weight: 700;
    color: var(--tcm-text-primary);
  }
  .section-count {
    font-size: 14px;
    color: var(--tcm-accent-color);
    background: rgba(0,0,0,0.03);
    padding: 6px 16px;
    border-radius: 20px;
    font-weight: 600;
  }
}

.records-list, .tongue-list, .wellness-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px;
}

.record-item, .tongue-item, .wellness-item {
  padding: 20px;
  background: var(--tcm-bg-color, #f9fafb);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
  
  &:hover {
    transform: translateX(6px);
    background: var(--tcm-card-bg, #fff);
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  }
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 24px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px;
  background: var(--tcm-bg-color, #f9fafb);
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  border: none;

  &:hover {
    transform: translateY(-8px);
    background: var(--tcm-card-bg, #fff);
    box-shadow: 0 12px 30px rgba(0,0,0,0.08);
  }

  .action-icon {
    font-size: 42px;
    transition: transform 0.3s;
  }
  &:hover .action-icon {
    transform: scale(1.1);
  }

  .action-label {
    font-size: 16px;
    color: var(--tcm-text-primary);
    font-weight: 600;
  }
}

/* Base styles for list inner elements */
.record-item { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.record-main { min-width: 0; flex: 1; }
.record-main .record-complaint { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
.record-main .record-time { font-size: 13px; color: var(--tcm-text-regular); }
.record-tags {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
  flex: 0 0 auto;
}
.detail-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
}
.tongue-header { display: flex; justify-content: space-between; align-items: center; }
.tongue-features { display: flex; gap: 8px; flex-wrap: wrap; }
.tongue-detail { margin-top: 16px; padding-top: 16px; border-top: 1px dashed rgba(0,0,0,0.1); }
.wellness-header { display: flex; justify-content: space-between; align-items: center; }
.wellness-main { display: flex; align-items: center; gap: 12px; }
.wellness-detail { margin-top: 16px; padding-top: 16px; border-top: 1px dashed rgba(0,0,0,0.1); }

:deep(.el-dialog) {
  border-radius: 24px !important;
  border: none;
  box-shadow: 0 20px 60px rgba(0,0,0,0.1) !important;
}
</style>
