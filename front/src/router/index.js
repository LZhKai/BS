import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Layout from '../layout/Layout.vue'
import VehicleList from '../views/VehicleList.vue'
import OwnerList from '../views/OwnerList.vue'
import ParkingRecordList from '../views/ParkingRecordList.vue'
import VehicleDetection from '../views/VehicleDetection.vue'
import RAGChat from '../views/RAGChat.vue'
import PlateRecognition from '../views/PlateRecognition.vue'

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
        path: '/owner',
        name: 'OwnerList',
        component: OwnerList
      },
      {
        path: '/parking',
        name: 'ParkingRecordList',
        component: ParkingRecordList
      },
      {
        path: '/rag',
        name: 'RAGChat',
        component: RAGChat
      },
      {
        path: '/detection',
        name: 'VehicleDetection',
        component: VehicleDetection
      },
      {
        path: '/plate-recognition',
        name: 'PlateRecognition',
        component: PlateRecognition
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
