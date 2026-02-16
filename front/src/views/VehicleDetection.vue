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
              <div class="stat-label">累计检测轿车数（去重）</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ detectionStats.truckCount }}</div>
              <div class="stat-label">累计检测货车数（去重）</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 视频显示区域 -->
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
const isVideoConnected = ref(false)
const videoLoading = ref(false)
const detectionChartRef = ref(null)
const typeChartRef = ref(null)
const videoCanvasRef = ref(null)
const canvasWidth = ref(1280)
const canvasHeight = ref(720)
let detectionChart = null
let typeChart = null
let videoImage = null

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

// 车辆类型统计（改为只显示当前帧的统计，不累加）
const vehicleTypeStats = {
  car: 0,
  truck: 0,
  bus: 0,
  motorcycle: 0
}

// 用于去重的车辆记录（基于位置和类型）
const detectedVehicles = new Set()

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

  // 更新车辆类型统计（使用去重逻辑，避免同一辆车重复计数）
  // 统计当前帧的车辆数量（用于显示）
  let currentFrameCar = 0
  let currentFrameTruck = 0
  let currentFrameBus = 0
  let currentFrameMotorcycle = 0
  
  if (data.vehicles && data.vehicles.length > 0) {
    data.vehicles.forEach(vehicle => {
      const className = vehicle.class.toLowerCase()
      
      // 统计当前帧的车辆数量
      if (className.includes('car')) {
        currentFrameCar++
      } else if (className.includes('truck')) {
        currentFrameTruck++
      } else if (className.includes('bus')) {
        currentFrameBus++
      } else if (className.includes('motorcycle')) {
        currentFrameMotorcycle++
      }
      
      // 生成车辆唯一标识（基于位置和类型，用于去重）
      // 使用中心点坐标和类型作为唯一标识
      const [x1, y1, x2, y2] = vehicle.bbox
      const centerX = Math.round((x1 + x2) / 2 / 30) // 每30像素为一个区域
      const centerY = Math.round((y1 + y2) / 2 / 30)
      const vehicleKey = `${className}_${centerX}_${centerY}`
      
      // 只统计新的车辆（去重），用于累计统计
      if (!detectedVehicles.has(vehicleKey)) {
        detectedVehicles.add(vehicleKey)
        
        // 统计累计数量（去重后）
        if (className.includes('car')) {
          vehicleTypeStats.car++
        } else if (className.includes('truck')) {
          vehicleTypeStats.truck++
        } else if (className.includes('bus')) {
          vehicleTypeStats.bus++
        } else if (className.includes('motorcycle')) {
          vehicleTypeStats.motorcycle++
        }
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
  // 使用去重后的累计数量
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

// 处理视频帧数据
const handleVideoFrame = (data) => {
  if (data.type === 'video_frame' && videoCanvasRef.value) {
    const frameData = data.data
    const canvas = videoCanvasRef.value
    const ctx = canvas.getContext('2d')
    
    // 创建图片对象
    const img = new Image()
    img.onload = () => {
      // 设置canvas尺寸（匹配视频尺寸）
      if (canvas.width !== img.width || canvas.height !== img.height) {
        canvas.width = img.width
        canvas.height = img.height
        canvasWidth.value = img.width
        canvasHeight.value = img.height
      }
      
      // 绘制视频帧（后端已经在帧上绘制了检测框）
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      
      // 如果需要在前端额外绘制检测框（更清晰的显示），可以启用下面的代码
      // 注意：后端已经在帧上绘制了检测框，这里可以增强显示效果
      if (frameData.vehicles && frameData.vehicles.length > 0) {
        frameData.vehicles.forEach(vehicle => {
          const [x1, y1, x2, y2] = vehicle.bbox
          const confidence = vehicle.confidence
          const className = vehicle.class
          
          // 绘制更明显的边界框（覆盖在后端绘制的框上）
          ctx.strokeStyle = '#00ff00'
          ctx.lineWidth = 3
          ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
          
          // 绘制标签背景
          const label = `${className}: ${(confidence * 100).toFixed(1)}%`
          ctx.fillStyle = 'rgba(0, 255, 0, 0.8)'
          ctx.font = 'bold 14px Arial'
          const textWidth = ctx.measureText(label).width
          ctx.fillRect(x1, y1 - 25, textWidth + 10, 25)
          
          // 绘制标签文字
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
    streamingWS.disconnectVideo()
    isConnected.value = false
    isVideoConnected.value = false
    ElMessage.info('已断开数据流连接')
  } else {
    // 连接检测数据流
    streamingWS.connectDetection((status) => {
      if (status === 'connected') {
        isConnected.value = true
        ElMessage.success('已连接数据流')
      } else if (status === 'error') {
        ElMessage.error('连接失败，请检查Python后端服务是否启动')
      }
    })
    streamingWS.subscribeDetection(handleDetectionData)
    
    // 连接视频流
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

