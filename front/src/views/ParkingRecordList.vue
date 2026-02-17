<template>
  <div class="parking-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>停车记录</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增记录
          </el-button>
        </div>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="车牌号">
          <el-input v-model="searchForm.plateNumber" placeholder="请输入车牌号" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择" clearable style="width: 140px">
            <el-option label="停车中" value="PARKING" />
            <el-option label="已离开" value="EXITED" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="tableData" border style="width: 100%">
        <el-table-column prop="plateNumber" label="车牌号" width="120" />
        <el-table-column prop="entryTime" label="进入时间" width="170" />
        <el-table-column prop="exitTime" label="离开时间" width="170">
          <template #default="scope">
            {{ scope.row.exitTime || '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="parkingDuration" label="停车时长(分钟)" width="130" align="right">
          <template #default="scope">
            {{ scope.row.parkingDuration != null ? scope.row.parkingDuration : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="parkingFee" label="停车费(元)" width="110" align="right">
          <template #default="scope">
            {{ scope.row.parkingFee != null ? scope.row.parkingFee : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="gateNumber" label="出入口" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.status === 'PARKING'" type="success">停车中</el-tag>
            <el-tag v-else-if="scope.row.status === 'EXITED'" type="info">已离开</el-tag>
            <el-tag v-else>{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" @close="handleDialogClose">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="关联车辆" prop="vehicleId">
          <el-select
            v-model="formData.vehicleId"
            placeholder="请选择车辆"
            clearable
            filterable
            style="width: 100%"
            @change="onVehicleChange"
          >
            <el-option
              v-for="v in vehicleList"
              :key="v.id"
              :label="`${v.plateNumber} ${v.ownerName ? '-' + v.ownerName : ''}`"
              :value="v.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="车牌号" prop="plateNumber">
          <el-input v-model="formData.plateNumber" placeholder="请输入或由关联车辆带出" />
        </el-form-item>
        <el-form-item label="进入时间" prop="entryTime">
          <el-date-picker
            v-model="formData.entryTime"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="选择进入时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="离开时间" prop="exitTime">
          <el-date-picker
            v-model="formData.exitTime"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="未离开可留空"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="出入口" prop="gateNumber">
          <el-input v-model="formData.gateNumber" placeholder="如：东门入口" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status" placeholder="请选择" style="width: 100%">
            <el-option label="停车中" value="PARKING" />
            <el-option label="已离开" value="EXITED" />
          </el-select>
        </el-form-item>
        <el-form-item label="停车费(元)" prop="parkingFee">
          <el-input-number v-model="formData.parkingFee" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getParkingPage,
  saveParking,
  updateParking,
  deleteParking,
  getParkingList
} from '../api/parking'
import { getVehicleList } from '../api/vehicle'

const loading = ref(false)
const vehicleList = ref([])
const allVehicleList = ref([])
const tableData = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增记录')
const formRef = ref(null)
const isEdit = ref(false)
const currentId = ref(null)

const searchForm = reactive({
  plateNumber: '',
  status: ''
})

const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

const formData = reactive({
  vehicleId: null,
  plateNumber: '',
  entryTime: '',
  exitTime: '',
  gateNumber: '',
  status: 'PARKING',
  parkingFee: 0
})

const formRules = {
  vehicleId: [{ required: true, message: '请选择关联车辆', trigger: 'change' }],
  plateNumber: [{ required: true, message: '请输入车牌号', trigger: 'blur' }],
  entryTime: [{ required: true, message: '请选择进入时间', trigger: 'change' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getParkingPage({
      current: pagination.current,
      size: pagination.size,
      ...searchForm
    })
    if (res.code === 200) {
      tableData.value = res.data.records
      pagination.total = res.data.total
    }
  } finally {
    loading.value = false
  }
}

const refreshVehicleOptions = async (editingVehicleId = null) => {
  const parkingRes = await getParkingList({ status: 'PARKING' })
  const busyIds = new Set((parkingRes?.data || []).map((r) => r.vehicleId).filter(Boolean))
  vehicleList.value = allVehicleList.value.filter((v) => !busyIds.has(v.id) || v.id === editingVehicleId)
}

const handleSearch = () => {
  pagination.current = 1
  loadData()
}

const handleReset = () => {
  searchForm.plateNumber = ''
  searchForm.status = ''
  handleSearch()
}

const handleAdd = async () => {
  isEdit.value = false
  dialogTitle.value = '新增记录'
  resetForm()
  await refreshVehicleOptions()
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑记录'
  currentId.value = row.id
  formData.vehicleId = row.vehicleId
  formData.plateNumber = row.plateNumber
  formData.entryTime = row.entryTime
  formData.exitTime = row.exitTime || ''
  formData.gateNumber = row.gateNumber || ''
  formData.status = row.status || 'PARKING'
  formData.parkingFee = row.parkingFee != null ? Number(row.parkingFee) : 0
  await refreshVehicleOptions(row.vehicleId)
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该停车记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    const res = await deleteParking(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadData()
    }
  })
}

const handleSizeChange = () => loadData()
const handleCurrentChange = () => loadData()

const onVehicleChange = (vehicleId) => {
  if (!vehicleId) return
  const v = vehicleList.value.find((x) => x.id === vehicleId)
  if (v) {
    formData.plateNumber = v.plateNumber
    formData.vehicleId = v.id
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    const payload = {
      vehicleId: formData.vehicleId || undefined,
      plateNumber: formData.plateNumber,
      entryTime: formData.entryTime,
      exitTime: formData.exitTime || null,
      gateNumber: formData.gateNumber || null,
      status: formData.status,
      parkingFee: formData.parkingFee
    }
    const res = isEdit.value
      ? await updateParking(currentId.value, payload)
      : await saveParking(payload)

    if (res.code === 200) {
      ElMessage.success(isEdit.value ? '更新成功' : '新增成功')
      dialogVisible.value = false
      loadData()
      await refreshVehicleOptions()
    } else {
      ElMessage.error(res.message || '操作失败')
    }
  })
}

const resetForm = () => {
  formData.vehicleId = null
  formData.plateNumber = ''
  formData.entryTime = ''
  formData.exitTime = ''
  formData.gateNumber = ''
  formData.status = 'PARKING'
  formData.parkingFee = 0
  if (formRef.value) formRef.value.resetFields()
}

const handleDialogClose = () => {
  resetForm()
  isEdit.value = false
  currentId.value = null
}

onMounted(async () => {
  loadData()
  try {
    const res = await getVehicleList()
    if (res.code === 200) {
      allVehicleList.value = res.data || []
      await refreshVehicleOptions()
    }
  } catch (e) {
    console.error('加载车辆列表失败', e)
  }
})
</script>

<style scoped>
.parking-container {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}
</style>
