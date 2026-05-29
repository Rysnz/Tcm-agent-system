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
          <el-select v-model="timeRange" placeholder="选择时间范围" style="width: 200px">
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
            />
          </div>
        </div>
        
        <!-- 统计卡片 -->
        <div class="stats-cards">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ stats.userCount }}</div>
              <div class="stat-label">用户总数</div>
            </div>
          </el-card>
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ stats.questionCount }}</div>
              <div class="stat-label">提问次数</div>
            </div>
          </el-card>
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ stats.tokensCount }}</div>
              <div class="stat-label">Tokens 总数</div>
            </div>
          </el-card>
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content satisfaction-content">
              <div class="satisfaction-item">
                <el-icon class="liked-icon"><ThumbUp /></el-icon>
                <span class="satisfaction-number liked">{{ stats.likedCount }}</span>
              </div>
              <div class="satisfaction-item">
                <el-icon class="disliked-icon"><ThumbDown /></el-icon>
                <span class="satisfaction-number disliked">{{ stats.dislikedCount }}</span>
              </div>
            </div>
            <div class="stat-label satisfaction-label">评价</div>
          </el-card>
        </div>
        
        <!-- 统计图表 -->
        <div class="chart-container">
          <h4 class="chart-title">统计图表</h4>
          <div class="chart-wrapper">
            <el-empty v-if="!chartData.length" description="暂无数据" />
            <div v-else class="chart">
              <!-- 折线图实现 -->
              <div class="chart-header">
                <div class="legend">
                  <div class="legend-item" v-for="(item, index) in chartLegend" :key="index">
                    <div class="legend-color" :style="{ backgroundColor: item.color }"></div>
                    <span>{{ item.name }}</span>
                  </div>
                </div>
              </div>
              <div class="chart-content">
                <!-- 横轴日期标签 -->
                <div class="x-axis">
                  <div class="x-label" v-for="(date, index) in chartDates" :key="index">
                    {{ date }}
                  </div>
                </div>
                <!-- 图表主体 -->
                <div class="chart-body">
                  <!-- 网格线 -->
                  <div class="grid-lines">
                    <div class="grid-line" v-for="(line, index) in 5" :key="index"></div>
                  </div>
                  <!-- 折线 -->
                  <div class="lines">
                    <!-- 前3个图表正常显示 -->
                    <div class="line-group" v-for="(data, index) in chartData.slice(0, 3)" :key="'normal-' + index">
                      <svg width="100%" height="100%" viewBox="0 0 800 300" class="line-svg">
                        <polyline 
                          :points="generateLinePoints(data.values)" 
                          :stroke="chartLegend[index].color" 
                          stroke-width="2" 
                          fill="none"
                          class="line"
                        />
                        <!-- 数据点 -->
                        <circle 
                          v-for="(point, pointIndex) in data.values" 
                          :key="pointIndex"
                          :cx="getPointX(pointIndex)" 
                          :cy="getPointY(point)" 
                          r="4"
                          :fill="chartLegend[index].color"
                          class="data-point"
                          @mouseenter="showTooltip(point, chartDates[pointIndex], data.name, chartLegend[index].color, $event)"
                          @mouseleave="hideTooltip"
                        />
                      </svg>
                    </div>
                    <!-- 用户满意度图表（赞同和反对在同一图中） -->
                    <div class="line-group" v-if="chartData[3]" key="satisfaction">
                      <svg width="100%" height="100%" viewBox="0 0 800 300" class="line-svg">
                        <!-- 赞同折线 -->
                        <polyline 
                          :points="generateLinePoints(chartData[3].likedValues)" 
                          :stroke="chartLegend[3].color" 
                          stroke-width="2" 
                          fill="none"
                          class="line"
                        />
                        <!-- 赞同数据点 -->
                        <circle 
                          v-for="(point, pointIndex) in chartData[3].likedValues" 
                          :key="'liked-' + pointIndex"
                          :cx="getPointX(pointIndex)" 
                          :cy="getPointY(point)" 
                          r="4"
                          :fill="chartLegend[3].color"
                          class="data-point"
                          @mouseenter="showTooltip(point, chartDates[pointIndex], '赞同', chartLegend[3].color, $event)"
                          @mouseleave="hideTooltip"
                        />
                        <!-- 反对折线 -->
                        <polyline 
                          :points="generateLinePoints(chartData[3].dislikedValues)" 
                          :stroke="chartLegend[4].color" 
                          stroke-width="2" 
                          fill="none"
                          class="line"
                        />
                        <!-- 反对数据点 -->
                        <circle 
                          v-for="(point, pointIndex) in chartData[3].dislikedValues" 
                          :key="'disliked-' + pointIndex"
                          :cx="getPointX(pointIndex)" 
                          :cy="getPointY(point)" 
                          r="4"
                          :fill="chartLegend[4].color"
                          class="data-point"
                          @mouseenter="showTooltip(point, chartDates[pointIndex], '反对', chartLegend[4].color, $event)"
                          @mouseleave="hideTooltip"
                        />
                      </svg>
                    </div>
                  </div>
                  <!-- 纵轴刻度 -->
                  <div class="y-axis">
                    <div class="y-label" v-for="(label, index) in yAxisLabels" :key="index">
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
                        <span class="tooltip-label">{{ tooltipData.name }}:</span>
                        <span class="tooltip-value">{{ tooltipData.value }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
    

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, ThumbUp, ThumbDown } from '@element-plus/icons-vue'
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
const stats = ref({
  userCount: 0,
  questionCount: 0,
  tokensCount: 0,
  likedCount: 0,
  dislikedCount: 0
})

// 图表数据
const chartData = ref([
  {
    name: '用户总数',
    values: [10, 20, 30, 40, 50, 60, 70]
  },
  {
    name: '提问次数',
    values: [50, 80, 120, 150, 200, 250, 300]
  },
  {
    name: 'Tokens总数',
    values: [1000, 1500, 2000, 2500, 3000, 3500, 4000]
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
const tooltipData = ref({ date: '', name: '', value: 0 })

// 生成折线点
const generateLinePoints = (values: number[]) => {
  return values.map((value, index) => `${getPointX(index)},${getPointY(value)}`).join(' ')
}

// 获取点的X坐标
const getPointX = (index: number) => {
  const width = 800
  const padding = 50
  const pointWidth = (width - 2 * padding) / (chartDates.value.length - 1)
  return padding + index * pointWidth
}

// 获取所有数据点的值（兼容不同格式）
const getAllValues = () => {
  const allValues: number[] = []
  chartData.value.forEach(data => {
    if (data.values) {
      allValues.push(...data.values)
    } else if (data.likedValues) {
      allValues.push(...data.likedValues)
    }
    if (data.dislikedValues) {
      allValues.push(...data.dislikedValues)
    }
  })
  return allValues
}

// 获取点的Y坐标
const getPointY = (value: number) => {
  const height = 300
  const padding = 30
  const allValues = getAllValues()
  const maxValue = Math.max(...allValues) || 100
  const minValue = Math.min(...allValues) || 0
  const range = maxValue - minValue || 1
  return height - padding - ((value - minValue) / range) * (height - 2 * padding)
}

// 纵轴标签
const yAxisLabels = computed(() => {
  const allValues = getAllValues()
  const maxValue = Math.max(...allValues) || 100
  const step = Math.ceil(maxValue / 5)
  return [0, step, step * 2, step * 3, step * 4, step * 5]
})

// 显示悬浮提示框
const showTooltip = (value: number, date: string, name: string, color: string, event: MouseEvent) => {
  tooltipData.value = { date, name, value }
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

onMounted(() => {
  loadAppInfo()
})
</script>

<style scoped>
.overview-container {
  padding: 30px;
  background: transparent;
  min-height: calc(100vh - 70px);
  color: #f3f4f6;
  overflow: auto;
}

.overview-card {
  max-width: 1200px;
  margin: 0 auto;
  background: rgba(15, 15, 15, 0.6) !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

:deep(.overview-card > .el-card__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
  padding: 20px 24px;
}

.card-header span {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5px;
}

.section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #fff;
  border-left: 3px solid #10b981;
  padding-left: 10px;
}

:deep(.el-divider) {
  border-top-color: rgba(255, 255, 255, 0.08);
  margin: 30px 0;
}

/* 应用信息 */
.app-info {
  display: flex;
  align-items: center;
  gap: 24px;
}

.app-icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-icon {
  width: 100px;
  height: 100px;
  border-radius: 16px;
  object-fit: cover;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.app-icon-placeholder {
  width: 100px;
  height: 100px;
  border-radius: 16px;
  background: linear-gradient(135deg, #10b981, #059669);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.app-details {
  flex: 1;
}

.app-name {
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 600;
  color: #fff;
}

.app-desc {
  margin: 0;
  color: #9ca3af;
  line-height: 1.6;
  font-size: 15px;
}

/* 公开访问链接 */
.access-link {
  display: flex;
  gap: 12px;
  align-items: center;
}

:deep(.access-link .el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.03);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

:deep(.access-link .el-input__inner) {
  color: #10b981;
  font-family: monospace;
}

/* 监控统计 */
.stats-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

:deep(.stats-header .el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.03);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

:deep(.stats-header .el-input__inner) {
  color: #fff;
}

.date-picker-container {
  margin-left: 10px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 36px;
}

.stat-card {
  text-align: center;
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid rgba(255, 255, 255, 0.05) !important;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.5);
  border-color: rgba(16, 185, 129, 0.3) !important;
}

.stat-content {
  padding: 24px 0;
}

.stat-number {
  font-size: 36px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 12px;
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.2);
}

.stat-label {
  font-size: 14px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.satisfaction-content {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 30px;
}

.satisfaction-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.liked-icon {
  font-size: 24px;
  color: #10b981;
}

.disliked-icon {
  font-size: 24px;
  color: #ef4444;
}

.satisfaction-number {
  font-size: 28px;
  font-weight: 700;
}

.satisfaction-number.liked {
  color: #10b981;
  text-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
}

.satisfaction-number.disliked {
  color: #ef4444;
  text-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
}

.satisfaction-label {
  margin-top: 4px;
  margin-bottom: 16px;
}

.chart-container {
  margin-top: 40px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #fff;
}

.chart-wrapper {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 24px;
  height: 400px;
}

.chart {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 24px;
}

.legend {
  display: flex;
  gap: 24px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #d1d5db;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
}

.chart-content {
  flex: 1;
  position: relative;
}

.x-axis {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
  font-size: 12px;
  color: #9ca3af;
}

.x-label {
  flex: 1;
  text-align: center;
}

.chart-body {
  position: relative;
  height: calc(100% - 36px);
  display: flex;
}

.grid-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.grid-line {
  height: 1px;
  background-color: rgba(255, 255, 255, 0.05);
  margin: 59px 0;
}

.lines {
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
  filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
}

.line {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.data-point {
  cursor: pointer;
  transition: all 0.3s ease;
}

.data-point:hover {
  r: 6;
  filter: brightness(1.5) drop-shadow(0 0 8px currentColor);
}

.y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
  padding-right: 16px;
  font-size: 12px;
  color: #9ca3af;
}

.y-label {
  text-align: right;
}

.tooltip {
  position: fixed;
  background: rgba(20, 20, 20, 0.9);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  z-index: 1000;
  pointer-events: none;
  transform: translate(-50%, -100%);
  box-shadow: 0 10px 25px rgba(0,0,0,0.5);
}

.tooltip-header {
  font-weight: 600;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 8px;
  color: #d1d5db;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tooltip-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.tooltip-label {
  color: #9ca3af;
}

.tooltip-value {
  font-weight: 600;
  color: #fff;
}
</style>