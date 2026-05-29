<template>
  <div class="admin-page">
    <div class="admin-head">
      <h2>后台管理</h2>
      <p>统一入口：概览、知识库、模型管理</p>
    </div>

    <el-tabs v-model="active" type="card">
      <el-tab-pane label="系统仪表盘" name="overview" />
      <el-tab-pane label="知识库" name="knowledge" />
      <el-tab-pane label="模型管理" name="model" />
    </el-tabs>

    <div v-if="active === 'overview'" class="panel-wrap">
      <Overview />
    </div>
    <div v-if="active === 'knowledge'" class="panel-wrap">
      <KnowledgeIndex />
    </div>
    <div v-if="active === 'model'" class="panel-wrap">
      <ModelSetting />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Overview from '@/views/Overview.vue'
import KnowledgeIndex from '@/views/knowledge/Index.vue'
import ModelSetting from '@/views/model/ModelSetting.vue'

const active = ref('overview')
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  padding: 24px;
  background-color: transparent;
  color: var(--tcm-text-primary);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

.admin-head {
  margin-bottom: 24px;
}

.admin-head h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--tcm-text-primary);
  background: linear-gradient(to right, var(--tcm-text-primary), var(--tcm-accent-color));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.admin-head p {
  margin: 8px 0 0;
  color: var(--tcm-text-regular);
  font-size: 15px;
}

:deep(.el-tabs__item) {
  color: var(--tcm-text-regular);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  border: none !important;
  border-radius: 99px;
  margin: 0 4px;
  height: 40px;
  line-height: 40px;
  padding: 0 24px !important;
  font-weight: 500;
}

:deep(.el-tabs__item.is-active) {
  color: #ffffff !important;
  background: var(--tcm-accent-color);
  font-weight: 600;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--tcm-accent-color) 30%, transparent);
}

:deep(.el-tabs__item:hover:not(.is-active)) {
  color: var(--tcm-text-primary);
  background: color-mix(in srgb, var(--tcm-text-primary) 5%, transparent);
}

:deep(.el-tabs--card > .el-tabs__header) {
  border-bottom: none;
  margin-bottom: 24px;
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__nav) {
  border: none;
  background: color-mix(in srgb, var(--tcm-text-primary) 3%, transparent);
  border-radius: 99px;
  padding: 6px;
  display: inline-flex;
  box-shadow: inset 0 2px 4px color-mix(in srgb, var(--tcm-text-primary) 5%, transparent);
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__item) {
  border-left: none;
  background: transparent;
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__item:first-child) {
  border-left: none;
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__item.is-active) {
  background: var(--tcm-accent-color);
  border-bottom-color: transparent;
}

.panel-wrap {
  margin-top: 20px;
  background: color-mix(in srgb, var(--tcm-text-primary) 2%, transparent);
  border: 1px solid color-mix(in srgb, var(--tcm-text-primary) 4%, transparent);
  border-radius: 24px;
  padding: 32px;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow: 0 20px 40px color-mix(in srgb, var(--tcm-text-primary) 10%, transparent), inset 0 1px 0 color-mix(in srgb, var(--tcm-text-primary) 5%, transparent);
}

/* 全局 el-table 高级定制 */
:deep(.el-table) {
  background-color: transparent;
  border-radius: 16px;
  overflow: hidden;
  --el-table-border-color: transparent;
  --el-table-border: none;
  --el-table-text-color: var(--tcm-text-primary);
  --el-table-header-text-color: var(--tcm-text-regular);
  --el-table-row-hover-bg-color: color-mix(in srgb, var(--tcm-text-primary) 4%, transparent);
  --el-table-current-row-bg-color: color-mix(in srgb, var(--tcm-accent-color) 10%, transparent);
  --el-table-header-bg-color: color-mix(in srgb, var(--tcm-text-primary) 2%, transparent);
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-expanded-cell-bg-color: transparent;
}

:deep(.el-table th.el-table__cell) {
  background-color: var(--el-table-header-bg-color) !important;
  border-bottom: 1px solid color-mix(in srgb, var(--tcm-text-primary) 5%, transparent) !important;
  padding: 16px 24px;
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.5px;
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid color-mix(in srgb, var(--tcm-text-primary) 3%, transparent) !important;
  padding: 20px 24px;
  transition: background-color 0.3s;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background-color: color-mix(in srgb, var(--tcm-text-primary) 1%, transparent) !important;
}

:deep(.el-table__inner-wrapper::before) {
  display: none;
}

:deep(.el-table .el-table__row:hover td.el-table__cell) {
  background-color: color-mix(in srgb, var(--tcm-accent-color) 5%, transparent) !important;
}
</style>
