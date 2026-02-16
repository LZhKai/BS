<template>
  <div class="plate-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>车牌识别入库</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="10">
          <el-card class="block-card">
            <template #header>上传识别</template>
            <el-upload
              class="uploader"
              drag
              :auto-upload="false"
              :show-file-list="true"
              :limit="1"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              accept=".jpg,.jpeg,.png,.bmp,.webp"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">拖拽文件到这里，或点击上传</div>
              <template #tip>
                <div class="el-upload__tip">支持 jpg/png/bmp/webp，最大 10MB</div>
              </template>
            </el-upload>

            <div class="actions">
              <el-button type="primary" :loading="recognizing" @click="runRecognition">
                开始识别
              </el-button>
              <el-button @click="resetCurrent">重置</el-button>
            </div>
          </el-card>
        </el-col>

        <el-col :span="14">
          <el-card class="block-card">
            <template #header>识别结果与入库</template>

            <el-form :model="formData" label-width="110px">
              <el-form-item label="车牌号">
                <el-input v-model="formData.plateNumber" placeholder="识别后可手动修正" />
              </el-form-item>
              <el-form-item label="省份补全">
                <el-select v-model="formData.province" placeholder="选择省份简称" style="width: 180px; margin-right: 10px">
                  <el-option
                    v-for="item in provinceOptions"
                    :key="item"
                    :label="item"
                    :value="item"
                  />
                </el-select>
                <el-button @click="autoCompletePlate">自动补全</el-button>
              </el-form-item>
              <el-form-item label="识别置信度">
                <el-progress
                  :percentage="Math.round((formData.confidence || 0) * 100)"
                  :stroke-width="14"
                  :show-text="true"
                />
              </el-form-item>
              <el-form-item label="候选车牌">
                <el-tag
                  v-for="item in candidates"
                  :key="item.plate_number"
                  style="margin-right: 8px; margin-bottom: 8px; cursor: pointer"
                  @click="formData.plateNumber = item.plate_number"
                >
                  {{ item.plate_number }} ({{ (item.confidence * 100).toFixed(1) }}%)
                </el-tag>
              </el-form-item>
              <el-form-item label="车主姓名" required>
                <el-input v-model="formData.ownerName" placeholder="必填" />
              </el-form-item>
              <el-form-item label="车主电话">
                <el-input v-model="formData.ownerPhone" placeholder="可选" />
              </el-form-item>
              <el-form-item label="品牌型号" required>
                <el-input v-model="formData.brandModel" placeholder="必填，如：比亚迪汉EV" />
              </el-form-item>
              <el-form-item label="车辆描述">
                <el-input
                  v-model="formData.description"
                  type="textarea"
                  :rows="3"
                  placeholder="可选"
                />
              </el-form-item>
              <el-form-item label="状态">
                <el-select v-model="formData.status" style="width: 100%">
                  <el-option label="正常" value="NORMAL" />
                  <el-option label="黑名单" value="BLACKLIST" />
                  <el-option label="过期" value="EXPIRED" />
                </el-select>
              </el-form-item>
            </el-form>

            <el-button
              type="success"
              :disabled="!canSave"
              :loading="saving"
              @click="confirmSave"
            >
              确认入库
            </el-button>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="history-card">
        <template #header>识别历史</template>
        <el-table :data="records" border style="width: 100%">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="recognizedPlate" label="识别车牌" width="150" />
          <el-table-column label="置信度" width="120">
            <template #default="scope">
              {{ ((scope.row.confidence || 0) * 100).toFixed(1) }}%
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120" />
          <el-table-column prop="errorMessage" label="失败原因" min-width="180" show-overflow-tooltip />
          <el-table-column prop="createdAt" label="时间" width="180" />
        </el-table>
        <div class="pagination">
          <el-pagination
            v-model:current-page="pagination.current"
            v-model:page-size="pagination.size"
            :total="pagination.total"
            layout="total, prev, pager, next"
            @current-change="loadRecords"
          />
        </div>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getPlateRecords, recognizePlate, saveRecognizedVehicle } from '../api/plate'

const selectedFile = ref(null)
const recognizing = ref(false)
const saving = ref(false)
const records = ref([])
const candidates = ref([])
const provinceOptions = [
  '京', '津', '沪', '渝', '冀', '豫', '云', '辽', '黑', '湘', '皖',
  '鲁', '新', '苏', '浙', '赣', '鄂', '桂', '甘', '晋', '蒙', '陕',
  '吉', '闽', '贵', '粤', '青', '藏', '川', '宁', '琼'
]

const formData = reactive({
  recordId: null,
  plateNumber: '',
  province: '粤',
  confidence: 0,
  ownerName: '',
  ownerPhone: '',
  brandModel: '',
  description: '',
  status: 'NORMAL'
})

const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

const canSave = computed(() => {
  return (
    !!formData.recordId &&
    !!formData.plateNumber &&
    !!formData.ownerName &&
    !!formData.brandModel
  )
})

const strictPlateRegex = /^[\u4e00-\u9fa5][A-Z][A-Z0-9]{5,6}$/
const relaxedPlateRegex = /^[A-Z][A-Z0-9]{5,6}$/

const autoCompletePlate = () => {
  const plate = (formData.plateNumber || '').trim().toUpperCase()
  if (!plate) return

  if (strictPlateRegex.test(plate)) {
    formData.province = plate[0]
    return
  }

  if (relaxedPlateRegex.test(plate) && formData.province) {
    formData.plateNumber = `${formData.province}${plate}`
  }
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleFileRemove = () => {
  selectedFile.value = null
}

const resetCurrent = () => {
  selectedFile.value = null
  candidates.value = []
  formData.recordId = null
  formData.plateNumber = ''
  formData.province = '粤'
  formData.confidence = 0
  formData.ownerName = ''
  formData.ownerPhone = ''
  formData.brandModel = ''
  formData.description = ''
  formData.status = 'NORMAL'
}

const runRecognition = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择图片')
    return
  }
  recognizing.value = true
  try {
    const res = await recognizePlate(selectedFile.value)
    formData.recordId = res.data.recordId
    formData.plateNumber = res.data.plateNumber
    formData.confidence = res.data.confidence
    candidates.value = res.data.candidates || []
    autoCompletePlate()
    ElMessage.success('识别成功，请补全信息后入库')
    loadRecords()
  } catch (e) {
    ElMessage.error(e.message || '识别失败')
    loadRecords()
  } finally {
    recognizing.value = false
  }
}

const confirmSave = async () => {
  if (!canSave.value) {
    ElMessage.warning('请先识别并补全必填字段')
    return
  }
  saving.value = true
  try {
    await saveRecognizedVehicle({
      recordId: formData.recordId,
      plateNumber: formData.plateNumber,
      ownerName: formData.ownerName,
      ownerPhone: formData.ownerPhone,
      brandModel: formData.brandModel,
      description: formData.description,
      status: formData.status
    })
    ElMessage.success('入库成功')
    resetCurrent()
    loadRecords()
  } catch (e) {
    ElMessage.error(e.message || '入库失败')
    loadRecords()
  } finally {
    saving.value = false
  }
}

const loadRecords = async () => {
  try {
    const res = await getPlateRecords({
      current: pagination.current,
      size: pagination.size
    })
    records.value = res.data.records || []
    pagination.total = res.data.total || 0
  } catch (e) {
    ElMessage.error('加载历史失败')
  }
}

onMounted(() => {
  loadRecords()
})

watch(
  () => formData.province,
  () => {
    if (relaxedPlateRegex.test((formData.plateNumber || '').trim().toUpperCase())) {
      autoCompletePlate()
    }
  }
)
</script>

<style scoped>
.plate-page {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.block-card {
  margin-bottom: 20px;
}

.actions {
  margin-top: 15px;
}

.history-card {
  margin-top: 20px;
}

.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}
</style>
