<template>
  <div class="profile-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">
        <el-icon><User /></el-icon>
        个人档案
      </h2>
      <div class="header-desc">管理您的健康数据与养生记录</div>
    </div>

    <!-- 健康概览卡片 -->
    <el-card class="overview-card" shadow="never">
      <div class="overview-header">
        <div class="overview-icon">📊</div>
        <div class="overview-title">健康概览</div>
      </div>
      <div class="overview-stats">
        <div class="stat-item">
          <div class="stat-value">{{ checkinStats.total_days }}</div>
          <div class="stat-label">打卡天数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ checkinStats.streak }}</div>
          <div class="stat-label">连续打卡</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ checkinStats.avg_completion }}%</div>
          <div class="stat-label">平均完成率</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ checkinStats.this_week }}</div>
          <div class="stat-label">本周打卡</div>
        </div>
      </div>
    </el-card>

    <!-- 主要内容区 -->
    <el-row :gutter="20" class="main-content">
      <!-- 左侧：问诊记录 -->
      <el-col :xs="24" :md="12">
        <el-card class="section-card" shadow="never">
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
                <el-tag v-if="record.primary_syndrome" type="primary" size="small">
                  {{ record.primary_syndrome }}
                </el-tag>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无问诊记录" :image-size="60">
            <el-button type="primary" @click="$router.push('/consult')">开始问诊</el-button>
          </el-empty>
        </el-card>
      </el-col>

      <!-- 右侧：舌象档案 -->
      <el-col :xs="24" :md="12">
        <el-card class="section-card" shadow="never">
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
      </el-col>
    </el-row>

    <!-- 养生计划记录 -->
    <el-card class="section-card mt-20" shadow="never">
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

    <!-- 快捷操作 -->
    <el-card class="section-card mt-20" shadow="never">
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { authApi, consultApi } from '@/api'
import dayjs from 'dayjs'

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
    console.log('档案API响应:', res)
    console.log('响应对象的所有键:', Object.keys(res))
    
    // 打印调试信息（如果存在）
    if (res.debug) {
      console.log('后端调试信息:', res.debug)
    } else {
      console.log('没有找到debug字段')
    }
    
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
    
    console.log('加载的数据:', {
      consultRecords: consultRecords.value.length,
      tongueRecords: tongueRecords.value.length,
      wellnessPlans: wellnessPlans.value.length
    })
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
    
    console.log('[DEBUG] 打卡记录:', allRecords)
    console.log('[DEBUG] 打卡日期:', dates)
    
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
    const completionRates = Object.values(allRecords).map((r: any) => {
      console.log('[DEBUG] 单条记录:', r, 'completion_rate:', r.completion_rate)
      return r.completion_rate || 0
    })
    console.log('[DEBUG] 所有完成率:', completionRates)
    checkinStats.value.avg_completion = completionRates.length 
      ? Math.round(completionRates.reduce((a: number, b: number) => a + b, 0) / completionRates.length)
      : 0
    console.log('[DEBUG] 平均完成率:', checkinStats.value.avg_completion)
    
    // 计算本周打卡数
    const weekStart = dayjs().startOf('week').format('YYYY-MM-DD')
    checkinStats.value.this_week = dates.filter(d => d >= weekStart).length
  } catch {
    // ignore
  }
}

// 查看问诊详情
const viewConsultDetail = (record: any) => {
  selectedConsult.value = record
  consultDialogVisible.value = true
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
  background: linear-gradient(180deg, #f7fcff 0%, #f4fbf6 100%);
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;

  .page-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 8px;
    font-size: 24px;
    color: #1a1a2e;
  }

  .header-desc {
    font-size: 14px;
    color: #888;
  }
}

/* ─── 健康概览卡片 ──────────────────────────────────── */
.overview-card {
  border-radius: 12px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
  border: 1px solid #b3d9ff;

  .overview-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;

    .overview-icon { font-size: 32px; }
    .overview-title { font-size: 18px; font-weight: 600; color: #1677ff; }
  }

  .overview-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;

    .stat-item {
      text-align: center;
      padding: 16px;
      background: rgba(255, 255, 255, 0.8);
      border-radius: 8px;

      .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #1677ff;
        margin-bottom: 4px;
      }

      .stat-label {
        font-size: 13px;
        color: #666;
      }
    }
  }
}

/* ─── 主要内容区 ──────────────────────────────────── */
.main-content {
  margin-bottom: 20px;
}

.section-card {
  border-radius: 12px;
  margin-bottom: 16px;

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: #333;
    }

    .section-count {
      font-size: 13px;
      color: #888;
    }
  }
}

.mt-20 {
  margin-top: 20px;
}

/* ─── 问诊记录 ──────────────────────────────────── */
.records-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;

  &:hover {
    border-color: #1677ff;
    background: #f0f7ff;
  }

  .record-main {
    flex: 1;

    .record-complaint {
      font-size: 14px;
      color: #333;
      margin-bottom: 4px;
    }

    .record-time {
      font-size: 12px;
      color: #999;
    }
  }

  .record-tags {
    margin-left: 12px;
  }
}

/* ─── 舌象档案 ──────────────────────────────────── */
.tongue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.tongue-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;

  &:hover {
    border-color: #1677ff;
    background: #f0f7ff;
  }

  .tongue-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .tongue-features {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }

    .tongue-time {
      font-size: 12px;
      color: #999;
      white-space: nowrap;
    }
  }

  .tongue-detail {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #e8eaf0;

    .diagnosis-summary {
      font-size: 13px;
      color: #333;
      line-height: 1.6;
      margin-bottom: 8px;
    }

    .diagnosis-suggestions {
      .suggestions-title {
        font-size: 12px;
        color: #666;
        margin-bottom: 4px;
      }

      ul {
        margin: 0;
        padding-left: 16px;

        li {
          font-size: 12px;
          color: #666;
          margin: 4px 0;
        }
      }
    }
  }
}

/* ─── 养生计划 ──────────────────────────────────── */
.wellness-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.wellness-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;

  &:hover {
    border-color: #1677ff;
    background: #f0f7ff;
  }

  .wellness-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .wellness-main {
      display: flex;
      align-items: center;
      gap: 8px;

      .wellness-source {
        font-size: 12px;
        color: #666;
      }
    }

    .wellness-time {
      font-size: 12px;
      color: #999;
      white-space: nowrap;
    }
  }

  .wellness-detail {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #e8eaf0;

    .plan-theme {
      font-size: 13px;
      color: #333;
      margin-bottom: 8px;

      .theme-label {
        color: #666;
      }
    }

    .plan-principles {
      .principles-label {
        font-size: 12px;
        color: #666;
        margin-bottom: 4px;
        display: block;
      }

      .principles-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }
    }
  }
}

/* ─── 快捷入口 ──────────────────────────────────── */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;

  .action-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 20px;
    background: #fafafa;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid transparent;

    &:hover {
      border-color: #1677ff;
      background: #f0f7ff;
      transform: translateY(-2px);
    }

    .action-icon {
      font-size: 32px;
    }

    .action-label {
      font-size: 14px;
      color: #333;
    }
  }
}

/* ─── 详情对话框 ──────────────────────────────────── */
.detail-content {
  .detail-section {
    margin-bottom: 16px;

    .section-label {
      font-size: 13px;
      color: #888;
      margin-bottom: 8px;
    }

    .section-value {
      font-size: 15px;
      color: #333;
    }
  }

  .feature-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;

    .feature-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: #fafafa;
      border-radius: 6px;

      .feature-label {
        font-size: 13px;
        color: #666;
      }
    }
  }

  .symptom-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

@media (max-width: 768px) {
  .overview-stats {
    grid-template-columns: repeat(2, 1fr) !important;
  }

  .quick-actions {
    grid-template-columns: repeat(2, 1fr) !important;
  }

  .tongue-list {
    grid-template-columns: 1fr !important;
  }
}
</style>
