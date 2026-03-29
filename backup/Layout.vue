<template>
  <el-container class="layout-container">
    <el-aside width="240px" class="sidebar">
      <div class="logo">
        <h2>中医智能问诊</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        router
      >
        <el-menu-item index="/application">
          <el-icon><Management /></el-icon>
          <span>设置</span>
        </el-menu-item>
        <el-menu-item index="/application/overview">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问诊</span>
        </el-menu-item>
        <el-menu-item index="/model">
          <el-icon><Cpu /></el-icon>
          <span>模型设置</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Document /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/workflow">
          <el-icon><Connection /></el-icon>
          <span>工作流</span>
        </el-menu-item>
        <el-menu-item index="/tools">
          <el-icon><Tools /></el-icon>
          <span>工具管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main class="main-content">
      <router-view :key="activeMenu" />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Management, Document, Connection, ChatDotRound, Tools, Cpu } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
  border-bottom: 1px solid #434a5e;
}

.logo h2 {
  margin: 0;
  color: #fff;
}

.sidebar-menu {
  border: none;
}

.sidebar-menu .el-menu-item {
  color: #bfcbd9;
}

.sidebar-menu .el-menu-item:hover {
  background-color: #263445;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: #409eff;
  color: #fff;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
