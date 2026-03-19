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
    <el-dialog v-model="dialogVisible" title="生成养生计划" width="440px" :close-on-click-modal="false">
      <el-form :model="planForm" label-width="80px">
        <el-form-item label="体质类型">
          <el-select v-model="planForm.constitution" placeholder="请选择体质" style="width: 100%">
            <el-option
              v-for="c in constitutions"
              :key="c.value"
              :label="c.label"
              :value="c.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="计划周期">
          <el-radio-group v-model="planForm.cycle_days">
            <el-radio :label="7">7天</el-radio>
            <el-radio :label="14">14天</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="参考问诊">
          <el-input v-model="planForm.syndrome" placeholder="主证型（选填，如：气虚血瘀证）" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="generatePlan">生成计划</el-button>
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
          <div class="summary-theme">
            <div class="theme-label">本周主题</div>
            <div class="theme-text">{{ currentPlan.theme }}</div>
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
            <div class="section-title">✅ 今日打卡清单</div>
            <div class="checklist">
              <el-checkbox
                v-for="item in todayPlan.checklist"
                :key="item"
                v-model="checklistState[selectedDay + ':' + item]"
              >
                {{ item }}
              </el-checkbox>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Sunny, Plus, Calendar, Clock, CircleCheckFilled, Check, Memo
} from '@element-plus/icons-vue'
import { consultApi, type WellnessPlan } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()

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
  syndrome: '',
})

const currentPlan = ref<WellnessPlan | null>(null)
const selectedDay = ref('')
const checkedDays = ref<Set<string>>(new Set())
const checklistState = ref<Record<string, boolean>>({})

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

const PLAN_STORAGE_KEY = 'tcm_wellness_plan'

const loadPlanFromStorage = () => {
  try {
    const raw = localStorage.getItem(PLAN_STORAGE_KEY)
    if (raw) {
      currentPlan.value = JSON.parse(raw)
      if (currentPlan.value?.daily_plans?.length) {
        selectedDay.value = currentPlan.value.daily_plans[0].date
      }
    }
  } catch {
    currentPlan.value = null
  }
}

const savePlanToStorage = (plan: WellnessPlan) => {
  localStorage.setItem(PLAN_STORAGE_KEY, JSON.stringify(plan))
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

const submitCheckin = async () => {
  if (!todayPlan.value) return

  const completedItems = todayPlan.value.checklist.filter(
    item => checklistState.value[selectedDay.value + ':' + item]
  )

  checkingIn.value = true
  try {
    await consultApi.wellnessCheckin({
      date: selectedDay.value,
      constitution: currentPlan.value!.constitution,
      completed_items: completedItems,
      energy_level: 3,
      sleep_quality: 3,
      mood_score: 3,
    })
    checkedDays.value.add(selectedDay.value)
    ElMessage.success('打卡成功！继续坚持 💪')
  } catch (err: any) {
    ElMessage.error('打卡失败：' + (err?.response?.data?.error || err?.message || '未知错误'))
  } finally {
    checkingIn.value = false
  }
}

onMounted(() => {
  loadPlanFromStorage()
  // Pre-fill from route query (e.g., from report page)
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
  background: #f5f7fb;
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

      &:hover { border-color: $primary; color: $primary; }
      &.active { background: $primary; color: #fff; border-color: $primary; }
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
      }

      .checkin-btn { width: 100%; }
    }
  }
}

/* ─── Weekly notes ─────────────────────────────────── */
.weekly-notes-card {
  border-radius: 12px;

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
</style>
