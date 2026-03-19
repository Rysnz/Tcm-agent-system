<template>
  <div class="report-page">
    <div class="report-container" v-loading="loading">
      <!-- 顶部操作栏 -->
      <div class="report-toolbar">
        <el-button @click="$router.back()" :icon="ArrowLeft" plain>返回</el-button>
        <h2 class="page-title">
          <el-icon><Document /></el-icon>
          中医问诊报告
        </h2>
        <el-button type="primary" :icon="Printer" @click="printReport">打印/导出</el-button>
      </div>

      <!-- 错误提示 -->
      <el-result
        v-if="error"
        icon="warning"
        title="报告获取失败"
        :sub-title="error"
      >
        <template #extra>
          <el-button type="primary" @click="$router.push('/consult')">返回问诊</el-button>
        </template>
      </el-result>

      <!-- 报告内容 -->
      <div v-else-if="report" class="report-content" id="report-print-area">
        <!-- 报告头部 -->
        <div class="report-header">
          <div class="report-logo">
            <img src="@/assets/assistant-avatar.png" alt="logo" />
            <div>
              <h3>中医智能问诊系统</h3>
              <span>TCM Multi-Agent System</span>
            </div>
          </div>
          <div class="report-meta">
            <div>
              <label>会话ID</label>
              <span>{{ sessionId }}</span>
            </div>
            <div>
              <label>生成时间</label>
              <span>{{ now }}</span>
            </div>
          </div>
        </div>

        <!-- 免责声明 -->
        <el-alert
          type="warning"
          :closable="false"
          class="disclaimer"
        >
          <template #title>
            ⚠️ 免责声明
          </template>
          本报告内容为健康参考建议与中医辨证参考，不构成任何医疗诊断结论，不能替代执业医师专业诊疗。如有疑问或症状较重，请及时就医。
        </el-alert>

        <!-- 安全提示（高风险时展示） -->
        <el-alert
          v-if="safetyInfo?.should_refer_immediately"
          type="error"
          :closable="false"
          class="risk-alert"
          title="⚠️ 检测到高风险症状"
        >
          <p>{{ safetyInfo.safety_message || '请立即前往医院就诊！' }}</p>
        </el-alert>

        <!-- 证型分析 -->
        <el-card class="section-card" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><DataAnalysis /></el-icon>
              辨证结果
            </div>
          </template>
          <div v-if="syndromes?.length" class="syndromes-list">
            <div
              v-for="(s, i) in syndromes"
              :key="i"
              class="syndrome-item"
              :class="{ primary: i === 0 }"
            >
              <div class="syndrome-name">
                {{ i === 0 ? '🏆 主证型：' : `候选 ${i + 1}：` }}
                <strong>{{ s.name }}</strong>
              </div>
              <el-progress
                :percentage="Math.round(s.confidence * 100)"
                :status="i === 0 ? 'success' : ''"
                :stroke-width="12"
              />
              <div class="syndrome-symptoms" v-if="s.supporting_symptoms?.length">
                <el-tag
                  v-for="sym in s.supporting_symptoms"
                  :key="sym"
                  size="small"
                  type="info"
                  effect="light"
                >{{ sym }}</el-tag>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无辨证结果" />
        </el-card>

        <!-- 调理建议 -->
        <el-card class="section-card" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><FirstAidKit /></el-icon>
              调理建议
            </div>
          </template>
          <div v-if="recommendations?.length" class="recommendations">
            <div
              v-for="(rec, i) in recommendations"
              :key="i"
              class="rec-item"
            >
              <el-tag type="primary" effect="plain" class="rec-category">
                {{ getCategoryEmoji(rec.category) }} {{ rec.category }}
              </el-tag>
              <div class="rec-content">{{ rec.content }}</div>
              <div v-if="rec.rationale" class="rec-rationale">
                <el-icon><InfoFilled /></el-icon>
                {{ rec.rationale }}
              </div>
              <el-alert
                v-if="rec.caution"
                type="warning"
                :title="'注意：' + rec.caution"
                :closable="false"
                class="rec-caution"
                size="small"
              />
            </div>
          </div>
          <el-empty v-else description="暂无调理建议" />
        </el-card>

        <!-- 参考依据 -->
        <el-card class="section-card" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><Reading /></el-icon>
              参考依据
            </div>
          </template>
          <div v-if="references?.length" class="references">
            <div v-for="(ref, i) in references" :key="i" class="ref-item">
              <el-tag size="small" type="info">{{ ref.source || '知识库' }}</el-tag>
              <span class="ref-score">相关度 {{ (ref.score * 100).toFixed(0) }}%</span>
              <div class="ref-content">{{ ref.content }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无参考文献" />
        </el-card>

        <!-- 完整报告文本 -->
        <el-card v-if="reportText" class="section-card report-text-card" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><Document /></el-icon>
              完整报告
            </div>
          </template>
          <div class="report-text" v-html="renderMarkdown(reportText)" />
        </el-card>

        <!-- 下一步操作 -->
        <div class="next-actions">
          <el-button type="primary" @click="goToWellness" size="large">
            <el-icon><Calendar /></el-icon>
            生成个性化养生计划
          </el-button>
          <el-button @click="$router.push('/consult')" size="large">
            <el-icon><Plus /></el-icon>
            开始新问诊
          </el-button>
        </div>
      </div>

      <!-- 无报告时引导 -->
      <el-result
        v-else-if="!loading"
        icon="info"
        title="报告尚未生成"
        sub-title="请先完成完整的问诊流程，系统会自动生成报告"
      >
        <template #extra>
          <el-button type="primary" @click="$router.push('/consult')">前往问诊</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Printer, Document, DataAnalysis, FirstAidKit, InfoFilled, Reading, Calendar, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { consultApi } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const sessionId = computed(() => (route.query.session_id as string) || '')

const loading = ref(false)
const error = ref('')
const report = ref<any>(null)
const now = ref(dayjs().format('YYYY-MM-DD HH:mm'))

const syndromes = computed(() => report.value?.report_json?.syndrome_candidates || report.value?.syndrome_candidates || [])
const recommendations = computed(() => report.value?.report_json?.recommendations || report.value?.recommendations || [])
const references = computed(() => report.value?.report_json?.references || report.value?.references || [])
const safetyInfo = computed(() => report.value?.report_json?.safety || report.value?.safety || null)
const reportText = computed(() => report.value?.report_text || '')

const renderMarkdown = (text: string): string => {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>')
    .replace(/^###\s(.+)$/gm, '<h5>$1</h5>')
    .replace(/^##\s(.+)$/gm, '<h4>$1</h4>')
    .replace(/^#\s(.+)$/gm, '<h3>$1</h3>')
    .replace(/^[-*]\s(.+)$/gm, '<li>$1</li>')
}

const getCategoryEmoji = (cat: string) => {
  const map: Record<string, string> = {
    饮食: '🥗', 作息: '💤', 运动: '🏃', 情志: '🧘', 穴位: '💆', 代茶饮: '🍵'
  }
  return map[cat] || '📌'
}

const printReport = () => {
  window.print()
}

const goToWellness = () => {
  const syndrome = syndromes.value[0]?.name || ''
  router.push({ path: '/wellness', query: { syndrome } })
}

onMounted(async () => {
  if (!sessionId.value) {
    error.value = '缺少会话ID参数'
    return
  }
  loading.value = true
  try {
    const res = await consultApi.getReport(sessionId.value)
    report.value = res
  } catch (err: any) {
    const msg = err?.response?.data?.error || err?.message || '获取报告失败'
    if (msg.includes('尚未生成') || msg.includes('not found')) {
      error.value = '报告尚未生成，请先完成完整的问诊流程'
    } else {
      error.value = msg
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
$border-color: #e8eaf0;
$primary: #1677ff;

.report-page {
  min-height: 100vh;
  background: #f5f7fb;
  padding: 24px;
}

.report-container {
  max-width: 860px;
  margin: 0 auto;
}

.report-toolbar {
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

.disclaimer { margin-bottom: 20px; }
.risk-alert { margin-bottom: 20px; }

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 20px;

  .report-logo {
    display: flex;
    align-items: center;
    gap: 12px;

    img {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      border: 2px solid rgba(255,255,255,0.3);
    }

    h3 { margin: 0; font-size: 18px; }
    span { font-size: 12px; opacity: 0.7; }
  }

  .report-meta {
    text-align: right;
    font-size: 12px;
    opacity: 0.8;

    div { margin-bottom: 4px; }
    label { margin-right: 8px; opacity: 0.7; }
  }
}

.section-card {
  margin-bottom: 20px;
  border-radius: 12px;

  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 15px;
    font-weight: 600;
  }
}

.syndromes-list {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .syndrome-item {
    padding: 16px;
    border-radius: 8px;
    background: #fafafa;
    border: 1px solid $border-color;

    &.primary {
      background: #e6f7ff;
      border-color: $primary;
    }

    .syndrome-name { margin-bottom: 8px; font-size: 14px; }
    .syndrome-symptoms { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
  }
}

.recommendations {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .rec-item {
    padding: 16px;
    border-radius: 8px;
    background: #fafafa;
    border: 1px solid $border-color;

    .rec-category { margin-bottom: 8px; }
    .rec-content { font-size: 14px; color: #333; margin: 6px 0; line-height: 1.7; }
    .rec-rationale {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #888;
      margin-top: 6px;
    }
    .rec-caution { margin-top: 8px; }
  }
}

.references {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .ref-item {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 8px;
    padding: 12px;
    background: #fafafa;
    border-radius: 8px;
    border: 1px solid $border-color;

    .ref-score { font-size: 11px; color: #999; }
    .ref-content { flex: 1; font-size: 13px; color: #555; min-width: 200px; }
  }
}

.report-text-card .report-text {
  line-height: 1.8;
  font-size: 14px;
  color: #333;

  :deep(h3), :deep(h4), :deep(h5) { margin: 12px 0 6px; }
  :deep(li) { margin-left: 16px; }
}

.next-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 24px 0;
}

@media print {
  .report-toolbar, .next-actions { display: none; }
  .report-page { padding: 0; background: none; }
  .report-container { max-width: none; }
}
</style>
