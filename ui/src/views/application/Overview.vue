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
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 20px 0;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-number.liked {
  color: #13ce66;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.satisfaction-content {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.satisfaction-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.liked-icon {
  font-size: 24px;
  color: #13ce66;
}

.disliked-icon {
  font-size: 24px;
  color: #f56c6c;
}

.satisfaction-number {
  font-size: 24px;
  font-weight: bold;
}

.satisfaction-number.liked {
  color: #13ce66;
}

.satisfaction-number.disliked {
  color: #f56c6c;
}

.satisfaction-label {
  margin-top: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.chart-container {
  margin-top: 30px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #303133;
}

.chart-wrapper {
  background: #fafafa;
  border-radius: 8px;
  padding: 20px;
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
  margin-bottom: 20px;
}

.legend {
  display: flex;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #606266;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.chart-content {
  flex: 1;
  position: relative;
}

.x-axis {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

.x-label {
  flex: 1;
  text-align: center;
}

.chart-body {
  position: relative;
  height: calc(100% - 30px);
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
  background-color: #ebeef5;
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
}

.line {
  transition: all 0.3s ease;
}

.data-point {
  cursor: pointer;
  transition: all 0.3s ease;
}

.data-point:hover {
  r: 6;
  filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.3));
}

.y-axis {
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
}

.tooltip {
  position: fixed;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 1000;
  pointer-events: none;
  transform: translate(-50%, -100%);
}

.tooltip-header {
  font-weight: bold;
  margin-bottom: 5px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  padding-bottom: 5px;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.tooltip-item {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.tooltip-label {
  color: #ccc;
}

.tooltip-value {
  font-weight: bold;
}
</style>