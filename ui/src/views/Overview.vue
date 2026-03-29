<template>
  <div class="dashboard-page">
    <div class="top-row">
      <h3>系统仪表盘</h3>
      <div class="filters">
        <el-select v-model="timeRange" style="width: 150px" @change="loadStats">
          <el-option label="过去7天" value="7" />
          <el-option label="过去30天" value="30" />
          <el-option label="过去90天" value="90" />
          <el-option label="过去半年" value="180" />
        </el-select>
      </div>
    </div>

    <el-row :gutter="12" class="kpis">
      <el-col :xs="24" :sm="12" :md="6" v-for="item in stats" :key="item.name">
        <el-card class="kpi-card">
          <div class="kpi-name">{{ item.description }}</div>
          <div class="kpi-value">{{ formatNumber(item.value) }}</div>
          <div class="kpi-desc" v-if="getKpiDescription(item.name)">{{ getKpiDescription(item.name) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <el-col :xs="24" :md="12" v-for="chart in chartData" :key="chart.name">
        <el-card class="chart-card">
          <template #header>{{ chart.name }}</template>
          <div class="simple-chart">
            <div class="bar" v-for="(v, i) in chart.values || []" :key="i" :style="barStyle(chart.values || [], v)">
              <span>{{ v }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { applicationApi, authApi } from '@/api'

const timeRange = ref('7')
const stats = ref<any[]>([])
const chartData = ref<any[]>([])

const formatNumber = (num: number) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return `${num || 0}`
}

const barStyle = (values: number[], value: number) => {
  const max = Math.max(...values, 1)
  const h = Math.max(8, Math.round((value / max) * 100))
  return { height: `${h}%` }
}

const loadStats = async () => {
  try {
    const [data, userStats] = await Promise.all([
      applicationApi.getStats({ timeRange: timeRange.value }),
      authApi.getAdminStats().catch(() => ({ registeredUserCount: 0 }))
    ])
    stats.value = [
      { name: 'registeredUserCount', description: '注册用户总数', value: userStats.registeredUserCount || 0 },
      { name: 'userCount', description: '活跃用户数', value: data.stats.userCount || 0 },
      { name: 'questionCount', description: '提问次数', value: data.stats.questionCount || 0 },
      { name: 'tokensCount', description: 'Token消耗', value: data.stats.tokensCount || 0 },
    ]

    chartData.value = (data.charts || [])
      .filter((c: any) => Array.isArray(c.values))
      .map((c: any) => ({ name: c.name, values: c.values }))
  } catch (error) {
    console.error('loadStats failed:', error)
    ElMessage.error('加载实时监控数据失败')
    stats.value = [
      { name: 'registeredUserCount', description: '注册用户总数', value: 0 },
      { name: 'userCount', description: '活跃用户数', value: 0 },
      { name: 'questionCount', description: '提问次数', value: 0 },
      { name: 'tokensCount', description: 'Token消耗', value: 0 },
    ]
    chartData.value = []
  }
}

const getKpiDescription = (name: string) => {
  if (name === 'registeredUserCount') return '注册用户总数（系统账户）'
  if (name === 'userCount') return '活跃用户数（时间范围内有问诊消息）'
  return ''
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard-page {
  padding: 0;
}

.top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.top-row h3 {
  margin: 0;
  color: #1f3228;
}

.kpis {
  margin-bottom: 12px;
}

.kpi-card {
  border-radius: 12px;
  border: 1px solid #e1ece4;
}

.kpi-name {
  font-size: 12px;
  color: #71877a;
}

.kpi-value {
  margin-top: 8px;
  font-size: 24px;
  color: #1f3228;
  font-weight: 700;
}

.kpi-desc {
  margin-top: 6px;
  font-size: 11px;
  color: #889d91;
}

.chart-card {
  margin-bottom: 12px;
  border-radius: 12px;
  border: 1px solid #e1ece4;
}

.simple-chart {
  height: 180px;
  display: flex;
  align-items: flex-end;
  gap: 6px;
}

.bar {
  flex: 1;
  background: linear-gradient(180deg, #3f9f8a, #2d7b64);
  border-radius: 6px 6px 0 0;
  min-height: 8px;
  position: relative;
}

.bar span {
  position: absolute;
  top: -18px;
  right: 0;
  font-size: 10px;
  color: #6f8478;
}
</style>
