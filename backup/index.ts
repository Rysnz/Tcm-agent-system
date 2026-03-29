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
      meta: {
        requiresAuth: true
      },
      children: [
        {
          path: '',
          redirect: '/application'
        },
        {
          path: 'application',
          name: 'Application',
          component: () => import('@/views/application/Setting.vue')
        },
        {
          path: 'application/overview',
          name: 'ApplicationOverview',
          component: () => import('@/views/application/Overview.vue')
        },
        {
          path: 'knowledge',
          name: 'Knowledge',
          component: () => import('@/views/knowledge/Index.vue')
        },
        {
          path: 'workflow',
          name: 'Workflow',
          component: () => import('@/views/workflow/Index.vue')
        },
        {
          path: 'tools',
          name: 'Tools',
          component: () => import('@/views/tools/Index.vue')
        },
        {
          path: 'model',
          name: 'Model',
          component: () => import('@/views/model/ModelSetting.vue')
        },
        {
          path: 'chat',
          name: 'Chat',
          component: () => import('@/views/chat/Index.vue')
        }
      ]
    }
  ]
})

// 添加路由守卫
import { isTokenValid } from '@/utils/token'

router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!isTokenValid()) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
