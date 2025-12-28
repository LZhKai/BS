import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Layout from '../layout/Layout.vue'
import VehicleList from '../views/VehicleList.vue'
import TrafficFlow from '../views/TrafficFlow.vue'
import VehicleDetection from '../views/VehicleDetection.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    component: Layout,
    redirect: '/vehicle',
    children: [
      {
        path: '/vehicle',
        name: 'VehicleList',
        component: VehicleList
      },
      {
        path: '/traffic',
        name: 'TrafficFlow',
        component: TrafficFlow
      },
      {
        path: '/detection',
        name: 'VehicleDetection',
        component: VehicleDetection
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const user = localStorage.getItem('user')
  if (to.path === '/login') {
    next()
  } else {
    if (user) {
      next()
    } else {
      next('/login')
    }
  }
})

export default router

