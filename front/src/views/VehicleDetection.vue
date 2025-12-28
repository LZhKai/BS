<template>
  <div class="vehicle-detection-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>车辆识别监控</span>
          <div>
            <el-button
              :type="videoStatus.isRunning ? 'danger' : 'primary'"
              @click="toggleVideoProcessing"
              :loading="videoLoading"
            >
              {{ videoStatus.isRunning ? '停止识别' : '开始识别' }}
            </el-button>
            <el-button
              :type="isConnected ? 'danger' : 'primary'"
              @click="toggleConnection"
              style="margin-left: 10px"
            >
              {{ isConnected ? '断开连接' : '连接数据流' }}
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计信息 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ detectionStats.totalDetections }}</div>
              <div class="stat-label">总识别次数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ detectionStats.currentCount }}</div>
              <div class="stat-label">当前帧车辆数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ detectionStats.carCount }}</div>
              <div class="stat-label">轿车</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ detectionStats.truckCount }}</div>
              <div class="stat-label">货车</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 识别结果图表 -->
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>车辆识别数量趋势</span>
            </template>
            <div ref="detectionChartRef" style="height: 400px"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>车辆类型分布</span>
            </template>
            <div ref="typeChartRef" style="height: 400px"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 识别历史记录 -->
      <el-card style="margin-top: 20px">
        <template #header>
          <span>识别历史记录</span>
        </template>
        <el-table :data="detectionHistory" border style="width: 100%" max-height="300">
          <el-table-column prop="timestamp" label="识别时间" width="180" />
          <el-table-column prop="vehicleCount" label="车辆数量" width="100" />
          <el-table-column prop="vehicles" label="车辆类型" width="200">
            <template #default="scope">
              <el-tag
                v-for="(vehicle, index) in scope.row.vehicles"
                :key="index"
                style="margin-right: 5px"
              >
                {{ vehicle.class }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="平均置信度" width="120">
            <template #default="scope">
              {{ (scope.row.confidence * 100).toFixed(1) }}%
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { streamingWS, startVideoProcessing, stopVideoProcessing, getVideoStatus } from '../api/streaming'

const isConnected = ref(false)
const videoLoading = ref(false)
const detectionChartRef = ref(null)
const typeChartRef = ref(null)
let detectionChart = null
let typeChart = null

const videoStatus = ref({
  isRunning: false
})

const detectionStats = ref({
  totalDetections: 0,
  currentCount: 0,
  carCount: 0,
  truckCount: 0
})

const detectionHistory = ref([])
const maxHistoryRecords = 50

// 时间序列数据
const detectionTimeSeries = {
  timestamps: [],
  counts: []
}

// 车辆类型统计
const vehicleTypeStats = {
  car: 0,
  truck: 0,
  bus: 0,
  motorcycle: 0
}

// 初始化图表
const initCharts = () => {
  // 识别数量趋势图
  detectionChart = echarts.init(detectionChartRef.value)
  detectionChart.setOption({
    title: {
      text: '车辆识别数量趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
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
        name: '识别数量',
        type: 'line',
        data: [],
        smooth: true,
        areaStyle: {}
      }
    ]
  })

  // 车辆类型分布图
  typeChart = echarts.init(typeChartRef.value)
  typeChart.setOption({
    title: {
      text: '车辆类型分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '车辆类型',
        type: 'pie',
        radius: '50%',
        data: [],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  })
}

// 更新图表
const updateCharts = (data) => {
  const timestamp = new Date(data.timestamp).toLocaleTimeString()
  
  // 更新识别数量趋势
  detectionTimeSeries.timestamps.push(timestamp)
  detectionTimeSeries.counts.push(data.vehicle_count || 0)

  if (detectionTimeSeries.timestamps.length > 20) {
    detectionTimeSeries.timestamps.shift()
    detectionTimeSeries.counts.shift()
  }

  detectionChart.setOption({
    xAxis: {
      data: detectionTimeSeries.timestamps
    },
    series: [
      {
        data: detectionTimeSeries.counts
      }
    ]
  })

  // 更新车辆类型统计
  if (data.vehicles && data.vehicles.length > 0) {
    data.vehicles.forEach(vehicle => {
      const className = vehicle.class.toLowerCase()
      if (className.includes('car')) {
        vehicleTypeStats.car++
      } else if (className.includes('truck')) {
        vehicleTypeStats.truck++
      } else if (className.includes('bus')) {
        vehicleTypeStats.bus++
      } else if (className.includes('motorcycle')) {
        vehicleTypeStats.motorcycle++
      }
    })
  }

  // 更新饼图
  typeChart.setOption({
    series: [
      {
        data: [
          { value: vehicleTypeStats.car, name: '轿车' },
          { value: vehicleTypeStats.truck, name: '货车' },
          { value: vehicleTypeStats.bus, name: '公交车' },
          { value: vehicleTypeStats.motorcycle, name: '摩托车' }
        ]
      }
    ]
  })

  // 更新统计数据
  detectionStats.value.totalDetections++
  detectionStats.value.currentCount = data.vehicle_count || 0
  detectionStats.value.carCount = vehicleTypeStats.car
  detectionStats.value.truckCount = vehicleTypeStats.truck

  // 更新历史记录
  const avgConfidence = data.vehicles && data.vehicles.length > 0
    ? data.vehicles.reduce((sum, v) => sum + v.confidence, 0) / data.vehicles.length
    : 0

  detectionHistory.value.unshift({
    timestamp: timestamp,
    vehicleCount: data.vehicle_count || 0,
    vehicles: data.vehicles || [],
    confidence: avgConfidence
  })

  if (detectionHistory.value.length > maxHistoryRecords) {
    detectionHistory.value.pop()
  }
}

// 处理识别数据
const handleDetectionData = (data) => {
  if (data.type === 'detection_data') {
    updateCharts(data.data)
  }
}

// 切换视频处理
const toggleVideoProcessing = async () => {
  videoLoading.value = true
  try {
    if (videoStatus.value.isRunning) {
      await stopVideoProcessing()
      videoStatus.value.isRunning = false
      ElMessage.success('视频处理已停止')
    } else {
      await startVideoProcessing()
      videoStatus.value.isRunning = true
      ElMessage.success('视频处理已启动')
    }
  } catch (error) {
    ElMessage.error('操作失败: ' + error.message)
  } finally {
    videoLoading.value = false
  }
}

// 切换连接
const toggleConnection = () => {
  if (isConnected.value) {
    streamingWS.disconnectDetection()
    isConnected.value = false
    ElMessage.info('已断开数据流连接')
  } else {
    streamingWS.connectDetection((status) => {
      if (status === 'connected') {
        isConnected.value = true
        ElMessage.success('已连接数据流')
      } else if (status === 'error') {
        ElMessage.error('连接失败，请检查Python后端服务是否启动')
      }
    })
    
    streamingWS.subscribeDetection(handleDetectionData)
  }
}

// 检查视频状态
const checkVideoStatus = async () => {
  try {
    const res = await getVideoStatus()
    if (res.code === 200) {
      videoStatus.value = res.data
    }
  } catch (error) {
    console.error('获取视频状态失败:', error)
  }
}

onMounted(() => {
  initCharts()
  checkVideoStatus()
  // 自动连接
  toggleConnection()
})

onBeforeUnmount(() => {
  streamingWS.disconnectDetection()
  if (detectionChart) {
    detectionChart.dispose()
  }
  if (typeChart) {
    typeChart.dispose()
  }
})
</script>

<style scoped>
.vehicle-detection-container {
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

