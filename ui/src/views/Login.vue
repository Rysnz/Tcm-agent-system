<template>
  <div class="auth-page">
    <div class="ambient-bg">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="noise-overlay"></div>
    </div>
    
    <div class="auth-shell glass-card">
      <div class="auth-brand">
        <h2>{{ isRegister ? '创建您的健康账户' : '欢迎回来' }}</h2>
        <p>{{ isRegister ? '注册后自动登录，云端保存问诊与健康档案' : '登录后同步历史问诊、舌象分析和养生计划' }}</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="auth-form"
      >
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large" autocomplete="username" />
        </el-form-item>

        <el-form-item v-if="isRegister" prop="email">
          <el-input v-model="form.email" placeholder="邮箱（选填）" size="large" autocomplete="email" />
        </el-form-item>

        <el-form-item v-if="isRegister" prop="display_name">
          <el-input v-model="form.display_name" placeholder="昵称（选填）" size="large" />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
            autocomplete="current-password"
          />
        </el-form-item>

        <template v-if="!isRegister">
          <el-form-item>
            <div class="helper-row">
              <el-checkbox v-model="rememberMe">记住账号</el-checkbox>
              <el-link type="primary" @click="forgetPassword">忘记密码？</el-link>
            </div>
          </el-form-item>
        </template>

        <el-form-item v-if="isRegister" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" size="large" class="action-btn" @click="submit">
            {{ isRegister ? '注册并登录' : '登录' }}
          </el-button>
        </el-form-item>

        <el-form-item>
          <el-button text class="switch-btn" @click="toggleMode">
            {{ isRegister ? '已有账号？返回登录' : '没有账号？去注册' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)
const rememberMe = ref(true)
const isRegister = ref(false)

const form = reactive({
  username: '',
  email: '',
  display_name: '',
  password: '',
  confirmPassword: ''
})

const confirmPasswordValidator = (_: any, value: string, callback: (err?: Error) => void) => {
  if (!isRegister.value) return callback()
  if (!value) return callback(new Error('请再次输入密码'))
  if (value !== form.password) return callback(new Error('两次密码输入不一致'))
  callback()
}

const passwordValidator = (_: any, value: string, callback: (err?: Error) => void) => {
  if (!value) return callback(new Error('请输入密码'))
  if (isRegister.value && (value.length < 6 || value.length > 32)) {
    return callback(new Error('注册密码长度为6-32位'))
  }
  callback()
}

const rules = computed(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20位', trigger: 'blur' }
  ],
  email: [
    {
      validator: (_: any, value: string, callback: (err?: Error) => void) => {
        if (!isRegister.value || !value) return callback()
        const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
        callback(ok ? undefined : new Error('邮箱格式不正确'))
      },
      trigger: 'blur'
    }
  ],
  password: [
    { validator: passwordValidator, trigger: 'blur' }
  ],
  confirmPassword: [{ validator: confirmPasswordValidator, trigger: 'blur' }]
}))

const saveAuth = (response: any) => {
  localStorage.setItem('token', response.access)
  localStorage.setItem('refreshToken', response.refresh)
  localStorage.setItem('user', JSON.stringify(response.user))
  window.dispatchEvent(new Event('auth-changed'))
}

const submit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    loading.value = true

    if (isRegister.value) {
      const response = await request.post('/auth/register/', {
        username: form.username.trim(),
        password: form.password,
        email: form.email.trim(),
        display_name: form.display_name.trim()
      })
      saveAuth(response)
      ElMessage.success('注册成功，已自动登录')
    } else {
      const response = await request.post('/auth/login/', {
        username: form.username.trim(),
        password: form.password
      })
      saveAuth(response)
      if (rememberMe.value) {
        localStorage.setItem('savedUsername', form.username.trim())
      } else {
        localStorage.removeItem('savedUsername')
      }
      ElMessage.success('登录成功')
    }

    const redirect = (route.query.redirect as string) || '/home'
    router.push(redirect)
  } catch (error: any) {
    const data = error?.response?.data || {}
    const firstFieldErr = Object.values(data).find((v) => Array.isArray(v)) as string[] | undefined
    ElMessage.error(firstFieldErr?.[0] || data.detail || data.error || '操作失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const toggleMode = () => {
  isRegister.value = !isRegister.value
  form.password = ''
  form.confirmPassword = ''
}

const forgetPassword = () => {
  ElMessage.info('请联系管理员重置密码')
}

onMounted(() => {
  const saved = localStorage.getItem('savedUsername')
  if (saved) form.username = saved
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  isolation: isolate;
  background-color: #ffffff;
  color: var(--tcm-text-primary);
  padding: 20px;
  overflow: hidden;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* 沉浸式流体背景 */
.ambient-bg {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.4;
  animation: float 20s infinite ease-in-out alternate;
}

.orb-1 { top: -10%; left: -10%; width: 50vw; height: 50vw; background: radial-gradient(circle, rgba(20,184,166,0.3) 0%, rgba(0,0,0,0) 70%); }
.orb-2 { bottom: -20%; right: -10%; width: 60vw; height: 60vw; background: radial-gradient(circle, rgba(139,92,246,0.2) 0%, rgba(0,0,0,0) 70%); animation-delay: -5s; }

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

.auth-shell {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 420px;
  border-radius: 32px;
  background: color-mix(in srgb, var(--tcm-card-bg) 70%, transparent);
  border: 1px solid var(--tcm-border-color);
  box-shadow: 0 24px 64px color-mix(in srgb, var(--tcm-border-color) 40%, transparent), inset 0 0 0 1px color-mix(in srgb, var(--tcm-text-primary) 5%, transparent);
  padding: 48px 40px;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
}

.auth-shell:hover {
  border-color: color-mix(in srgb, var(--tcm-border-color) 80%, transparent);
  box-shadow: 0 24px 64px color-mix(in srgb, var(--tcm-border-color) 50%, transparent), 0 0 32px rgba(20, 184, 166, 0.15);
}

.auth-brand h2 {
  margin: 0;
  color: var(--tcm-text-primary);
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  background: linear-gradient(135deg, var(--tcm-text-primary) 0%, var(--tcm-accent-color) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.auth-brand p {
  margin: 12px 0 32px;
  color: var(--tcm-text-regular);
  font-size: 15px;
  line-height: 1.6;
}

.helper-row {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 8px;
}

.action-btn {
  width: 100%;
  height: 52px;
  border-radius: 99px;
  background: linear-gradient(135deg, rgba(20,184,166,0.9), rgba(139,92,246,0.9));
  border: none;
  color: #ffffff;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 0.5px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.action-btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 12px 24px rgba(20, 184, 166, 0.4), 0 4px 12px rgba(139, 92, 246, 0.3);
}

.switch-btn {
  width: 100%;
  height: 44px;
  border-radius: 99px;
  color: var(--tcm-text-regular);
  border: 1px solid var(--tcm-border-color);
  transition: all 0.3s;
}

.switch-btn:hover {
  color: var(--tcm-text-primary);
  border-color: var(--tcm-text-primary);
  background: color-mix(in srgb, var(--tcm-text-primary) 5%, transparent);
}

:deep(.auth-form .el-form-item) {
  margin-bottom: 24px;
}

:deep(.auth-form .el-input__wrapper) {
  background: color-mix(in srgb, var(--tcm-text-primary) 4%, transparent);
  border-radius: 99px;
  padding: 0 24px;
  box-shadow: none;
  border: 1px solid var(--tcm-border-color);
  transition: all 0.3s ease;
}

:deep(.auth-form .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.15);
  border-color: rgba(20, 184, 166, 0.5);
  background: color-mix(in srgb, var(--tcm-text-primary) 6%, transparent);
}

:deep(.auth-form .el-input__inner) {
  color: var(--tcm-text-primary);
  height: 48px;
  font-size: 15px;
}

:deep(.auth-form .el-input__inner::placeholder) {
  color: var(--tcm-text-regular);
}

:deep(.el-checkbox__label) {
  color: var(--tcm-text-regular);
}

:deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: var(--tcm-accent-color);
}

:deep(.el-checkbox__inner) {
  background: color-mix(in srgb, var(--tcm-text-primary) 5%, transparent);
  border: 1px solid var(--tcm-border-color);
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background: var(--tcm-accent-color);
  border-color: var(--tcm-accent-color);
}

@media (max-width: 640px) {
  .auth-shell {
    max-width: 100%;
    border-radius: 20px;
    padding: 30px 20px;
  }
}
</style>
