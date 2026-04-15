import request from './request'
import { io } from 'socket.io-client'

class StreamingWebSocket {
  constructor() {
    this.detectionSocket = null
    this.videoSocket = null
    this.detectionCallbacks = []
    this.monitorAggCallbacks = []
    this.videoCallbacks = []
  }

  connectDetection(callback) {
    if (this.detectionSocket && this.detectionSocket.connected) {
      if (callback) callback('connected')
      return
    }

    const wsUrl = 'http://localhost:5000'
    this.detectionSocket = io(wsUrl + '/stream/monitor', {
      transports: ['polling']
    })

    this.detectionSocket.on('connect', () => {
      console.log('Detection socket connected')
      if (callback) callback('connected')
    })

    this.detectionSocket.on('detection_data', (data) => {
      this.detectionCallbacks.forEach((cb) => cb({ type: 'detection_data', data }))
    })
    this.detectionSocket.on('monitor_agg_data', (data) => {
      this.monitorAggCallbacks.forEach((cb) => cb({ type: 'monitor_agg_data', data }))
    })

    this.detectionSocket.on('connected', (data) => {
      console.log('Detection server ack:', data)
    })

    this.detectionSocket.on('connect_error', (error) => {
      console.error('Detection socket error:', error)
      if (callback) callback('error', error)
    })

    this.detectionSocket.on('disconnect', () => {
      console.log('Detection socket disconnected')
      if (callback) callback('closed')
    })
  }

  subscribeDetection(callback) {
    if (!this.detectionCallbacks.includes(callback)) {
      this.detectionCallbacks.push(callback)
    }
  }

  subscribeMonitorAgg(callback) {
    if (!this.monitorAggCallbacks.includes(callback)) {
      this.monitorAggCallbacks.push(callback)
    }
  }

  unsubscribeDetection(callback) {
    this.detectionCallbacks = this.detectionCallbacks.filter((cb) => cb !== callback)
  }

  unsubscribeMonitorAgg(callback) {
    this.monitorAggCallbacks = this.monitorAggCallbacks.filter((cb) => cb !== callback)
  }

  disconnectDetection() {
    if (this.detectionSocket) {
      this.detectionSocket.disconnect()
      this.detectionSocket = null
    }
    this.detectionCallbacks = []
    this.monitorAggCallbacks = []
  }

  connectVideo(callback) {
    if (this.videoSocket && this.videoSocket.connected) {
      if (callback) callback('connected')
      return
    }

    const wsUrl = 'http://localhost:5000'
    this.videoSocket = io(wsUrl + '/stream/monitor-video', {
      transports: ['polling']
    })

    this.videoSocket.on('connect', () => {
      console.log('Video socket connected')
      if (callback) callback('connected')
    })

    this.videoSocket.on('video_frame', (data) => {
      this.videoCallbacks.forEach((cb) => cb({ type: 'video_frame', data }))
    })

    this.videoSocket.on('connected', (data) => {
      console.log('Video server ack:', data)
    })

    this.videoSocket.on('connect_error', (error) => {
      console.error('Video socket error:', error)
      if (callback) callback('error', error)
    })

    this.videoSocket.on('disconnect', () => {
      console.log('Video socket disconnected')
      if (callback) callback('closed')
    })
  }

  subscribeVideo(callback) {
    if (!this.videoCallbacks.includes(callback)) {
      this.videoCallbacks.push(callback)
    }
  }

  unsubscribeVideo(callback) {
    this.videoCallbacks = this.videoCallbacks.filter((cb) => cb !== callback)
  }

  disconnectVideo() {
    if (this.videoSocket) {
      this.videoSocket.disconnect()
      this.videoSocket = null
    }
    this.videoCallbacks = []
  }

  disconnectAll() {
    this.disconnectDetection()
    this.disconnectVideo()
  }
}

export const streamingWS = new StreamingWebSocket()

export const startVideoProcessing = (source) => {
  return request({
    url: 'http://localhost:5000/api/monitor/start',
    method: 'post',
    data: { source }
  })
}

export const stopVideoProcessing = () => {
  return request({
    url: 'http://localhost:5000/api/monitor/stop',
    method: 'post'
  })
}

export const getVideoStatus = () => {
  return request({
    url: 'http://localhost:5000/api/monitor/status',
    method: 'get'
  })
}