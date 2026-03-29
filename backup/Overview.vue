<template>
  <div class="overview-container">
    <el-card shadow="hover" class="overview-card">
      <template #header>
        <div class="card-header">
          <span>中医智能问诊系统</span>
        </div>
      </template>
      
      <!-- 应用信息 -->
      <div class="section">
        <h3 class="section-title">应用信息</h3>
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
          <el-input v-model="publicUrl" readonly />
          <el-button type="primary" @click="copyLink">复制链接</el-button>
          <el-button type="success" @click="openDemo">演示</el-button>
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
            <div class="stat-content">
              <div class="stat-number">{{ stats.satisfactionRate }}%</div>
              <div class="stat-label">用户满意度</div>
            </div>
          </el-card>
        </div>
        
        <!-- 统计图表 -->
        <div class="chart-container">
          <h4 class="chart-title">统计图表</h4>
          <div class="chart-placeholder">
            <el-icon class="chart-icon"><DataLine /></el-icon>
            <p>图表功能开发中...</p>
          </div>
        </div>
      </div>
    </el-card>
    

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, DataLine } from '@element-plus/icons-vue'
import { applicationApi, type Application } from '@/api'

const router = useRouter()

// 应用信息
const appInfo = ref({
  name: '中医智能问诊系统',
  icon: '',
  desc: ''
})

// 公开访问链接 - 指向对话界面
const publicUrl = ref('http://localhost:3000/chat')

// 监控统计
const timeRange = ref('7')
const dateRange = ref([])
const stats = ref({
  userCount: 123,
  questionCount: 456,
  tokensCount: 7890,
  satisfactionRate: 95
})

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

// 打开演示
const openDemo = () => {
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
  max-width: 1000px;
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

/* API 访问凭据 */
.api-info {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.api-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.api-keys {
  margin-top: 10px;
}

.api-keys-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
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

.chart-placeholder {
  height: 300px;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.chart-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

/* 对话框样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>