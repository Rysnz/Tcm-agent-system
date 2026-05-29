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
        <el-button type="primary" :icon="Download" :loading="exporting" @click="exportPdf">导出 PDF</el-button>
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

        <div class="bento-grid">
          <!-- 证型分析 -->
          <el-card class="section-card bento-syndromes" shadow="never">
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
        </div>

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
import { ArrowLeft, Download, Document, DataAnalysis, FirstAidKit, InfoFilled, Reading, Calendar, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { consultApi } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const sessionId = computed(() => (route.query.session_id as string) || '')

const loading = ref(false)
const exporting = ref(false)
const error = ref('')
const report = ref<any>(null)
const now = ref(dayjs().format('YYYY-MM-DD HH:mm'))

const extractReportSection = (text: string, startLabels: string[], stopLabels: string[]): string => {
  if (!text) return ''
  const lines = text.split(/\r?\n/)
  const startIndex = lines.findIndex((line) => startLabels.some((label) => line.includes(label)))
  if (startIndex < 0) return ''

  const sectionLines: string[] = []
  for (let i = startIndex + 1; i < lines.length; i += 1) {
    const line = lines[i].trim()
    if (stopLabels.some((label) => line.includes(label))) break
    if (line && !/^[-─]{4,}$/.test(line)) sectionLines.push(line)
  }
  return sectionLines.join('\n')
}

const formatEvidenceChain = (evidence: any): string => {
  if (!evidence) return ''
  if (typeof evidence === 'string') return evidence

  const parts: string[] = []
  if (evidence.chief_complaint) parts.push(`主诉：${evidence.chief_complaint}`)
  if (Array.isArray(evidence.symptoms) && evidence.symptoms.length) {
    parts.push(`症状：${evidence.symptoms.join('、')}`)
  }
  if (evidence.primary_syndrome) parts.push(`主证型：${evidence.primary_syndrome}`)
  if (evidence.syndrome_confidence) {
    parts.push(`置信度：${Math.round(evidence.syndrome_confidence * 100)}%`)
  }
  return parts.join('；')
}

const syndromes = computed(() => report.value?.report_json?.syndrome_candidates || report.value?.syndrome_candidates || [])
const recommendations = computed(() => {
  const direct = report.value?.recommendations
  if (Array.isArray(direct) && direct.length) return direct

  const jsonRecommendations = report.value?.report_json?.recommendations
  if (Array.isArray(jsonRecommendations) && jsonRecommendations.length) {
    return jsonRecommendations.map((item: any) => (
      typeof item === 'string'
        ? { category: '调理建议', content: item, rationale: '' }
        : item
    ))
  }

  const summary = report.value?.report_json?.recommendations_summary
  if (summary) return [{ category: '调理建议', content: summary, rationale: '来自问诊报告摘要' }]

  const extracted = extractReportSection(reportText.value, ['详细建议', '调理建议'], ['证据链', '参考依据', '随访建议', '安全提示', '免责声明'])
  return extracted ? [{ category: '调理建议', content: extracted, rationale: '来自完整问诊报告' }] : []
})
const references = computed(() => {
  const direct = report.value?.references
  if (Array.isArray(direct) && direct.length) return direct

  const jsonReferences = report.value?.report_json?.references
  if (Array.isArray(jsonReferences) && jsonReferences.length) {
    return jsonReferences.map((item: any) => (
      typeof item === 'string'
        ? { source: '报告参考', content: item, score: 0 }
        : item
    ))
  }

  const evidence = report.value?.report_json?.evidence_chain || report.value?.evidence_chain
  const formattedEvidence = formatEvidenceChain(evidence)
  if (formattedEvidence) return [{ source: '证据链', content: formattedEvidence, score: 0 }]

  const extracted = extractReportSection(reportText.value, ['参考依据', '证据链'], ['随访建议', '安全提示', '免责声明'])
  return extracted ? [{ source: '报告依据', content: extracted, score: 0 }] : []
})
const safetyInfo = computed(() => report.value?.report_json?.safety || report.value?.safety || null)
const reportText = computed(() => report.value?.report_text || '')

const escapeHtml = (raw: string): string =>
  raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')

const renderMarkdown = (text: string): string => {
  if (!text) return ''
  // Sanitize HTML first, then apply safe markdown transformations
  const safe = escapeHtml(text)
  return safe
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

const exportPdf = async () => {
  if (!sessionId.value) return

  exporting.value = true
  try {
    const blob = await consultApi.exportReportPdf(sessionId.value)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `中医问诊报告_${sessionId.value.slice(0, 8)}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('PDF 已开始下载')
  } catch (err: any) {
    ElMessage.error(err?.message || 'PDF 导出失败')
  } finally {
    exporting.value = false
  }
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
$border-color: var(--tcm-border-color, rgba(15, 23, 42, 0.08));
$primary: var(--tcm-accent-color, #10B981);
$text-primary: var(--tcm-text-primary, #1f2937);
$text-regular: var(--tcm-text-regular, #4b5563);
$text-muted: var(--el-text-color-secondary, #6b7280);
$card-bg: color-mix(in srgb, var(--tcm-card-bg, #ffffff) 94%, transparent);

.report-page {
  min-height: 100vh;
  background: var(--tcm-ambient-gradient, var(--tcm-page-bg, #f8fafc));
  padding: 30px;
  color: $text-primary;
}

.report-container {
  max-width: 900px;
  margin: 0 auto;
}

.report-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;

  .el-button {
    background: $card-bg;
    border: 1px solid $border-color;
    color: $text-regular;
    
    &:hover { background: color-mix(in srgb, var(--tcm-accent-color, #10B981) 9%, var(--tcm-card-bg, #ffffff)); border-color: color-mix(in srgb, var(--tcm-accent-color, #10B981) 35%, transparent); color: $primary; }
    
    &.el-button--primary {
      background: linear-gradient(135deg, $primary, var(--theme-accent-hover, #059669));
      border: none;
      color: #fff;
      &:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3); }
    }
  }

  .page-title {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0;
    font-size: 24px;
    color: $text-primary;
    background: none;
    -webkit-background-clip: text;
    -webkit-text-fill-color: currentColor;
  }
}

.disclaimer, .risk-alert { margin-bottom: 24px; border-radius: 12px; }

.disclaimer {
  :deep(.el-alert__title) { color: #b45309; font-weight: 700; }
  :deep(.el-alert__description) { color: #92400e; }
}

:deep(.el-empty__description p) {
  color: $text-muted;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: $card-bg;
  backdrop-filter: blur(20px);
  border: 1px solid $border-color;
  color: $text-primary;
  padding: 30px;
  border-radius: 24px;
  margin-bottom: 24px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 55px rgba(15, 23, 42, 0.12);
  }

  .report-logo {
    display: flex;
    align-items: center;
    gap: 16px;

    img {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      border: 2px solid rgba(16, 185, 129, 0.3);
      padding: 2px;
    }

    h3 { margin: 0 0 6px; font-size: 20px; color: $primary; }
    span { font-size: 13px; color: $text-muted; letter-spacing: 1px; text-transform: uppercase; }
  }

  .report-meta {
    text-align: right;
    font-size: 13px;
    color: $text-regular;

    div { margin-bottom: 8px; }
    label { margin-right: 12px; color: $text-muted; }
  }
}

.bento-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  margin-bottom: 24px;

  > .bento-syndromes,
  > .section-card:nth-child(2),
  > .section-card:nth-child(3),
  > .report-text-card {
    grid-column: 1;
  }
}

.section-card {
  margin-bottom: 0;
  border-radius: 24px;
  background: $card-bg !important;
  backdrop-filter: blur(20px);
  border: 1px solid $border-color !important;
  box-shadow: 0 16px 38px rgba(15, 23, 42, 0.07);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 48px rgba(15, 23, 42, 0.11);
  }

  :deep(.el-card__header) {
    border-bottom: none;
    padding: 24px 24px 0;
  }

  :deep(.el-card__body) {
    padding: 24px;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    
    .el-icon { font-size: 18px; color: $primary; }
  }
}

.syndromes-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
  align-items: stretch;

  .syndrome-item {
    padding: 20px;
    border-radius: 12px;
    background: color-mix(in srgb, var(--tcm-text-primary, #1f2937) 4%, transparent);
    border: 1px solid $border-color;

    &.primary {
      background: color-mix(in srgb, var(--tcm-accent-color, #10B981) 10%, transparent);
      border-color: color-mix(in srgb, var(--tcm-accent-color, #10B981) 32%, transparent);
    }

    .syndrome-name { margin-bottom: 12px; font-size: 15px; color: $text-primary; }
    .syndrome-symptoms { 
      margin-top: 16px; 
      display: flex; 
      flex-wrap: wrap; 
      gap: 8px; 
      
      .el-tag {
        background: color-mix(in srgb, var(--tcm-text-primary, #1f2937) 5%, transparent);
        border: 1px solid $border-color;
        color: $text-regular;
      }
    }
  }
}

.recommendations {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  align-items: stretch;

  .rec-item {
    display: flex;
    flex-direction: column;
    padding: 20px;
    border-radius: 12px;
    background: color-mix(in srgb, var(--tcm-text-primary, #1f2937) 4%, transparent);
    border: 1px solid $border-color;

    .rec-category { align-self: flex-start; margin-bottom: 12px; background: color-mix(in srgb, var(--tcm-accent-color, #10B981) 12%, transparent); border-color: color-mix(in srgb, var(--tcm-accent-color, #10B981) 24%, transparent); color: $primary; }
    .rec-content { font-size: 15px; color: $text-primary; margin: 8px 0; line-height: 1.8; }
    .rec-rationale {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: $text-muted;
      margin-top: 12px;
      background: color-mix(in srgb, var(--tcm-accent-color, #10B981) 7%, transparent);
      padding: 10px 12px;
      border-radius: 8px;
    }
    .rec-caution { margin-top: 12px; }
  }
}

.references {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .ref-item {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 12px;
    padding: 16px;
    background: color-mix(in srgb, var(--tcm-text-primary, #1f2937) 4%, transparent);
    border-radius: 12px;
    border: 1px solid $border-color;

    .ref-score { font-size: 12px; color: $text-muted; }
    .ref-content { flex: 1; font-size: 14px; color: $text-regular; min-width: 200px; line-height: 1.6; }
    
    .el-tag {
      background: rgba(16, 185, 129, 0.1);
      border-color: rgba(16, 185, 129, 0.2);
      color: $primary;
    }
  }
}

.report-text-card .report-text {
  line-height: 1.8;
  font-size: 15px;
  color: $text-primary;

  :deep(h3), :deep(h4), :deep(h5) { margin: 16px 0 8px; color: $text-primary; }
  :deep(li) { margin-left: 20px; margin-bottom: 6px; }
  :deep(strong) { color: $primary; }
}

.next-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 32px 0;
  
  .el-button {
    height: 50px;
    padding: 0 32px;
    border-radius: 25px;
    font-size: 15px;
    
    &.el-button--primary {
      background: linear-gradient(135deg, $primary, var(--theme-accent-hover, #059669));
      border: none;
      box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
      &:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3); }
    }
    
    &:not(.el-button--primary) {
      background: $card-bg;
      border: 1px solid $border-color;
      color: $text-regular;
      &:hover { background: color-mix(in srgb, var(--tcm-accent-color, #10B981) 9%, var(--tcm-card-bg, #ffffff)); color: $primary; border-color: color-mix(in srgb, var(--tcm-accent-color, #10B981) 35%, transparent); }
    }
  }
}

@media print {
  .report-toolbar, .next-actions { display: none; }
  .report-page { padding: 0; background: none; color: #000; }
  .report-container { max-width: none; }
  .section-card { background: #fff !important; border: 1px solid #ddd !important; }
}
</style>
