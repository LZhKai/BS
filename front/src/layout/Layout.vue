<template>
  <el-container class="layout-container">
    <el-header class="layout-header">
      <div class="header-left">
        <h2>智能小区车辆管理系统</h2>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-icon><User /></el-icon>
            {{ userInfo?.realName || userInfo?.username }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-container>
      <el-aside width="200px" class="layout-aside">
        <el-menu
          :default-active="activeMenu"
          router
          class="sidebar-menu"
        >
          <el-menu-item index="/vehicle">
            <el-icon><Truck /></el-icon>
            <span>车辆管理</span>
          </el-menu-item>
          <el-menu-item index="/owner">
            <el-icon><User /></el-icon>
            <span>车主管理</span>
          </el-menu-item>
          <el-menu-item index="/parking">
            <el-icon><Document /></el-icon>
            <span>停车记录</span>
          </el-menu-item>
          <el-menu-item index="/rag">
            <el-icon><ChatLineRound /></el-icon>
            <span>智能问答</span>
          </el-menu-item>
          <el-menu-item index="/traffic">
            <el-icon><DataAnalysis /></el-icon>
            <span>车流量统计</span>
          </el-menu-item>
          <el-menu-item index="/detection">
            <el-icon><VideoCamera /></el-icon>
            <span>车辆识别</span>
          </el-menu-item>
          <el-menu-item index="/plate-recognition">
            <el-icon><Document /></el-icon>
            <span>车牌识别入库</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userInfo = ref(null)

const activeMenu = computed(() => route.path)

onMounted(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    userInfo.value = JSON.parse(userStr)
  }
})

const handleCommand = (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      localStorage.removeItem('user')
      router.push('/login')
    })
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.layout-header {
  background: #409eff;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.layout-aside {
  background: #304156;
}

.sidebar-menu {
  border-right: none;
  background: #304156;
}

.sidebar-menu .el-menu-item {
  color: #bfcbd9;
}

.sidebar-menu .el-menu-item:hover {
  background: #263445;
  color: #409eff;
}

.sidebar-menu .el-menu-item.is-active {
  background: #409eff;
  color: white;
}

.layout-main {
  background: #f0f2f5;
  padding: 20px;
}
</style>
