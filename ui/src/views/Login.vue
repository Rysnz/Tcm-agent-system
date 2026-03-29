<template>
  <div class="auth-page">
    <div class="auth-shell">
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

<style>
.auth-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  isolation: isolate;
  background:
    radial-gradient(circle at 12% 15%, rgba(61, 153, 121, 0.2), transparent 32%),
    radial-gradient(circle at 88% 12%, rgba(67, 129, 179, 0.18), transparent 34%),
    linear-gradient(135deg, #f7fcff 0%, #f0f8f2 100%);
  padding: 20px;
}

.auth-shell {
  width: 100%;
  max-width: 420px;
  border-radius: 18px;
  border: 1px solid #dce9e1;
  background: rgba(255, 255, 255, 0.93);
  box-shadow: 0 20px 48px rgba(24, 54, 38, 0.12);
  padding: 26px 24px 18px;
  backdrop-filter: blur(10px);
}

.auth-brand h2 {
  margin: 0;
  color: #1e3227;
  font-size: 26px;
  line-height: 1.2;
}

.auth-brand p {
  margin: 8px 0 18px;
  color: #708679;
  font-size: 13px;
}

.helper-row {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2f9776, #2a86a3);
  border: none;
}

.switch-btn {
  width: 100%;
}

.auth-form .el-form-item {
  margin-bottom: 14px;
}

.auth-form .el-input__wrapper {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #d7e6dc inset;
}

.auth-form .el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1px #56aa84 inset;
}

.auth-form .el-button + .el-button {
  margin-left: 0;
}

@media (max-width: 640px) {
  .auth-shell {
    max-width: 100%;
    border-radius: 14px;
    padding: 22px 16px 14px;
  }
}
</style>
