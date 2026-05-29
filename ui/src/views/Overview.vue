<template>
  <div class="overview-container">
    <section class="hero-panel">
      <div class="monitor-controls">
        <div class="status-pill">
          <span class="status-dot"></span>
          <span>数据更新时间 {{ monitor.generatedAt || '--' }}</span>
        </div>
        <div class="range-controls">
          <el-select v-model="timeRange" placeholder="时间范围" class="range-select">
            <el-option label="过去7天" value="7" />
            <el-option label="过去30天" value="30" />
            <el-option label="过去90天" value="90" />
            <el-option label="过去半年" value="180" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <el-date-picker
            v-if="timeRange === 'custom'"
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            class="date-range"
          />
          <el-button :loading="loading" @click="loadStats">刷新</el-button>
        </div>
      </div>
    </section>

    <section class="metrics-grid">
      <div v-for="card in metricCards" :key="card.label" class="metric-card">
        <div class="metric-top">
          <span class="metric-label">{{ card.label }}</span>
          <span class="metric-note">{{ card.note }}</span>
        </div>
        <div class="metric-value">{{ card.value }}</div>
        <div class="metric-sub">{{ card.sub }}</div>
      </div>
    </section>

    <section class="charts-grid">
      <div v-for="chart in trendCharts" :key="chart.name" class="trend-card">
        <div class="trend-head">
          <div>
            <span class="trend-title">{{ chart.name }}</span>
            <span class="trend-range">{{ monitor.range?.label || '' }}</span>
          </div>
          <strong>{{ sumValues(chart.values) }}</strong>
        </div>
        <svg viewBox="0 0 320 120" class="sparkline" preserveAspectRatio="none">
          <path class="grid-path" d="M0 30 H320 M0 60 H320 M0 90 H320" />
          <polyline
            :points="sparklinePoints(chart.values)"
            :stroke="chart.color"
            fill="none"
            stroke-width="4"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <circle
            v-for="(point, index) in sparklineCircles(chart.values)"
            :key="index"
            :cx="point.x"
            :cy="point.y"
            r="3.5"
            :fill="chart.color"
          />
        </svg>
        <div class="chart-dates">
          <span>{{ chart.dates?.[0] || '--' }}</span>
          <span>{{ chart.dates?.[chart.dates.length - 1] || '--' }}</span>
        </div>
      </div>
    </section>

    <section class="detail-grid">
      <div class="monitor-panel">
        <div class="panel-head">
          <h4>问诊阶段分布</h4>
          <span>{{ stats.sessionCount || 0 }} 个会话</span>
        </div>
        <div v-if="monitor.stageDistribution.length" class="bar-list">
          <div v-for="item in monitor.stageDistribution" :key="item.stage" class="bar-row">
            <div class="bar-meta">
              <span>{{ item.label }}</span>
              <strong>{{ item.count }}</strong>
            </div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${Math.max(item.percent, 4)}%` }"></div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无阶段数据" />
      </div>

      <div class="monitor-panel">
        <div class="panel-head">
          <h4>证型分布</h4>
          <span>{{ stats.reportCount || 0 }} 份报告</span>
        </div>
        <div v-if="monitor.syndromeDistribution.length" class="syndrome-list">
          <div v-for="item in monitor.syndromeDistribution" :key="item.name" class="syndrome-item">
            <div>
              <strong>{{ item.name }}</strong>
              <span>{{ item.percent }}%</span>
            </div>
            <small>{{ item.count }} 次</small>
          </div>
        </div>
        <el-empty v-else description="暂无证型数据" />
      </div>

      <div class="monitor-panel agent-panel">
        <div class="panel-head">
          <h4>Agent 执行质量</h4>
          <span>成功率 {{ stats.agentSuccessRate || 0 }}%</span>
        </div>
        <div v-if="monitor.agentPerformance.length" class="agent-table">
          <div class="agent-row agent-header">
            <span>Agent</span>
            <span>调用</span>
            <span>成功率</span>
            <span>均耗时</span>
          </div>
          <div v-for="agent in monitor.agentPerformance" :key="agent.agent" class="agent-row">
            <span>{{ agent.agent }}</span>
            <span>{{ agent.total }}</span>
            <span :class="{ danger: agent.successRate < 90 }">{{ agent.successRate }}%</span>
            <span>{{ formatDuration(agent.avgDurationMs) }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无 Agent 日志" />
      </div>

      <div class="monitor-panel">
        <div class="panel-head">
          <h4>最近异常</h4>
          <span>{{ monitor.recentErrors.length }} 条</span>
        </div>
        <div v-if="monitor.recentErrors.length" class="error-list">
          <div v-for="item in monitor.recentErrors" :key="`${item.agent}-${item.time}`" class="error-item">
            <div>
              <strong>{{ item.agent }}</strong>
              <span>{{ item.stage }} · {{ item.time }}</span>
            </div>
            <p>{{ item.message }}</p>
          </div>
        </div>
        <el-empty v-else description="近期无异常记录" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound } from '@element-plus/icons-vue'
import { applicationApi, type ChartItem, type StatsData, type StatsResponse } from '@/api'

const router = useRouter()

const appInfo = ref({
  name: '中医智能问诊系统',
  icon: '',
  desc: '',
})

const publicUrl = ref(`${window.location.origin}/consult`)
const loading = ref(false)
const timeRange = ref('7')
const dateRange = ref<[Date, Date] | []>([])

const stats = ref<StatsData>({
  registeredUserCount: 0,
  activeUserCount: 0,
  sessionCount: 0,
  completedSessionCount: 0,
  reportCount: 0,
  highRiskCount: 0,
  questionCount: 0,
  tokensCount: 0,
  agentCallCount: 0,
  agentSuccessRate: 0,
  avgAgentDurationMs: 0,
  avgQuestionsPerSession: 0,
})

const trendCharts = ref<ChartItem[]>([])
const monitor = ref<NonNullable<StatsResponse['monitor']>>({
  generatedAt: '',
  range: { start: '', end: '', label: '' },
  stageDistribution: [],
  syndromeDistribution: [],
  agentPerformance: [],
  recentErrors: [],
})

const metricCards = computed(() => [
  {
    label: '注册用户',
    value: formatNumber(stats.value.registeredUserCount || 0),
    note: '账户规模',
    sub: `活跃用户 ${formatNumber(stats.value.activeUserCount || 0)}`,
  },
  {
    label: '问诊会话',
    value: formatNumber(stats.value.sessionCount || 0),
    note: '所选周期',
    sub: `完成 ${formatNumber(stats.value.completedSessionCount || 0)} · 报告 ${formatNumber(stats.value.reportCount || 0)}`,
  },
  {
    label: '用户提问',
    value: formatNumber(stats.value.questionCount || 0),
    note: '问诊轮次',
    sub: `平均 ${stats.value.avgQuestionsPerSession || 0} 轮/会话`,
  },
  {
    label: '高风险提醒',
    value: formatNumber(stats.value.highRiskCount || 0),
    note: '安全监测',
    sub: stats.value.highRiskCount ? '演示时可说明转诊提示' : '当前周期未触发',
  },
  {
    label: 'Agent 调用',
    value: formatNumber(stats.value.agentCallCount || 0),
    note: '编排链路',
    sub: `成功率 ${stats.value.agentSuccessRate || 0}%`,
  },
  {
    label: '平均耗时',
    value: formatDuration(stats.value.avgAgentDurationMs || 0),
    note: 'Agent 执行',
    sub: `Token记录 ${formatNumber(stats.value.tokensCount || 0)}`,
  },
])

const formatNumber = (value: number) => new Intl.NumberFormat('zh-CN').format(value || 0)

const formatDuration = (ms: number) => {
  if (!ms) return '0ms'
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const formatDate = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const sumValues = (values: number[] = []) => values.reduce((sum, value) => sum + (Number(value) || 0), 0)

const normalizeValues = (values: number[] = []) => {
  const safeValues = values.length ? values : [0]
  const max = Math.max(...safeValues, 1)
  const min = Math.min(...safeValues, 0)
  const range = max - min || 1
  return safeValues.map((value, index) => {
    const x = safeValues.length === 1 ? 160 : (index / (safeValues.length - 1)) * 300 + 10
    const y = 104 - ((value - min) / range) * 88
    return { x, y }
  })
}

const sparklinePoints = (values: number[] = []) => normalizeValues(values).map((point) => `${point.x},${point.y}`).join(' ')
const sparklineCircles = (values: number[] = []) => normalizeValues(values)

const copyLink = () => {
  navigator.clipboard.writeText(publicUrl.value)
    .then(() => ElMessage.success('链接复制成功'))
    .catch(() => ElMessage.error('链接复制失败'))
}

const goToChat = () => {
  router.push('/consult')
}

const loadAppInfo = async () => {
  try {
    const applications = await applicationApi.getApplications()
    if (applications.length > 0) {
      const app = applications[0]
      appInfo.value = {
        name: app.name,
        icon: app.icon,
        desc: app.desc,
      }
    }
  } catch (error) {
    console.error('加载应用信息失败:', error)
  }
}

const loadStats = async () => {
  if (timeRange.value === 'custom' && (!Array.isArray(dateRange.value) || dateRange.value.length !== 2)) {
    return
  }

  loading.value = true
  try {
    const params: { timeRange?: string; startDate?: string; endDate?: string } = { timeRange: timeRange.value }
    if (timeRange.value === 'custom' && Array.isArray(dateRange.value) && dateRange.value.length === 2) {
      params.startDate = formatDate(dateRange.value[0])
      params.endDate = formatDate(dateRange.value[1])
    }

    const response = await applicationApi.getStats(params)
    stats.value = {
      ...stats.value,
      ...response.stats,
      activeUserCount: response.stats.activeUserCount ?? response.stats.userCount ?? 0,
    }
    trendCharts.value = response.charts || []
    monitor.value = response.monitor || monitor.value
  } catch (error) {
    console.error('加载监控数据失败:', error)
    ElMessage.error('加载监控数据失败')
  } finally {
    loading.value = false
  }
}

watch(timeRange, () => {
  if (timeRange.value !== 'custom') {
    loadStats()
  }
})

watch(dateRange, () => {
  if (timeRange.value === 'custom' && Array.isArray(dateRange.value) && dateRange.value.length === 2) {
    loadStats()
  }
})

onMounted(() => {
  loadAppInfo()
  loadStats()
})
</script>

<style scoped>
.overview-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  color: var(--tcm-text-primary);
}

.hero-panel,
.metric-card,
.trend-card,
.monitor-panel {
  background: color-mix(in srgb, var(--tcm-card-bg) 82%, transparent);
  border: 1px solid var(--tcm-border-color);
  box-shadow: 0 18px 40px color-mix(in srgb, var(--tcm-shadow) 85%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.hero-panel {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px;
  border-radius: 20px;
}

.app-summary {
  display: flex;
  align-items: center;
  gap: 22px;
  min-width: 0;
}

.app-icon-container {
  flex: 0 0 auto;
}

.app-icon,
.app-icon-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 18px;
}

.app-icon {
  object-fit: cover;
}

.app-icon-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  color: #fff;
  background: linear-gradient(135deg, var(--tcm-accent-color), #14b8a6);
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--tcm-accent-color);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.app-summary h3 {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
}

.app-desc {
  margin: 8px 0 14px;
  color: var(--tcm-text-regular);
  line-height: 1.6;
}

.public-link {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.public-link span {
  padding: 8px 12px;
  border-radius: 10px;
  color: var(--tcm-accent-color);
  background: color-mix(in srgb, var(--tcm-accent-color) 10%, transparent);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 13px;
}

.monitor-controls {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  color: var(--tcm-text-regular);
  background: color-mix(in srgb, var(--tcm-text-primary) 5%, transparent);
  font-size: 13px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 12px #22c55e;
}

.range-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.range-select {
  width: 160px;
}

.date-range {
  width: 280px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  min-height: 138px;
  padding: 20px;
  border-radius: 16px;
}

.metric-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.metric-label {
  color: var(--tcm-text-regular);
  font-size: 13px;
  font-weight: 700;
}

.metric-note {
  color: var(--tcm-accent-color);
  font-size: 12px;
}

.metric-value {
  margin-top: 20px;
  font-size: 32px;
  line-height: 1;
  font-weight: 800;
}

.metric-sub {
  margin-top: 12px;
  color: var(--tcm-text-regular);
  font-size: 13px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.trend-card {
  padding: 18px;
  border-radius: 16px;
  overflow: hidden;
}

.trend-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.trend-title {
  display: block;
  font-weight: 700;
}

.trend-range {
  display: block;
  margin-top: 4px;
  color: var(--tcm-text-regular);
  font-size: 12px;
}

.trend-head strong {
  font-size: 24px;
}

.sparkline {
  width: 100%;
  height: 120px;
}

.grid-path {
  stroke: color-mix(in srgb, var(--tcm-text-primary) 8%, transparent);
  stroke-width: 1;
}

.chart-dates {
  display: flex;
  justify-content: space-between;
  color: var(--tcm-text-regular);
  font-size: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.monitor-panel {
  min-height: 280px;
  padding: 22px;
  border-radius: 18px;
}

.agent-panel {
  grid-column: span 2;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-head h4 {
  margin: 0;
  font-size: 17px;
}

.panel-head span {
  color: var(--tcm-text-regular);
  font-size: 13px;
}

.bar-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bar-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.bar-track {
  height: 9px;
  overflow: hidden;
  border-radius: 999px;
  background: color-mix(in srgb, var(--tcm-text-primary) 8%, transparent);
}

.bar-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--tcm-accent-color), #14b8a6);
}

.syndrome-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.syndrome-item {
  padding: 14px;
  border: 1px solid var(--tcm-border-color);
  border-radius: 14px;
  background: color-mix(in srgb, var(--tcm-text-primary) 4%, transparent);
}

.syndrome-item div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.syndrome-item strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.syndrome-item span {
  color: var(--tcm-accent-color);
  font-weight: 700;
}

.syndrome-item small {
  display: block;
  margin-top: 8px;
  color: var(--tcm-text-regular);
}

.agent-table {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--tcm-border-color);
  border-radius: 14px;
}

.agent-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.3fr) 0.7fr 0.8fr 0.8fr;
  gap: 12px;
  align-items: center;
  padding: 13px 16px;
  border-bottom: 1px solid var(--tcm-border-color);
  font-size: 14px;
}

.agent-row:last-child {
  border-bottom: 0;
}

.agent-header {
  color: var(--tcm-text-regular);
  background: color-mix(in srgb, var(--tcm-text-primary) 4%, transparent);
  font-size: 12px;
  font-weight: 700;
}

.danger {
  color: #f97316;
  font-weight: 700;
}

.error-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.error-item {
  padding: 14px;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, #ef4444 28%, var(--tcm-border-color));
  background: color-mix(in srgb, #ef4444 8%, transparent);
}

.error-item div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.error-item span {
  color: var(--tcm-text-regular);
  font-size: 12px;
}

.error-item p {
  margin: 8px 0 0;
  color: var(--tcm-text-regular);
  line-height: 1.5;
}

@media (max-width: 1200px) {
  .metrics-grid,
  .charts-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-panel {
    flex-direction: column;
  }

  .monitor-controls {
    align-items: flex-start;
  }
}

@media (max-width: 760px) {
  .app-summary,
  .range-controls {
    align-items: flex-start;
    flex-direction: column;
  }

  .metrics-grid,
  .charts-grid,
  .detail-grid,
  .syndrome-list {
    grid-template-columns: 1fr;
  }

  .agent-panel {
    grid-column: span 1;
  }

  .agent-row {
    grid-template-columns: 1fr;
  }
}
</style>
