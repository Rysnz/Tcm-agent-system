<template>
  <div class="wellness-page bento-layout">
    <!-- 页面头 -->
    <div class="page-header bento-header">
      <h2 class="page-title gradient-text">
        <el-icon><Sunny /></el-icon>
        个性化养生管理
      </h2>
      <el-button type="primary" class="round-btn glass-btn" @click="dialogVisible = true" :icon="Plus">
        生成新计划
      </el-button>
    </div>

    <!-- 体质选择对话框 -->
    <el-dialog v-model="dialogVisible" title="生成养生计划" width="560px" :close-on-click-modal="false" class="glass-dialog">
      <el-form :model="planForm" label-width="100px">
        <el-form-item label="参考问诊报告">
          <el-select 
            v-model="planForm.selectedReport" 
            placeholder="选择问诊报告（推荐）" 
            style="width: 100%"
            clearable
            @change="onReportChange"
          >
            <el-option
              v-for="r in userReports"
              :key="r.session_id"
              :label="formatReportOptionLabel(r)"
              :value="r.session_id"
            >
              <div class="report-option">
                <span class="report-date">{{ formatReportDate(r) }}</span>
                <span class="report-syndrome">{{ r.primary_syndrome }}</span>
                <span class="report-complaint">{{ r.chief_complaint }}</span>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">根据问诊报告可生成更精准的养生方案</div>
        </el-form-item>
        <el-form-item label="体质类型">
          <el-select v-model="planForm.constitution" placeholder="请选择体质" style="width: 100%">
            <el-option
              v-for="c in constitutions"
              :key="c.value"
              :label="c.label"
              :value="c.value"
            />
          </el-select>
          <div v-if="recommendedConstitution" class="recommend-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>根据问诊报告，推荐选择：<el-tag type="primary" size="small" @click="applyRecommendation" class="recommend-tag">{{ recommendedConstitution }}</el-tag></span>
          </div>
        </el-form-item>
        <el-form-item label="计划周期">
          <el-radio-group v-model="planForm.cycle_days">
            <el-radio :value="7">7天</el-radio>
            <el-radio :value="14">14天</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" class="round-btn">取消</el-button>
        <el-button type="primary" class="round-btn" :loading="generating" @click="generatePlan">生成计划</el-button>
      </template>
    </el-dialog>

    <!-- 计划编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑微调养生计划" width="700px" :close-on-click-modal="false" class="glass-dialog">
      <el-form :model="editForm" label-width="100px" v-if="editForm">
        <el-form-item label="本周主题">
          <el-input v-model="editForm.theme" placeholder="请输入本周主题" />
        </el-form-item>
        <el-form-item label="核心原则">
          <div class="principles-editor">
            <el-tag
              v-for="(p, idx) in editForm.key_principles"
              :key="idx"
              closable
              @close="removePrinciple(idx)"
              type="success"
              effect="light"
              class="bento-tag-sm"
            >{{ p }}</el-tag>
            <el-input
              v-if="newPrincipleVisible"
              ref="newPrincipleInputRef"
              v-model="newPrinciple"
              size="small"
              style="width: 120px;"
              @keyup.enter="addPrinciple"
              @blur="addPrinciple"
            />
            <el-button v-else size="small" @click="showNewPrincipleInput" class="round-btn-sm">+ 添加原则</el-button>
          </div>
        </el-form-item>
        <el-form-item label="周备注">
          <el-input
            v-model="editForm.weekly_notes"
            type="textarea"
            :rows="3"
            placeholder="请输入本周备注"
          />
        </el-form-item>
        <el-divider content-position="left">每日计划详情</el-divider>
        <el-form-item label="选择日期">
          <el-select v-model="selectedEditDay" placeholder="请选择要编辑的日期" style="width: 100%">
            <el-option
              v-for="day in editForm.daily_plans"
              :key="day.date"
              :label="formatDayLabel(day.date)"
              :value="day.date"
            />
          </el-select>
        </el-form-item>
        <template v-if="selectedEditDayPlan">
          <el-form-item label="睡眠建议">
            <el-input v-model="selectedEditDayPlan.sleep_advice" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="晨间作息">
            <el-input v-model="selectedEditDayPlan.morning_routine" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="早餐建议">
            <el-input v-model="selectedEditDayPlan.diet_breakfast" />
          </el-form-item>
          <el-form-item label="午餐建议">
            <el-input v-model="selectedEditDayPlan.diet_lunch" />
          </el-form-item>
          <el-form-item label="晚餐建议">
            <el-input v-model="selectedEditDayPlan.diet_dinner" />
          </el-form-item>
          <el-form-item label="运动建议">
            <el-input v-model="selectedEditDayPlan.exercise" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="情志调节">
            <el-input v-model="selectedEditDayPlan.emotion_adjustment" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="穴位保健">
            <el-input v-model="selectedEditDayPlan.acupoint_care" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="代茶饮">
            <el-input v-model="selectedEditDayPlan.tea_recommendation" type="textarea" :rows="2" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false" class="round-btn">取消</el-button>
        <el-button type="primary" class="round-btn" @click="saveEditedPlan">保存修改</el-button>
      </template>
    </el-dialog>

    <!-- 当前计划 -->
    <div v-if="currentPlan" class="modern-bento-grid">
      <!-- 计划摘要 -->
      <div class="bento-tile plan-summary-tile col-span-12">
        <div class="summary-header">
          <div class="summary-left">
            <div class="constitution-badge">
              {{ currentPlan.constitution }}
            </div>
            <div class="summary-dates">
              <el-icon><Calendar /></el-icon>
              {{ currentPlan.start_date }} ~ {{ currentPlan.end_date }}
            </div>
          </div>
          <div class="summary-right">
            <div class="summary-theme">
              <div class="theme-label">本周主题</div>
              <div class="theme-text">{{ currentPlan.theme }}</div>
            </div>
            <el-button type="primary" plain class="round-btn action-btn" @click="openEditDialog">
              <el-icon><Edit /></el-icon>
              编辑微调
            </el-button>
          </div>
        </div>
        <div class="key-principles">
          <div class="principles-title">核心原则</div>
          <div class="principles-tags">
            <span
              v-for="p in currentPlan.key_principles"
              :key="p"
              class="principle-pill"
            >{{ p }}</span>
          </div>
        </div>
      </div>

      <!-- 每日计划（时间轴） -->
      <div class="bento-tile daily-plans-tile col-span-12 lg-col-span-8">
        <div class="bento-tile-header">
          <div class="card-title gradient-title">
            <el-icon><Clock /></el-icon>
            每日计划
          </div>
        </div>

        <el-scrollbar class="days-nav-scrollbar">
          <div class="days-nav">
            <div
              v-for="day in currentPlan.daily_plans"
              :key="day.date"
              class="day-tab"
              :class="{ active: selectedDay === day.date, checked: checkedDays.has(day.date) }"
              @click="selectedDay = day.date"
            >
              <div class="day-label">{{ formatDayLabel(day.date) }}</div>
              <div class="day-indicator" v-if="checkedDays.has(day.date)"></div>
            </div>
          </div>
        </el-scrollbar>

        <!-- 当日详情 -->
        <div v-if="todayPlan" class="day-detail">
          <div class="detail-masonry">
            <div class="masonry-item" v-for="item in todayItems" :key="item.icon">
              <div class="detail-icon">{{ item.icon }}</div>
              <div class="detail-body">
                <div class="detail-label">{{ item.label }}</div>
                <div class="detail-value">{{ item.value }}</div>
              </div>
            </div>
          </div>

          <div class="extra-cares-grid">
            <!-- 穴位保健 -->
            <div v-if="todayPlan.acupoint_care" class="care-tile">
              <div class="section-title">💆 穴位保健</div>
              <p>{{ todayPlan.acupoint_care }}</p>
            </div>

            <!-- 代茶饮 -->
            <div v-if="todayPlan.tea_recommendation" class="care-tile">
              <div class="section-title">🍵 代茶饮</div>
              <p>{{ todayPlan.tea_recommendation }}</p>
              <div class="bento-warning-alert">
                <el-icon><Warning /></el-icon>
                请在执业中医师指导下使用
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 侧边栏：打卡清单 & 周备注 -->
      <div class="side-col col-span-12 lg-col-span-4">
        <!-- 打卡清单 -->
        <div v-if="todayPlan" class="bento-tile checklist-tile">
          <div class="section-title">今日打卡</div>
          <div class="checklist">
            <div
              v-for="item in todayPlan.checklist"
              :key="item"
              class="checklist-item"
              :class="{ checked: checklistState[selectedDay + ':' + item] }"
              @click="toggleChecklistItem(item)"
            >
              <div class="check-circle"></div>
              <span class="check-text">{{ item }}</span>
            </div>
          </div>
          <el-button
            class="checkin-btn"
            @click="submitCheckin"
            :loading="checkingIn"
            :class="{ 'btn-completed': todayPlan.checklist.every(item => checklistState[selectedDay + ':' + item]) }"
          >
            <el-icon><Check /></el-icon>
            提交打卡
          </el-button>
        </div>

        <!-- 周备注 -->
        <div class="bento-tile weekly-notes-tile">
          <div class="bento-tile-header">
            <div class="card-title"><el-icon><Memo /></el-icon> 本周备注</div>
          </div>
          <p class="weekly-notes-text">{{ currentPlan.weekly_notes }}</p>
          <div class="bento-info-alert">
            免责声明：以上建议仅供健康参考，不构成医疗建议。如有不适请及时就医。
          </div>
        </div>
      </div>
    </div>

    <!-- 无计划时的引导 -->
    <div v-else class="empty-state modern-bento-grid">
      <div class="bento-tile col-span-12 empty-bento">
        <div class="empty-content">
          <div class="empty-illustration">🌿</div>
          <h3>暂无养生计划</h3>
          <p>生成专属您的个性化体质调理方案</p>
          <el-button type="primary" class="round-btn generate-btn" @click="dialogVisible = true">生成我的养生计划</el-button>
        </div>
      </div>

      <!-- 9种体质 不对称网格便当盒 -->
      <div class="col-span-12 constitution-intro-section">
        <h3 class="section-heading">九种体质说明</h3>
        <div class="asymmetrical-bento-grid">
          <div 
            class="constitution-tile" 
            v-for="(c, index) in constitutions" 
            :key="c.value" 
            @click="quickGenerate(c.value)"
            :class="'tile-style-' + (index % 4)"
          >
            <div class="tile-top">
              <span class="const-emoji">{{ c.emoji }}</span>
              <div class="action-icon">
                <el-icon><ArrowRight /></el-icon>
              </div>
            </div>
            <div class="tile-bottom">
              <div class="const-name">{{ c.label }}</div>
              <div class="const-desc">{{ c.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Sunny, Plus, Calendar, Clock, CircleCheckFilled, Check, Memo, Edit, InfoFilled, ArrowRight, Warning
} from '@element-plus/icons-vue'
import { consultApi, authApi, type WellnessPlan } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()

// 获取当前用户ID
const getCurrentUserId = () => {
  const token = localStorage.getItem('token')
  if (!token) return 'anonymous'
  try {
    // 从JWT token中解析用户ID
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.user_id || payload.sub || 'anonymous'
  } catch {
    return 'anonymous'
  }
}

const constitutions = [
  { value: '平和质', label: '平和质', emoji: '🌟', desc: '体质均衡，身体健康' },
  { value: '气虚质', label: '气虚质', emoji: '😴', desc: '容易疲乏，气短自汗' },
  { value: '阳虚质', label: '阳虚质', emoji: '🥶', desc: '怕冷，手足不温' },
  { value: '阴虚质', label: '阴虚质', emoji: '🔥', desc: '手足心热，易口干' },
  { value: '痰湿质', label: '痰湿质', emoji: '💧', desc: '形体肥胖，腹部松软' },
  { value: '湿热质', label: '湿热质', emoji: '☀️', desc: '面垢油光，易生痤疮' },
  { value: '血瘀质', label: '血瘀质', emoji: '🫁', desc: '肤色晦暗，易有淤斑' },
  { value: '气郁质', label: '气郁质', emoji: '😔', desc: '情绪不稳，容易焦虑' },
  { value: '特禀质', label: '特禀质', emoji: '🌸', desc: '过敏体质，适应力差' },
]

const dialogVisible = ref(false)
const generating = ref(false)
const checkingIn = ref(false)

const planForm = ref({
  constitution: '',
  cycle_days: 7,
  selectedReport: '',  // 选择的问诊报告ID
  syndrome: '',  // 主证型（从问诊报告自动填充）
})

const currentPlan = ref<WellnessPlan | null>(null)
const selectedDay = ref('')
const checkedDays = ref<Set<string>>(new Set())
const checklistState = ref<Record<string, boolean>>({})
const isLoggedIn = ref(!!localStorage.getItem('token'))
type UserReport = {
  session_id: string
  chief_complaint: string
  primary_syndrome: string
  symptoms: string[]
  created_at: string
  consult_time?: string
  report_generated_at?: string
  updated_at?: string
  date_label?: string
  summary: string
}
const userReports = ref<UserReport[]>([])
const recommendedConstitution = ref('')  // 推荐的体质类型

// 编辑功能相关
const editDialogVisible = ref(false)
const editForm = ref<any>(null)
const selectedEditDay = ref('')
const newPrincipleVisible = ref(false)
const newPrinciple = ref('')
const newPrincipleInputRef = ref()

const selectedEditDayPlan = computed(() => {
  if (!editForm.value || !selectedEditDay.value) return null
  return editForm.value.daily_plans.find((d: any) => d.date === selectedEditDay.value) || null
})

const todayPlan = computed(() => {
  if (!currentPlan.value || !selectedDay.value) return null
  return currentPlan.value.daily_plans.find(d => d.date === selectedDay.value) || null
})

const todayItems = computed(() => {
  if (!todayPlan.value) return []
  return [
    { icon: '💤', label: '睡眠建议', value: todayPlan.value.sleep_advice },
    { icon: '🌅', label: '晨间作息', value: todayPlan.value.morning_routine },
    { icon: '🥣', label: '早餐建议', value: todayPlan.value.diet_breakfast },
    { icon: '🍱', label: '午餐建议', value: todayPlan.value.diet_lunch },
    { icon: '🌙', label: '晚餐建议', value: todayPlan.value.diet_dinner },
    { icon: '🏃', label: '运动建议', value: todayPlan.value.exercise },
    { icon: '🧘', label: '情志调节', value: todayPlan.value.emotion_adjustment },
  ].filter(i => i.value)
})

const formatDayLabel = (dateStr: string) => {
  const d = dayjs(dateStr)
  const today = dayjs().format('YYYY-MM-DD')
  if (dateStr === today) return '今天'
  return d.format('MM/DD')
}

const formatReportDate = (report: UserReport) => {
  if (report.date_label) return report.date_label
  const time = report.consult_time || report.created_at
  const parsed = dayjs(time)
  return parsed.isValid() ? parsed.format('MM-DD HH:mm') : '时间未知'
}

const formatReportOptionLabel = (report: UserReport) => {
  return `${formatReportDate(report)} - ${report.primary_syndrome}`
}

const PLAN_STORAGE_KEY = `tcm_wellness_plan_${getCurrentUserId()}`

const loadPlanFromStorage = () => {
  try {
    const raw = localStorage.getItem(PLAN_STORAGE_KEY)
    if (raw) {
      currentPlan.value = JSON.parse(raw)
      if (currentPlan.value?.daily_plans?.length) {
        const today = dayjs().format('YYYY-MM-DD')
        // Default to today's plan if it exists
        const todayPlan = currentPlan.value.daily_plans.find((d: any) => d.date === today)
        selectedDay.value = todayPlan ? todayPlan.date : currentPlan.value.daily_plans[0].date
      }
    }
  } catch {
    currentPlan.value = null
  }
}

const savePlanToStorage = (plan: WellnessPlan) => {
  localStorage.setItem(PLAN_STORAGE_KEY, JSON.stringify(plan))
}

// Load checked items from storage
const loadCheckedItemsFromStorage = () => {
  try {
    const userId = getCurrentUserId()
    const raw = localStorage.getItem(`tcm_checklist_state_${userId}`)
    if (raw) {
      checklistState.value = JSON.parse(raw)
    }
    const checkedRaw = localStorage.getItem(`tcm_checked_days_${userId}`)
    if (checkedRaw) {
      checkedDays.value = new Set(JSON.parse(checkedRaw))
    }
  } catch {
    // ignore
  }
}

// Save checked items to storage
const saveCheckedItemsToStorage = () => {
  const userId = getCurrentUserId()
  localStorage.setItem(`tcm_checklist_state_${userId}`, JSON.stringify(checklistState.value))
  localStorage.setItem(`tcm_checked_days_${userId}`, JSON.stringify([...checkedDays.value]))
}

// 保存打卡记录到本地存储（用于健康概览统计）
const saveCheckinToStorage = (date: string, completedItems: string[], totalItems: number) => {
  const userId = getCurrentUserId()
  const storageKey = userId === 'anonymous' 
    ? 'tcm_checkin_records_anonymous' 
    : `tcm_checkin_records_${userId}`
  
  try {
    const existing = localStorage.getItem(storageKey)
    const records = existing ? JSON.parse(existing) : {}
    
    records[date] = {
      completed_items: completedItems,
      total_items: totalItems,
      completed_count: completedItems.length,
      completion_rate: totalItems > 0 ? Math.round((completedItems.length / totalItems) * 100) : 0,
    }
    
    localStorage.setItem(storageKey, JSON.stringify(records))
  } catch (err) {
    console.warn('保存打卡记录失败:', err)
  }
}

// 加载用户的问诊报告列表
const loadUserReports = async () => {
  try {
    const res = await consultApi.getWellnessReports()
    userReports.value = res.reports || []
  } catch (err) {
    console.error('加载问诊报告失败:', err)
  }
}

// 选择问诊报告后自动填充体质和证型
const onReportChange = (sessionId: string) => {
  if (!sessionId) {
    planForm.value.syndrome = ''
    recommendedConstitution.value = ''
    return
  }
  const report = userReports.value.find(r => r.session_id === sessionId)
  if (report) {
    planForm.value.syndrome = report.primary_syndrome
    // 根据证型推断体质
    const syndromeToConstitution: Record<string, string> = {
      '气虚证': '气虚质',
      '阳虚证': '阳虚质',
      '阴虚证': '阴虚质',
      '痰湿证': '痰湿质',
      '湿热证': '湿热质',
      '血瘀证': '血瘀质',
      '气郁证': '气郁质',
      '特禀证': '特禀质',
      // 兼容其他常见证型名称
      '气阴两虚证': '气虚质',
      '肝郁气滞证': '气郁质',
      '脾胃虚弱证': '气虚质',
      '肝肾阴虚证': '阴虚质',
      '脾肾阳虚证': '阳虚质',
      '寒凝经脉证': '阳虚质',
      '肝阳上亢证': '阴虚质',
      '阴虚火旺证': '阴虚质',
      '肾阳虚证': '阳虚质',
      '肾阴虚证': '阴虚质',
      '脾虚证': '气虚质',
      '肝虚证': '气虚质',
      // 新增证型
      '肝郁化火证': '气郁质',
      '肝火上炎证': '气郁质',
      '心火上炎证': '阴虚质',
      '胃火炽盛证': '湿热质',
      '肺气虚证': '气虚质',
      '心脾气虚证': '气虚质',
      '心肾不交证': '阴虚质',
      '脾虚湿盛证': '痰湿质',
      '湿热蕴脾证': '湿热质',
      '寒湿困脾证': '痰湿质',
      '肝胆湿热证': '湿热质',
      '瘀血阻络证': '血瘀质',
      '气血两虚证': '气虚质',
      '阳虚水泛证': '阳虚质',
    }
    const inferredConstitution = syndromeToConstitution[report.primary_syndrome]
    if (inferredConstitution) {
      recommendedConstitution.value = inferredConstitution
      // 不自动填充，让用户点击推荐标签来应用
    } else {
      recommendedConstitution.value = ''
    }
  }
}

// 应用推荐的体质
const applyRecommendation = () => {
  if (recommendedConstitution.value) {
    planForm.value.constitution = recommendedConstitution.value
    ElMessage.success(`已应用推荐体质：${recommendedConstitution.value}`)
  }
}

const generatePlan = async () => {
  if (!planForm.value.constitution) {
    ElMessage.warning('请先选择体质类型')
    return
  }
  generating.value = true
  try {
    const feedback = planForm.value.syndrome
      ? { syndrome: planForm.value.syndrome }
      : undefined
    const res = await consultApi.generateWellnessPlan(
      planForm.value.constitution,
      planForm.value.cycle_days,
      feedback,
    )
    currentPlan.value = res.plan
    if (res.plan.daily_plans.length) {
      selectedDay.value = res.plan.daily_plans[0].date
    }
    savePlanToStorage(res.plan)
    if (isLoggedIn.value) {
      try {
        await authApi.saveWellnessArchive({
          constitution: planForm.value.constitution,
          cycle_days: planForm.value.cycle_days,
          source_syndrome: planForm.value.syndrome,
          plan_json: res.plan,
        })
      } catch {
        // ignore archive save failure
      }
    }
    dialogVisible.value = false
    ElMessage.success('养生计划已生成！')
  } catch (err: any) {
    ElMessage.error('生成失败：' + (err?.response?.data?.error || err?.message || '未知错误'))
  } finally {
    generating.value = false
  }
}

const quickGenerate = async (constitution: string) => {
  planForm.value.constitution = constitution
  await generatePlan()
}

// 打开编辑对话框
const openEditDialog = () => {
  if (!currentPlan.value) return
  // 深拷贝当前计划
  editForm.value = JSON.parse(JSON.stringify(currentPlan.value))
  selectedEditDay.value = editForm.value.daily_plans[0]?.date || ''
  editDialogVisible.value = true
}

// 添加核心原则
const addPrinciple = () => {
  if (newPrinciple.value.trim()) {
    editForm.value.key_principles.push(newPrinciple.value.trim())
    newPrinciple.value = ''
  }
  newPrincipleVisible.value = false
}

// 显示新原则输入框
const showNewPrincipleInput = () => {
  newPrincipleVisible.value = true
  nextTick(() => {
    newPrincipleInputRef.value?.focus()
  })
}

// 删除核心原则
const removePrinciple = (idx: number) => {
  editForm.value.key_principles.splice(idx, 1)
}

// 保存编辑后的计划
const saveEditedPlan = () => {
  if (!editForm.value) return
  currentPlan.value = editForm.value
  savePlanToStorage(editForm.value)
  editDialogVisible.value = false
  ElMessage.success('计划已更新！')
}

// 切换打卡项状态
const toggleChecklistItem = (item: string) => {
  const key = selectedDay.value + ':' + item
  checklistState.value[key] = !checklistState.value[key]
  saveCheckedItemsToStorage()
}

const submitCheckin = async () => {
  if (!todayPlan.value) return

  console.log('[DEBUG] selectedDay:', selectedDay.value)
  console.log('[DEBUG] checklistState:', checklistState.value)
  console.log('[DEBUG] todayPlan.checklist:', todayPlan.value.checklist)

  const completedItems = todayPlan.value.checklist.filter(
    item => checklistState.value[selectedDay.value + ':' + item]
  )
  
  console.log('[DEBUG] completedItems:', completedItems)

  // 检查是否有勾选的项目
  if (completedItems.length === 0) {
    ElMessage.warning('请先勾选已完成的项目再打卡')
    return
  }

  checkingIn.value = true
  try {
    // 先保存到本地存储
    saveCheckinToStorage(selectedDay.value, completedItems, todayPlan.value.checklist.length)
    saveCheckedItemsToStorage()
    checkedDays.value.add(selectedDay.value)
    
    // 尝试保存到后端（允许失败）
    try {
      await consultApi.wellnessCheckin({
        date: selectedDay.value,
        constitution: currentPlan.value!.constitution,
        completed_items: completedItems,
        energy_level: 3,
        sleep_quality: 3,
        mood_score: 3,
      })
    } catch (apiErr) {
      // 忽略 API 错误，不影响本地打卡
      console.warn('保存到后端失败，但本地打卡已保存:', apiErr)
    }
    
    // 如果已登录，同时保存到档案
    if (isLoggedIn.value) {
      try {
        await authApi.saveWellnessCheckin({
          date: selectedDay.value,
          constitution: currentPlan.value!.constitution,
          completed_items: completedItems,
          total_items: todayPlan.value.checklist.length,
          energy_level: 3,
          sleep_quality: 3,
          mood_score: 3,
        })
      } catch (archiveErr) {
        // 忽略档案保存失败，不影响打卡功能
        console.warn('保存打卡档案失败:', archiveErr)
      }
    }
    
    ElMessage.success('打卡成功！继续坚持 💪')
  } catch (err: any) {
    ElMessage.error('打卡失败：' + (err?.response?.data?.error || err?.message || '未知错误'))
  } finally {
    checkingIn.value = false
  }
}



onMounted(() => {
  loadPlanFromStorage()
  loadCheckedItemsFromStorage()
  loadUserReports()
  if (!isLoggedIn.value) {
    ElMessage.info('当前为访客模式，登录后可保存养生档案')
  }
  const syndrome = route.query.syndrome as string
  if (syndrome) {
    planForm.value.syndrome = syndrome
  }
})
</script>

<style scoped lang="scss">
.wellness-page {
  min-height: 100vh;
  background: var(--tcm-bg-color);
  padding: 30px;
  color: var(--tcm-text-primary);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.bento-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.gradient-text {
  margin: 0;
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--tcm-text-primary) 0%, var(--tcm-accent-color) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: flex;
  align-items: center;
  gap: 12px;
}

.gradient-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--tcm-text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}

.glass-btn {
  background: color-mix(in srgb, var(--tcm-accent-color) 15%, transparent);
  border: 1px solid color-mix(in srgb, var(--tcm-accent-color) 30%, transparent);
  color: var(--tcm-accent-color);
  backdrop-filter: blur(10px);
  &:hover {
    background: var(--tcm-accent-color);
    color: var(--tcm-bg-color);
    transform: scale(1.05);
    box-shadow: 0 10px 20px var(--tcm-shadow);
  }
}

.round-btn {
  border-radius: 20px;
  padding: 10px 24px;
  font-weight: 600;
  transition: all 0.3s ease;
}

/* ─── 统一 Bento Tile 基础 ─────────────────────────────────── */
.modern-bento-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 24px;
}

.col-span-12 { grid-column: span 12; }
.lg-col-span-8 { @media (min-width: 1024px) { grid-column: span 8; } }
.lg-col-span-4 { @media (min-width: 1024px) { grid-column: span 4; } }

.bento-tile {
  background: var(--tcm-card-bg);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: 32px;
  border: 1px solid var(--tcm-border-color);
  box-shadow: 0 20px 40px var(--tcm-shadow), inset 0 1px 0 var(--tcm-border-color);
  padding: 32px;
  transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 30px 60px var(--tcm-shadow), inset 0 1px 0 var(--tcm-border-color);
    border-color: var(--tcm-border-color);
  }
}

.bento-tile-header {
  margin-bottom: 24px;
  .card-title {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 20px;
    font-weight: 700;
    color: var(--tcm-text-primary);
  }
}

/* ─── Plan summary ─────────────────────────────────── */
.plan-summary-tile {
  background: linear-gradient(135deg, color-mix(in srgb, var(--tcm-accent-color) 10%, transparent), var(--tcm-card-bg));
  
  .summary-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;

    .summary-left {
      display: flex;
      flex-direction: column;
      gap: 16px;

      .constitution-badge {
        display: inline-block;
        background: color-mix(in srgb, var(--tcm-accent-color) 20%, transparent);
        color: var(--tcm-accent-color);
        border: 1px solid color-mix(in srgb, var(--tcm-accent-color) 30%, transparent);
        padding: 8px 20px;
        border-radius: 20px;
        font-size: 18px;
        font-weight: 700;
        width: fit-content;
      }

      .summary-dates {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 15px;
        color: var(--tcm-text-regular);
        font-weight: 500;
      }
    }

    .summary-right {
      display: flex;
      align-items: flex-end;
      gap: 32px;
      .summary-theme {
        text-align: right;
        .theme-label { font-size: 14px; color: var(--tcm-text-regular); margin-bottom: 8px; font-weight: 600; }
        .theme-text { font-size: 28px; font-weight: 800; color: var(--tcm-text-primary); }
      }
      .action-btn {
        background: var(--tcm-page-bg); border: 1px solid var(--tcm-border-color); color: var(--tcm-text-primary);
        &:hover { background: var(--tcm-border-color); transform: scale(1.05); }
      }
    }
  }

  .key-principles {
    .principles-title { font-size: 15px; color: var(--tcm-text-regular); margin-bottom: 12px; font-weight: 600; }
    .principles-tags { 
      display: flex; flex-wrap: wrap; gap: 12px; 
      .principle-pill {
        background: var(--tcm-page-bg);
        border: 1px solid var(--tcm-border-color);
        padding: 6px 16px;
        border-radius: 16px;
        font-size: 14px;
        color: var(--tcm-text-regular);
        font-weight: 500;
      }
    }
  }
}

/* ─── Daily plans ──────────────────────────────────── */
.daily-plans-tile {
  min-height: 500px;
}

.days-nav-scrollbar {
  margin: 0 -32px 24px -32px;
  padding: 0 32px;
  
  .days-nav {
    display: flex;
    gap: 16px;
    padding-bottom: 16px;
    
    .day-tab {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 12px 24px;
      border-radius: 24px;
      background: var(--tcm-page-bg);
      border: 1px solid var(--tcm-border-color);
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.3s;
      color: var(--tcm-text-regular);
      font-weight: 600;

      &:hover { background: var(--tcm-border-color); transform: translateY(-2px); }
      &.active { background: var(--tcm-accent-color); color: var(--tcm-bg-color); box-shadow: 0 10px 20px var(--tcm-shadow); border-color: var(--tcm-accent-color); }
      &.checked .day-label { color: var(--tcm-accent-color); }
      &.active.checked .day-label { color: var(--tcm-bg-color); }

      .day-label { font-size: 15px; z-index: 2; position: relative; }
      
      .day-indicator {
        position: absolute;
        top: 6px;
        right: 6px;
        width: 6px;
        height: 6px;
        background: var(--tcm-accent-color);
        border-radius: 50%;
        box-shadow: 0 0 5px var(--tcm-accent-color);
      }
      &.active .day-indicator { background: var(--tcm-bg-color); box-shadow: 0 0 5px var(--tcm-bg-color); }
    }
  }
}

.day-detail {
  .detail-masonry {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 24px;

    .masonry-item {
      display: flex;
      align-items: flex-start;
      gap: 16px;
      padding: 20px;
      background: var(--tcm-page-bg);
      border-radius: 20px;
      border: 1px solid var(--tcm-border-color);
      transition: all 0.3s;

      &:hover { transform: translateY(-4px); background: var(--tcm-border-color); }

      .detail-icon { font-size: 28px; flex-shrink: 0; filter: drop-shadow(0 0 10px var(--tcm-shadow)); }
      .detail-label { font-size: 13px; color: var(--tcm-text-regular); margin-bottom: 6px; font-weight: 600; }
      .detail-value { font-size: 15px; color: var(--tcm-text-primary); line-height: 1.5; font-weight: 500; }
    }
  }

  .extra-cares-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;

    .care-tile {
      padding: 24px;
      background: var(--tcm-page-bg);
      border-radius: 24px;
      border: 1px solid var(--tcm-border-color);

      .section-title { font-size: 16px; font-weight: 700; color: var(--tcm-text-primary); margin-bottom: 12px; }
      p { font-size: 15px; color: var(--tcm-text-regular); line-height: 1.6; margin: 0 0 16px; }

      .bento-warning-alert {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(245, 158, 11, 0.1);
        color: #fbbf24;
        padding: 8px 16px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid rgba(245, 158, 11, 0.2);
      }
    }
  }
}

/* ─── Side Col (Checklist & Notes) ─────────────────── */
.side-col {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.checklist-tile {
  background: linear-gradient(135deg, var(--tcm-card-bg), color-mix(in srgb, var(--tcm-accent-color) 5%, transparent));
  flex: 1;

  .section-title { font-size: 20px; font-weight: 700; color: var(--tcm-text-primary); margin-bottom: 24px; }

  .checklist {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 24px;

    .checklist-item {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px 20px;
      background: var(--tcm-page-bg);
      border-radius: 16px;
      cursor: pointer;
      transition: all 0.3s;
      border: 1px solid var(--tcm-border-color);

      &:hover { background: var(--tcm-border-color); transform: translateX(4px); }

      .check-circle {
        width: 24px; height: 24px; border-radius: 50%;
        border: 2px solid var(--tcm-border-color);
        display: flex; align-items: center; justify-content: center;
        transition: all 0.3s;
      }
      .check-text { font-size: 15px; color: var(--tcm-text-primary); font-weight: 500; transition: all 0.3s; }

      &.checked {
        background: color-mix(in srgb, var(--tcm-accent-color) 15%, transparent);
        border-color: color-mix(in srgb, var(--tcm-accent-color) 30%, transparent);
        .check-circle {
          background: var(--tcm-accent-color); border-color: var(--tcm-accent-color);
          &::after { content: ''; width: 6px; height: 10px; border: solid var(--tcm-bg-color); border-width: 0 2px 2px 0; transform: rotate(45deg) translateY(-2px); }
        }
        .check-text { color: var(--tcm-accent-color); text-decoration: line-through; opacity: 0.8; }
      }
    }
  }

  .checkin-btn {
    width: 100%; height: 56px; border-radius: 20px; font-size: 16px; font-weight: 600;
    background: var(--tcm-page-bg); border: 1px solid var(--tcm-border-color); color: var(--tcm-text-primary);
    &:hover { background: var(--tcm-border-color); }
    &.btn-completed { background: var(--tcm-accent-color); border-color: var(--tcm-accent-color); color: var(--tcm-bg-color); box-shadow: 0 10px 25px var(--tcm-shadow); }
  }
}

.weekly-notes-tile {
  .weekly-notes-text {
    font-size: 15px; color: var(--tcm-text-regular); line-height: 1.6; margin: 0 0 20px;
    padding: 20px; background: var(--tcm-page-bg); border-radius: 20px;
  }
  .bento-info-alert {
    font-size: 13px; color: var(--tcm-text-regular); padding: 12px 16px;
    background: var(--tcm-page-bg); border-radius: 12px; border-left: 3px solid var(--tcm-text-regular);
  }
}

/* ─── Empty state ──────────────────────────────────── */
.empty-bento {
  padding: 60px 0;
  display: flex; justify-content: center; align-items: center; text-align: center;
  
  .empty-illustration { font-size: 80px; margin-bottom: 24px; filter: drop-shadow(0 10px 20px var(--tcm-shadow)); }
  h3 { font-size: 24px; color: var(--tcm-text-primary); margin: 0 0 12px; }
  p { font-size: 16px; color: var(--tcm-text-regular); margin: 0 0 32px; }
  .generate-btn { font-size: 16px; padding: 12px 32px; height: auto; }
}

/* ─── Asymmetrical Bento Grid ──────────────────────────────────── */
.constitution-intro-section {
  .section-heading { font-size: 24px; color: var(--tcm-text-primary); margin: 40px 0 24px; font-weight: 700; text-align: center; }
}

.asymmetrical-bento-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  grid-auto-rows: 200px;
  gap: 20px;

  .constitution-tile {
    background: var(--tcm-card-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--tcm-border-color);
    border-radius: 32px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;

    &::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
      background: radial-gradient(circle at top right, var(--tcm-border-color), transparent 70%);
      opacity: 0; transition: opacity 0.4s;
    }

    &:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 20px 40px var(--tcm-shadow);
      border-color: var(--tcm-border-color);
      &::before { opacity: 1; }
      .action-icon { background: var(--tcm-text-primary); color: var(--tcm-bg-color); transform: translateX(4px); }
    }

    .tile-top {
      display: flex; justify-content: space-between; align-items: flex-start;
      .const-emoji { font-size: 40px; filter: drop-shadow(0 4px 8px var(--tcm-shadow)); }
      .action-icon {
        width: 36px; height: 36px; border-radius: 50%; background: var(--tcm-page-bg);
        display: flex; align-items: center; justify-content: center; color: var(--tcm-text-primary);
        transition: all 0.3s;
      }
    }

    .tile-bottom {
      .const-name { font-size: 20px; font-weight: 700; color: var(--tcm-text-primary); margin-bottom: 8px; }
      .const-desc { font-size: 14px; color: var(--tcm-text-regular); line-height: 1.5; }
    }
  }

  /* 非对称跨列 */
  .constitution-tile:nth-child(1) { grid-column: span 2; grid-row: span 1; background: linear-gradient(135deg, color-mix(in srgb, var(--tcm-accent-color) 15%, transparent), var(--tcm-card-bg)); }
  .constitution-tile:nth-child(4) { grid-row: span 2; }
  .constitution-tile:nth-child(7) { grid-column: span 2; }
  
  @media (max-width: 768px) {
    .constitution-tile { grid-column: span 1 !important; grid-row: span 1 !important; }
  }
}

/* ─── Modal/Dialog Overrides ──────────────────────────────────── */
:deep(.glass-dialog) {
  background: var(--tcm-card-bg) !important;
  backdrop-filter: blur(40px);
  border: 1px solid var(--tcm-border-color);
  border-radius: 32px;
  box-shadow: 0 40px 80px var(--tcm-shadow) !important;
  
  .el-dialog__title { color: var(--tcm-text-primary); font-weight: 700; font-size: 20px; }
  .el-form-item__label { color: var(--tcm-text-regular); font-weight: 600; }
  
  .el-input__wrapper, .el-textarea__inner { background: var(--tcm-page-bg); box-shadow: 0 0 0 1px var(--tcm-border-color) inset; color: var(--tcm-text-primary); }
  .el-input__wrapper:hover, .el-input__wrapper.is-focus { box-shadow: 0 0 0 1px var(--tcm-accent-color) inset; }
}

.report-option {
  display: flex; flex-direction: column; gap: 6px; padding: 8px 0;
  .report-syndrome { font-size: 15px; font-weight: 700; color: var(--tcm-accent-color); }
  .report-complaint { font-size: 13px; color: var(--tcm-text-regular); }
}
.form-tip { font-size: 13px; color: var(--tcm-text-regular); margin-top: 8px; }

@media (max-width: 1024px) {
  .summary-right { flex-direction: column; align-items: flex-end; gap: 16px !important; }
}
</style>
