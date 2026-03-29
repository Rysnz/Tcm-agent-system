<template>
  <div class="operate-textarea">
    <!-- 已上传文件显示 -->
    <div v-if="fileAllList.length > 0" class="uploaded-files-list">
      <div
        v-for="(file, index) in fileAllList"
        :key="index"
        class="uploaded-file-item"
      >
        <!-- 文件类型图标 -->
        <div class="file-type-icon">
          <el-icon v-if="file.type === 'image'">
            <Picture />
          </el-icon>
          <el-icon v-else-if="file.type === 'video'">
            <VideoPlay />
          </el-icon>
          <el-icon v-else-if="file.type === 'audio'">
            <Headset />
          </el-icon>
          <el-icon v-else>
            <Document />
          </el-icon>
        </div>
        
        <!-- 文件名称 -->
        <div class="file-name">{{ file.name }}</div>
        
        <!-- 上传状态 -->
        <div v-if="file.loading" class="file-loading">
          <el-icon class="loading-icon">
            <Loading />
          </el-icon>
        </div>
        
        <!-- 删除按钮 -->
        <el-button
          v-if="!file.loading"
          type="text"
          size="small"
          @click="handleRemoveFile(file, index)"
          class="file-delete-btn"
        >
          <el-icon>
            <Delete />
          </el-icon>
        </el-button>
      </div>
    </div>
    
    <!-- 录音时长显示 -->
    <div v-if="isRecording" class="operate flex align-center recording-info">
      <span class="el-text el-text--info recording-time">{{ formatTime(recorderTime) }}</span>
      <button class="el-button el-button--primary is-text" @click="stopRecording">
        <span><i class="el-icon app-icon"><svg viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" style="height: 100%; width: 100%;"><path d="M981.333333 512c0 259.2-210.133333 469.333333-469.333333 469.333333S42.666667 771.2 42.666667 512 252.8 42.666667 512 42.666667s469.333333 210.133333 469.333333 469.333333z m-85.333333 0a384 384 0 1 0-768 0 384 384 0 0 0 768 0zM384 341.333333h256c23.466667 0 42.666667 19.072 42.666667 42.666667v256c0 23.552-19.2 42.666667-42.666667 42.666667H384c-23.466667 0-42.666667-19.114667-42.666667-42.666667V384c0-23.594667 19.2-42.666667 42.666667-42.666667z" fill="currentColor"></path></svg></i></span>
      </button>
    </div>
    
    <!-- 滚动容器 -->
    <div class="el-scrollbar">
      <div class="el-scrollbar__wrap el-scrollbar__wrap--hidden-default" style="max-height: 136px;">
        <div class="el-scrollbar__view" style=""></div>
      </div>
      <div class="el-scrollbar__bar is-horizontal" style="display: none;">
        <div class="el-scrollbar__thumb" style="transform: translateX(0%);"></div>
      </div>
      <div class="el-scrollbar__bar is-vertical" style="display: none;">
        <div class="el-scrollbar__thumb" style="transform: translateY(0%);"></div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="flex" style="align-items: end;">
      <!-- 文本输入框 -->
      <div class="el-textarea">
        <textarea
          class="el-textarea__inner"
          maxlength="100000"
          tabindex="0"
          autocomplete="off"
          placeholder="请输入问题"
          rows="2"
          style="min-height: 47px; height: 47px;"
          v-model="inputValue"
          @keydown="handleKeyDown"
          @paste="handlePaste"
          @drop="handleDrop"
          @dragover.prevent
          :disabled="disabled"
        ></textarea>
      </div>
      
      <!-- 操作按钮区域 -->
      <div class="operate flex align-center">
        <!-- 语音输入按钮 -->
        <span class="flex align-center">
          <button
            aria-disabled="false"
            type="button"
            class="el-button is-text"
            @click="toggleVoiceInput"
            :disabled="disabled || uploading"
            :class="{ 'recording': isRecording }"
          >
            <span>
              <i class="el-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
                  <path fill="currentColor" d="M512 128a128 128 0 0 0-128 128v256a128 128 0 1 0 256 0V256a128 128 0 0 0-128-128m0-64a192 192 0 0 1 192 192v256a192 192 0 1 1-384 0V256A192 192 0 0 1 512 64m-32 832v-64a288 288 0 0 1-288-288v-32a32 32 0 0 1 64 0v32a224 224 0 0 0 224 224h64a224 224 0 0 0 224-224v-32a32 32 0 1 1 64 0v32a288 288 0 0 1-288 288v64h64a32 32 0 1 1 0 64H416a32 32 0 1 1 0-64z"></path>
                </svg>
              </i>
            </span>
          </button>
        </span>
        
        <!-- 文件上传按钮 -->
        <span v-if="enableFileUpload" class="flex align-center">
          <input
            ref="fileInput"
            type="file"
            :multiple="true"
            :accept="fileAccept"
            style="display: none;"
            @change="handleFileInputChange"
          />
          <button
            aria-disabled="false"
            type="button"
            class="el-button is-text"
            @click="triggerFileInput"
          >
            <span>
              <el-icon>
                <Plus />
              </el-icon>
            </span>
          </button>
        </span>
        
        <!-- 分隔线 -->
        <div class="el-divider el-divider--vertical" role="separator" style="--el-border-style: solid;"></div>
        
        <!-- 发送按钮 -->
        <button
          type="button"
          class="el-button is-text sent-button"
          :disabled="disabled || !canSend"
          @click="handleSend"
        >
          <span>
            发送
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElUpload } from 'element-plus'
import { Plus, Microphone, Delete, Loading, Picture, VideoPlay, Headset, Document } from '@element-plus/icons-vue'
import { chatApi } from '@/api'

// 组件属性
const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  applicationId: {
    type: String,
    default: 'default'
  },
  enableFileUpload: {
    type: Boolean,
    default: true
  }
})

// 事件
const emit = defineEmits<{
  send: [message: string, files: Array<any>]
}>()

// 输入值
const inputValue = ref('')

// 发送状态
const sending = ref(false)

// 上传状态
const uploading = ref(false)

// 录音状态
const isRecording = ref(false)
const recorderStatus = ref<'START' | 'TRANSCRIBING' | 'STOP'>('STOP')
const recorderTime = ref(0)
let recorderTimer: number | null = null

// 文件上传相关
const fileList = ref<any[]>([])
const fileAllList = ref<any[]>([])
const isDragging = ref(false)
const maxFileCount = 10
const maxFileSize = 50 * 1024 * 1024 // 50MB

// 文件类型配置
const fileTypes = {
  image: ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
  video: ['mp4', 'avi', 'mkv', 'mov', 'flv', 'wmv'],
  audio: ['mp3', 'wav', 'ogg', 'aac', 'm4a'],
  document: ['pdf', 'docx', 'txt', 'xls', 'xlsx', 'md', 'html', 'csv', 'ppt', 'doc']
}

// 计算属性
const uploadUrl = computed(() => {
  return `/chat/upload_file/`
})

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return {
    Authorization: token ? `Bearer ${token}` : ''
  }
})

const fileAccept = computed(() => {
  const allExtensions = Object.values(fileTypes).flat()
  return allExtensions.map(ext => `.${ext}`).join(',')
})

const canSend = computed(() => {
  const result = (inputValue.value.trim() !== '' || fileAllList.value.length > 0) && !sending.value && !uploading.value
  console.log('canSend computed:', {
    inputValue: inputValue.value,
    fileAllListLength: fileAllList.value.length,
    sending: sending.value,
    uploading: uploading.value,
    result: result
  })
  return result
})

// 格式化时间
const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 处理键盘事件
const handleKeyDown = (event: KeyboardEvent) => {
  // Enter 发送消息，Ctrl/Shift/Alt/meta+Enter 换行
  if (event.key === 'Enter' && !event.ctrlKey && !event.shiftKey && !event.altKey && !event.metaKey) {
    event.preventDefault()
    handleSend()
  }
}

// 处理粘贴事件
const handlePaste = async (event: ClipboardEvent) => {
  const items = event.clipboardData?.items
  if (!items) return

  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.type.startsWith('image/')) {
      event.preventDefault()
      const file = item.getAsFile()
      if (file) {
        await handleFileUpload(file)
      }
    }
  }
}

// 处理拖放事件
const handleDrop = async (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false
  
  const files = event.dataTransfer?.files
  if (!files) return

  for (let i = 0; i < files.length; i++) {
    await handleFileUpload(files[i])
  }
}

// 处理文件上传前的验证
const beforeUpload = (file: File) => {
  // 检查文件数量
  if (fileAllList.value.length >= maxFileCount) {
    ElMessage.error(`最多只能上传 ${maxFileCount} 个文件`)
    return false
  }
  
  // 检查文件大小
  if (file.size > maxFileSize) {
    ElMessage.error(`单个文件大小不能超过 ${maxFileSize / 1024 / 1024}MB`)
    return false
  }
  
  // 检查文件类型
  const fileName = file.name.toLowerCase()
  const fileExt = fileName.split('.').pop() || ''
  const isAllowed = Object.values(fileTypes).some(types => types.includes(fileExt))
  
  if (!isAllowed) {
    ElMessage.error('不支持的文件类型')
    return false
  }
  
  return true
}

// 触发文件选择
const fileInput = ref<HTMLInputElement | null>(null)

const triggerFileInput = () => {
  fileInput.value?.click()
}

// 处理文件选择
const handleFileInputChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (files) {
    for (let i = 0; i < files.length; i++) {
      handleFileUpload(files[i])
    }
    // 清空文件选择，允许重新选择相同文件
    input.value = ''
  }
}

// 处理文件上传
const handleFileUpload = async (file: File) => {
  if (!beforeUpload(file)) return
  
  uploading.value = true
  
  try {
    // 确定文件类型
    let fileType = 'other'
    const fileName = file.name.toLowerCase()
    const fileExt = fileName.split('.').pop() || ''
    
    if (fileTypes.image.includes(fileExt)) {
      fileType = 'image'
    } else if (fileTypes.video.includes(fileExt)) {
      fileType = 'video'
    } else if (fileTypes.audio.includes(fileExt)) {
      fileType = 'audio'
    } else if (fileTypes.document.includes(fileExt)) {
      fileType = 'document'
    }
    
    // 添加到文件列表
    const fileItem = {
      name: file.name,
      size: file.size,
      type: fileType,
      file: file,
      loading: true,
      url: '',
      id: Date.now().toString()
    }
    
    fileAllList.value.push(fileItem)
    
    // 执行上传
    const formData = new FormData()
    formData.append('file', file)
    
    console.log('Uploading file:', file.name)
    console.log('FormData:', formData)
    
    const response = await chatApi.uploadFile(formData)
    
    console.log('Upload response:', response)
    console.log('Response keys:', Object.keys(response))
    console.log('Response url:', response.url)
    console.log('Response file_id:', response.file_id)
    
    // 更新文件状态
    const index = fileAllList.value.findIndex(item => item.id === fileItem.id)
    if (index !== -1) {
      fileAllList.value[index] = {
        ...fileAllList.value[index],
        loading: false,
        url: response.url,
        file_id: response.file_id
      }
      console.log('Updated file item:', fileAllList.value[index])
    }
    
    ElMessage.success('文件上传成功')
  } catch (error) {
    console.error('文件上传失败:', error)
    ElMessage.error('文件上传失败')
    // 移除失败的文件
    const index = fileAllList.value.findIndex(item => item.file === file)
    if (index !== -1) {
      fileAllList.value.splice(index, 1)
    }
  } finally {
    uploading.value = false
  }
}

// 处理移除文件
const handleRemoveFile = (file: any, index: number) => {
  fileAllList.value.splice(index, 1)
  ElMessage.success('文件已移除')
}

// 处理发送消息
const handleSend = async () => {
  console.log('handleSend called')
  console.log('canSend.value:', canSend.value)
  console.log('inputValue.value:', inputValue.value)
  console.log('fileAllList.value:', fileAllList.value)
  console.log('sending.value:', sending.value)
  console.log('uploading.value:', uploading.value)
  
  if (!canSend.value) {
    console.log('Cannot send, canSend is false')
    return
  }
  
  sending.value = true
  
  try {
    const message = inputValue.value.trim()
    const files = fileAllList.value.filter(file => !file.loading)
    
    console.log('message:', message)
    console.log('files:', files)
    console.log('files.length:', files.length)
    console.log('files[0]:', files[0])
    
    if (message || files.length > 0) {
      console.log('Emitting send event with message:', message, 'and files:', files)
      emit('send', message, files)
      
      // 清空输入
      inputValue.value = ''
      fileAllList.value = []
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败')
  } finally {
    sending.value = false
  }
}

// 导入recorder-core库及WAV引擎
import * as RecorderCore from 'recorder-core'
import 'recorder-core/src/engine/wav'

// 获取Recorder构造函数
const Recorder = (RecorderCore as any).default || RecorderCore

// 关闭recorder-core的日志
Recorder.CLog = function() {}

// 录音管理器类，参考MaxKB实现
class RecorderManage {
  private recorder: any = null
  private mediaStream: MediaStream | null = null
  private uploadRecording: (blob: Blob, duration: number) => void
  
  constructor(uploadRecording: (blob: Blob, duration: number) => void) {
    this.uploadRecording = uploadRecording
  }
  
  // 初始化录音设备
  async open(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // 请求麦克风权限
        navigator.mediaDevices.getUserMedia({ audio: true })
          .then(stream => {
            this.mediaStream = stream
            
            // 创建Recorder实例，生成WAV格式音频，配置符合讯飞API要求的参数
            const recorder = new Recorder({
              type: 'wav',
              sampleRate: 16000,
              sampleBits: 16,
              numChannels: 1,
              stream: stream
            })
            
            // 打开录音设备
            recorder.open(() => {
              this.recorder = recorder
              resolve()
            }, (error: any) => {
              this.errorCallback(error)
              reject(error)
            })
          })
          .catch(error => {
            this.errorCallback(error)
            reject(error)
          })
      } catch (error) {
        this.errorCallback(error)
        reject(error)
      }
    })
  }
  
  // 开始录音
  start(): void {
    if (this.recorder) {
      this.recorder.start()
      recorderStatus.value = 'START'
      
      // 启动录音时长计时器
      if (recorderTimer) {
        clearInterval(recorderTimer)
      }
      recorderTimer = window.setInterval(() => {
        recorderTime.value++
        // 60秒自动停止录音
        if (recorderTime.value >= 60) {
          clearInterval(recorderTimer)
          recorderTimer = null
          this.stop()
        }
      }, 1000)
    }
  }
  
  // 停止录音
  stop(): void {
    if (this.recorder) {
      isRecording.value = false
      recorderStatus.value = 'TRANSCRIBING'
      
      // 停止录音时长计时器
      if (recorderTimer) {
        clearInterval(recorderTimer)
        recorderTimer = null
      }
      
      ElMessage.info('正在识别语音...')
      
      this.recorder.stop(
        // 成功回调
        (blob: Blob, duration: number) => {
          this.close()
          this.uploadRecording(blob, duration)
        },
        // 错误回调
        (error: any) => {
          this.errorCallback(error)
          this.close()
        }
      )
    } else {
      // 如果录音实例不存在，直接重置状态
      isRecording.value = false
      recorderStatus.value = 'STOP'
      if (recorderTimer) {
        clearInterval(recorderTimer)
        recorderTimer = null
      }
      ElMessage.warning('录音已结束或未开始')
    }
  }
  
  // 关闭录音设备
  private close(): void {
    // 关闭录音实例
    if (this.recorder) {
      this.recorder.close()
      this.recorder = null
    }
    
    // 停止媒体流
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop())
      this.mediaStream = null
    }
  }
  
  // 错误处理
  private errorCallback(error: any): void {
    console.error('录音错误:', error)
    
    // 重置状态
    isRecording.value = false
    recorderStatus.value = 'STOP'
    if (recorderTimer) {
      clearInterval(recorderTimer)
      recorderTimer = null
    }
    
    // 关闭录音设备
    this.close()
    
    // 显示错误信息
    const errorMsg = error instanceof Error ? error.message : '未知错误'
    if (error.name === 'NotAllowedError') {
      ElMessage.error('浏览器未授权使用麦克风，请在浏览器设置中允许')
    } else if (error.name === 'NotFoundError') {
      ElMessage.error('未找到麦克风设备')
    } else if (error.name === 'NotReadableError') {
      ElMessage.error('麦克风设备不可用')
    } else {
      ElMessage.error('录音失败: ' + errorMsg)
    }
  }
}

// 创建录音管理器实例
const uploadRecording = async (audioBlob: Blob, duration: number) => {
  try {
    if (!audioBlob) {
      console.error('录音文件为空')
      ElMessage.error('停止录音失败: 录音文件为空')
      recorderStatus.value = 'STOP'
      return
    }
    
    const result = await chatApi.speechToText(audioBlob, props.applicationId)
    if (result) {
      inputValue.value = result.text || ''
      recorderStatus.value = 'STOP'
      if (result.text) {
        ElMessage.success('语音识别成功')
      } else {
        ElMessage.info('语音识别成功，但未检测到语音')
      }
    } else {
      recorderStatus.value = 'STOP'
      ElMessage.error('语音识别失败: 返回结果格式不正确')
    }
  } catch (error) {
    console.error('语音识别失败:', error)
    const errorMsg = error instanceof Error ? error.message : '未知错误'
    ElMessage.error('语音识别失败: ' + errorMsg)
    recorderStatus.value = 'STOP'
  }
}

// 录音管理器实例
const recorderManage = new RecorderManage(uploadRecording)

// 开始录音
const startRecording = async () => {
  try {
    isRecording.value = true
    recorderTime.value = 0
    
    ElMessage.info('开始录音，请说出您的问题...')
    
    // 初始化录音设备
    await recorderManage.open()
    
    // 开始录音
    recorderManage.start()
  } catch (error) {
    console.error('开始录音失败:', error)
    isRecording.value = false
  }
}

// 停止录音
const stopRecording = () => {
  recorderManage.stop()
}

// 语音输入相关
const toggleVoiceInput = async () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}
</script>

<style scoped>
/* MaxKB 样式 */
.operate-textarea {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background-color: #ffffff;
  border-top: 1px solid #ebeef5;
}

/* Flex 布局工具类 */
.flex {
  display: flex;
}

.align-center {
  align-items: center;
}

/* 上传文件列表 */
.uploaded-files-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.uploaded-file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  max-width: 100%;
}

.file-type-icon {
  font-size: 16px;
  color: #606266;
}

.file-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-loading {
  display: flex;
  align-items: center;
  gap: 4px;
}

.loading-icon {
  font-size: 14px;
  color: #409eff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.file-delete-btn {
  font-size: 14px;
  color: #909399;
  transition: color 0.3s;
}

.file-delete-btn:hover {
  color: #f56c6c;
}

/* 录音信息 */
.recording-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background-color: #fef0f0;
  border: 1px solid #fbc4ab;
  border-radius: 6px;
  color: #f56c6c;
  font-size: 14px;
  margin-bottom: 10px;
}

.recording-time {
  font-weight: bold;
  font-size: 16px;
}

/* 操作区域 */
.operate {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 10px;
}

.operate .el-button {
  padding: 5px;
}

.operate .el-icon {
  font-size: 18px;
  color: #909399;
  transition: color 0.3s;
}

.operate .el-button:hover .el-icon {
  color: #409eff;
}

/* 发送按钮 */
.sent-button {
  margin-left: 5px;
}

.sent-button .el-icon {
  font-size: 20px;
  color: #909399;
  transition: color 0.3s;
}

.sent-button:hover .el-icon {
  color: #409eff;
}

.sent-button .el-icon.active {
  color: #409eff;
}

/* 录音按钮 */
.voice-input-btn {
  font-size: 20px;
  color: #909399;
  transition: color 0.3s;
}

.voice-input-btn:hover {
  color: #409eff;
}

.voice-input-btn.recording {
  color: #f56c6c;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

/* 文本区域 */
.el-textarea {
  flex: 1;
}

.el-textarea__inner {
  border-radius: 8px;
  resize: none;
  transition: all 0.3s;
}

.el-textarea__inner:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}
</style>