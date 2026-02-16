import axios from 'axios'
import { ElMessage } from 'element-plus'

// 专用于 Python 后端（back_python，默认 5000 端口）
const service = axios.create({
  baseURL: '/py-api',
  timeout: 10000
})

service.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code === 200) {
      return res
    } else {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
  },
  error => {
    ElMessage.error(error.message || '请求失败')
    return Promise.reject(error)
  }
)

export default service

