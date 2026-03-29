<template>
  <div class="wellness-page">
    <!-- 页面头 -->
    <div class="page-header">
      <h2 class="page-title">
        <el-icon><Sunny /></el-icon>
        个性化养生管理
      </h2>
      <el-button type="primary" @click="dialogVisible = true" :icon="Plus">
        生成新计划
      </el-button>
    </div>

    <!-- 体质选择对话框 -->
    <el-dialog v-model="dialogVisible" title="生成养生计划" width="560px" :close-on-click-modal="false">
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
              :label="r.date_label + ' - ' + r.primary_syndrome"
              :value="r.session_id"
            >
              <div class="report-option">
                <span class="report-date">{{ r.date_label }}</span>
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
            <el-radio :label="7">7天</el-radio>
            <el-radio :label="14">14天</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="generatePlan">生成计划</el-button>
      </template>
    </el-dialog>

    <!-- 计划编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑微调养生计划" width="700px" :close-on-click-modal="false">
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
            <el-button v-else size="small" @click="showNewPrincipleInput">+ 添加原则</el-button>
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
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEditedPlan">保存修改</el-button>
      </template>
    </el-dialog>

    <!-- 当前计划 -->
    <div v-if="currentPlan" class="plan-content">
      <!-- 计划摘要 -->
      <el-card class="plan-summary" shadow="never">
        <div class="summary-header">
          <div class="summary-left">
            <el-tag type="primary" size="large" effect="plain">
              {{ currentPlan.constitution }}
            </el-tag>
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
            <el-button type="primary" plain size="small" @click="openEditDialog">
              <el-icon><Edit /></el-icon>
              编辑微调
            </el-button>
          </div>
        </div>
        <div class="key-principles">
          <div class="principles-title">核心原则</div>
          <div class="principles-tags">
            <el-tag
              v-for="p in currentPlan.key_principles"
              :key="p"
              type="success"
              effect="light"
            >{{ p }}</el-tag>
          </div>
        </div>
      </el-card>

      <!-- 每日计划（时间轴） -->
      <el-card shadow="never" class="daily-plans-card">
        <template #header>
          <div class="card-title">
            <el-icon><Clock /></el-icon>
            每日计划
          </div>
        </template>

        <el-scrollbar>
          <div class="days-nav">
            <div
              v-for="day in currentPlan.daily_plans"
              :key="day.date"
              class="day-tab"
              :class="{ active: selectedDay === day.date, checked: checkedDays.has(day.date) }"
              @click="selectedDay = day.date"
            >
              <div class="day-label">{{ formatDayLabel(day.date) }}</div>
              <el-icon v-if="checkedDays.has(day.date)" class="day-check"><CircleCheckFilled /></el-icon>
            </div>
          </div>
        </el-scrollbar>

        <!-- 当日详情 -->
        <div v-if="todayPlan" class="day-detail">
          <div class="detail-grid">
            <div class="detail-item" v-for="item in todayItems" :key="item.icon">
              <div class="detail-icon">{{ item.icon }}</div>
              <div class="detail-body">
                <div class="detail-label">{{ item.label }}</div>
                <div class="detail-value">{{ item.value }}</div>
              </div>
            </div>
          </div>

          <!-- 穴位保健 -->
          <div v-if="todayPlan.acupoint_care" class="acupoint-section">
            <div class="section-title">💆 穴位保健</div>
            <p>{{ todayPlan.acupoint_care }}</p>
          </div>

          <!-- 代茶饮 -->
          <div v-if="todayPlan.tea_recommendation" class="tea-section">
            <div class="section-title">🍵 代茶饮</div>
            <p>{{ todayPlan.tea_recommendation }}</p>
            <el-alert
              type="warning"
              :closable="false"
              title="请在执业中医师指导下使用"
              size="small"
            />
          </div>

          <!-- 打卡清单 -->
          <div class="checklist-section">
            <div class="section-title">今日打卡清单</div>
            <div class="checklist">
              <div
                v-for="item in todayPlan.checklist"
                :key="item"
                class="checklist-item"
                :class="{ checked: checklistState[selectedDay + ':' + item] }"
                @click="toggleChecklistItem(item)"
              >
                {{ item }}
              </div>
            </div>
            <el-button
              type="success"
              class="checkin-btn"
              @click="submitCheckin"
              :loading="checkingIn"
            >
              <el-icon><Check /></el-icon>
              提交打卡
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 周备注 -->
      <el-card shadow="never" class="weekly-notes-card">
        <template #header>
          <div class="card-title"><el-icon><Memo /></el-icon> 本周备注</div>
        </template>
        <p class="weekly-notes-text">{{ currentPlan.weekly_notes }}</p>
        <el-alert
          type="info"
          :closable="false"
          title="免责声明：以上建议仅供健康参考，不构成医疗建议。如有不适请及时就医。"
        />
      </el-card>
    </div>

    <!-- 无计划时的引导 -->
    <div v-else class="empty-state">
      <el-empty description="暂无养生计划">
        <template #image>
          <div class="empty-illustration">🌿</div>
        </template>
        <el-button type="primary" @click="dialogVisible = true">生成我的养生计划</el-button>
      </el-empty>

      <!-- 体质介绍 -->
      <el-card shadow="never" class="constitution-intro">
        <template #header>
          <span class="card-title">九种体质说明</span>
        </template>
        <el-row :gutter="12">
          <el-col :xs="12" :sm="8" :md="6" v-for="c in constitutions" :key="c.value">
            <div class="constitution-card" @click="quickGenerate(c.value)">
              <div class="const-emoji">{{ c.emoji }}</div>
              <div class="const-name">{{ c.label }}</div>
              <div class="const-desc">{{ c.desc }}</div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Sunny, Plus, Calendar, Clock, CircleCheckFilled, Check, Memo, Edit, InfoFilled
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
const userReports = ref<Array<{ session_id: string; chief_complaint: string; primary_syndrome: string; symptoms: string[]; created_at: string; summary: string }>>([])
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
$border-color: #e8eaf0;
$primary: #1677ff;

.wellness-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f7fcff 0%, #f4fbf6 100%);
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;

  .page-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-size: 20px;
    color: #1a1a2e;
  }
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
}

/* ─── Plan summary ─────────────────────────────────── */
.plan-summary {
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid #ddebe1;

  .summary-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .summary-left {
      display: flex;
      flex-direction: column;
      gap: 8px;

      .summary-dates {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        color: #666;
      }
    }

    .summary-theme {
      text-align: right;

      .theme-label { font-size: 12px; color: #888; margin-bottom: 4px; }
      .theme-text { font-size: 16px; font-weight: 600; color: $primary; }
    }
  }

  .key-principles {
    .principles-title { font-size: 13px; color: #666; margin-bottom: 8px; }
    .principles-tags { display: flex; flex-wrap: wrap; gap: 6px; }
  }
}

/* ─── Daily plans ──────────────────────────────────── */
.daily-plans-card {
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid #ddebe1;

  .days-nav {
    display: flex;
    gap: 8px;
    padding: 4px 0 12px;

    .day-tab {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      padding: 8px 14px;
      border-radius: 8px;
      border: 1px solid $border-color;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s;

      &:hover { border-color: #2f9776; color: #2f9776; }
      &.active { background: linear-gradient(135deg, #2f9776, #2b84a2); color: #fff; border-color: #2f9776; }
      &.checked { border-color: #52c41a; }

      .day-label { font-size: 12px; }
      .day-check { color: #52c41a; font-size: 14px; }
    }
  }

  .day-detail {
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 12px;
      margin-bottom: 16px;

      .detail-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 12px;
        background: #fafafa;
        border-radius: 8px;
        border: 1px solid $border-color;

        .detail-icon { font-size: 20px; flex-shrink: 0; }
        .detail-label { font-size: 12px; color: #888; margin-bottom: 4px; }
        .detail-value { font-size: 13px; color: #333; line-height: 1.5; }
      }
    }

    .acupoint-section, .tea-section {
      padding: 16px;
      background: #f0f9ff;
      border-radius: 8px;
      margin-bottom: 12px;

      p { margin: 6px 0 8px; font-size: 14px; color: #333; line-height: 1.7; }
    }

    .section-title { font-size: 14px; font-weight: 600; margin-bottom: 6px; }

    .checklist-section {
      margin-top: 16px;
      padding: 16px;
      background: #fafffe;
      border-radius: 8px;
      border: 1px solid #d9f7be;

      .section-title { margin-bottom: 12px; }

      .checklist {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 16px;

        .checklist-item {
          display: flex;
          align-items: center;
          padding: 12px 16px;
          background: #fff;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          border: 2px solid #e8eaf0;
          font-size: 14px;
          color: #333;

          &:hover {
            border-color: #52c41a;
            background: #f6ffed;
          }

          &.checked {
            background: #f6ffed;
            border-color: #52c41a;
            color: #52c41a;
          }
        }
      }

      .checkin-btn { width: 100%; }
    }
  }
}

/* ─── Weekly notes ─────────────────────────────────── */
.weekly-notes-card {
  border-radius: 12px;
  border: 1px solid #ddebe1;

  .weekly-notes-text {
    font-size: 14px;
    color: #333;
    line-height: 1.8;
    margin-bottom: 16px;
  }
}

/* ─── Empty state ──────────────────────────────────── */
.empty-state {
  .empty-illustration { font-size: 72px; text-align: center; }

  .constitution-intro {
    margin-top: 24px;
    border-radius: 12px;

    .constitution-card {
      padding: 16px;
      border-radius: 12px;
      border: 1px solid $border-color;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;
      margin-bottom: 12px;

      &:hover {
        border-color: $primary;
        box-shadow: 0 4px 12px rgba(22, 119, 255, 0.1);
        transform: translateY(-2px);
      }

      .const-emoji { font-size: 28px; margin-bottom: 6px; }
      .const-name { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
      .const-desc { font-size: 11px; color: #888; }
    }
  }
}

/* ─── Report option ──────────────────────────────────── */
.report-option {
  display: flex;
  flex-direction: column;
  gap: 2px;

  .report-syndrome {
    font-size: 13px;
    font-weight: 600;
    color: #333;
  }

  .report-complaint {
    font-size: 12px;
    color: #888;
  }
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* ─── Summary right ──────────────────────────────────── */
.summary-right {
  display: flex;
  align-items: center;
  gap: 16px;

  .summary-theme {
    text-align: right;

    .theme-label { font-size: 12px; color: #888; margin-bottom: 4px; }
    .theme-text { font-size: 16px; font-weight: 600; color: $primary; }
  }
}

/* ─── Principles editor ──────────────────────────────── */
.principles-editor {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

/* ─── 推荐体质提示 ──────────────────────────────── */
.recommend-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: #1677ff;
  background: #f0f7ff;
  padding: 8px 12px;
  border-radius: 6px;

  .recommend-tag {
    cursor: pointer;
    margin-left: 4px;
    
    &:hover {
      opacity: 0.8;
    }
  }
}
</style>
