import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/views/Layout.vue'

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
        // ── 后台管理页（原有功能保留）────────────────────
        {
          path: 'overview',
          name: 'Overview',
          component: () => import('@/views/Overview.vue')
        },
        {
          path: 'model',
          name: 'ModelManagement',
          component: () => import('@/views/model/ModelSetting.vue')
        },
        {
          path: 'knowledge',
          name: 'Knowledge',
          component: () => import('@/views/knowledge/Index.vue')
        },
        {
          path: 'knowledge/:id/setting',
          name: 'KnowledgeSetting',
          component: () => import('@/views/knowledge/Setting.vue')
        }
      ]
    }
  ]
})

export default router
