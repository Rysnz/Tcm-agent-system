import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/views/Layout.vue'
import { isTokenValid } from '@/utils/token'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue')
    },
    {
      path: '/',
      component: Layout,
      children: [
        {
          path: '',
          redirect: '/home'
        },
        // ── 新版主页 ──────────────────────────────────────
        {
          path: 'home',
          name: 'Home',
          component: () => import('@/views/Home.vue')
        },
        // ── 新版多智能体问诊 ──────────────────────────────
        {
          path: 'consult',
          name: 'Consult',
          component: () => import('@/views/consult/Index.vue')
        },
        {
          path: 'consult/tongue',
          name: 'ConsultTongue',
          component: () => import('@/views/consult/Tongue.vue')
        },
        {
          path: 'consult/report',
          name: 'ConsultReport',
          component: () => import('@/views/consult/Report.vue')
        },
        // ── 养生管理 ──────────────────────────────────────
        {
          path: 'wellness',
          name: 'Wellness',
          component: () => import('@/views/wellness/Index.vue')
        },
        {
          path: 'admin',
          name: 'AdminWorkspace',
          meta: { requiresAdmin: true },
          component: () => import('@/views/admin/Index.vue')
        },
        {
          path: 'profile',
          name: 'Profile',
          meta: { requiresAuth: true },
          component: () => import('@/views/Profile.vue')
        },
        // ── 后台管理页（原有功能保留）────────────────────
        {
          path: 'overview',
          redirect: '/admin'
        },
        {
          path: 'model',
          redirect: '/admin'
        },
        {
          path: 'knowledge',
          redirect: '/admin'
        },
        {
          path: 'knowledge/:id/setting',
          meta: { requiresAdmin: true },
          component: () => import('@/views/knowledge/Setting.vue')
        }
      ]
    }
  ]
})

router.beforeEach((to, _from, next) => {
  if (to.path === '/login') {
    next()
    return
  }

  const hasValidToken = isTokenValid()

  if (to.matched.some((record) => record.meta?.requiresAuth) && !hasValidToken) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  if (to.matched.some((record) => record.meta?.requiresAdmin)) {
    if (!hasValidToken) {
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
    try {
      const userRaw = localStorage.getItem('user')
      const user = userRaw ? JSON.parse(userRaw) : null
      if (!user?.is_staff) {
        next('/home')
        return
      }
    } catch {
      next('/home')
      return
    }
  }

  next()
})

export default router
