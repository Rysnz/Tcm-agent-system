<template>
  <div class="tools-container awwwards-theme">
    <div class="ambient-bg">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="noise-overlay"></div>
    </div>
    
    <div class="main-content">
      <div class="header glass-panel">
        <h2 class="gradient-text">工具管理</h2>
        <button class="btn-glow" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          添加工具
        </button>
      </div>
      
      <div class="table-wrapper glass-panel">
        <el-table :data="tools" class="custom-table" style="width: 100%">
          <el-table-column prop="name" label="工具名称" width="200" />
          <el-table-column prop="tool_type" label="工具类型" width="150" />
          <el-table-column prop="desc" label="描述" show-overflow-tooltip />
          <el-table-column prop="is_active" label="状态" width="120">
            <template #default="{ row }">
              <span :class="['status-dot', row.is_active ? 'active' : 'inactive']"></span>
              {{ row.is_active ? '已激活' : '未激活' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right" align="center">
            <template #default="{ row }">
              <button class="btn-action primary" @click="testTool(row)">测试</button>
              <button class="btn-action danger" @click="deleteTool(row)">删除</button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    
    <el-dialog v-model="showCreateDialog" title="添加工具" width="600px" class="glass-dialog">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="工具名称">
          <el-input v-model="formData.name" placeholder="请输入工具名称" />
        </el-form-item>
        <el-form-item label="工具类型">
          <el-select v-model="formData.tool_type" placeholder="请选择工具类型">
            <el-option label="辨证分析" value="diagnosis" />
            <el-option label="方剂推荐" value="prescription_search" />
            <el-option label="药材查询" value="herb_query" />
            <el-option label="古籍检索" value="classic_search" />
            <el-option label="配伍禁忌检查" value="contraindication_check" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.desc" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn-outline" @click="showCreateDialog = false">取消</button>
        <button class="btn-glow" @click="saveTool" style="margin-left: 12px;">确定</button>
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

<style scoped lang="scss">
:root {
  --abyss: #050505;
  --surface: rgba(255, 255, 255, 0.03);
  --border: rgba(255, 255, 255, 0.08);
}

.awwwards-theme {
  position: relative;
  width: 100%;
  min-height: 100vh;
  background-color: #050505;
  color: #ffffff;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  overflow-x: hidden;
  padding: 0;
  box-sizing: border-box;
}

/* 沉浸式背景 */
.ambient-bg {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.3;
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
  position: relative;
  z-index: 10;
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.glass-panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  margin-bottom: 24px;
}

.gradient-text {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(to right, #fff, #14b8a6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 按钮样式 */
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

.btn-action {
  background: transparent; border: none; font-size: 13px; cursor: pointer; padding: 4px 8px;
  transition: all 0.3s; border-radius: 4px; margin: 0 4px;
}
.btn-action.primary { color: #14b8a6; }
.btn-action.primary:hover { background: rgba(20, 184, 166, 0.1); }
.btn-action.danger { color: #ef4444; }
.btn-action.danger:hover { background: rgba(239, 68, 68, 0.1); }

/* 表格包装 */
.table-wrapper {
  padding: 24px;
}

.status-dot {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px;
}
.status-dot.active { background: #10b981; box-shadow: 0 0 8px #10b981; }
.status-dot.inactive { background: #6b7280; }

/* 覆盖 Element Plus 表格与弹窗样式 */
:deep(.el-table) {
  background: transparent !important;
  color: #a1a1aa;
}
:deep(.el-table th.el-table__cell) {
  background: rgba(255, 255, 255, 0.02) !important;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
:deep(.el-table td.el-table__cell) {
  background: transparent !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}
:deep(.el-table--enable-row-hover .el-table__body tr:hover > td.el-table__cell) {
  background-color: rgba(255, 255, 255, 0.05) !important;
}
:deep(.el-table::before) { display: none; }
:deep(.el-table__inner-wrapper::before) { display: none; }

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
