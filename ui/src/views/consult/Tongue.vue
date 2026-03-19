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

      <el-row :gutter="24">
        <!-- 上传区 -->
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="upload-card">
            <template #header>
              <span class="card-title">上传舌象图片</span>
            </template>

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

            <!-- 会话绑定 -->
            <div class="session-bind" v-if="!sessionId">
              <el-alert
                title="当前无活动问诊会话"
                type="info"
                :closable="false"
                description="舌象分析结果将记录到指定会话中，您也可以先开始问诊再上传。"
              />
              <el-input
                v-model="manualSessionId"
                placeholder="输入问诊会话ID（选填）"
                class="mt-12"
                clearable
              />
            </div>
            <div v-else class="session-tag">
              <el-tag type="success">
                <el-icon><Link /></el-icon>
                已绑定会话：{{ sessionId }}
              </el-tag>
            </div>

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
          </el-card>
        </el-col>

        <!-- 分析结果 -->
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="result-card" v-loading="analyzing">
            <template #header>
              <span class="card-title">分析结果</span>
            </template>

            <div v-if="!result && !analyzing" class="result-empty">
              <el-icon class="empty-icon"><Picture /></el-icon>
              <p>上传并分析舌象图片后，结果将展示在此处</p>
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

              <!-- 操作提示 -->
              <el-alert
                type="success"
                :closable="false"
                class="mt-16"
                title="分析完成"
                description="舌象信息已记录到问诊会话，系统将在辨证时综合考虑这些信息。"
              />

              <el-button
                type="primary"
                class="mt-16"
                style="width: 100%;"
                @click="goToConsult"
              >
                返回继续问诊
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, View, Upload, Delete, Search, Picture,
  Link, Flag, Reading
} from '@element-plus/icons-vue'
import { consultApi, type ObservationResult } from '@/api'

const route = useRoute()
const router = useRouter()

const sessionId = computed(() => (route.query.session_id as string) || '')
const manualSessionId = ref('')

const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const analyzing = ref(false)
const result = ref<ObservationResult | null>(null)

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

  const targetSessionId = sessionId.value || manualSessionId.value
  if (!targetSessionId) {
    ElMessage.warning('请先前往问诊页面开始一次问诊，或手动输入会话ID')
    return
  }

  analyzing.value = true
  try {
    const res = await consultApi.uploadTongueImage(targetSessionId, selectedFile.value)
    result.value = res
    ElMessage.success('舌象分析完成！')
  } catch (err: any) {
    ElMessage.error('分析失败：' + (err?.response?.data?.error || err?.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
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

.upload-card {
  border-radius: 12px;
  margin-bottom: 20px;

  .tongue-uploader {
    :deep(.el-upload-dragger) {
      width: 100%;
      height: 220px;
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
    height: 220px;

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

  .session-bind { margin-top: 16px; }
  .session-tag { margin-top: 12px; }

  .analyze-btn {
    width: 100%;
    margin-top: 16px;
    height: 42px;
  }

  .mt-12 { margin-top: 12px; }
}

.result-card {
  border-radius: 12px;
  margin-bottom: 20px;

  .result-empty {
    text-align: center;
    padding: 40px 20px;
    color: #bbb;

    .empty-icon { font-size: 48px; margin-bottom: 12px; }
    p { font-size: 13px; }
  }

  .result-content {
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
</style>
