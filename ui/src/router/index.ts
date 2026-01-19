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
      path: '/chat',
      name: 'Chat',
      component: () => import('@/views/chat/Index.vue')
    },
    {
      path: '/',
      component: Layout,
      children: [
        {
          path: '',
          redirect: '/overview'
        },
        {
          path: 'overview',
          name: 'Overview',
          component: () => import('@/views/Overview.vue')
        },
        {
          path: 'application',
          name: 'Application',
          component: () => import('@/views/application/Setting.vue')
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
