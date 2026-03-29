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
  padding: 18px;
  background: linear-gradient(180deg, #f8fcff 0%, #f3f9f5 100%);
}

.admin-head {
  margin-bottom: 12px;
}

.admin-head h2 {
  margin: 0;
  color: #1e3327;
}

.admin-head p {
  margin: 6px 0 0;
  color: #687f72;
}

.panel-wrap {
  margin-top: 10px;
}
</style>
