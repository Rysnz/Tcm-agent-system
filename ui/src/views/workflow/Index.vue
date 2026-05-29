<template>
  <div class="workflow-container awwwards-theme">
    <div class="ambient-bg">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="noise-overlay"></div>
    </div>
    
    <div class="main-content">
      <div class="header glass-panel">
        <h2 class="gradient-text">工作流编辑器</h2>
        <div class="header-actions">
          <button class="btn-glow" @click="saveWorkflow">
            <el-icon><Check /></el-icon>
            保存工作流
          </button>
          <button class="btn-outline" @click="validateWorkflow">
            <el-icon><CircleCheck /></el-icon>
            验证工作流
          </button>
        </div>
      </div>
      
      <div class="workflow-canvas glass-panel" ref="canvasRef">
        <div
          v-for="node in nodes"
          :key="node.id"
          class="workflow-node"
          :style="getNodeStyle(node)"
          :data-type="node.type"
          @mousedown="startDrag(node, $event)"
        >
          <div class="node-header">{{ getNodeLabel(node) }}</div>
          <div class="node-body">{{ getNodeDescription(node) }}</div>
        </div>
        
        <svg class="workflow-edges">
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="10"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" class="edge-arrow" />
            </marker>
          </defs>
          <line
            v-for="edge in edges"
            :key="edge.id"
            :x1="getNodePosition(edge.source).x + 150"
            :y1="getNodePosition(edge.source).y + 30"
            :x2="getNodePosition(edge.target).x"
            :y2="getNodePosition(edge.target).y + 30"
            stroke-width="2"
            class="edge-line"
            marker-end="url(#arrowhead)"
          />
        </svg>
      </div>
    </div>
    
    <el-dialog v-model="showNodeDialog" title="节点配置" width="600px">
      <el-form :model="nodeFormData" label-width="100px">
        <el-form-item label="节点类型">
          <el-select v-model="nodeFormData.type" disabled>
            <el-option label="开始" value="start" />
            <el-option label="LLM" value="llm" />
            <el-option label="知识库检索" value="knowledge_retrieval" />
            <el-option label="工具调用" value="tool_call" />
            <el-option label="结束" value="end" />
          </el-select>
        </el-form-item>
        <el-form-item label="节点名称">
          <el-input v-model="nodeFormData.label" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="nodeFormData.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item v-if="nodeFormData.type === 'llm'" label="提示词">
          <el-input v-model="nodeFormData.prompt_template" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item v-if="nodeFormData.type === 'tool_call'" label="工具名称">
          <el-select v-model="nodeFormData.tool_name">
            <el-option label="辨证分析" value="diagnosis" />
            <el-option label="方剂推荐" value="prescription_search" />
            <el-option label="药材查询" value="herb_query" />
            <el-option label="古籍检索" value="classic_search" />
            <el-option label="配伍禁忌检查" value="contraindication_check" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNodeDialog = false" class="btn-outline">取消</el-button>
        <el-button type="primary" @click="saveNodeConfig" class="btn-glow">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, CircleCheck } from '@element-plus/icons-vue'
import { applicationApi } from '@/api'

const route = useRoute()
const nodes = ref<any[]>([])
const edges = ref<any[]>([])

const showNodeDialog = ref(false)
const nodeFormData = reactive({
  id: '',
  type: 'llm',
  label: '',
  description: '',
  prompt_template: '',
  tool_name: ''
})

const getNodeStyle = (node: any) => {
  const typeColors: Record<string, string> = {
    start: '#67c23a',
    llm: '#409eff',
    knowledge_retrieval: '#e6a23c',
    tool_call: '#f56c6c',
    end: '#909399'
  }
  return {
    left: node.position.x + 'px',
    top: node.position.y + 'px',
    backgroundColor: typeColors[node.type] || '#409eff'
  }
}

const getNodeLabel = (node: any) => node.data.label || node.type

const getNodeDescription = (node: any) => node.data.description || ''

const getNodePosition = (nodeId: string) => {
  const node = nodes.value.find(n => n.id === nodeId)
  return node ? node.position : { x: 0, y: 0 }
}

const startDrag = (node: any, event: MouseEvent) => {
  const startX = event.clientX
  const startY = event.clientY
  const startLeft = node.position.x
  const startTop = node.position.y
  
  const onMouseMove = (e: MouseEvent) => {
    const dx = e.clientX - startX
    const dy = e.clientY - startY
    node.position.x = startLeft + dx
    node.position.y = startTop + dy
  }
  
  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const currentApplicationId = ref('')

const loadWorkflow = async () => {
  try {
    const applications = await applicationApi.getApplications()
    if (applications.length > 0) {
      const app = applications[0]
      currentApplicationId.value = app.id
      
      if (app.work_flow && app.work_flow.nodes && app.work_flow.edges) {
        nodes.value = app.work_flow.nodes
        edges.value = app.work_flow.edges
      } else {
        initDefaultWorkflow()
      }
    } else {
      initDefaultWorkflow()
    }
  } catch (error) {
    console.error('加载工作流失败:', error)
    initDefaultWorkflow()
  }
}

const initDefaultWorkflow = () => {
  nodes.value = [
    {
      id: 'start',
      type: 'start',
      data: { label: '开始', description: '中医问诊开始' },
      position: { x: 50, y: 100 }
    },
    {
      id: 'llm1',
      type: 'llm',
      data: { label: '症状采集', description: '收集用户症状信息' },
      position: { x: 250, y: 100 }
    },
    {
      id: 'tool1',
      type: 'tool_call',
      data: { label: '辨证分析', description: '根据症状进行中医辨证' },
      position: { x: 450, y: 100 }
    },
    {
      id: 'knowledge1',
      type: 'knowledge_retrieval',
      data: { label: '知识库检索', description: '从中医知识库检索相关信息' },
      position: { x: 650, y: 100 }
    },
    {
      id: 'end',
      type: 'end',
      data: { label: '结束', description: '问诊结束' },
      position: { x: 850, y: 100 }
    }
  ]
  edges.value = [
    { id: 'e1', source: 'start', target: 'llm1' },
    { id: 'e2', source: 'llm1', target: 'tool1' },
    { id: 'e3', source: 'tool1', target: 'knowledge1' },
    { id: 'e4', source: 'knowledge1', target: 'end' }
  ]
}

const saveWorkflow = async () => {
  if (!currentApplicationId.value) {
    ElMessage.error('未找到应用ID')
    return
  }
  
  try {
    await applicationApi.saveWorkflow({
      application_id: currentApplicationId.value,
      nodes: nodes.value,
      edges: edges.value
    })
    ElMessage.success('工作流已保存')
  } catch (error) {
    console.error('保存工作流失败:', error)
    ElMessage.error('保存工作流失败')
  }
}

const validateWorkflow = async () => {
  if (!currentApplicationId.value) {
    ElMessage.error('未找到应用ID')
    return
  }
  
  try {
    const result = await applicationApi.validateWorkflow({
      application_id: currentApplicationId.value
    })
    
    if (result.valid) {
      ElMessage.success('工作流验证通过')
    } else {
      ElMessage.warning(`工作流验证失败: ${result.errors.join(', ')}`)
    }
  } catch (error) {
    console.error('验证工作流失败:', error)
    ElMessage.error('验证工作流失败')
  }
}

const saveNodeConfig = () => {
  const node = nodes.value.find(n => n.id === nodeFormData.id)
  if (node) {
    node.data.label = nodeFormData.label
    node.data.description = nodeFormData.description
    node.data.prompt_template = nodeFormData.prompt_template
    node.data.tool_name = nodeFormData.tool_name
  }
  showNodeDialog.value = false
}

onMounted(() => {
  loadWorkflow()
})
</script>

<style scoped lang="scss">
.awwwards-theme {
  position: relative;
  width: 100%;
  min-height: calc(100vh - 60px);
  background-color: #050505;
  color: #ffffff;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  overflow: hidden;
}

/* 动态背景 */
.ambient-bg {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0; pointer-events: none; overflow: hidden;
}
.orb {
  position: absolute; border-radius: 50%; filter: blur(100px); opacity: 0.3;
  animation: float 20s infinite ease-in-out alternate;
}
.orb-1 { top: -10%; left: -10%; width: 50vw; height: 50vw; background: radial-gradient(circle, rgba(20,184,166,0.3) 0%, transparent 70%); }
.orb-2 { bottom: -20%; right: -10%; width: 60vw; height: 60vw; background: radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 70%); animation-delay: -5s; }
.noise-overlay {
  position: absolute; inset: 0;
  background: url('data:image/svg+xml;utf8,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)" opacity="0.05"/%3E%3C/svg%3E');
  mix-blend-mode: overlay;
}

@keyframes float {
  0% { transform: scale(1) translate(0, 0); }
  50% { transform: scale(1.1) translate(2%, 2%); }
  100% { transform: scale(0.9) translate(-2%, -2%); }
}

.main-content {
  position: relative; z-index: 10; display: flex; flex-direction: column;
  height: 100%; padding: 20px; box-sizing: border-box; gap: 20px;
}

.glass-panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
}

.gradient-text {
  margin: 0; font-size: 24px; font-weight: 700;
  background: linear-gradient(to right, #fff, #14b8a6, #8b5cf6);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

.header-actions {
  display: flex;
  gap: 16px;
}

/* 发光按钮 */
.btn-glow {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; background: linear-gradient(135deg, rgba(20,184,166,0.2), rgba(139,92,246,0.2));
  border: 1px solid rgba(255,255,255,0.1); border-radius: 100px; color: #fff; font-size: 14px; cursor: pointer; transition: all 0.4s;
}
.btn-glow:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(20, 184, 166, 0.3); border-color: rgba(255,255,255,0.3); }

.btn-outline {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 100px; color: #fff; font-size: 14px; background: transparent; cursor: pointer; transition: all 0.3s;
}
.btn-outline:hover { background: rgba(255, 255, 255, 0.05); border-color: #fff; }

.workflow-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 0 50px rgba(0,0,0,0.5);
  background-image: 
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* 节点玻璃拟态化 */
.workflow-node {
  position: absolute;
  width: 180px;
  border-radius: 12px;
  cursor: move;
  background-color: rgba(20, 20, 20, 0.7) !important;
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255,255,255,0.1);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  transition: box-shadow 0.3s, border-color 0.3s;
  overflow: hidden;
}
.workflow-node:hover {
  box-shadow: 0 12px 40px rgba(20,184,166,0.3);
  border-color: rgba(20,184,166,0.5);
}

/* 根据 data-type 注入光效 */
.workflow-node[data-type="start"]::before { content:''; position:absolute; top:0; left:0; width:100%; height:4px; background: #10b981; }
.workflow-node[data-type="llm"]::before { content:''; position:absolute; top:0; left:0; width:100%; height:4px; background: #8b5cf6; }
.workflow-node[data-type="knowledge_retrieval"]::before { content:''; position:absolute; top:0; left:0; width:100%; height:4px; background: #14b8a6; }
.workflow-node[data-type="tool_call"]::before { content:''; position:absolute; top:0; left:0; width:100%; height:4px; background: #f59e0b; }
.workflow-node[data-type="end"]::before { content:''; position:absolute; top:0; left:0; width:100%; height:4px; background: #ef4444; }

.node-header {
  padding: 12px 16px;
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.node-body {
  padding: 12px 16px;
  color: #a1a1aa;
  font-size: 12px;
  line-height: 1.5;
}

.workflow-edges {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none;
}
.edge-line {
  stroke: rgba(20, 184, 166, 0.6);
  transition: stroke 0.3s;
}
.edge-arrow {
  fill: rgba(20, 184, 166, 0.6);
}

/* 弹窗及表单暗黑覆盖 */
:deep(.el-dialog) {
  background: rgba(15, 15, 15, 0.85) !important;
  backdrop-filter: blur(30px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
}
:deep(.el-dialog__title) { color: #fff; font-weight: 600; }
:deep(.el-form-item__label) { color: #a1a1aa !important; }
:deep(.el-input__wrapper), :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  box-shadow: none !important;
  color: #fff;
}
:deep(.el-input__inner) { color: #fff; }
:deep(.el-select-dropdown) {
  background: rgba(20, 20, 20, 0.9) !important;
  border: 1px solid rgba(255,255,255,0.1);
  backdrop-filter: blur(20px);
}
:deep(.el-select-dropdown__item) { color: #a1a1aa; }
:deep(.el-select-dropdown__item.hover), :deep(.el-select-dropdown__item:hover) {
  background: rgba(255,255,255,0.08); color: #fff;
}
</style>
