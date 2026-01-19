<template>
  <div class="workflow-container">
    <div class="header">
      <h2>工作流编辑器</h2>
      <div class="header-actions">
        <el-button type="primary" @click="saveWorkflow">
          <el-icon><Check /></el-icon>
          保存工作流
        </el-button>
        <el-button @click="validateWorkflow">
          <el-icon><CircleCheck /></el-icon>
          验证工作流
        </el-button>
      </div>
    </div>
    
    <div class="workflow-canvas" ref="canvasRef">
      <div
        v-for="node in nodes"
        :key="node.id"
        class="workflow-node"
        :style="getNodeStyle(node)"
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
            <polygon points="0 0, 10 3.5, 0 7" fill="#409eff" />
          </marker>
        </defs>
        <line
          v-for="edge in edges"
          :key="edge.id"
          :x1="getNodePosition(edge.source).x + 150"
          :y1="getNodePosition(edge.source).y + 30"
          :x2="getNodePosition(edge.target).x"
          :y2="getNodePosition(edge.target).y + 30"
          stroke="#409eff"
          stroke-width="2"
          marker-end="url(#arrowhead)"
        />
      </svg>
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
        <el-button @click="showNodeDialog = false">取消</el-button>
        <el-button type="primary" @click="saveNodeConfig">确定</el-button>
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

<style scoped>
.workflow-container {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}

.header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.workflow-canvas {
  flex: 1;
  position: relative;
  background: #f5f7fa;
  overflow: hidden;
}

.workflow-node {
  position: absolute;
  width: 150px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  cursor: move;
}

.node-header {
  padding: 8px 12px;
  color: #fff;
  font-weight: bold;
  border-radius: 4px 4px 0 0;
}

.node-body {
  padding: 12px;
  background: #fff;
  border-radius: 0 0 4px 4px;
  font-size: 12px;
}

.workflow-edges {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
