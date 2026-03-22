<template>
  <el-container class="layout-container">
    <el-header class="topbar">
      <div class="logo" @click="$router.push('/home')" style="cursor:pointer;">
        <h2>🌿 中医智能问诊</h2>
      </div>
      <el-menu
        :default-active="$route.path"
        class="topbar-menu"
        router
        mode="horizontal"
        :ellipsis="false"
      >
        <!-- 主要功能 -->
        <el-menu-item index="/home">
          <el-icon><House /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/consult">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问诊</span>
        </el-menu-item>
        <el-menu-item index="/consult/tongue">
          <el-icon><View /></el-icon>
          <span>舌象分析</span>
        </el-menu-item>
        <el-menu-item index="/wellness">
          <el-icon><Sunny /></el-icon>
          <span>养生管理</span>
        </el-menu-item>
        <!-- 后台管理分组（仅登录后可见） -->
        <el-sub-menu v-if="isLoggedIn" index="/admin" class="admin-menu">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>后台管理</span>
          </template>
          <el-menu-item index="/overview">
            <el-icon><DataAnalysis /></el-icon>
            概览
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon><Document /></el-icon>
            知识库
          </el-menu-item>
          <el-menu-item index="/model">
            <el-icon><Cpu /></el-icon>
            模型管理
          </el-menu-item>
        </el-sub-menu>
        <!-- 未登录时显示管理员入口 -->
        <el-menu-item v-else index="/login" class="admin-login-btn">
          <el-icon><Lock /></el-icon>
          <span>管理员登录</span>
        </el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="main-content">
      <router-view :key="$route.fullPath" />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { DataAnalysis, Document, Cpu, House, ChatDotRound, View, Sunny, Setting, Lock } from '@element-plus/icons-vue'
import { isTokenValid } from '@/utils/token'

// Reactive: recomputed whenever localStorage changes (e.g., after login/logout)
const isLoggedIn = computed(() => isTokenValid())
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.topbar {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  gap: 24px;
  height: 60px;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  flex-shrink: 0;
}

.logo h2 {
  margin: 0;
  background: linear-gradient(135deg, #fff 0%, #a8c8ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  letter-spacing: 1px;
  white-space: nowrap;
}

.topbar-menu {
  border: none;
  background-color: transparent;
  color: #fff;
  gap: 4px;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: rgba(255,255,255,0.75);
  --el-menu-active-color: #fff;
  --el-menu-hover-bg-color: rgba(255,255,255,0.1);
  --el-menu-border-color: transparent;
}

.topbar-menu :deep(.el-menu-item) {
  height: 60px;
  line-height: 60px;
  border-bottom: 3px solid transparent;
  padding: 0 14px;
  border-radius: 6px 6px 0 0;
  transition: all 0.2s ease;
  font-weight: 500;
  color: rgba(255,255,255,0.75);
}

.topbar-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff;
}

.topbar-menu :deep(.el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.2) !important;
  color: #fff;
  border-bottom-color: #409eff;
}

.topbar-menu :deep(.el-sub-menu__title) {
  height: 60px;
  line-height: 60px;
  color: rgba(255,255,255,0.75);
  border-bottom: 3px solid transparent;
  padding: 0 14px;
  border-radius: 6px 6px 0 0;
  font-weight: 500;
}

.topbar-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff;
}

.admin-login-btn :deep(.el-menu-item) {
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  border-radius: 6px !important;
  margin: 10px 4px !important;
  height: 36px !important;
  line-height: 36px !important;
}

.main-content {
  background-color: #f5f7fb;
  padding: 0;
  flex: 1;
  overflow: auto;
}
</style>
