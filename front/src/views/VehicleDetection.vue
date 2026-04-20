<template>
  <div class="vehicle-detection-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>车辆监控</span>
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

      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ detectionStats.totalDetections }}</div>
              <div class="stat-label">累计唯一车辆数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ detectionStats.currentCount }}</div>
              <div class="stat-label">当前识别车辆数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ detectionStats.carCount }}</div>
              <div class="stat-label">累计轿车数(去重)</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ detectionStats.truckCount }}</div>
              <div class="stat-label">累计货车数(去重)</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card style="margin-top: 20px">
        <template #header>
          <span>实时视频监控</span>
        </template>
        <div class="video-container">
          <canvas
            ref="videoCanvasRef"
            class="video-canvas"
            :width="canvasWidth"
            :height="canvasHeight"
          ></canvas>
          <div v-if="!isVideoConnected" class="video-placeholder">
            <el-icon><VideoCamera /></el-icon>
            <p>等待视频流连接...</p>
          </div>
        </div>
      </el-card>

      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>车辆监控数量趋势</span>
            </template>
            <div ref="detectionChartRef" style="height: 400px"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>车辆类型分布(去重)</span>
            </template>
            <div ref="typeChartRef" style="height: 400px"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-card style="margin-top: 20px">
        <template #header>
          <span>识别历史记录</span>
        </template>
        <el-table :data="detectionHistory" border style="width: 100%" max-height="300">
          <el-table-column prop="timestamp" label="识别时间" width="180" />
          <el-table-column prop="vehicleCount" label="车辆总数" width="100" />
          <el-table-column prop="typeCounts" label="类型计数" width="220">
            <template #default="scope">
              <el-tag
                v-for="(item, index) in formatTypeSummary(scope.row.typeCounts)"
                :key="index"
                style="margin-right: 5px"
              >
                {{ item }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="vehicles" label="车辆明细" width="260">
            <template #default="scope">
              <el-tag
                v-for="(vehicle, index) in scope.row.vehicles"
                :key="index"
                style="margin-right: 5px"
              >
                {{ formatVehicleTag(vehicle) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="平均置信度(全部)" width="140">
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
const isVideoConnected = ref(false)
const videoLoading = ref(false)
const detectionChartRef = ref(null)
const typeChartRef = ref(null)
const videoCanvasRef = ref(null)
const canvasWidth = ref(1280)
const canvasHeight = ref(720)
const sparkEnabled = ref(false)
let detectionChart = null
let typeChart = null
let statusTimer = null
let lastAggUpdateAt = 0

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

const detectionTimeSeries = {
  timestamps: [],
  counts: []
}

const vehicleTypeStats = {
  car: 0,
  truck: 0,
  bus: 0,
  motorcycle: 0
}

const VEHICLE_TYPE_LABELS = {
  car: 'car',
  truck: 'truck',
  bus: 'bus',
  motorcycle: 'motorcycle',
  unknown: 'unknown'
}

const VEHICLE_TYPE_COLORS = {
  car: '#00ff00',
  truck: '#ff8c00',
  bus: '#1e90ff',
  motorcycle: '#ffd700',
  unknown: '#ffffff'
}

const normalizeVehicleType = (className) => {
  const name = String(className || '').toLowerCase()
  if (name.includes('truck')) return 'truck'
  if (name.includes('bus')) return 'bus'
  if (name.includes('motorcycle') || name.includes('motorbike')) return 'motorcycle'
  if (name.includes('car')) return 'car'
  return 'unknown'
}

const resolveVehicleType = (vehicle = {}) => {
  const classId = Number(vehicle.class_id)
  if (classId === 7) return 'truck'
  if (classId === 5) return 'bus'
  if (classId === 3) return 'motorcycle'
  if (classId === 2) return 'car'
  return normalizeVehicleType(vehicle.class)
}

const buildTypeCounts = (vehicles) => {
  const counts = {
    car: 0,
    truck: 0,
    bus: 0,
    motorcycle: 0,
    unknown: 0
  }
  vehicles.forEach((vehicle) => {
    const type = resolveVehicleType(vehicle)
    counts[type] += 1
  })
  return counts
}

const formatTypeSummary = (typeCounts = {}) => {
  return Object.keys(typeCounts)
    .filter((key) => (typeCounts[key] || 0) > 0)
    .map((key) => `${VEHICLE_TYPE_LABELS[key] || key}: ${typeCounts[key]}`)
}

const formatVehicleTag = (vehicle) => {
  const type = resolveVehicleType(vehicle)
  const classId = vehicle.class_id ?? '-'
  return `${VEHICLE_TYPE_LABELS[type] || type}(${classId})#${vehicle.track_id ?? '-'}`
}

const initCharts = () => {
  detectionChart = echarts.init(detectionChartRef.value)
  detectionChart.setOption({
    title: {
      text: '车辆监控数量趋势',
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
        name: '当前识别车辆数',
        type: 'line',
        data: [],
        smooth: true,
        areaStyle: {}
      }
    ]
  })

  typeChart = echarts.init(typeChartRef.value)
  typeChart.setOption({
    title: {
      text: '车辆类型分布(去重)',
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

const updateSummaryCharts = (data) => {
  const timestamp = new Date(data.timestamp || Date.now()).toLocaleTimeString()
  const flowTotalCount = data.totalCount ?? data.currentHourCount ?? 0

  detectionTimeSeries.timestamps.push(timestamp)
  detectionTimeSeries.counts.push(flowTotalCount)

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

  if (data.unique_by_type) {
    vehicleTypeStats.car = data.unique_by_type.car || 0
    vehicleTypeStats.truck = data.unique_by_type.truck || 0
    vehicleTypeStats.bus = data.unique_by_type.bus || 0
    vehicleTypeStats.motorcycle = data.unique_by_type.motorcycle || 0
  }

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

  detectionStats.value.totalDetections = data.todayCount ?? detectionStats.value.totalDetections
  detectionStats.value.currentCount = flowTotalCount
  detectionStats.value.carCount = vehicleTypeStats.car
  detectionStats.value.truckCount = vehicleTypeStats.truck
}

const appendDetectionHistory = (data) => {
  const timestamp = new Date(data.timestamp || Date.now()).toLocaleTimeString()
  const flowTotalCount = data.totalCount ?? data.vehicle_count ?? 0
  const vehicles = data.vehicles || []
  const typeCounts = buildTypeCounts(vehicles)
  const avgConfidence = vehicles.length > 0
    ? vehicles.reduce((sum, v) => sum + v.confidence, 0) / vehicles.length
    : 0

  detectionHistory.value.unshift({
    timestamp,
    vehicleCount: flowTotalCount,
    typeCounts,
    vehicles,
    confidence: avgConfidence
  })

  if (detectionHistory.value.length > maxHistoryRecords) {
    detectionHistory.value.pop()
  }
}

const handleDetectionData = (data) => {
  if (data.type === 'detection_data') {
    // Fallback:
    // 1) Spark unavailable -> always use detection stream
    // 2) Spark enabled but aggregate stream stale -> temporarily fallback
    const now = Date.now()
    if (!sparkEnabled.value || now - lastAggUpdateAt > 8000) {
      updateSummaryCharts(data.data)
    }
    appendDetectionHistory(data.data)
  }
}

const handleMonitorAggData = (data) => {
  if (data.type === 'monitor_agg_data') {
    lastAggUpdateAt = Date.now()
    updateSummaryCharts(data.data)
  }
}

const handleVideoFrame = (data) => {
  if (data.type === 'video_frame' && videoCanvasRef.value) {
    const frameData = data.data
    const canvas = videoCanvasRef.value
    const ctx = canvas.getContext('2d')

    const img = new Image()
    img.onload = () => {
      if (canvas.width !== img.width || canvas.height !== img.height) {
        canvas.width = img.width
        canvas.height = img.height
        canvasWidth.value = img.width
        canvasHeight.value = img.height
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

      if (frameData.vehicles && frameData.vehicles.length > 0) {
        frameData.vehicles.forEach((vehicle) => {
          const [x1, y1, x2, y2] = vehicle.bbox
          const confidence = vehicle.confidence
          const vehicleType = resolveVehicleType(vehicle)
          const className = VEHICLE_TYPE_LABELS[vehicleType] || vehicle.class || 'unknown'
          const classId = vehicle.class_id ?? '-'
          const trackId = vehicle.track_id ?? '-'
          const color = VEHICLE_TYPE_COLORS[vehicleType] || VEHICLE_TYPE_COLORS.unknown

          ctx.strokeStyle = color
          ctx.lineWidth = 3
          ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

          const label = `${className}(${classId})#${trackId}: ${(confidence * 100).toFixed(1)}%`
          ctx.fillStyle = `${color}CC`
          ctx.font = 'bold 14px Arial'
          const textWidth = ctx.measureText(label).width
          ctx.fillRect(x1, y1 - 25, textWidth + 10, 25)

          ctx.fillStyle = '#000'
          ctx.fillText(label, x1 + 5, y1 - 8)
        })
      }
    }

    img.onerror = () => {
      console.error('视频帧加载失败')
    }
    img.src = 'data:image/jpeg;base64,' + frameData.frame
  }
}

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

const toggleConnection = () => {
  if (isConnected.value) {
    streamingWS.disconnectDetection()
    streamingWS.disconnectVideo()
    isConnected.value = false
    isVideoConnected.value = false
    ElMessage.info('已断开数据流连接')
  } else {
    streamingWS.connectDetection((status) => {
      if (status === 'connected') {
        isConnected.value = true
        ElMessage.success('已连接识别数据流')
      } else if (status === 'error') {
        ElMessage.error('连接失败，请检查 Python 后端服务是否已启动')
      }
    })
    streamingWS.subscribeDetection(handleDetectionData)
    streamingWS.subscribeMonitorAgg(handleMonitorAggData)

    streamingWS.connectVideo((status) => {
      if (status === 'connected') {
        isVideoConnected.value = true
        ElMessage.success('已连接视频流')
      } else if (status === 'error') {
        ElMessage.error('视频流连接失败')
      }
    })
    streamingWS.subscribeVideo(handleVideoFrame)
  }
}

const checkVideoStatus = async () => {
  try {
    const wasRunning = !!videoStatus.value.isRunning
    const res = await getVideoStatus()
    if (res.code === 200) {
      const data = res.data
      videoStatus.value = {
        isRunning: !!(data.is_running ?? data.isRunning),
        status: data.status
      }
      sparkEnabled.value = !!data.spark_enabled
      if (wasRunning && !videoStatus.value.isRunning) {
        ElMessage.info('视频已结束，识别已自动停止')
      }
    }
  } catch (error) {
    console.error('获取视频状态失败', error)
  }
}

onMounted(() => {
  initCharts()
  checkVideoStatus()
  statusTimer = setInterval(checkVideoStatus, 3000)
  toggleConnection()
})

onBeforeUnmount(() => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
  streamingWS.disconnectDetection()
  streamingWS.disconnectVideo()
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

.video-container {
  position: relative;
  width: 100%;
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.video-canvas {
  max-width: 100%;
  height: auto;
  display: block;
}

.video-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #999;
}

.video-placeholder .el-icon {
  font-size: 48px;
  margin-bottom: 10px;
}
</style>
