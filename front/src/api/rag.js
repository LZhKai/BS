import requestPy from './request_py'

// 触发后端重建车辆向量索引
export const rebuildRagIndex = () => {
  return requestPy({
    url: '/rag/index',
    method: 'post'
  })
}

// 智能问答 / 向量检索接口
export const askRagQuestion = (data) => {
  return requestPy({
    url: '/rag/search',
    method: 'post',
    data
  })
}

// 获取智能问答历史
export const getRagHistory = (params) => {
  return requestPy({
    url: '/rag/history',
    method: 'get',
    params
  })
}

