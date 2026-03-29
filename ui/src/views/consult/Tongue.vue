<template>
  <div class="tongue-page">
    <div class="tongue-container">
      <!-- 页面头 -->
      <div class="page-header">
        <el-button @click="$router.back()" :icon="ArrowLeft" plain>返回</el-button>
        <h2 class="page-title">
          <el-icon><View /></el-icon>
          舌象分析（望诊）
        </h2>
        <div style="width: 80px;" />
      </div>

      <!-- 说明卡片 -->
      <el-card class="guide-card" shadow="never">
        <div class="guide-content">
          <div class="guide-icon">📷</div>
          <div>
            <h4>拍摄建议</h4>
            <ul>
              <li>在自然光线下伸出舌头正对摄像头</li>
              <li>保持舌面平展，舌尖向前</li>
              <li>避免饮食后立即拍摄（建议饭后 30 分钟以上）</li>
              <li>图片清晰、无遮挡</li>
            </ul>
          </div>
        </div>
      </el-card>

      <el-row :gutter="24" class="main-row">
        <!-- 上传区 -->
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="upload-card fixed-height-card">
            <template #header>
              <span class="card-title">上传舌象图片</span>
            </template>

            <div class="card-body">
              <el-upload
                class="tongue-uploader"
                :show-file-list="false"
                :before-upload="beforeUpload"
                :on-change="handleFileChange"
                accept="image/*"
                drag
              >
                <div v-if="!previewUrl" class="upload-placeholder">
                  <el-icon class="upload-icon"><Upload /></el-icon>
                  <p>点击或拖拽图片到此处</p>
                  <small>支持 JPG / PNG / WEBP，最大 5MB</small>
                </div>
                <div v-else class="preview-wrapper">
                  <img :src="previewUrl" class="preview-img" alt="舌象预览" />
                  <div class="preview-overlay">
                    <el-button type="primary" circle @click.stop="previewUrl = ''; selectedFile = null">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </el-upload>

              <el-button
                type="primary"
                class="analyze-btn"
                :loading="analyzing"
                :disabled="!selectedFile"
                @click="analyzeImage"
              >
                <el-icon><Search /></el-icon>
                开始舌象分析
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- 分析结果 -->
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="result-card fixed-height-card" v-loading="analyzing">
            <template #header>
              <span class="card-title">分析结果</span>
            </template>

            <div class="card-body">
              <div v-if="!result && !analyzing" class="result-empty">
                <el-icon class="empty-icon"><Picture /></el-icon>
                <p>上传并分析舌象图片后，结果将展示在此处</p>
              </div>

              <div v-else-if="analyzing" class="result-analyzing">
                <div class="analyzing-animation">
                  <div class="pulse-ring"></div>
                  <div class="pulse-ring delay-1"></div>
                  <div class="pulse-ring delay-2"></div>
                  <el-icon class="analyzing-icon"><Picture /></el-icon>
                </div>
                <p class="analyzing-text">正在分析舌象...</p>
                <p class="analyzing-hint">AI 正在识别舌色、苔色、舌形等特征</p>
              </div>

              <div v-else-if="result" class="result-content">
                <!-- 舌象特征 -->
                <div class="feature-grid">
                  <div class="feature-item" v-for="feat in featureList" :key="feat.key">
                    <div class="feat-label">{{ feat.label }}</div>
                    <div class="feat-value">
                      <el-tag v-if="feat.value" :type="feat.tagType" effect="light">
                        {{ feat.value }}
                      </el-tag>
                      <span v-else class="feat-unknown">未检测到</span>
                    </div>
                  </div>
                </div>

                <!-- 图像特征标签 -->
                <div v-if="result.observation.image_features?.length" class="image-features">
                  <div class="feat-section-title">
                    <el-icon><Flag /></el-icon>
                    检测到的视觉特征
                  </div>
                  <div class="feature-tags">
                    <el-tag
                      v-for="f in result.observation.image_features"
                      :key="f"
                      type="warning"
                      effect="light"
                    >{{ f }}</el-tag>
                  </div>
                </div>

                <!-- 分析完成提示 -->
                <el-alert
                  type="success"
                  :closable="false"
                  class="mt-16"
                  title="分析完成"
                  description="舌象特征信息已提取完成。"
                />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 舌象诊断（独立区域） -->
      <el-card v-if="result?.observation?.diagnosis?.summary" shadow="never" class="diagnosis-card">
        <template #header>
          <span class="card-title">
            <el-icon><FirstAidKit /></el-icon>
            舌象诊断
          </span>
        </template>
        <div class="diagnosis-content">
          <p class="diagnosis-summary">{{ result.observation.diagnosis.summary }}</p>
          
          <el-row :gutter="24">
            <el-col :xs="24" :md="12">
              <div v-if="result.observation.diagnosis.indications?.length" class="diagnosis-indications">
                <div class="sub-title">可能提示的身体状况：</div>
                <ul>
                  <li v-for="(item, idx) in result.observation.diagnosis.indications" :key="idx">
                    {{ item }}
                  </li>
                </ul>
              </div>
            </el-col>
            <el-col :xs="24" :md="12">
              <div v-if="result.observation.diagnosis.suggestions?.length" class="diagnosis-suggestions">
                <div class="sub-title">调理建议：</div>
                <ul>
                  <li v-for="(item, idx) in result.observation.diagnosis.suggestions" :key="idx">
                    {{ item }}
                  </li>
                </ul>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- 操作按钮 -->
      <div v-if="result" class="result-actions">
        <el-button
          v-if="manualSessionId || sessionId"
          type="primary"
          size="large"
          @click="goToConsult"
        >
          <el-icon><Connection /></el-icon>
          前往问诊
        </el-button>
        <el-button
          size="large"
          @click="resetAnalysis"
        >
          <el-icon><Refresh /></el-icon>
          重新分析
        </el-button>
      </div>

      <!-- 舌象对照图 -->
      <el-card class="reference-card" shadow="never">
        <template #header>
          <span class="card-title">
            <el-icon><Reading /></el-icon>
            舌象辨析参考
          </span>
        </template>
        <el-table :data="tongueReference" border stripe>
          <el-table-column prop="feature" label="特征" width="120" />
          <el-table-column prop="normal" label="正常" width="100" />
          <el-table-column prop="variants" label="常见异常" />
          <el-table-column prop="indication" label="常见提示" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, View, Upload, Delete, Search, Picture,
  Flag, Reading, FirstAidKit, Connection, Refresh
} from '@element-plus/icons-vue'
import { consultApi, type ObservationResult } from '@/api'
import { authApi } from '@/api'

const route = useRoute()
const router = useRouter()

const sessionId = computed(() => (route.query.session_id as string) || '')
const manualSessionId = ref('')

const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const analyzing = ref(false)
const result = ref<ObservationResult | null>(null)
const isLoggedIn = ref(!!localStorage.getItem('token'))

const featureList = computed(() => {
  if (!result.value) return []
  const obs = result.value.observation
  return [
    { key: 'tongue_color', label: '舌色', value: obs.tongue_color, tagType: 'danger' },
    { key: 'tongue_coating', label: '苔色', value: obs.tongue_coating, tagType: 'warning' },
    { key: 'coating_thickness', label: '苔厚薄', value: obs.coating_thickness, tagType: 'info' },
    { key: 'coating_texture', label: '苔质', value: obs.coating_texture, tagType: 'info' },
    { key: 'tongue_shape', label: '舌形', value: obs.tongue_shape, tagType: 'success' },
    { key: 'face_color', label: '面色', value: obs.face_color, tagType: 'warning' },
  ]
})

const tongueReference = [
  {
    feature: '舌色',
    normal: '淡红',
    variants: '淡白 / 红 / 绛 / 紫 / 青',
    indication: '淡白→气血虚，红绛→热证，紫→血瘀',
  },
  {
    feature: '苔色',
    normal: '薄白',
    variants: '白 / 黄 / 灰黑',
    indication: '黄苔→热证，灰黑→重证',
  },
  {
    feature: '苔厚薄',
    normal: '薄',
    variants: '厚 / 无苔（剥苔）',
    indication: '厚苔→积滞，剥苔→阴虚',
  },
  {
    feature: '苔质',
    normal: '润',
    variants: '燥 / 腻 / 剥',
    indication: '腻苔→痰湿，燥苔→津液亏损',
  },
  {
    feature: '舌形',
    normal: '正常',
    variants: '胖大 / 瘦薄 / 裂纹',
    indication: '胖大→水湿，裂纹→阴虚',
  },
]

const beforeUpload = (_file: File) => false // prevent auto-upload

const handleFileChange = (file: any) => {
  const raw: File = file.raw
  if (!raw) return

  if (raw.size > 5 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过5MB')
    return
  }

  selectedFile.value = raw
  previewUrl.value = URL.createObjectURL(raw)
  result.value = null
}

const analyzeImage = async () => {
  if (!selectedFile.value) return

  const targetSessionId = sessionId.value || manualSessionId.value || ''

  analyzing.value = true
  try {
    const res = await consultApi.uploadTongueImage(targetSessionId, selectedFile.value)
    result.value = res

    if (isLoggedIn.value) {
      try {
        await authApi.saveTongueArchive({
          session_id: targetSessionId,
          image_name: selectedFile.value?.name || '',
          analysis_json: res,
        })
      } catch {
        // ignore archive save failure
      }
    }

    ElMessage.success('舌象分析完成！')
  } catch (err: any) {
    ElMessage.error('分析失败：' + (err?.response?.data?.error || err?.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
}

const resetAnalysis = () => {
  result.value = null
  previewUrl.value = ''
  selectedFile.value = null
}

const goToConsult = () => {
  router.push('/consult')
}
</script>

<style scoped lang="scss">
$border-color: #e8eaf0;
$primary: #1677ff;

.tongue-page {
  min-height: 100vh;
  background: #f5f7fb;
  padding: 24px;
}

.tongue-container {
  max-width: 1000px;
  margin: 0 auto;
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

.guide-card {
  margin-bottom: 20px;
  border-radius: 12px;

  .guide-content {
    display: flex;
    align-items: flex-start;
    gap: 16px;

    .guide-icon { font-size: 40px; flex-shrink: 0; }

    h4 { margin: 0 0 8px; }
    ul { margin: 0; padding-left: 20px; li { margin: 4px 0; font-size: 13px; color: #555; } }
  }
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
}

/* ─── 固定高度卡片布局 ──────────────────────────────── */
.main-row {
  display: flex;
  flex-wrap: wrap;
}

.fixed-height-card {
  border-radius: 12px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  height: 520px;

  :deep(.el-card__header) {
    flex-shrink: 0;
  }

  :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .card-body {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
}

.upload-card {
  .tongue-uploader {
    flex: 1;

    :deep(.el-upload-dragger) {
      width: 100%;
      height: 100%;
      min-height: 200px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 12px;
    }
  }

  .upload-placeholder {
    text-align: center;

    .upload-icon { font-size: 48px; color: $primary; margin-bottom: 12px; }
    p { font-size: 14px; color: #555; margin: 0 0 6px; }
    small { color: #bbb; }
  }

  .preview-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 200px;

    .preview-img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 8px;
    }

    .preview-overlay {
      position: absolute;
      top: 8px;
      right: 8px;
    }
  }

  .session-bind { 
    margin-top: 12px;
    flex-shrink: 0;
  }

  .analyze-btn {
    width: 100%;
    margin-top: 12px;
    height: 42px;
    flex-shrink: 0;
  }

  .mt-12 { margin-top: 12px; }
}

.result-card {
  .result-empty, .result-analyzing {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #666;

    .empty-icon { 
      font-size: 48px; 
      margin-bottom: 12px;
      color: #ccc;
    }
    p { font-size: 14px; }
  }

  .result-analyzing {
    .analyzing-animation {
      position: relative;
      width: 80px;
      height: 80px;
      margin-bottom: 20px;

      .analyzing-icon {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 36px;
        color: $primary;
        z-index: 1;
      }

      .pulse-ring {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 60px;
        height: 60px;
        border: 3px solid $primary;
        border-radius: 50%;
        opacity: 0;
        animation: pulse 2s ease-out infinite;

        &.delay-1 { animation-delay: 0.5s; }
        &.delay-2 { animation-delay: 1s; }
      }
    }

    .analyzing-text {
      font-size: 16px;
      font-weight: 600;
      color: #333;
      margin: 0 0 8px;
    }

    .analyzing-hint {
      font-size: 13px;
      color: #888;
      margin: 0;
    }
  }

  .result-content {
    flex: 1;
    overflow-y: auto;

    .feature-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      margin-bottom: 16px;

      .feature-item {
        padding: 12px;
        background: #fafafa;
        border-radius: 8px;
        border: 1px solid $border-color;

        .feat-label { font-size: 12px; color: #888; margin-bottom: 6px; }
        .feat-unknown { font-size: 12px; color: #bbb; }
      }
    }

    .image-features {
      margin-top: 8px;

      .feat-section-title {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        color: #666;
        margin-bottom: 8px;
      }

      .feature-tags { display: flex; flex-wrap: wrap; gap: 6px; }
    }

    .mt-16 { margin-top: 16px; }
  }
}

.reference-card {
  border-radius: 12px;
}

/* ─── 舌象诊断卡片 ──────────────────────────────────── */
.diagnosis-card {
  border-radius: 12px;
  margin-top: 24px;
  background: linear-gradient(135deg, #f0f7ff 0%, #e6f7ff 100%);
  border: 1px solid #b3d9ff;

  .diagnosis-content {
    .diagnosis-summary {
      font-size: 15px;
      line-height: 1.8;
      color: #333;
      margin: 0 0 16px;
      padding: 16px;
      background: #fff;
      border-radius: 8px;
      border-left: 4px solid #1890ff;
    }

    .diagnosis-indications, .diagnosis-suggestions {
      .sub-title {
        font-size: 14px;
        font-weight: 600;
        color: #555;
        margin-bottom: 12px;
      }

      ul {
        margin: 0;
        padding-left: 20px;

        li {
          font-size: 14px;
          color: #666;
          margin: 8px 0;
          line-height: 1.6;
        }
      }
    }
  }
}

/* ─── 操作按钮 ──────────────────────────────────── */
.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
}

/* ─── 脉冲动画 ──────────────────────────────────── */
@keyframes pulse {
  0% {
    width: 40px;
    height: 40px;
    opacity: 0.8;
  }
  100% {
    width: 100px;
    height: 100px;
    opacity: 0;
  }
}
</style>
