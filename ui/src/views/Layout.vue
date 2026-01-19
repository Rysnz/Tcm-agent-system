<template>
  <el-container class="layout-container">
    <el-header class="topbar">
      <div class="logo">
        <h2>中医智能问诊</h2>
      </div>
      <el-menu
        :default-active="$route.path"
        class="topbar-menu"
        router
        mode="horizontal"
        :ellipsis="false"
      >
        <el-menu-item index="/overview">
          <el-icon><DataAnalysis /></el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/application">
          <el-icon><Management /></el-icon>
          <span>设置</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Document /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/model">
          <el-icon><Cpu /></el-icon>
          <span>模型管理</span>
        </el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="main-content">
      <router-view :key="$route.fullPath" />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { DataAnalysis, Management, Document, Cpu } from '@element-plus/icons-vue'
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.topbar {
  background: linear-gradient(135deg, #1e3a8a 0%, #2c3e50 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  gap: 24px;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
}

.logo h2 {
  margin: 0;
  background: linear-gradient(135deg, #fff 0%, #e0e7ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  letter-spacing: 1px;
}

.topbar-menu {
  border: none;
  background-color: transparent;
  color: #fff;
  gap: 8px;
}

.topbar-menu .el-menu-item {
  color: #c0c4cc;
  height: 60px;
  line-height: 60px;
  border-bottom: 3px solid transparent;
  margin: 0;
  padding: 0 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.topbar-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  transform: translateY(-2px);
}

.topbar-menu .el-menu-item.is-active {
  background: rgba(64, 158, 255, 0.15);
  color: #fff;
  border-bottom-color: transparent;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  flex: 1;
  overflow: auto;
}
</style>
