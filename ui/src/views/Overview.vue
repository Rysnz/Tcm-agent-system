<template>
  <div class="overview-container">
    <el-card shadow="hover" class="overview-card">
      <template #header>
        <div class="card-header">
          <span>概览</span>
        </div>
      </template>
      
      <!-- 应用信息 -->
      <div class="section">
        <h3 class="section-title">概览</h3>
        <div class="app-info">
          <div class="app-icon-container">
            <img v-if="appInfo.icon" :src="appInfo.icon" class="app-icon" />
            <div v-else class="app-icon-placeholder">
              <el-icon><ChatDotRound /></el-icon>
            </div>
          </div>
          <div class="app-details">
            <h4 class="app-name">{{ appInfo.name || '中医智能问诊系统' }}</h4>
            <p class="app-desc">{{ appInfo.desc || '中医智能问诊系统，提供专业的中医健康咨询服务' }}</p>
          </div>
        </div>
      </div>
      
      <el-divider />
      
      <!-- 公开访问链接 -->
      <div class="section">
        <h3 class="section-title">公开访问链接</h3>
        <div class="access-link">
          <el-input v-model="publicUrl" readonly style="flex: 1;" />
          <el-button type="primary" @click="copyLink">复制链接</el-button>
          <el-button type="success" @click="goToChat">去对话</el-button>
        </div>
      </div>
      
      <el-divider />
      
      <!-- 监控统计 -->
      <div class="section">
        <h3 class="section-title">监控统计</h3>
        <div class="stats-header">
          <el-select 
            v-model="timeRange" 
            placeholder="选择时间范围" 
            style="width: 200px"
            @change="handleTimeRangeChange"
          >
            <el-option label="过去7天" value="7" />
            <el-option label="过去30天" value="30" />
            <el-option label="过去90天" value="90" />
            <el-option label="过去半年" value="180" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <div v-if="timeRange === 'custom'" class="date-picker-container">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 300px"
              @change="handleDateRangeChange"
            />
          </div>
        </div>
        
        <!-- 统计卡片 -->
        <div class="stats-cards">
          <el-card shadow="hover" class="stat-card" v-for="stat in stats" :key="stat.name">
            <div class="stat-content">
              <div class="stat-header" :style="{ color: stat.color }">
                <component :is="getIconComponent(stat.icon)" class="stat-icon" />
                <span class="stat-label">{{ stat.description }}</span>
              </div>
              <div class="stat-number" :style="{ color: stat.color }">
                <template v-if="stat.name === 'satisfactionRate'">
                  <span class="satisfaction-icon">👍</span>
                  <span class="satisfied-count">{{ stat.satisfiedCount || 0 }}</span>
                  <span class="satisfaction-divider">/</span>
                  <span class="dissatisfied-icon">👎</span>
                  <span class="dissatisfied-count">{{ stat.dissatisfiedCount || 0 }}</span>
                </template>
                <template v-else>
                  {{ formatNumber(stat.value) }}
                </template>
              </div>
            </div>
          </el-card>
        </div>
        
        <!-- 统计图表 -->
        <div class="charts-container">
          <div class="chart-item" v-for="(chartItem, index) in chartData" :key="index">
            <el-card shadow="hover" class="chart-card">
              <template #header>
                <div class="chart-item-header">
                  <div class="chart-item-title">
                    <span>{{ chartItem.name }}</span>
                  </div>
                </div>
              </template>
              <div class="chart-wrapper">
                <div class="chart">
                  <!-- 折线图实现 -->
                  <div class="chart-content">
                    <!-- 横轴日期标签 -->
                    <div class="x-axis">
                      <div class="x-label" v-for="(date, dateIndex) in chartDates" :key="dateIndex">
                        {{ date }}
                      </div>
                    </div>
                    <!-- 图表主体 -->
                    <div class="chart-body">
                      <!-- 网格线 -->
                      <div class="grid-lines">
                        <div class="grid-line" v-for="(line, lineIndex) in 5" :key="lineIndex"></div>
                      </div>
                      <!-- 折线 -->
                      <div class="lines">
                        <!-- 用户满意度图表（赞同和反对在同一图中） -->
                        <div class="line-group" v-if="chartItem.likedValues">
                          <svg width="100%" height="100%" viewBox="0 0 600 250" class="line-svg">
                            <!-- 赞同折线 -->
                            <polyline 
                              :points="generateLinePoints(chartItem.likedValues)" 
                              :stroke="chartLegend[3].color" 
                              stroke-width="2" 
                              fill="none"
                              class="line"
                            />
                            <!-- 赞同数据点 -->
                            <circle 
                              v-for="(point, pointIndex) in chartItem.likedValues" 
                              :key="'liked-' + pointIndex"
                              :cx="getPointX(pointIndex)" 
                              :cy="getPointY(chartItem.likedValues, point)" 
                              r="4"
                              :fill="chartLegend[3].color"
                              class="data-point"
                              @mouseenter="showTooltip(point, chartDates[pointIndex], '赞同', chartLegend[3].color, $event)"
                              @mouseleave="hideTooltip"
                            />
                            <!-- 反对折线 -->
                            <polyline 
                              :points="generateLinePoints(chartItem.dislikedValues)" 
                              :stroke="chartLegend[4].color" 
                              stroke-width="2" 
                              fill="none"
                              class="line"
                            />
                            <!-- 反对数据点 -->
                            <circle 
                              v-for="(point, pointIndex) in chartItem.dislikedValues" 
                              :key="'disliked-' + pointIndex"
                              :cx="getPointX(pointIndex)" 
                              :cy="getPointY(chartItem.dislikedValues, point)" 
                              r="4"
                              :fill="chartLegend[4].color"
                              class="data-point"
                              @mouseenter="showTooltip(point, chartDates[pointIndex], '反对', chartLegend[4].color, $event)"
                              @mouseleave="hideTooltip"
                            />
                          </svg>
                        </div>
                        <!-- 其他图表（正常显示） -->
                        <div class="line-group" v-else>
                          <svg width="100%" height="100%" viewBox="0 0 600 250" class="line-svg">
                            <polyline 
                              :points="generateLinePoints(chartItem.values)" 
                              :stroke="chartItem.color" 
                              stroke-width="2" 
                              fill="none"
                              class="line"
                            />
                            <!-- 数据点 -->
                            <circle 
                              v-for="(point, pointIndex) in chartItem.values" 
                              :key="pointIndex"
                              :cx="getPointX(pointIndex)" 
                              :cy="getPointY(chartItem.values, point)" 
                              r="4"
                              :fill="chartItem.color"
                              class="data-point"
                              @mouseenter="showTooltip(point, chartDates[pointIndex], chartItem.name, chartItem.color, $event)"
                              @mouseleave="hideTooltip"
                            />
                          </svg>
                        </div>
                      </div>
                      <!-- 纵轴刻度 -->
                      <div class="y-axis">
                        <div class="y-label" v-for="(label, labelIndex) in getYAxisLabels(chartItem.likedValues || chartItem.values)" :key="labelIndex">
                          {{ label }}
                        </div>
                      </div>
                      <!-- 悬浮提示框 -->
                      <div 
                        v-if="tooltipVisible" 
                        class="tooltip" 
                        :style="{
                          left: tooltipPosition.x + 'px',
                          top: tooltipPosition.y + 'px'
                        }"
                      >
                        <div class="tooltip-header">{{ tooltipData.date }}</div>
                        <div class="tooltip-content">
                          <div class="tooltip-item">
                            <span class="tooltip-label" :style="{ color: tooltipData.color }">{{ tooltipData.name }}:</span>
                            <span class="tooltip-value">{{ tooltipData.value }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, User, Message, Document, Star } from '@element-plus/icons-vue'
import { applicationApi } from '@/api'

const router = useRouter()

// 应用信息
const appInfo = ref({
  name: '中医智能问诊系统',
  icon: '',
  desc: ''
})

// 公开访问链接
const publicUrl = ref('http://localhost:3000/chat')

// 监控统计
const timeRange = ref('7')
const dateRange = ref([])

// 统计数据类型定义
interface StatData {
  name: string;
  value: number;
  trend?: number;  // 环比增长率
  satisfiedCount?: number;  // 满意数
  dissatisfiedCount?: number;  // 不满意数
  icon: string;
  color: string;
  description: string;
}

// 统计数据
const stats = ref<StatData[]>([
  {
    name: 'userCount',
    value: 123,
    icon: 'User',
    color: '#409eff',
    description: '用户总数'
  },
  {
    name: 'questionCount',
    value: 456,
    icon: 'Message',
    color: '#67c23a',
    description: '提问次数'
  },
  {
    name: 'tokensCount',
    value: 7890,
    icon: 'Document',
    color: '#e6a23c',
    description: 'Tokens 总数'
  },
  {
    name: 'satisfactionRate',
    value: 95,
    icon: 'Star',
    color: '#f56c6c',
    description: '用户满意度'
  }
])

// 图表数据
// 图表数据
const chartData = ref([
  {
    name: '用户总数',
    values: [10, 20, 30, 40, 50, 60, 70],
    color: '#409eff',
    icon: 'User'
  },
  {
    name: '提问次数',
    values: [50, 80, 120, 150, 200, 250, 300],
    color: '#67c23a',
    icon: 'Message'
  },
  {
    name: 'Tokens总数',
    values: [1000, 1500, 2000, 2500, 3000, 3500, 4000],
    color: '#e6a23c',
    icon: 'Document'
  },
  {
    name: '用户满意度',
    likedValues: [5, 8, 12, 15, 20, 25, 30],
    dislikedValues: [1, 2, 3, 2, 4, 3, 5]
  }
])

// 图表图例
const chartLegend = ref([
  { name: '用户总数', color: '#409eff' },
  { name: '提问次数', color: '#67c23a' },
  { name: 'Tokens总数', color: '#e6a23c' },
  { name: '赞同', color: '#13ce66' },
  { name: '反对', color: '#f56c6c' }
])

// 图表日期
const chartDates = ref(['1月1日', '1月2日', '1月3日', '1月4日', '1月5日', '1月6日', '1月7日'])

// 悬浮提示框
const tooltipVisible = ref(false)
const tooltipPosition = ref({ x: 0, y: 0 })
const tooltipData = ref({ date: '', name: '', value: 0, color: '' })

// 获取点的X坐标
const getPointX = (index: number) => {
  const width = 600
  const padding = 50
  const pointWidth = (width - 2 * padding) / (chartDates.value.length - 1)
  return padding + index * pointWidth
}

// 获取点的Y坐标
const getPointY = (values: number[], value: number) => {
  const height = 250
  const padding = 30
  const maxValue = Math.max(...values)
  const minValue = Math.min(...values)
  const range = maxValue - minValue || 1
  return height - padding - ((value - minValue) / range) * (height - 2 * padding)
}

// 生成折线点
const generateLinePoints = (values: number[]) => {
  return values.map((value, index) => `${getPointX(index)},${getPointY(values, value)}`).join(' ')
}

// 纵轴标签
const getYAxisLabels = (values: number[]) => {
  const maxValue = Math.max(...values)
  const step = Math.ceil(maxValue / 5)
  return [step * 5, step * 4, step * 3, step * 2, step, 0]
}

// 显示悬浮提示框
const showTooltip = (value: number, date: string, name: string, color: string, event: MouseEvent) => {
  tooltipData.value = { date, name, value, color }
  tooltipPosition.value = { x: event.clientX + 10, y: event.clientY - 50 }
  tooltipVisible.value = true
}

// 隐藏悬浮提示框
const hideTooltip = () => {
  tooltipVisible.value = false
}

// 复制链接
const copyLink = () => {
  navigator.clipboard.writeText(publicUrl.value)
    .then(() => {
      ElMessage.success('链接复制成功')
    })
    .catch(() => {
      ElMessage.error('链接复制失败')
    })
}

// 跳转到对话界面
const goToChat = () => {
  router.push('/chat')
}

// 获取图标组件
const getIconComponent = (iconName: string) => {
  switch (iconName) {
    case 'User':
      return User
    case 'Message':
      return Message
    case 'Document':
      return Document
    case 'Star':
      return Star
    default:
      return User
  }
}

// 数字格式化函数
const formatNumber = (num: number): string => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  } else if (num >= 1000) {
    return num.toLocaleString()
  }
  return num.toString()
}

// 计算环比增长率
const calculateTrend = (currentValue: number, previousValue: number): number => {
  if (previousValue === 0) {
    return currentValue > 0 ? 100 : 0
  }
  return ((currentValue - previousValue) / previousValue) * 100
}

// 加载统计数据
const loadStats = async () => {
  try {
    // 构建请求参数
    const params: any = {
      timeRange: timeRange.value
    }
    
    // 如果是自定义日期范围，添加开始和结束日期
    if (timeRange.value === 'custom' && dateRange.value && dateRange.value.length === 2) {
      params.startDate = dateRange.value[0]
      params.endDate = dateRange.value[1]
    }
    
    // 调用真实API获取统计数据
    const response = await applicationApi.getStats(params)
    console.log('API响应:', response)
    const statsData = response.stats
    const chartsData = response.charts
    console.log('statsData:', statsData)
    
    // 从图表数据中计算趋势（今天 vs 昨天）
    let userTrend = 0
    let questionTrend = 0
    let tokensTrend = 0
    let satisfactionTrend = 0
    
    if (chartsData && chartsData.length > 0) {
      const values = chartsData[0].values
      if (values && values.length >= 2) {
        const currentDate = values[values.length - 1]
        const previousDate = values[values.length - 2]
        
        // 找到对应指标的值
        const userChart = chartsData.find((c: any) => c.name === '用户总数')
        const questionChart = chartsData.find((c: any) => c.name === '提问次数')
        const tokensChart = chartsData.find((c: any) => c.name === 'Tokens 总数')
        const satisfactionChart = chartsData.find((c: any) => c.name === '用户满意度')
        
        if (userChart && userChart.values.length >= 2) {
          userTrend = calculateTrend(userChart.values[userChart.values.length - 1], userChart.values[userChart.values.length - 2])
        }
        if (questionChart && questionChart.values.length >= 2) {
          questionTrend = calculateTrend(questionChart.values[questionChart.values.length - 1], questionChart.values[questionChart.values.length - 2])
        }
        if (tokensChart && tokensChart.values.length >= 2) {
          tokensTrend = calculateTrend(tokensChart.values[tokensChart.values.length - 1], tokensChart.values[tokensChart.values.length - 2])
        }
        if (satisfactionChart && satisfactionChart.likedValues && satisfactionChart.likedValues.length >= 2) {
          const totalCurrent = (satisfactionChart.likedValues[satisfactionChart.likedValues.length - 1] || 0) + 
                              (satisfactionChart.dislikedValues[satisfactionChart.dislikedValues.length - 1] || 0)
          const totalPrevious = (satisfactionChart.likedValues[satisfactionChart.likedValues.length - 2] || 0) + 
                               (satisfactionChart.dislikedValues[satisfactionChart.dislikedValues.length - 2] || 0)
          satisfactionTrend = calculateTrend(totalCurrent, totalPrevious)
        }
      }
    }
    
    // 更新统计数据（添加趋势值）
    stats.value = [
      {
        name: 'userCount',
        value: statsData.userCount,
        trend: userTrend,
        icon: 'User',
        color: '#409eff',
        description: '用户总数'
      },
      {
        name: 'questionCount',
        value: statsData.questionCount,
        trend: questionTrend,
        icon: 'Message',
        color: '#67c23a',
        description: '提问次数'
      },
      {
        name: 'tokensCount',
        value: statsData.tokensCount,
        trend: tokensTrend,
        icon: 'Document',
        color: '#e6a23c',
        description: 'Tokens 总数'
      },
      {
        name: 'satisfactionRate',
        value: statsData.satisfactionRate,
        trend: satisfactionTrend,
        satisfiedCount: statsData.likedCount || 0,
        dissatisfiedCount: statsData.dislikedCount || 0,
        icon: 'Star',
        color: '#f56c6c',
        description: '用户满意度'
      }
    ]
    
    // 更新图表数据
    if (chartsData && chartsData.length > 0) {
      chartData.value = chartsData
      // 更新图表日期
      if (chartsData[0].dates && chartsData[0].dates.length > 0) {
        chartDates.value = chartsData[0].dates
      }
    }
    
    ElMessage.success('统计数据加载成功')
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
    
    // 加载失败时使用模拟数据
    stats.value = [
      {
        name: 'userCount',
        value: 123,
        trend: 0,
        icon: 'User',
        color: '#409eff',
        description: '用户总数'
      },
      {
        name: 'questionCount',
        value: 456,
        trend: 0,
        icon: 'Message',
        color: '#67c23a',
        description: '提问次数'
      },
      {
        name: 'tokensCount',
        value: 7890,
        trend: 0,
        icon: 'Document',
        color: '#e6a23c',
        description: 'Tokens 总数'
      },
      {
        name: 'satisfactionRate',
        value: 95,
        trend: 0,
        satisfiedCount: 19,
        dissatisfiedCount: 1,
        icon: 'Star',
        color: '#f56c6c',
        description: '用户满意度'
      }
    ]
  }
}

// 时间范围变化时重新加载数据
const handleTimeRangeChange = () => {
  loadStats()
}

// 日期范围变化时重新加载数据
const handleDateRangeChange = () => {
  if (timeRange.value === 'custom') {
    loadStats()
  }
}

// 加载应用信息
const loadAppInfo = async () => {
  try {
    const applications = await applicationApi.getApplications()
    if (applications.length > 0) {
      const app = applications[0]
      appInfo.value = {
        name: app.name,
        icon: app.icon,
        desc: app.desc
      }
    }
  } catch (error) {
    console.error('加载应用信息失败:', error)
    ElMessage.error('加载应用信息失败')
  }
}

// 定时刷新数据
let refreshTimer: any = null

const startRefreshTimer = () => {
  // 每30秒自动刷新数据
  refreshTimer = setInterval(() => {
    loadStats()
  }, 30000)
}

const stopRefreshTimer = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  loadAppInfo()
  loadStats()
  startRefreshTimer()
})

onUnmounted(() => {
  stopRefreshTimer()
})
</script>

<style scoped>
.overview-container {
  padding: 20px;
}

.overview-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #303133;
}

/* 应用信息 */
.app-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.app-icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-icon {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  object-fit: cover;
}

.app-icon-placeholder {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  background-color: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: #909399;
}

.app-details {
  flex: 1;
}

.app-name {
  margin: 0 0 10px 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.app-desc {
  margin: 0;
  color: #606266;
  line-height: 1.5;
}

/* 公开访问链接 */
.access-link {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* 监控统计 */
.stats-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.date-picker-container {
  margin-left: 10px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 30px;
}

.stat-card {
  text-align: left;
  transition: all 0.3s ease;
  border-radius: 16px;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
}

.stat-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.stat-header {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  gap: 12px;
  margin-bottom: 20px;
  width: 100%;
  height: auto;
}

.stat-icon {
  font-size: 20px;
  width: 20px;
  height: 20px;
  display: inline-block;
  padding: 8px;
  border-radius: 10px;
}

.stat-label {
  font-size: 14px;
  font-weight: 500;
  color: inherit;
  display: inline-block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  letter-spacing: -1px;
}

.stat-number .satisfaction-icon,
.stat-number .dissatisfied-icon {
  margin-right: 4px;
  font-size: 24px;
}

.stat-number .satisfied-count {
  color: #67c23a;
  margin-right: 4px;
}

.stat-number .satisfaction-divider {
  margin: 0 8px;
  color: #909399;
}

.stat-number .dissatisfied-count {
  color: #f56c6c;
}

.stat-number .satisfaction-total {
  color: #909399;
  font-weight: normal;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.trend-arrow {
  font-weight: 600;
}

.trend-arrow.up {
  color: #67c23a;
}

.trend-arrow.down {
  color: #f56c6c;
}

.trend-value {
  color: #606266;
  font-weight: 500;
}

/* 图表容器 */
.charts-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-top: 30px;
}

.chart-item {
  width: 100%;
}

.chart-card {
  height: 100%;
  border-radius: 16px;
  overflow: hidden;
}

.chart-item-header {
  display: flex !important;
  justify-content: flex-start !important;
  align-items: center !important;
  width: 100%;
  height: auto;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.chart-item-title {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  flex-direction: row !important;
  width: auto;
  height: auto;
  white-space: nowrap;
}

.chart-item-icon {
  font-size: 18px;
  width: 18px;
  height: 18px;
  display: inline-block;
  padding: 6px;
  border-radius: 8px;
}

.chart-wrapper {
  background: linear-gradient(180deg, #fafafa 0%, #f5f7fa 100%);
  border-radius: 12px;
  padding: 24px;
  height: 320px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
}

.chart {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-content {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
}

.x-axis {
  order: 2;
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
  font-size: 12px;
  color: #909399;
  padding-left: 50px;
}

.x-label {
  flex: 1;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chart-body {
  order: 1;
  position: relative;
  flex: 1;
  display: flex;
}

.grid-lines {
  order: 1;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  pointer-events: none;
}

.grid-line {
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(0, 0, 0, 0.05) 50%, transparent 100%);
}

.lines {
  order: 1;
  flex: 1;
  position: relative;
  overflow: hidden;
}

.line-group {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.line-svg {
  width: 100%;
  height: 100%;
}

.line {
  transition: all 0.3s ease;
}

.data-point {
  cursor: pointer;
  transition: all 0.3s ease;
}

.data-point:hover {
  r: 7;
  filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.2));
}

.y-axis {
  order: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
  padding-right: 10px;
  font-size: 12px;
  color: #909399;
}

.y-label {
  text-align: right;
  white-space: nowrap;
}

.tooltip {
  position: fixed;
  background: rgba(0, 0, 0, 0.85);
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  z-index: 1000;
  pointer-events: none;
  transform: translate(-50%, -100%);
  min-width: 140px;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.tooltip-header {
  font-weight: 600;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding-bottom: 8px;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tooltip-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.tooltip-label {
  color: #e0e0e0;
}

.tooltip-value {
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .overview-card {
    max-width: 100%;
  }
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-container {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .overview-container {
    padding: 12px;
  }
  
  .stats-cards {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .charts-container {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .app-info {
    flex-direction: column;
    text-align: center;
  }
  
  .access-link {
    flex-direction: column;
    gap: 12px;
  }
  
  .stats-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .date-picker-container {
    margin-left: 0;
    margin-top: 10px;
  }
  
  .chart-wrapper {
    padding: 16px;
    height: 280px;
  }
  
  .x-axis {
    padding-left: 30px;
    font-size: 10px;
  }
  
  .y-axis {
    padding-right: 5px;
    font-size: 10px;
  }
  
  .chart-item-header {
    padding: 16px;
  }
  
  .stat-number {
    font-size: 28px;
  }
  
  .stat-icon {
    font-size: 18px;
    width: 18px;
    height: 18px;
  }
}
</style>