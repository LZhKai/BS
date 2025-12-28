import request from './request'
import { io } from 'socket.io-client'

// WebSocket连接管理
class StreamingWebSocket {
  constructor() {
    this.trafficSocket = null
    this.detectionSocket = null
    this.trafficCallbacks = []
    this.detectionCallbacks = []
  }

  // 连接车流量数据流
  connectTraffic(callback) {
    if (this.trafficSocket && this.trafficSocket.readyState === WebSocket.OPEN) {
      if (callback) callback('connected')
      return
    }

    // 使用Socket.IO客户端连接
    const wsUrl = `http://localhost:5000`
    this.trafficSocket = io(wsUrl + '/stream/traffic', {
      transports: ['websocket', 'polling']
    })

    this.trafficSocket.on('connect', () => {
      console.log('车流量WebSocket连接已建立')
      if (callback) callback('connected')
    })

    this.trafficSocket.on('traffic_data', (data) => {
      this.trafficCallbacks.forEach(cb => cb({ type: 'traffic_data', data }))
    })

    this.trafficSocket.on('connected', (data) => {
      console.log('连接确认:', data)
    })

    this.trafficSocket.on('connect_error', (error) => {
      console.error('车流量WebSocket连接错误:', error)
      if (callback) callback('error', error)
    })

    this.trafficSocket.on('disconnect', () => {
      console.log('车流量WebSocket连接已关闭')
      if (callback) callback('closed')
    })
  }

  // 连接车辆识别数据流
  connectDetection(callback) {
    if (this.detectionSocket && this.detectionSocket.connected) {
      if (callback) callback('connected')
      return
    }

    // 使用Socket.IO客户端连接
    const wsUrl = `http://localhost:5000`
    this.detectionSocket = io(wsUrl + '/stream/detection', {
      transports: ['websocket', 'polling']
    })

    this.detectionSocket.on('connect', () => {
      console.log('车辆识别WebSocket连接已建立')
      if (callback) callback('connected')
    })

    this.detectionSocket.on('detection_data', (data) => {
      this.detectionCallbacks.forEach(cb => cb({ type: 'detection_data', data }))
    })

    this.detectionSocket.on('connected', (data) => {
      console.log('连接确认:', data)
    })

    this.detectionSocket.on('connect_error', (error) => {
      console.error('车辆识别WebSocket连接错误:', error)
      if (callback) callback('error', error)
    })

    this.detectionSocket.on('disconnect', () => {
      console.log('车辆识别WebSocket连接已关闭')
      if (callback) callback('closed')
    })
  }

  // 订阅车流量数据
  subscribeTraffic(callback) {
    if (!this.trafficCallbacks.includes(callback)) {
      this.trafficCallbacks.push(callback)
    }
  }

  // 订阅车辆识别数据
  subscribeDetection(callback) {
    if (!this.detectionCallbacks.includes(callback)) {
      this.detectionCallbacks.push(callback)
    }
  }

  // 取消订阅
  unsubscribeTraffic(callback) {
    this.trafficCallbacks = this.trafficCallbacks.filter(cb => cb !== callback)
  }

  unsubscribeDetection(callback) {
    this.detectionCallbacks = this.detectionCallbacks.filter(cb => cb !== callback)
  }

  // 断开连接
  disconnectTraffic() {
    if (this.trafficSocket) {
      this.trafficSocket.disconnect()
      this.trafficSocket = null
    }
    this.trafficCallbacks = []
  }

  disconnectDetection() {
    if (this.detectionSocket) {
      this.detectionSocket.disconnect()
      this.detectionSocket = null
    }
    this.detectionCallbacks = []
  }

  disconnectAll() {
    this.disconnectTraffic()
    this.disconnectDetection()
  }
}

export const streamingWS = new StreamingWebSocket()

// REST API
export const getTrafficStats = () => {
  return request({
    url: 'http://localhost:5000/api/traffic/stats',
    method: 'get'
  })
}

export const startVideoProcessing = (source) => {
  return request({
    url: 'http://localhost:5000/api/video/start',
    method: 'post',
    data: { source }
  })
}

export const stopVideoProcessing = () => {
  return request({
    url: 'http://localhost:5000/api/video/stop',
    method: 'post'
  })
}

export const getVideoStatus = () => {
  return request({
    url: 'http://localhost:5000/api/video/status',
    method: 'get'
  })
}

