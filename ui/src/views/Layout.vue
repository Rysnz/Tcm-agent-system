<template>
  <el-container class="layout-shell">
    <el-header class="topbar">
      <div class="brand" @click="router.push('/home')">
        <span class="brand-dot" />
        <div>
          <h1>青络中医智能问诊</h1>
          <p>Public Health Copilot</p>
        </div>
      </div>

      <el-menu
        :default-active="$route.path"
        class="nav"
        router
        mode="horizontal"
        :ellipsis="false"
      >
        <el-menu-item index="/home"><el-icon><House /></el-icon>首页</el-menu-item>
        <el-menu-item index="/consult"><el-icon><ChatDotRound /></el-icon>智能问诊</el-menu-item>
        <el-menu-item index="/consult/tongue"><el-icon><View /></el-icon>舌象分析</el-menu-item>
        <el-menu-item index="/wellness"><el-icon><Sunny /></el-icon>养生管理</el-menu-item>

        <el-menu-item index="/login" v-if="!isLoggedIn" class="right-slot">
          <el-icon><User /></el-icon>登录/注册
        </el-menu-item>
        <el-sub-menu index="/account" v-else class="right-slot">
          <template #title><el-icon><User /></el-icon>{{ userName }}</template>
          <el-menu-item index="/profile"><el-icon><UserFilled /></el-icon>个人档案</el-menu-item>
          <el-menu-item index="/admin" v-if="isAdmin"><el-icon><Setting /></el-icon>后台设置</el-menu-item>
          <el-menu-item index="" @click="logout"><el-icon><SwitchButton /></el-icon>退出登录</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-header>

    <el-main class="main-content">
      <router-view :key="$route.fullPath" />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { House, ChatDotRound, View, Sunny, Setting, User, UserFilled, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()

const getAuthState = () => {
  try {
    const token = localStorage.getItem('token')
    const raw = localStorage.getItem('user')
    const user = raw ? JSON.parse(raw) : null
    return { loggedIn: !!token, user }
  } catch {
    return { loggedIn: false, user: null }
  }
}

const authState = ref(getAuthState())
const syncAuthState = () => {
  authState.value = getAuthState()
}

const isLoggedIn = computed(() => authState.value.loggedIn)
const userInfo = computed(() => authState.value.user)
const userName = computed(() => userInfo.value?.display_name || userInfo.value?.username || '我的账户')
const isAdmin = computed(() => !!userInfo.value?.is_staff)

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('refreshToken')
  localStorage.removeItem('user')
  syncAuthState()
  window.dispatchEvent(new Event('auth-changed'))
  ElMessage.success('已退出登录')
  router.push('/home')
}

onMounted(() => {
  window.addEventListener('auth-changed', syncAuthState)
  window.addEventListener('storage', syncAuthState)
})

onUnmounted(() => {
  window.removeEventListener('auth-changed', syncAuthState)
  window.removeEventListener('storage', syncAuthState)
})
</script>

<style scoped>
.layout-shell {
  height: 100vh;
  background: radial-gradient(circle at top right, #e8f3ff 0%, #f9fcff 40%, #f6fbf8 100%);
}

.topbar {
  height: 68px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  border-bottom: 1px solid #e3ece5;
  backdrop-filter: blur(8px);
  background: rgba(255, 255, 255, 0.86);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  margin-right: 16px;
}

.brand-dot {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, #2f9d72, #66b98f);
  box-shadow: 0 0 0 6px rgba(47, 157, 114, 0.12);
}

.brand h1 {
  margin: 0;
  font-size: 15px;
  color: #1f2f27;
}

.brand p {
  margin: 0;
  font-size: 11px;
  color: #7b8f84;
}

.nav {
  border: none;
  background: transparent;
  width: 100%;
  --el-menu-bg-color: transparent;
  --el-menu-border-color: transparent;
  --el-menu-hover-bg-color: rgba(47, 157, 114, 0.12);
  --el-menu-active-color: #1d6a4d;
}

.nav :deep(.el-menu-item),
.nav :deep(.el-sub-menu__title) {
  height: 68px;
  line-height: 68px;
  border-bottom: 2px solid transparent;
}

.nav :deep(.right-slot) {
  margin-left: auto;
}

.main-content {
  padding: 0;
  height: calc(100vh - 68px);
  overflow: auto;
}
</style>
