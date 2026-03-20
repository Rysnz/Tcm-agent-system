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
        // ── 后台管理页（需要登录）────────────────────────
        {
          path: 'overview',
          name: 'Overview',
          component: () => import('@/views/Overview.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'model',
          name: 'ModelManagement',
          component: () => import('@/views/model/ModelSetting.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'knowledge',
          name: 'Knowledge',
          component: () => import('@/views/knowledge/Index.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'knowledge/:id/setting',
          name: 'KnowledgeSetting',
          component: () => import('@/views/knowledge/Setting.vue'),
          meta: { requiresAuth: true }
        }
      ]
    }
  ]
})

// 全局路由守卫：保护需要登录的页面
router.beforeEach((to, _from, next) => {
  if (to.meta.requiresAuth && !isTokenValid()) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
