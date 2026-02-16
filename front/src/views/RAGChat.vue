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
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { rebuildRagIndex } from '../api/rag'

const question = ref('')
const answer = ref('')
const vehicles = ref([])
const loading = ref(false)
const indexLoading = ref(false)

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
  )}&top_k=5`

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
</style>

