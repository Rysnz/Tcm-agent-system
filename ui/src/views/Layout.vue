<template>
  <el-container class="layout-shell">
    <el-header class="topbar">
      <div class="brand" @click="router.push('/home')">
        <div class="brand-logo">
          <div class="brand-dot glow" />
          <div class="brand-dot static" />
        </div>
        <div class="brand-text">
          <h1>杏林语康</h1>
          <p>AI Copilot</p>
        </div>
      </div>

      <el-menu
        :default-active="$route.path"
        class="nav"
        router
        mode="horizontal"
        :ellipsis="false"
      >
        <el-menu-item index="/home">
          <el-icon><House /></el-icon>首页
        </el-menu-item>
        <el-menu-item index="/consult">
          <el-icon><ChatDotRound /></el-icon>智能问诊
        </el-menu-item>
        <el-menu-item index="/consult/tongue">
          <el-icon><View /></el-icon>舌象分析
        </el-menu-item>
        <el-menu-item index="/wellness">
          <el-icon><Sunny /></el-icon>养生管理
        </el-menu-item>

        <div class="right-slot flex items-center">
          <el-dropdown @command="changeTheme" trigger="click" class="theme-switcher">
            <span class="el-dropdown-link">
              <el-icon><MagicStick /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item 
                  v-for="theme in themes" 
                  :key="theme.value" 
                  :command="theme.value"
                  :class="{ 'is-active': currentTheme === theme.value }"
                >
                  {{ theme.label }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-menu-item index="/login" v-if="!isLoggedIn" class="login-btn">
            <el-icon><User /></el-icon>登录 / 注册
          </el-menu-item>
          <el-sub-menu index="/account" v-else class="user-menu">
            <template #title>
              <div class="user-avatar">
                <el-icon><User /></el-icon>
              </div>
              <span>{{ userName }}</span>
            </template>
            <el-menu-item index="/profile"><el-icon><UserFilled /></el-icon>个人档案</el-menu-item>
            <el-menu-item index="/admin" v-if="isAdmin"><el-icon><Setting /></el-icon>后台设置</el-menu-item>
            <el-menu-item index="" @click="logout" class="logout-item"><el-icon><SwitchButton /></el-icon>退出登录</el-menu-item>
          </el-sub-menu>
        </div>
      </el-menu>
    </el-header>

    <el-main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" :key="$route.fullPath" />
        </transition>
      </router-view>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { House, ChatDotRound, View, Sunny, Setting, User, UserFilled, SwitchButton, MagicStick } from '@element-plus/icons-vue'

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

const currentTheme = ref(localStorage.getItem('app-theme') || 'tcm-zen')

const themes = [
  { value: 'tcm-zen', label: 'TCM Zen (中医禅意)' },
  { value: 'modern-clinical', label: 'Modern Clinical (现代临床)' },
  { value: 'dark-future', label: 'Dark Future (暗黑未来)' }
]

const changeTheme = (theme: string) => {
  currentTheme.value = theme
  localStorage.setItem('app-theme', theme)
  document.documentElement.setAttribute('data-theme', theme)
  if (theme === 'dark-future') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('refreshToken')
  localStorage.removeItem('user')
  syncAuthState()
  window.dispatchEvent(new Event('auth-changed'))
  ElMessage.success({
    message: '已退出登录',
    customClass: currentTheme.value === 'dark-future' ? 'dark-message' : ''
  })
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
  background-color: var(--theme-bg);
  color: var(--theme-text);
  overflow: hidden;
}

.topbar {
  height: 70px;
  display: flex;
  align-items: center;
  padding: 0 30px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--theme-border);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  background: var(--theme-overlay);
  position: relative;
  z-index: 100;
}

/* Brand styling */
.brand {
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  margin-right: 40px;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.brand:hover {
  transform: scale(1.02);
}

.brand-logo {
  position: relative;
  width: 24px;
  height: 24px;
}

.brand-dot {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--theme-accent), var(--theme-accent-hover));
}

.brand-dot.static {
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.2);
}

.brand-dot.glow {
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
  filter: blur(8px);
  opacity: 0.8;
  animation: pulse 3s infinite alternate;
}

@keyframes pulse {
  0% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
  100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0.9; }
}

.brand-text h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--theme-text);
}

.brand-text p {
  margin: 0;
  font-size: 11px;
  font-weight: 400;
  color: var(--theme-accent);
  letter-spacing: 2px;
  opacity: 0.8;
  text-transform: uppercase;
}

/* Nav Menu Overrides */
.nav {
  border-bottom: none !important;
  flex: 1;
}

.nav :deep(.el-menu-item),
.nav :deep(.el-sub-menu__title) {
  height: 70px;
  line-height: 70px;
  font-size: 14px;
  font-weight: 500;
  color: var(--theme-text-secondary) !important;
  transition: all 0.3s ease;
  background: transparent !important;
  border-bottom: 2px solid transparent !important;
}

.nav :deep(.el-menu-item:hover),
.nav :deep(.el-sub-menu__title:hover) {
  color: var(--theme-text) !important;
  background: var(--theme-border-light) !important;
}

.nav :deep(.el-menu-item.is-active) {
  color: var(--theme-accent) !important;
  border-bottom: 2px solid var(--theme-accent) !important;
  background: var(--theme-border-light) !important;
}

.nav :deep(.el-icon) {
  margin-right: 6px;
  font-size: 16px;
  transition: transform 0.3s ease;
}

.nav :deep(.el-menu-item:hover .el-icon) {
  transform: translateY(-2px);
}

.right-slot {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 16px;
}

.theme-switcher {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  height: 70px;
  padding: 0 10px;
}

.theme-switcher .el-dropdown-link {
  display: flex;
  align-items: center;
  color: var(--theme-text-secondary);
  transition: color 0.3s ease;
}

.theme-switcher:hover .el-dropdown-link {
  color: var(--theme-accent);
}

.nav :deep(.login-btn) {
  background: var(--theme-card-bg) !important;
  border: 1px solid var(--theme-accent) !important;
  border-bottom: 1px solid var(--theme-accent) !important;
  border-radius: 8px;
  height: 38px !important;
  line-height: 36px !important;
  padding: 0 20px !important;
  color: var(--theme-accent) !important;
  margin-top: 16px;
}

.nav :deep(.login-btn:hover) {
  background: var(--theme-border-light) !important;
  border-color: var(--theme-accent-hover) !important;
  border-bottom-color: var(--theme-accent-hover) !important;
}

.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--theme-card-bg);
  border: 1px solid var(--theme-border);
  color: var(--theme-text);
  margin-right: 8px;
}

.user-avatar .el-icon {
  margin-right: 0 !important;
  font-size: 14px;
}

/* Main Content Area */
.main-content {
  padding: 0;
  height: calc(100vh - 70px);
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  background-color: var(--theme-page-bg);
}

/* Page Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease, transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>