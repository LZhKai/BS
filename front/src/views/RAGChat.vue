<template>
  <div class="rag-chat-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>智能问答（RAG）</span>
          <el-button type="primary" :loading="indexLoading" @click="handleRebuildIndex">
            重新构建向量索引
          </el-button>
        </div>
      </template>

      <div class="chat-area">
        <el-input
          v-model="question"
          type="textarea"
          :rows="3"
          placeholder="请输入问题，例如：白色的车有多少辆？或：给出银色商务车，帮我找出符合条件的车辆及车主停车位。"
        />
        <div class="chat-actions">
          <el-button type="primary" :loading="loading" @click="handleAsk">发送</el-button>
          <el-button @click="handleClear">清空</el-button>
        </div>

        <el-divider>回答</el-divider>
        <div class="answer-area">
          <p v-if="!answer">请在上方输入问题并点击发送。</p>
          <div v-else class="answer-text">
            {{ answer }}
          </div>
        </div>

        <el-divider v-if="vehicles.length">检索到的相关车辆</el-divider>
        <el-table
          v-if="vehicles.length"
          :data="vehicles"
          border
          style="width: 100%"
        >
          <el-table-column prop="plate_number" label="车牌号" width="120" />
          <el-table-column prop="brand_model" label="品牌型号" width="160" show-overflow-tooltip />
          <el-table-column prop="owner_name" label="车主姓名" width="120" />
          <el-table-column prop="owner_phone" label="车主电话" width="150" />
          <el-table-column prop="owner_address" label="车主地址/车位" min-width="180" show-overflow-tooltip />
          <el-table-column prop="description" label="车辆描述" min-width="220" show-overflow-tooltip />
        </el-table>

        <el-divider>问答历史</el-divider>
        <el-table :data="historyRecords" border style="width: 100%">
          <el-table-column prop="createTime" label="时间" width="180" />
          <el-table-column prop="question" label="问题" min-width="220" show-overflow-tooltip />
          <el-table-column prop="answer" label="回答" min-width="300" show-overflow-tooltip />
          <el-table-column prop="hitCount" label="命中数" width="90" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="errorMessage" label="错误信息" min-width="180" show-overflow-tooltip />
        </el-table>
        <div class="history-pagination">
          <el-pagination
            v-model:current-page="historyPagination.current"
            v-model:page-size="historyPagination.size"
            :total="historyPagination.total"
            layout="total, prev, pager, next"
            @current-change="loadHistory"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { rebuildRagIndex, getRagHistory } from '../api/rag'

const question = ref('')
const answer = ref('')
const vehicles = ref([])
const loading = ref(false)
const indexLoading = ref(false)
const historyRecords = ref([])
const defaultTopK = 10
const historyPagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

let eventSource = null

const closeEventSource = () => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

const handleAsk = () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }

  // 关闭之前的流
  closeEventSource()
  // 重置显示
  answer.value = ''
  vehicles.value = []
  loading.value = true

  const url = `/py-api/rag/stream?question=${encodeURIComponent(
    question.value
  )}&top_k=${defaultTopK}`

  const es = new EventSource(url)
  eventSource = es

  // 接收检索到的车辆列表
  es.addEventListener('meta', (e) => {
    try {
      const data = JSON.parse(e.data || '{}')
      vehicles.value = data.vehicles || []
    } catch (err) {
      console.error('解析 meta 事件失败:', err)
    }
  })

  // 默认 message 事件：逐 token 追加回答
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data || '{}')
      if (data.token) {
        answer.value += data.token
      }
    } catch (err) {
      console.error('解析 message 事件失败:', err)
    }
  }

  // 结束事件
  es.addEventListener('end', () => {
    closeEventSource()
    loading.value = false
    loadHistory()
  })

  es.addEventListener('error', (e) => {
    try {
      const data = JSON.parse(e.data || '{}')
      if (data.message) {
        ElMessage.error(`问答失败：${data.message}`)
      }
    } catch (_) {
      // ignore parse error
    }
  })

  es.onerror = (err) => {
    console.error('SSE 连接出错:', err)
    closeEventSource()
    loading.value = false
  }
}

const handleClear = () => {
  question.value = ''
  answer.value = ''
  vehicles.value = []
  closeEventSource()
}

const handleRebuildIndex = async () => {
  indexLoading.value = true
  try {
    const res = await rebuildRagIndex()
    if (res.code === 200) {
      ElMessage.success(`索引重建成功，车辆数：${res.data.count}`)
    }
  } catch (e) {
    console.error('重建索引失败:', e)
  } finally {
    indexLoading.value = false
  }
}

const loadHistory = async () => {
  try {
    const res = await getRagHistory({
      current: historyPagination.current,
      size: historyPagination.size
    })
    historyRecords.value = res.data.records || []
    historyPagination.total = res.data.total || 0
  } catch (e) {
    ElMessage.error('加载问答历史失败')
  }
}

onMounted(() => {
  loadHistory()
})

onUnmounted(() => {
  closeEventSource()
})
</script>

<style scoped>
.rag-chat-container {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.answer-area {
  min-height: 120px;
}

.answer-text {
  white-space: pre-wrap;
  line-height: 1.6;
  padding: 12px 14px;
  border-radius: 6px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  max-height: 260px;
  overflow-y: auto;
  font-size: 14px;
}

.history-pagination {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}
</style>

