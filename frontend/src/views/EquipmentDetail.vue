<template>
  <div class="equipment-detail-page">
    <el-button 
      type="primary" 
      :icon="ArrowLeft" 
      @click="router.back()"
      style="margin-bottom: 20px; margin-right: 10px;"
    >
      返回
    </el-button>

    <el-card v-if="loading" shadow="hover">
      <el-skeleton :rows="8" animated />
    </el-card>

    <el-card v-else-if="equipment" shadow="hover" class="detail-card">
      <template #header>
        <div class="detail-header">
          <h2>{{ equipment.name }}</h2>
          <el-tag :type="getStatusType(equipment.status)" size="large">
            {{ getStatusText(equipment.status) }}
          </el-tag>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="设备ID">{{ equipment.id }}</el-descriptions-item>
        <el-descriptions-item label="设备名称">{{ equipment.name }}</el-descriptions-item>
        <el-descriptions-item label="实验室">
          {{ equipment.lab_name || '未分配' }}
        </el-descriptions-item>
        <el-descriptions-item label="类别">
          {{ equipment.category === 1 ? '学院' : equipment.category === 2 ? '实验室' : '未分类' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(equipment.status)">
            {{ getStatusText(equipment.status) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div class="detail-actions">
        <el-button v-if="!userStore.isAdmin && equipment.status === 1" type="primary" size="large" @click="handleBook">
          <el-icon><Calendar /></el-icon>
          立即预约
        </el-button>
        
        <template v-if="userStore.isAdmin">
        <el-button type="warning" @click="handleEdit">
          <el-icon><Edit /></el-icon>
          编辑设备
        </el-button>
        <el-button type="danger" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除设备
        </el-button>
        </template>
      </div>
    </el-card>

    <el-empty v-else description="设备不存在" />

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑设备"
      width="600px"
      @close="resetEditForm"
    >
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="实验室" prop="lab_id">
          <el-select v-model="editForm.lab_id" placeholder="请选择实验室" style="width: 100%">
            <el-option
              v-for="lab in labs"
              :key="lab.id"
              :label="lab.name"
              :value="lab.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="类别" prop="category">
          <el-select v-model="editForm.category" placeholder="请选择类别" style="width: 100%">
            <el-option label="学院" :value="1" />
            <el-option label="实验室" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="editForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="可用" :value="1" />
            <el-option label="使用中" :value="2" />
            <el-option label="维护中" :value="3" />
            <el-option label="已停用" :value="0" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleUpdate">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 预约对话框 -->
    <el-dialog v-model="showBookDialog" title="预约设备" width="500px">
      <el-form :model="bookForm" label-width="80px">
        <el-form-item label="设备名称">
          <el-input v-model="bookForm.equipmentName" disabled />
        </el-form-item>
        <el-form-item label="预约日期">
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="请选择预约日期"
            style="width: 100%"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
            @change="handleDateChange"
          />
        </el-form-item>
        
        <!-- 可用时间段显示 -->
        <el-form-item v-if="equipment && equipment.id" label="选择时间段">
          <div class="timeslots-container">
            <div class="timeslots-header">
              <span class="timeslots-tip">
                <el-icon><Clock /></el-icon>
                <span v-if="selectedDate">
                  已选择日期：{{ selectedDate }}，请点击下方时间段快速选择
                </span>
                <span v-else>
                  请先选择日期，然后选择使用时间段
                </span>
              </span>
            </div>
            <div v-if="availableTimeslots.length > 0" class="timeslots-list">
              <el-tag
                v-for="slot in availableTimeslots"
                :key="slot.slot_id"
                class="timeslot-tag"
                :class="{ 'timeslot-selected': isTimeslotSelected(slot) }"
                @click="selectTimeslot(slot)"
                effect="plain"
                type="info"
              >
                {{ formatTimeslot(slot) }}
              </el-tag>
            </div>
            <div v-else class="no-timeslots">
              <el-empty 
                :image-size="60" 
                description="暂无可用时间段"
                v-if="selectedDate"
              />
            </div>
          </div>
        </el-form-item>
        
        <el-form-item label="用途说明">
          <el-input v-model="bookForm.description" type="textarea" rows="3" placeholder="请填写预约用途" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBookDialog = false">取消</el-button>
        <el-button type="primary" :loading="bookLoading" @click="submitBooking">提交预约</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Delete, Calendar, Clock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getEquipmentById, updateEquipment, deleteEquipment } from '@/api/equipment'
import { createReservation } from '@/api/reservation'
import { getLabList } from '@/api/laboratory'
import { getAvailableTimeslots, getAvailableDates } from '@/api/timeslot'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const equipment = ref(null)
const labs = ref([])
const loading = ref(false)
const showEditDialog = ref(false)
const editLoading = ref(false)

const editForm = reactive({
  name: '',
  lab_id: null,
  category: 2,
  status: 1
})

const editRules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  lab_id: [{ required: true, message: '请选择实验室', trigger: 'change' }],
  category: [{ required: true, message: '请选择类别', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const editFormRef = ref(null)

// 预约相关
const showBookDialog = ref(false)
const bookLoading = ref(false)
const bookForm = reactive({
  equipmentName: '',
  start_time: null,
  end_time: null,
  description: ''
})

// 可用时间段相关
const availableTimeslots = ref([])
const selectedDate = ref(null)
const availableDates = ref([]) // 存储可用日期列表

// 获取设备详情
const fetchEquipmentDetail = async () => {
  const id = route.params.id
  if (!id) return

  loading.value = true
  try {
    const response = await getEquipmentById(id)
    if (response.code === 200) {
      equipment.value = response.data
    }
  } catch (error) {
    console.error('获取设备详情失败:', error)
    ElMessage.error('获取设备详情失败')
  } finally {
    loading.value = false
  }
}

// 获取实验室列表
const fetchLabs = async () => {
  try {
    const response = await getLabList()
    if (response.code === 200) {
      labs.value = response.data.items || response.data || []
    }
  } catch (error) {
    console.error('获取实验室列表失败:', error)
  }
}

// 编辑
const handleEdit = () => {
  if (!equipment.value) return
  
  editForm.name = equipment.value.name || ''
  editForm.lab_id = equipment.value.lab_id || null
  editForm.category = equipment.value.category || 2
  editForm.status = equipment.value.status !== undefined ? equipment.value.status : 1
  showEditDialog.value = true
}

// 更新
const handleUpdate = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true
      try {
        const id = route.params.id
        const { ...formData } = editForm
        // 确保数据类型正确
        const requestData = {
          name: formData.name,
          lab_id: formData.lab_id,
          category: Number(formData.category),
          status: Number(formData.status)
        }
        const response = await updateEquipment(id, requestData)
        if (response.code === 200) {
          ElMessage.success('更新成功')
          showEditDialog.value = false
          fetchEquipmentDetail()
        }
      } catch (error) {
        console.error('更新设备失败:', error)
      } finally {
        editLoading.value = false
      }
    }
  })
}

// 删除
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除该设备吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const id = route.params.id
    const response = await deleteEquipment(id)
    if (response.code === 200) {
      ElMessage.success('删除成功')
      router.push('/equipment')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除设备失败:', error)
    }
  }
}

// 预约操作
const handleBook = async () => {
  if (!equipment.value) return
  bookForm.equipmentName = equipment.value.name
  bookForm.start_time = null
  bookForm.end_time = null
  bookForm.description = ''
  availableTimeslots.value = []
  selectedDate.value = null
  availableDates.value = []
  showBookDialog.value = true
  // 获取设备的可用日期
  await fetchAvailableDates(equipment.value.id)
}

// 获取可用日期
const fetchAvailableDates = async (equipId) => {
  if (!equipId) return
  
  try {
    const res = await getAvailableDates(equipId, null, 60) // 查询未来60天
    if (res.code === 200) {
      availableDates.value = res.data || []
    }
  } catch (error) {
    console.error('获取可用日期失败:', error)
    availableDates.value = []
  }
}

// 获取可用时间段
const fetchAvailableTimeslots = async (equipId, date = null) => {
  if (!equipId) return
  
  try {
    const res = await getAvailableTimeslots(equipId, date)
    if (res.code === 200) {
      availableTimeslots.value = res.data || []
    }
  } catch (error) {
    console.error('获取可用时间段失败:', error)
    availableTimeslots.value = []
  }
}

// 处理日期选择变化
const handleDateChange = async (date) => {
  if (!equipment.value) {
    if (date) {
      ElMessage.warning('设备信息加载中，请稍候')
      selectedDate.value = null
    }
    return
  }
  
  if (date) {
    selectedDate.value = date
    // 清空之前选择的时间段
    bookForm.start_time = null
    bookForm.end_time = null
    // 获取该日期的可用时间段
    await fetchAvailableTimeslots(equipment.value.id, date)
  } else {
    selectedDate.value = null
    bookForm.start_time = null
    bookForm.end_time = null
    availableTimeslots.value = []
  }
}

// 格式化时间段显示
const formatTimeslot = (slot) => {
  const start = slot.start_time.substring(0, 5) // 取 HH:mm
  const end = slot.end_time.substring(0, 5)
  return `${start} - ${end}`
}

// 检查时间段是否被选中
const isTimeslotSelected = (slot) => {
  if (!bookForm.start_time || !bookForm.end_time) return false
  if (!selectedDate.value) return false
  
  // 提取时间部分进行比较
  const startTimeOnly = bookForm.start_time.split(' ')[1]?.substring(0, 5) // HH:mm
  const endTimeOnly = bookForm.end_time.split(' ')[1]?.substring(0, 5)
  const slotStart = slot.start_time.substring(0, 5)
  const slotEnd = slot.end_time.substring(0, 5)
  
  return startTimeOnly === slotStart && endTimeOnly === slotEnd
}

// 选择时间段
const selectTimeslot = (slot) => {
  if (!selectedDate.value) {
    ElMessage.warning('请先选择日期')
    return
  }
  
  if (!equipment.value) {
    ElMessage.warning('设备信息加载中，请稍候')
    return
  }
  
  // 构建完整的日期时间
  const startDateTime = `${selectedDate.value} ${slot.start_time}`
  const endDateTime = `${selectedDate.value} ${slot.end_time}`
  
  bookForm.start_time = startDateTime
  bookForm.end_time = endDateTime
  ElMessage.success('已选择时间段')
}

const submitBooking = async () => {
  if (!selectedDate.value) {
    ElMessage.warning('请选择预约日期')
    return
  }
  if (!bookForm.start_time || !bookForm.end_time) {
    ElMessage.warning('请选择时间段')
    return
  }
  
  // 验证开始和结束时间是否在同一天
  const startDate = bookForm.start_time.split(' ')[0]
  const endDate = bookForm.end_time.split(' ')[0]
  if (startDate !== endDate || startDate !== selectedDate.value) {
    ElMessage.warning('开始和结束时间必须在同一天')
    return
  }
  
  bookLoading.value = true
  try {
    const data = {
      equip_id: equipment.value.id,
      start_time: bookForm.start_time,
      end_time: bookForm.end_time,
      description: bookForm.description
    }
    const res = await createReservation(data)
    if (res.code === 200) {
      ElMessage.success('预约申请已提交')
      showBookDialog.value = false
    }
  } catch (e) {
    console.error(e)
  } finally {
    bookLoading.value = false
  }
}

// 禁用过去的日期以及没有可用时间段的日期
const disabledDate = (time) => {
  // 禁用今天之前的日期（今天允许选择）
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  if (time.getTime() < today.getTime()) {
    return true
  }
  
  // 如果有可用日期列表，禁用不在列表中的日期
  if (availableDates.value && availableDates.value.length > 0) {
    const dateStr = time.toISOString().split('T')[0]
    return !availableDates.value.includes(dateStr)
  }
  
  // 如果没有可用日期列表，允许选择（可能是还在加载中）
  return false
}


// 重置编辑表单
const resetEditForm = () => {
  Object.assign(editForm, {
    name: '',
    lab_id: null,
    category: 2,
    status: 1
  })
  editFormRef.value?.resetFields()
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    1: '可用',
    2: '使用中',
    3: '维护中',
    0: '已停用'
  }
  return statusMap[status] || '未知'
}

// 获取状态类型
const getStatusType = (status) => {
  const statusMap = {
    1: 'success',  // 可用
    2: 'warning',  // 使用中
    3: 'info',  // 维护中
    0: 'danger'  // 已停用
  }
  return statusMap[status] || ''
}

// 初始化
onMounted(() => {
  fetchLabs()
  fetchEquipmentDetail()
})
</script>

<style scoped lang="scss">
.equipment-detail-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.detail-card {
  border-radius: 8px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  h2 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: #333;
  }
}

.detail-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.timeslots-container {
  width: 100%;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.timeslots-header {
  margin-bottom: 12px;
  
  .timeslots-tip {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #606266;
    
    .el-icon {
      font-size: 14px;
    }
  }
}

.timeslots-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.timeslot-tag {
  cursor: pointer;
  padding: 8px 16px;
  font-size: 13px;
  transition: all 0.3s;
  border: 1px solid #dcdfe6;
  
  &:hover {
    background-color: #ecf5ff;
    border-color: #409eff;
    color: #409eff;
  }
  
  &.timeslot-selected {
    background-color: #409eff;
    border-color: #409eff;
    color: #fff;
  }
}

.no-timeslots {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 20px 0;
}
</style>
