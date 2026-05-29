<template>
  <div class="tongue-page">
    <div class="tongue-container">
      <!-- 页面头 -->
      <div class="page-header">
        <el-button @click="$router.back()" :icon="ArrowLeft" plain class="bento-back-btn">返回</el-button>
        <h2 class="page-title">
          <el-icon><View /></el-icon>
          舌象分析（望诊）
        </h2>
        <div style="width: 80px;" />
      </div>

      <div class="bento-layout-grid">
        <!-- 说明卡片 -->
        <div class="bento-tile guide-tile">
          <div class="guide-content">
            <div class="guide-icon">📷</div>
            <div>
              <h4>拍摄建议</h4>
              <ul>
                <li>在自然光线下伸出舌头正对摄像头</li>
                <li>保持舌面平展，舌尖向前</li>
                <li>避免饮食后立即拍摄</li>
                <li>图片清晰、无遮挡</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- 上传区 -->
        <div class="bento-tile upload-tile">
          <div class="bento-tile-header">
            <span class="card-title">上传舌象图片</span>
          </div>

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
        </div>

        <!-- 分析结果 -->
        <div class="bento-tile result-tile" v-loading="analyzing">
          <div class="bento-tile-header">
            <span class="card-title">分析结果</span>
          </div>

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
                <div class="feature-item bento-sub-tile" v-for="feat in featureList" :key="feat.key">
                  <div class="feat-label">{{ feat.label }}</div>
                  <div class="feat-value">
                    <el-tag v-if="feat.value" :type="feat.tagType" effect="light" class="modern-tag">
                      {{ feat.value }}
                    </el-tag>
                    <span v-else class="feat-unknown">未检测到</span>
                  </div>
                </div>
              </div>

              <!-- 图像特征标签 -->
              <div v-if="result.observation.image_features?.length" class="image-features bento-sub-tile">
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
                    class="modern-tag"
                  >{{ f }}</el-tag>
                </div>
              </div>

              <!-- 分析完成提示 -->
              <div class="modern-alert mt-16">
                <div class="alert-content">
                  <span class="alert-title">分析完成</span>
                  <span class="alert-desc">舌象特征信息已提取完成。</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 舌象诊断（独立区域） -->
        <div v-if="result?.observation?.diagnosis?.summary" class="bento-tile diagnosis-tile">
          <div class="bento-tile-header">
            <span class="card-title">
              <el-icon><FirstAidKit /></el-icon>
              舌象诊断
            </span>
          </div>
          <div class="diagnosis-content">
            <p class="diagnosis-summary">{{ result.observation.diagnosis.summary }}</p>
            
            <div class="diagnosis-grid">
              <div v-if="result.observation.diagnosis.indications?.length" class="diagnosis-box bento-sub-tile">
                <div class="sub-title">可能提示的身体状况：</div>
                <ul>
                  <li v-for="(item, idx) in result.observation.diagnosis.indications" :key="idx">
                    {{ item }}
                  </li>
                </ul>
              </div>
              <div v-if="result.observation.diagnosis.suggestions?.length" class="diagnosis-box bento-sub-tile">
                <div class="sub-title">调理建议：</div>
                <ul>
                  <li v-for="(item, idx) in result.observation.diagnosis.suggestions" :key="idx">
                    {{ item }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div v-if="result" class="bento-tile actions-tile">
          <div class="result-actions">
            <el-button
              v-if="manualSessionId || sessionId"
              type="primary"
              size="large"
              class="modern-btn primary-btn"
              @click="goToConsult"
            >
              <el-icon><Connection /></el-icon>
              前往问诊
            </el-button>
            <el-button
              size="large"
              class="modern-btn secondary-btn"
              @click="resetAnalysis"
            >
              <el-icon><Refresh /></el-icon>
              重新分析
            </el-button>
          </div>
        </div>

        <!-- 舌象对照图 -->
        <div class="bento-tile reference-tile">
          <div class="bento-tile-header">
            <span class="card-title">
              <el-icon><Reading /></el-icon>
              舌象辨析参考
            </span>
          </div>
          <div class="reference-table-wrapper">
            <el-table :data="tongueReference" border stripe class="modern-table">
              <el-table-column prop="feature" label="特征" width="120" />
              <el-table-column prop="normal" label="正常" width="100" />
              <el-table-column prop="variants" label="常见异常" />
              <el-table-column prop="indication" label="常见提示" />
            </el-table>
          </div>
        </div>
      </div>
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
$primary: var(--tcm-accent-color);

.tongue-page {
  min-height: 100vh;
  background: transparent;
  padding: 30px;
  color: var(--tcm-text-primary);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.tongue-container {
  max-width: 1100px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;

  .bento-back-btn {
    background: var(--tcm-page-bg);
    border: 1px solid var(--tcm-border-color);
    border-radius: 20px;
    padding: 8px 20px;
    color: var(--tcm-text-regular);
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
    &:hover { background: var(--tcm-page-bg); border-color: var(--tcm-accent-color); color: var(--tcm-accent-color); transform: scale(1.05); }
  }

  .page-title {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0;
    font-size: 26px;
    font-weight: 700;
    color: var(--tcm-text-primary);
  }
}

/* ─── 现代 Bento 布局系统 ──────────────────────────────── */
.bento-layout-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  grid-auto-rows: minmax(auto, auto);
  gap: 24px;
}

.bento-tile {
  background: var(--tcm-card-bg);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: 32px;
  border: 1px solid var(--tcm-border-color);
  box-shadow: var(--tcm-shadow);
  padding: 32px;
  transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--tcm-shadow);
    border-color: var(--tcm-accent-color);
  }
}

.bento-sub-tile {
  background: var(--tcm-page-bg);
  border-radius: 20px;
  border: 1px solid var(--tcm-border-color);
  padding: 20px;
}

.bento-tile-header {
  margin-bottom: 24px;
  .card-title {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 18px;
    font-weight: 700;
    color: var(--tcm-text-primary);
  }
}

/* ─── 个别区块定义 ──────────────────────────────── */
.guide-tile {
  grid-column: span 12;
  padding: 24px 32px;

  .guide-content {
    display: flex;
    align-items: center;
    gap: 24px;

    .guide-icon { font-size: 48px; flex-shrink: 0; filter: drop-shadow(0 0 15px var(--tcm-border-color)); }

    h4 { margin: 0 0 12px; color: var(--tcm-text-primary); font-size: 18px; font-weight: 600; }
    ul { 
      margin: 0; 
      padding-left: 0;
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      list-style: none;
      li { 
        font-size: 14px; 
        color: var(--tcm-text-regular);
        background: var(--tcm-page-bg);
        padding: 8px 16px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
        &::before { content: "•"; color: var(--tcm-accent-color); font-weight: bold; }
      } 
    }
  }
}

.upload-tile {
  grid-column: span 5;
  height: 540px;

  .card-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .tongue-uploader {
    flex: 1;
    display: flex;
    flex-direction: column;

    :deep(.el-upload) { height: 100%; }
    :deep(.el-upload-dragger) {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 24px;
      background: var(--tcm-page-bg);
      border: 2px dashed var(--tcm-border-color);
      transition: all 0.3s;

      &:hover {
        border-color: var(--tcm-accent-color);
        background: var(--tcm-bg-color);
        transform: scale(1.02);
      }
    }
  }

  .upload-placeholder {
    text-align: center;
    .upload-icon { font-size: 64px; color: var(--tcm-accent-color); margin-bottom: 20px; opacity: 0.9; }
    p { font-size: 16px; font-weight: 600; color: var(--tcm-text-primary); margin: 0 0 10px; }
    small { color: var(--tcm-text-regular); font-size: 13px; }
  }

  .preview-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    max-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;

    .preview-img {
      width: 100%;
      height: 100%;
      max-height: 300px;
      object-fit: contain;
      border-radius: 20px;
      box-shadow: var(--tcm-shadow);
    }

    .preview-overlay {
      position: absolute;
      top: 16px;
      right: 16px;
      
      .el-button {
        background: var(--tcm-page-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--tcm-border-color);
        color: #ef4444;
        width: 44px;
        height: 44px;
        font-size: 20px;
        &:hover { background: #ef4444; color: #fff; transform: scale(1.1); border-color: #ef4444; }
      }
    }
  }

  .analyze-btn {
    width: 100%;
    height: 56px;
    border-radius: 16px;
    font-size: 16px;
    font-weight: 600;
    background: var(--tcm-accent-color);
    border: none;
    color: #fff;
    box-shadow: var(--tcm-shadow);
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: var(--tcm-shadow);
      opacity: 0.9;
    }
    
    &:disabled {
      background: var(--tcm-page-bg);
      color: var(--tcm-text-regular);
      box-shadow: none;
      border: 1px solid var(--tcm-border-color);
    }
  }
}

.result-tile {
  grid-column: span 7;
  height: 540px;

  .card-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    padding-right: 8px;

    &::-webkit-scrollbar { width: 6px; }
    &::-webkit-scrollbar-thumb { background: var(--tcm-border-color); border-radius: 3px; }
  }

  .result-empty, .result-analyzing {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: var(--tcm-text-regular);

    .empty-icon { font-size: 72px; margin-bottom: 24px; color: var(--tcm-border-color); }
    p { font-size: 16px; max-width: 60%; line-height: 1.6; }
  }

  .result-analyzing {
    .analyzing-animation {
      position: relative;
      width: 120px;
      height: 120px;
      margin-bottom: 30px;

      .analyzing-icon {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 48px;
        color: var(--tcm-accent-color);
        z-index: 1;
      }

      .pulse-ring {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 80px;
        height: 80px;
        border: 2px solid var(--tcm-accent-color);
        border-radius: 50%;
        opacity: 0;
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;

        &.delay-1 { animation-delay: 0.6s; }
        &.delay-2 { animation-delay: 1.2s; }
      }
    }

    .analyzing-text { font-size: 20px; font-weight: 700; color: var(--tcm-text-primary); margin: 0 0 12px; }
    .analyzing-hint { font-size: 15px; color: var(--tcm-text-regular); margin: 0; }
  }

  .feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 24px;

    .feature-item {
      display: flex;
      flex-direction: column;
      gap: 12px;
      align-items: flex-start;

      .feat-label { font-size: 14px; font-weight: 600; color: var(--tcm-text-regular); }
      .feat-unknown { font-size: 14px; color: var(--tcm-text-regular); font-style: italic; }
      
      .modern-tag {
        border-radius: 12px;
        padding: 6px 12px;
        font-size: 14px;
        font-weight: 600;
        border: none;
      }
      :deep(.el-tag--danger) { background: var(--el-color-danger-light-9); color: var(--el-color-danger); }
      :deep(.el-tag--warning) { background: var(--el-color-warning-light-9); color: var(--el-color-warning); }
      :deep(.el-tag--success) { background: var(--el-color-success-light-9); color: var(--el-color-success); }
      :deep(.el-tag--info) { background: var(--el-color-info-light-9); color: var(--el-color-info); }
    }
  }

  .image-features {
    .feat-section-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 15px;
      font-weight: 600;
      color: var(--tcm-text-primary);
      margin-bottom: 16px;
    }
    .feature-tags { 
      display: flex; 
      flex-wrap: wrap; 
      gap: 10px; 
      
      .modern-tag {
        background: rgba(245,158,11,0.1);
        border: 1px solid rgba(245,158,11,0.2);
        color: var(--el-color-warning);
        border-radius: 12px;
        padding: 6px 14px;
        font-weight: 600;
      }
    }
  }

  .modern-alert {
    background: linear-gradient(135deg, var(--tcm-bg-color), var(--tcm-page-bg));
    border: 1px solid var(--tcm-accent-color);
    border-radius: 16px;
    padding: 16px 20px;
    margin-top: 24px;
    
    .alert-content {
      display: flex;
      flex-direction: column;
      gap: 4px;
      
      .alert-title { font-size: 15px; font-weight: 700; color: var(--tcm-accent-color); }
      .alert-desc { font-size: 14px; color: var(--tcm-text-regular); }
    }
  }
}

.diagnosis-tile {
  grid-column: span 12;
  background: var(--tcm-card-bg);
  border-color: var(--tcm-border-color);

  .diagnosis-content {
    .diagnosis-summary {
      font-size: 18px;
      line-height: 1.6;
      color: var(--tcm-text-primary);
      font-weight: 500;
      margin: 0 0 24px;
      padding: 24px;
      background: var(--tcm-page-bg);
      border-radius: 20px;
      border-left: 6px solid var(--tcm-accent-color);
    }

    .diagnosis-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 24px;

      .diagnosis-box {
        .sub-title {
          font-size: 16px;
          font-weight: 700;
          color: var(--tcm-text-primary);
          margin-bottom: 16px;
          display: flex;
          align-items: center;
          &::before {
            content: "";
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--tcm-accent-color);
            margin-right: 10px;
          }
        }
        ul {
          margin: 0; padding-left: 24px;
          li { font-size: 15px; color: var(--tcm-text-regular); margin: 12px 0; line-height: 1.6; }
        }
      }
    }
  }
}

.actions-tile {
  grid-column: span 12;
  padding: 24px;
  background: var(--tcm-card-bg);
  border-color: var(--tcm-border-color);

  .result-actions {
    display: flex;
    gap: 20px;
    justify-content: center;
    
    .modern-btn {
      height: 56px;
      padding: 0 40px;
      border-radius: 28px;
      font-size: 16px;
      font-weight: 600;
      
      &.primary-btn {
        background: var(--tcm-accent-color);
        color: #fff;
        border: none;
        &:hover { transform: scale(1.05); box-shadow: var(--tcm-shadow); opacity: 0.9; }
      }
      
      &.secondary-btn {
        background: var(--tcm-page-bg);
        border: 1px solid var(--tcm-border-color);
        color: var(--tcm-text-primary);
        &:hover { background: var(--tcm-bg-color); transform: scale(1.05); border-color: var(--tcm-accent-color); }
      }
    }
  }
}

.reference-tile {
  grid-column: span 12;

  .reference-table-wrapper {
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid var(--tcm-border-color);
  }

  :deep(.modern-table) {
    background: transparent;
    --el-table-border-color: var(--tcm-border-color);
    --el-table-header-bg-color: var(--tcm-page-bg);
    --el-table-header-text-color: var(--tcm-text-primary);
    --el-table-row-hover-bg-color: var(--tcm-bg-color);
    --el-table-text-color: var(--tcm-text-primary);
    
    th.el-table__cell { background: var(--tcm-page-bg) !important; font-weight: 600; padding: 16px; }
    tr { background: var(--tcm-card-bg) !important; }
    td.el-table__cell { border-bottom: 1px solid var(--tcm-border-color); color: var(--tcm-text-regular); padding: 16px; }
  }
}

/* ─── 动画 ──────────────────────────────────── */
@keyframes pulse {
  0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.8; }
  100% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
}

@media (max-width: 992px) {
  .upload-tile, .result-tile { grid-column: span 12; height: auto; min-height: 400px; }
  .diagnosis-tile .diagnosis-content .diagnosis-grid { grid-template-columns: 1fr; }
  .result-tile .feature-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
