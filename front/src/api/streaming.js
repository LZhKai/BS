import request from './request'
import { io } from 'socket.io-client'

class StreamingWebSocket {
  constructor() {
    this.trafficSocket = null
    this.detectionSocket = null
    this.videoSocket = null
    this.trafficCallbacks = []
    this.detectionCallbacks = []
    this.videoCallbacks = []
  }

  connectTraffic(callback) {
    if (this.trafficSocket && this.trafficSocket.connected) {
      if (callback) callback('connected')
      return
    }

    const wsUrl = 'http://localhost:5000'
    this.trafficSocket = io(wsUrl + '/stream/traffic', {
      transports: ['polling']
    })

    this.trafficSocket.on('connect', () => {
      console.log('Traffic socket connected')
      if (callback) callback('connected')
    })

    this.trafficSocket.on('traffic_data', (data) => {
      this.trafficCallbacks.forEach((cb) => cb({ type: 'traffic_data', data }))
    })

    this.trafficSocket.on('connected', (data) => {
      console.log('Traffic server ack:', data)
    })

    this.trafficSocket.on('connect_error', (error) => {
      console.error('Traffic socket error:', error)
      if (callback) callback('error', error)
    })

    this.trafficSocket.on('disconnect', () => {
      console.log('Traffic socket disconnected')
      if (callback) callback('closed')
    })
  }

  connectDetection(callback) {
    if (this.detectionSocket && this.detectionSocket.connected) {
      if (callback) callback('connected')
      return
    }

    const wsUrl = 'http://localhost:5000'
    this.detectionSocket = io(wsUrl + '/stream/detection', {
      transports: ['polling']
    })

    this.detectionSocket.on('connect', () => {
      console.log('Detection socket connected')
      if (callback) callback('connected')
    })

    this.detectionSocket.on('detection_data', (data) => {
      this.detectionCallbacks.forEach((cb) => cb({ type: 'detection_data', data }))
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

  subscribeTraffic(callback) {
    if (!this.trafficCallbacks.includes(callback)) {
      this.trafficCallbacks.push(callback)
    }
  }

  subscribeDetection(callback) {
    if (!this.detectionCallbacks.includes(callback)) {
      this.detectionCallbacks.push(callback)
    }
  }

  unsubscribeTraffic(callback) {
    this.trafficCallbacks = this.trafficCallbacks.filter((cb) => cb !== callback)
  }

  unsubscribeDetection(callback) {
    this.detectionCallbacks = this.detectionCallbacks.filter((cb) => cb !== callback)
  }

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

  connectVideo(callback) {
    if (this.videoSocket && this.videoSocket.connected) {
      if (callback) callback('connected')
      return
    }

    const wsUrl = 'http://localhost:5000'
    this.videoSocket = io(wsUrl + '/stream/video', {
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
    this.disconnectTraffic()
    this.disconnectDetection()
    this.disconnectVideo()
  }
}

export const streamingWS = new StreamingWebSocket()

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