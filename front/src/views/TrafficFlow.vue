<template>
  <div class="traffic-flow-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>实时车流量统计</span>
          <div>
            <el-button
              :type="isConnected ? 'danger' : 'primary'"
              @click="toggleConnection"
            >
              {{ isConnected ? '断开连接' : '连接数据流' }}
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.todayCount }}</div>
              <div class="stat-label">今日车流量</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.currentHourCount }}</div>
              <div class="stat-label">当前小时</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.entryCount }}</div>
              <div class="stat-label">进入车辆</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.exitCount }}</div>
              <div class="stat-label">离开车辆</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 图表区域 -->
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>实时车流量趋势</span>
            </template>
            <div ref="trafficChartRef" style="height: 400px"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>进出车辆对比</span>
            </template>
            <div ref="comparisonChartRef" style="height: 400px"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 实时数据表格 -->
      <el-card style="margin-top: 20px">
        <template #header>
          <span>实时数据流</span>
        </template>
        <el-table :data="realtimeData" border style="width: 100%" max-height="300">
          <el-table-column prop="timestamp" label="时间" width="180" />
          <el-table-column prop="entryCount" label="进入" width="100" />
          <el-table-column prop="exitCount" label="离开" width="100" />
          <el-table-column prop="totalCount" label="总计" width="100" />
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { streamingWS } from '../api/streaming'

const isConnected = ref(false)
const trafficChartRef = ref(null)
const comparisonChartRef = ref(null)
let trafficChart = null
let comparisonChart = null

const stats = ref({
  todayCount: 0,
  currentHourCount: 0,
  entryCount: 0,
  exitCount: 0
})

const realtimeData = ref([])
const maxDataPoints = 20 // 最多显示20条数据

// 时间序列数据
const timeSeriesData = {
  timestamps: [],
  entryData: [],
  exitData: [],
  totalData: []
}

// 初始化图表
const initCharts = () => {
  // 车流量趋势图
  trafficChart = echarts.init(trafficChartRef.value)
  trafficChart.setOption({
    title: {
      text: '实时车流量趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['进入', '离开', '总计'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value',
      name: '车辆数'
    },
    series: [
      {
        name: '进入',
        type: 'line',
        data: [],
        smooth: true
      },
      {
        name: '离开',
        type: 'line',
        data: [],
        smooth: true
      },
      {
        name: '总计',
        type: 'line',
        data: [],
        smooth: true
      }
    ]
  })

  // 进出车辆对比图
  comparisonChart = echarts.init(comparisonChartRef.value)
  comparisonChart.setOption({
    title: {
      text: '进出车辆对比',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['进入', '离开'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value',
      name: '车辆数'
    },
    series: [
      {
        name: '进入',
        type: 'bar',
        data: []
      },
      {
        name: '离开',
        type: 'bar',
        data: []
      }
    ]
  })
}

// 更新图表数据
const updateCharts = (data) => {
  const timestamp = new Date(data.timestamp).toLocaleTimeString()
  
  // 更新时间序列数据
  timeSeriesData.timestamps.push(timestamp)
  timeSeriesData.entryData.push(data.entryCount || 0)
  timeSeriesData.exitData.push(data.exitCount || 0)
  timeSeriesData.totalData.push(data.totalCount || 0)

  // 限制数据点数量
  if (timeSeriesData.timestamps.length > maxDataPoints) {
    timeSeriesData.timestamps.shift()
    timeSeriesData.entryData.shift()
    timeSeriesData.exitData.shift()
    timeSeriesData.totalData.shift()
  }

  // 更新趋势图
  trafficChart.setOption({
    xAxis: {
      data: timeSeriesData.timestamps
    },
    series: [
      {
        data: timeSeriesData.entryData
      },
      {
        data: timeSeriesData.exitData
      },
      {
        data: timeSeriesData.totalData
      }
    ]
  })

  // 更新对比图
  comparisonChart.setOption({
    xAxis: {
      data: timeSeriesData.timestamps
    },
    series: [
      {
        data: timeSeriesData.entryData
      },
      {
        data: timeSeriesData.exitData
      }
    ]
  })

  // 更新实时数据表格
  realtimeData.value.unshift({
    timestamp: timestamp,
    entryCount: data.entryCount || 0,
    exitCount: data.exitCount || 0,
    totalCount: data.totalCount || 0
  })
  
  if (realtimeData.value.length > maxDataPoints) {
    realtimeData.value.pop()
  }

  // 更新统计数据
  stats.value.entryCount += data.entryCount || 0
  stats.value.exitCount += data.exitCount || 0
  stats.value.todayCount = stats.value.entryCount + stats.value.exitCount
  stats.value.currentHourCount = data.totalCount || 0
}

// 处理WebSocket数据
const handleTrafficData = (data) => {
  if (data.type === 'traffic_data') {
    updateCharts(data.data)
  }
}

// 切换连接
const toggleConnection = () => {
  if (isConnected.value) {
    streamingWS.disconnectTraffic()
    isConnected.value = false
    ElMessage.info('已断开数据流连接')
  } else {
    streamingWS.connectTraffic((status) => {
      if (status === 'connected') {
        isConnected.value = true
        ElMessage.success('已连接数据流')
      } else if (status === 'error') {
        ElMessage.error('连接失败，请检查Python后端服务是否启动')
      }
    })
    
    streamingWS.subscribeTraffic(handleTrafficData)
  }
}

onMounted(() => {
  initCharts()
  // 自动连接
  toggleConnection()
})

onBeforeUnmount(() => {
  streamingWS.disconnectTraffic()
  if (trafficChart) {
    trafficChart.dispose()
  }
  if (comparisonChart) {
    comparisonChart.dispose()
  }
})
</script>

<style scoped>
.traffic-flow-container {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}
</style>

