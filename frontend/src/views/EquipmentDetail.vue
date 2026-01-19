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
        <el-form-item label="预约时间">
          <el-date-picker
            v-model="bookForm.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            style="width: 100%"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            :disabled-date="disabledDate"
            :disabled-time="disabledTime"
            @calendar-change="handleCalendarChange"
          />
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
import { ArrowLeft, Edit, Delete, Calendar } from '@element-plus/icons-vue'
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
  timeRange: [],
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
  bookForm.timeRange = []
  bookForm.description = ''
  availableTimeslots.value = []
  selectedDate.value = null
  availableDates.value = []
  showBookDialog.value = true
  // 获取设备的可用时间段和可用日期
  await Promise.all([
    fetchAvailableTimeslots(equipment.value.id, null),
    fetchAvailableDates(equipment.value.id)
  ])
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

// 处理日期选择器日历变化
const handleCalendarChange = async (dates) => {
  if (!equipment.value) return
  
  // 如果选择了日期，获取该日期的可用时间段
  if (dates && dates.length > 0) {
    const date = dates[0]
    if (date) {
      const dateStr = typeof date === 'string' ? date.split(' ')[0] : date.toISOString().split('T')[0]
      selectedDate.value = dateStr
      await fetchAvailableTimeslots(equipment.value.id, dateStr)
    }
  } else {
    selectedDate.value = null
    // 如果没有选择日期，获取所有可用时间段
    await fetchAvailableTimeslots(equipment.value.id, null)
  }
}

const submitBooking = async () => {
  if (!bookForm.timeRange || bookForm.timeRange.length < 2) {
    ElMessage.warning('请选择预约时间')
    return
  }
  bookLoading.value = true
  try {
    const data = {
      equip_id: equipment.value.id, // 确保字段名为 equip_id
      start_time: bookForm.timeRange[0],
      end_time: bookForm.timeRange[1],
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

// 禁用过去的时间以及不可用的时间段
const disabledTime = (date) => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const isToday = date && new Date(date).getTime() >= today.getTime() && 
                  new Date(date).getTime() < today.getTime() + 24 * 60 * 60 * 1000
  
  // 如果没有可用时间段配置，只禁用过去的时间
  if (!availableTimeslots.value || availableTimeslots.value.length === 0) {
    if (isToday) {
      return {
        disabledHours: () => {
          const hours = []
          for (let i = 0; i < now.getHours(); i++) {
            hours.push(i)
          }
          return hours
        },
        disabledMinutes: (hour) => {
          const minutes = []
          if (hour === now.getHours()) {
            for (let i = 0; i <= now.getMinutes(); i++) {
              minutes.push(i)
            }
          }
          return minutes
        },
        disabledSeconds: (hour, minute) => {
          const seconds = []
          if (hour === now.getHours() && minute === now.getMinutes()) {
            for (let i = 0; i <= now.getSeconds(); i++) {
              seconds.push(i)
            }
          }
          return seconds
        }
      }
    }
    return {}
  }
  
  // 构建可用时间段的集合
  const availableRanges = availableTimeslots.value.map(slot => {
    const [startH, startM, startS] = slot.start_time.split(':').map(Number)
    const [endH, endM, endS] = slot.end_time.split(':').map(Number)
    return {
      start: startH * 3600 + startM * 60 + startS, // 转换为秒数
      end: endH * 3600 + endM * 60 + endS
    }
  })
  
  // 检查某个时间点是否在可用时间段内
  const isTimeAvailable = (hour, minute, second) => {
    const timeInSeconds = hour * 3600 + minute * 60 + second
    return availableRanges.some(range => timeInSeconds >= range.start && timeInSeconds < range.end)
  }
  
  // 禁用不在可用时间段内的小时
  const disabledHours = []
  for (let hour = 0; hour < 24; hour++) {
    // 检查该小时是否有任何可用时间
    const hasAvailableTime = availableRanges.some(range => {
      const hourStart = hour * 3600
      const hourEnd = (hour + 1) * 3600
      return range.start < hourEnd && range.end > hourStart
    })
    
    if (!hasAvailableTime) {
      disabledHours.push(hour)
    } else if (isToday && hour < now.getHours()) {
      // 如果是今天，还要禁用已经过去的小时
      disabledHours.push(hour)
    }
  }
  
  // 禁用不在可用时间段内的分钟和秒
  const disabledMinutesMap = {}
  const disabledSecondsMap = {}
  
  // 为每个小时计算禁用的分钟
  for (let hour = 0; hour < 24; hour++) {
    if (disabledHours.includes(hour)) {
      // 如果整个小时都被禁用，禁用所有分钟
      disabledMinutesMap[hour] = Array.from({ length: 60 }, (_, i) => i)
      continue
    }
    
    disabledMinutesMap[hour] = []
    for (let minute = 0; minute < 60; minute++) {
      // 检查该分钟是否有任何可用时间
      const hasAvailableTime = availableRanges.some(range => {
        const minuteStart = hour * 3600 + minute * 60
        const minuteEnd = minuteStart + 60
        return range.start < minuteEnd && range.end > minuteStart
      })
      
      if (!hasAvailableTime) {
        disabledMinutesMap[hour].push(minute)
      } else if (isToday && hour === now.getHours() && minute <= now.getMinutes()) {
        // 如果是今天且是当前小时，禁用已过去的分钟
        disabledMinutesMap[hour].push(minute)
      }
      
      // 为每个分钟计算禁用的秒
      if (!hasAvailableTime || (isToday && hour === now.getHours() && minute < now.getMinutes())) {
        const key = `${hour}-${minute}`
        disabledSecondsMap[key] = Array.from({ length: 60 }, (_, i) => i)
      } else if (isToday && hour === now.getHours() && minute === now.getMinutes()) {
        const key = `${hour}-${minute}`
        disabledSecondsMap[key] = []
        for (let second = 0; second <= now.getSeconds(); second++) {
          disabledSecondsMap[key].push(second)
        }
      } else {
        // 检查该秒是否在可用时间段内
        const key = `${hour}-${minute}`
        disabledSecondsMap[key] = []
        for (let second = 0; second < 60; second++) {
          if (!isTimeAvailable(hour, minute, second)) {
            disabledSecondsMap[key].push(second)
          }
        }
      }
    }
  }
  
  return {
    disabledHours: () => disabledHours,
    disabledMinutes: (hour) => disabledMinutesMap[hour] || [],
    disabledSeconds: (hour, minute) => {
      const key = `${hour}-${minute}`
      return disabledSecondsMap[key] || []
    }
  }
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
</style>
