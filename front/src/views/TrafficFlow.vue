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
import { streamingWS, getTrafficStats } from '../api/streaming'

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
const maxDataPoints = 20

const timeSeriesData = {
  timestamps: [],
  entryData: [],
  exitData: [],
  totalData: []
}

const initCharts = () => {
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

const updateCharts = (data) => {
  const entryCount = data.entryCount ?? data.entry_count ?? 0
  const exitCount = data.exitCount ?? data.exit_count ?? 0
  const totalCount = data.totalCount ?? data.total_count ?? (entryCount + exitCount)
  const timestamp = new Date(data.timestamp || Date.now()).toLocaleTimeString()

  timeSeriesData.timestamps.push(timestamp)
  timeSeriesData.entryData.push(entryCount)
  timeSeriesData.exitData.push(exitCount)
  timeSeriesData.totalData.push(totalCount)

  if (timeSeriesData.timestamps.length > maxDataPoints) {
    timeSeriesData.timestamps.shift()
    timeSeriesData.entryData.shift()
    timeSeriesData.exitData.shift()
    timeSeriesData.totalData.shift()
  }

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

  realtimeData.value.unshift({
    timestamp,
    entryCount,
    exitCount,
    totalCount
  })

  if (realtimeData.value.length > maxDataPoints) {
    realtimeData.value.pop()
  }

  stats.value.entryCount += entryCount
  stats.value.exitCount += exitCount
  stats.value.todayCount = stats.value.entryCount + stats.value.exitCount
  stats.value.currentHourCount = totalCount
}

const handleTrafficData = (data) => {
  if (data.type === 'traffic_data') {
    updateCharts(data.data)
  }
}

const loadInitialStats = async () => {
  try {
    const res = await getTrafficStats()
    if (res.code === 200 && res.data) {
      stats.value.todayCount = res.data.todayCount ?? res.data.today_count ?? 0
      stats.value.currentHourCount = res.data.currentHourCount ?? res.data.current_hour_count ?? 0
      stats.value.entryCount = res.data.entryCount ?? res.data.entry_count ?? 0
      stats.value.exitCount = res.data.exitCount ?? res.data.exit_count ?? 0
    }
  } catch (error) {
    // ignore initial stats failure
  }
}

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
        ElMessage.error('连接失败，请检查 Python 后端服务是否启动')
      }
    })

    streamingWS.subscribeTraffic(handleTrafficData)
  }
}

onMounted(() => {
  initCharts()
  loadInitialStats()
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
