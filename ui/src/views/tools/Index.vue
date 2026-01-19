<template>
  <div class="tools-container">
    <div class="header">
      <h2>工具管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        添加工具
      </el-button>
    </div>
    
    <el-table :data="tools" stripe>
      <el-table-column prop="name" label="工具名称" width="200" />
      <el-table-column prop="tool_type" label="工具类型" width="150" />
      <el-table-column prop="desc" label="描述" show-overflow-tooltip />
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '激活' : '未激活' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="testTool(row)">测试</el-button>
          <el-button link type="danger" @click="deleteTool(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog v-model="showCreateDialog" title="添加工具" width="600px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="工具名称">
          <el-input v-model="formData.name" placeholder="请输入工具名称" />
        </el-form-item>
        <el-form-item label="工具类型">
          <el-select v-model="formData.tool_type">
            <el-option label="辨证分析" value="diagnosis" />
            <el-option label="方剂推荐" value="prescription_search" />
            <el-option label="药材查询" value="herb_query" />
            <el-option label="古籍检索" value="classic_search" />
            <el-option label="配伍禁忌检查" value="contraindication_check" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.desc" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTool">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { toolsApi } from '@/api'

const route = useRoute()
const tools = ref<any[]>([])
const showCreateDialog = ref(false)
const formData = ref({
  name: '',
  tool_type: '',
  desc: ''
})

const loadTools = async () => {
  try {
    tools.value = await toolsApi.getTools()
  } catch (error) {
    ElMessage.error('加载工具列表失败')
  }
}

const saveTool = async () => {
  try {
    await toolsApi.createTool(formData.value)
    ElMessage.success('添加成功')
    showCreateDialog.value = false
    loadTools()
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

const testTool = async (row: any) => {
  try {
    const result = await toolsApi.callTool({
      tool_name: row.tool_type,
      params: { test: true }
    })
    ElMessage.success('测试成功')
  } catch (error) {
    ElMessage.error('测试失败')
  }
}

const deleteTool = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该工具吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    ElMessage.success('删除成功')
    loadTools()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadTools()
})

watch(() => route.path, (newPath) => {
  if (newPath === '/tools') {
    loadTools()
  }
}, { immediate: true })
</script>

<style scoped>
.tools-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
