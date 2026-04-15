<template>
  <div class="vehicle-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="header-title">
            <el-icon><Van /></el-icon>
            车辆管理
          </span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增车辆
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="车牌号">
          <el-input
            v-model="searchForm.plateNumber"
            placeholder="请输入车牌号"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="车主姓名">
          <el-input
            v-model="searchForm.ownerName"
            placeholder="请输入车主姓名"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="请选择状态"
            clearable
            style="width: 150px"
          >
            <el-option label="正常" value="NORMAL" />
            <el-option label="黑名单" value="BLACKLIST" />
            <el-option label="过期" value="EXPIRED" />
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

      <!-- 表格 -->
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="plateNumber" label="车牌号" width="150" />
        <el-table-column prop="ownerName" label="车主姓名" width="120" />
        <el-table-column prop="ownerPhone" label="车主电话" width="150" />
        <el-table-column prop="brandModel" label="品牌型号" width="140" show-overflow-tooltip />
        <el-table-column prop="description" label="车辆描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.status === 'NORMAL'" type="success">正常</el-tag>
            <el-tag v-else-if="scope.row.status === 'BLACKLIST'" type="danger">黑名单</el-tag>
            <el-tag v-else-if="scope.row.status === 'EXPIRED'" type="warning">过期</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="handleEdit(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-button
          type="danger"
          :disabled="selectedIds.length === 0"
          @click="handleBatchDelete"
        >
          批量删除
        </el-button>
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

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="车牌号" prop="plateNumber">
          <el-input v-model="formData.plateNumber" placeholder="请输入车牌号" />
        </el-form-item>
        <el-form-item label="关联车主">
          <el-select v-model="formData.ownerId" placeholder="请选择车主（可选）" clearable style="width: 100%" @change="onOwnerChange">
            <el-option
              v-for="item in ownerList"
              :key="item.id"
              :label="`${item.name} - ${item.phone || ''}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="车主姓名" prop="ownerName">
          <el-input v-model="formData.ownerName" placeholder="请输入或由关联车主自动带出" />
        </el-form-item>
        <el-form-item label="车主电话" prop="ownerPhone">
          <el-input v-model="formData.ownerPhone" placeholder="请输入或由关联车主自动带出" />
        </el-form-item>
        <el-form-item label="品牌型号" prop="brandModel">
          <el-input v-model="formData.brandModel" placeholder="如：大众帕萨特、丰田汉兰达" />
        </el-form-item>
        <el-form-item label="车辆描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="5" placeholder="车辆特性描述，可写较多内容：颜色、配置、常停位置、备注等" maxlength="2000" show-word-limit />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="正常" value="NORMAL" />
            <el-option label="黑名单" value="BLACKLIST" />
            <el-option label="过期" value="EXPIRED" />
          </el-select>
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
  getVehiclePage,
  saveVehicle,
  updateVehicle,
  deleteVehicle,
  deleteVehicleBatch
} from '../api/vehicle'
import { getOwnerList } from '../api/owner'

const loading = ref(false)
const ownerList = ref([])
const tableData = ref([])
const selectedIds = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增车辆')
const formRef = ref(null)
const isEdit = ref(false)
const currentId = ref(null)

const searchForm = reactive({
  plateNumber: '',
  ownerName: '',
  status: ''
})

const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

const formData = reactive({
  plateNumber: '',
  ownerId: null,
  ownerName: '',
  ownerPhone: '',
  brandModel: '',
  description: '',
  status: 'NORMAL'
})

const formRules = {
  plateNumber: [
    { required: true, message: '请输入车牌号', trigger: 'blur' }
  ]
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const res = await getVehiclePage({
      current: pagination.current,
      size: pagination.size,
      ...searchForm
    })
    if (res.code === 200) {
      tableData.value = res.data.records
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.current = 1
  loadData()
}

// 重置
const handleReset = () => {
  searchForm.plateNumber = ''
  searchForm.ownerName = ''
  searchForm.status = ''
  handleSearch()
}

// 新增
const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增车辆'
  dialogVisible.value = true
  resetForm()
}

// 编辑
const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑车辆'
  currentId.value = row.id
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该车辆吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteVehicle(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        loadData()
      }
    } catch (error) {
      console.error('删除失败:', error)
    }
  })
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要删除的车辆')
    return
  }
  ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 条记录吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteVehicleBatch(selectedIds.value)
      if (res.code === 200) {
        ElMessage.success('批量删除成功')
        selectedIds.value = []
        loadData()
      }
    } catch (error) {
      console.error('批量删除失败:', error)
    }
  })
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map(item => item.id)
}

// 分页大小变化
const handleSizeChange = () => {
  loadData()
}

// 当前页变化
const handleCurrentChange = () => {
  loadData()
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        let res
        if (isEdit.value) {
          res = await updateVehicle(currentId.value, formData)
        } else {
          res = await saveVehicle(formData)
        }
        if (res.code === 200) {
          ElMessage.success(isEdit.value ? '更新成功' : '新增成功')
          dialogVisible.value = false
          loadData()
        }
      } catch (error) {
        console.error('提交失败:', error)
      }
    }
  })
}

// 重置表单
const resetForm = () => {
  formData.plateNumber = ''
  formData.ownerId = null
  formData.ownerName = ''
  formData.ownerPhone = ''
  formData.brandModel = ''
  formData.description = ''
  formData.status = 'NORMAL'
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 对话框关闭
const handleDialogClose = () => {
  resetForm()
  isEdit.value = false
  currentId.value = null
}

// 选择车主时自动带出姓名、电话
const onOwnerChange = (ownerId) => {
  if (!ownerId) {
    formData.ownerName = ''
    formData.ownerPhone = ''
    return
  }
  const owner = ownerList.value.find(o => o.id === ownerId)
  if (owner) {
    formData.ownerName = owner.name
    formData.ownerPhone = owner.phone || ''
  }
}

onMounted(async () => {
  loadData()
  try {
    const res = await getOwnerList()
    if (res.code === 200) {
      ownerList.value = res.data || []
    }
  } catch (e) {
    console.error('加载车主列表失败', e)
  }
})
</script>

<style scoped>
.vehicle-container {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.search-form {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

