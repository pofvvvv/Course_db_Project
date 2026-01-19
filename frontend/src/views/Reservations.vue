<template>
  <div class="reservations-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon><Calendar /></el-icon>
        预约管理
      </h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建预约
      </el-button>
    </div>

    <el-tabs v-model="activeTab" class="reservation-tabs" @tab-change="handleTabChange">
      <!-- 我的预约 Tab -->
      <el-tab-pane label="我的预约" name="my">
        <el-card shadow="hover" class="table-card">
          <div class="filter-bar">
            <el-radio-group v-model="statusFilter" @change="fetchMyReservations">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button :label="0">待审批</el-radio-button>
              <el-radio-button :label="1">已通过</el-radio-button>
              <el-radio-button :label="2">已拒绝</el-radio-button>
              <el-radio-button :label="3">已取消</el-radio-button>
            </el-radio-group>
            <el-button :icon="Refresh" circle @click="fetchMyReservations" />
          </div>

          <el-table :data="myReservations" v-loading="loading" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="equip_name" label="设备名称" min-width="150" />
            <el-table-column label="预约时间" min-width="200">
              <template #default="{ row }">
                {{ formatDate(row.start_time) }} 至 {{ formatDate(row.end_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button 
                  v-if="row.status === 0" 
                  type="danger" 
                  link 
                  @click="handleCancel(row)"
                >
                  取消
                </el-button>
                <el-button type="primary" link @click="handleView(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.page_size"
              :total="total"
              layout="total, prev, pager, next"
              @current-change="fetchMyReservations"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 管理员审批 Tab -->
      <el-tab-pane v-if="userStore.isAdmin" label="预约审批" name="admin">
        <el-card shadow="hover" class="table-card">
          <div class="filter-bar">
            <el-radio-group v-model="adminStatusFilter" @change="fetchAdminReservations">
              <el-radio-button :label="0">待审批</el-radio-button>
              <el-radio-button label="">全部记录</el-radio-button>
            </el-radio-group>
            <el-button :icon="Refresh" circle @click="fetchAdminReservations" />
          </div>

          <el-table :data="adminReservations" v-loading="loading" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="user_name" label="申请人" width="120" />
            <el-table-column prop="equip_name" label="设备名称" min-width="150" />
            <el-table-column label="预约时间" min-width="200">
              <template #default="{ row }">
                {{ formatDate(row.start_time) }} <br/> {{ formatDate(row.end_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="description" label="用途说明" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <div v-if="row.status === 0">
                  <el-button type="success" link @click="handleApprove(row)">通过</el-button>
                  <el-button type="danger" link @click="handleReject(row)">拒绝</el-button>
                </div>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="adminPagination.page"
              v-model:page-size="adminPagination.page_size"
              :total="adminTotal"
              layout="total, prev, pager, next"
              @current-change="fetchAdminReservations"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建预约对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建预约" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="选择设备">
          <el-select 
            v-model="createForm.equipment_id" 
            filterable 
            remote
            :remote-method="searchEquipment"
            placeholder="请输入设备名称搜索"
            :loading="equipmentLoading"
            style="width: 100%"
          >
            <el-option
              v-for="item in equipmentOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="预约时间">
          <el-date-picker
            v-model="createForm.timeRange"
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
        
        <!-- 可用时间段显示 -->
        <el-form-item v-if="createForm.equipment_id" label="可预约时间段">
          <div class="timeslots-container">
            <div class="timeslots-header">
              <span class="timeslots-tip">
                <el-icon><Clock /></el-icon>
                <span v-if="selectedDate">
                  已选择日期：{{ selectedDate }}，点击下方时间段快速选择
                </span>
                <span v-else>
                  请先在上方选择日期，然后点击时间段快速选择时间
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
              <span v-else style="color: #909399; font-size: 13px;">
                请先选择日期查看可用时间段
              </span>
            </div>
          </div>
        </el-form-item>
        
        <el-form-item label="用途说明">
          <el-input v-model="createForm.description" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCreate" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="预约详情" width="500px">
      <el-descriptions :column="1" border v-if="currentReservation">
        <el-descriptions-item label="设备名称">{{ currentReservation.equip_name }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatDate(currentReservation.start_time) }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ formatDate(currentReservation.end_time) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentReservation.status)">{{ getStatusText(currentReservation.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="用途说明">{{ currentReservation.description }}</el-descriptions-item>
        <el-descriptions-item label="审批意见" v-if="currentReservation.reject_reason">
          {{ currentReservation.reject_reason }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { Calendar, Plus, Refresh, Clock } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getReservationList, createReservation, cancelReservation, approveReservation, rejectReservation } from '@/api/reservation'
import { getEquipmentList } from '@/api/equipment'
import { getAvailableTimeslots, getAvailableDates } from '@/api/timeslot'

const userStore = useUserStore()
const activeTab = ref('my')
const loading = ref(false)

// 我的预约相关
const myReservations = ref([])
const statusFilter = ref('')
const pagination = reactive({ page: 1, page_size: 10 })
const total = ref(0)

// 管理员相关
const adminReservations = ref([])
const adminStatusFilter = ref(0) // 默认显示待审批
const adminPagination = reactive({ page: 1, page_size: 10 })
const adminTotal = ref(0)

// 创建相关
const showCreateDialog = ref(false)
const submitting = ref(false)
const equipmentLoading = ref(false)
const equipmentOptions = ref([])
const createForm = reactive({
  equipment_id: null,
  timeRange: [],
  description: ''
})

// 可用时间段相关
const availableTimeslots = ref([]) // 存储可用时间段
const selectedDate = ref(null) // 当前选择的日期
const availableDates = ref([]) // 存储可用日期列表

// 详情相关
const showDetailDialog = ref(false)
const currentReservation = ref(null)

// 获取我的预约
const fetchMyReservations = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      status: statusFilter.value,
      mine: true // 假设后端支持此参数区分
    }
    const res = await getReservationList(params)
    if (res.code === 200) {
      myReservations.value = res.data.items || res.data
      total.value = res.data.total || myReservations.value.length
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 获取管理员列表
const fetchAdminReservations = async () => {
  if (!userStore.isAdmin) return
  loading.value = true
  try {
    const params = {
      page: adminPagination.page,
      page_size: adminPagination.page_size,
      status: adminStatusFilter.value
    }
    const res = await getReservationList(params)
    if (res.code === 200) {
      adminReservations.value = res.data.items || res.data
      adminTotal.value = res.data.total || adminReservations.value.length
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleTabChange = (tab) => {
  if (tab === 'my') fetchMyReservations()
  else fetchAdminReservations()
}

// 创建预约
const handleCreate = () => {
  showCreateDialog.value = true
  createForm.equipment_id = null
  createForm.timeRange = []
  createForm.description = ''
  availableTimeslots.value = []
  selectedDate.value = null
  availableDates.value = []
  searchEquipment('') // 加载初始设备列表
}

// 监听设备选择变化，获取可用时间段和可用日期
watch(() => createForm.equipment_id, async (newEquipId) => {
  if (newEquipId) {
    await Promise.all([
      fetchAvailableTimeslots(newEquipId, null),
      fetchAvailableDates(newEquipId)
    ])
  } else {
    availableTimeslots.value = []
    availableDates.value = []
  }
})

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

// 处理日期选择器日历变化（用户点击日期时）
const handleCalendarChange = async (dates) => {
  if (!createForm.equipment_id) return
  
  // 如果选择了日期，获取该日期的可用时间段
  if (dates && dates.length > 0) {
    const date = dates[0]
    if (date) {
      // 处理不同的日期格式
      let dateStr
      if (typeof date === 'string') {
        dateStr = date.split(' ')[0]
      } else if (date instanceof Date) {
        dateStr = date.toISOString().split('T')[0]
      } else {
        // 可能是数组中的第一个元素
        const dateObj = Array.isArray(date) ? date[0] : date
        dateStr = dateObj instanceof Date ? dateObj.toISOString().split('T')[0] : dateObj.split(' ')[0]
      }
      
      if (dateStr && dateStr !== selectedDate.value) {
        selectedDate.value = dateStr
        // 立即获取该日期的可用时间段，用于禁用不可用时间
        await fetchAvailableTimeslots(createForm.equipment_id, dateStr)
      }
    }
  } else {
    selectedDate.value = null
    // 如果没有选择日期，获取所有可用时间段
    await fetchAvailableTimeslots(createForm.equipment_id, null)
  }
}

// 监听时间范围变化，更新selectedDate
watch(() => createForm.timeRange, async (newRange) => {
  if (newRange && newRange.length > 0 && newRange[0] && createForm.equipment_id) {
    const dateStr = newRange[0].split(' ')[0]
    if (dateStr !== selectedDate.value) {
      selectedDate.value = dateStr
      // 当时间范围变化时，也要更新该日期的可用时间段
      await fetchAvailableTimeslots(createForm.equipment_id, dateStr)
    }
  }
})

const searchEquipment = async (query) => {
  equipmentLoading.value = true
  try {
    const res = await getEquipmentList({ keyword: query, page_size: 20 })
    if (res.code === 200) {
      equipmentOptions.value = res.data.items || res.data
    }
  } finally {
    equipmentLoading.value = false
  }
}

const submitCreate = async () => {
  if (!createForm.equipment_id || !createForm.timeRange || createForm.timeRange.length < 2) {
    ElMessage.warning('请完善预约信息')
    return
  }
  submitting.value = true
  try {
    const data = {
      equip_id: createForm.equipment_id, // 确保字段名为 equip_id
      start_time: createForm.timeRange[0],
      end_time: createForm.timeRange[1],
      description: createForm.description
    }
    const res = await createReservation(data)
    if (res.code === 200) {
      ElMessage.success('预约提交成功')
      showCreateDialog.value = false
      fetchMyReservations()
    }
  } catch (error) {
    console.error(error)
  } finally {
    submitting.value = false
  }
}

// 取消预约
const handleCancel = async (row) => {
  try {
    await ElMessageBox.confirm('确定要取消该预约吗？', '提示', { type: 'warning' })
    const res = await cancelReservation(row.id)
    if (res.code === 200) {
      ElMessage.success('已取消')
      // 实时更新界面：如果当前是在筛选状态下（非全部），则移除该条目
      if (statusFilter.value !== '') {
        const index = myReservations.value.findIndex(item => item.id === row.id)
        if (index !== -1) myReservations.value.splice(index, 1)
      } else {
        row.status = 3 // 更新状态为已取消
      }
      fetchMyReservations() // 后台刷新以确保数据一致
    }
  } catch (e) {
    if (e !== 'cancel') {
      // 如果取消失败（例如已经是取消状态），也刷新列表以显示最新状态
      fetchMyReservations()
    }
  }
}

// 审批
const handleApprove = async (row) => {
  try {
    const res = await approveReservation(row.id)
    if (res.code === 200) {
      ElMessage.success('已通过')
      // 实时更新：如果是待审批列表，移除该条目
      if (adminStatusFilter.value === 0) {
        const index = adminReservations.value.findIndex(item => item.id === row.id)
        if (index !== -1) adminReservations.value.splice(index, 1)
      } else {
        row.status = 1
      }
      fetchAdminReservations()
    }
  } catch (e) {}
}

const handleReject = async (row) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝理由', '拒绝预约', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    const res = await rejectReservation(row.id, { reason: value })
    if (res.code === 200) {
      ElMessage.success('已拒绝')
      if (adminStatusFilter.value === 0) {
        const index = adminReservations.value.findIndex(item => item.id === row.id)
        if (index !== -1) adminReservations.value.splice(index, 1)
      } else {
        row.status = 2
      }
      fetchAdminReservations()
    }
  } catch (e) {}
}

const handleView = (row) => {
  currentReservation.value = row
  showDetailDialog.value = true
}

// 工具函数
const getStatusText = (status) => {
  const map = { 0: '待审批', 1: '已通过', 2: '已拒绝', 3: '已取消' }
  return map[status] || '未知'
}

const getStatusType = (status) => {
  const map = { 0: 'warning', 1: 'success', 2: 'danger', 3: 'info' }
  return map[status] || ''
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}

// 格式化时间段显示
const formatTimeslot = (slot) => {
  const start = slot.start_time.substring(0, 5) // 取 HH:mm
  const end = slot.end_time.substring(0, 5)
  return `${start} - ${end}`
}

// 检查时间段是否被选中
const isTimeslotSelected = (slot) => {
  if (!createForm.timeRange || createForm.timeRange.length < 2) return false
  
  const [startTime, endTime] = createForm.timeRange
  if (!startTime || !endTime) return false
  
  // 提取时间部分进行比较
  const startTimeOnly = startTime.split(' ')[1]?.substring(0, 5) // HH:mm
  const endTimeOnly = endTime.split(' ')[1]?.substring(0, 5)
  const slotStart = slot.start_time.substring(0, 5)
  const slotEnd = slot.end_time.substring(0, 5)
  
  return startTimeOnly === slotStart && endTimeOnly === slotEnd
}

// 选择时间段
const selectTimeslot = (slot) => {
  // 如果没有选择日期，尝试从时间范围中获取日期
  let targetDate = selectedDate.value
  
  if (!targetDate) {
    // 如果时间范围中已有日期，使用它
    if (createForm.timeRange && createForm.timeRange.length > 0 && createForm.timeRange[0]) {
      targetDate = createForm.timeRange[0].split(' ')[0]
    } else {
      // 否则使用今天
      const today = new Date()
      targetDate = today.toISOString().split('T')[0]
    }
    selectedDate.value = targetDate
    // 更新该日期的可用时间段
    if (createForm.equipment_id) {
      fetchAvailableTimeslots(createForm.equipment_id, targetDate)
    }
  }
  
  // 构建完整的日期时间
  const startDateTime = `${targetDate} ${slot.start_time}`
  const endDateTime = `${targetDate} ${slot.end_time}`
  
  createForm.timeRange = [startDateTime, endDateTime]
  ElMessage.success('已选择时间段')
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
  
  // 如果没有可用日期列表，允许选择（可能是还在加载中或没有配置时间段）
  return false
}

// 禁用过去的时间以及不可用的时间段
const disabledTime = (date) => {
  if (!date || !createForm.equipment_id) {
    return {}
  }
  
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const selectedDateObj = new Date(date)
  const selectedDateOnly = new Date(selectedDateObj.getFullYear(), selectedDateObj.getMonth(), selectedDateObj.getDate())
  const isToday = selectedDateOnly.getTime() === today.getTime()
  
  // 从传入的 date 参数中提取日期字符串
  const dateStr = selectedDateOnly.toISOString().split('T')[0]
  
  // 如果 selectedDate 与当前处理的日期不匹配，且 availableTimeslots 为空，只禁用过去的时间
  // 注意：这里我们假设如果 selectedDate 存在，availableTimeslots 已经是该日期的可用时间段
  if (!selectedDate.value || selectedDate.value !== dateStr) {
    // 如果还没有选择该日期，或者 availableTimeslots 不是该日期的，只禁用过去的时间
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
  
  // 如果 availableTimeslots 为空，只禁用过去的时间
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
      // 该小时完全不在任何可用时间段内，禁用
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
        // 该分钟不在任何可用时间段内，禁用
        disabledMinutesMap[hour].push(minute)
      } else if (isToday && hour === now.getHours() && minute <= now.getMinutes()) {
        // 如果是今天且是当前小时，禁用已过去的分钟
        disabledMinutesMap[hour].push(minute)
      }
      
      // 为每个分钟计算禁用的秒
      const key = `${hour}-${minute}`
      if (!hasAvailableTime || (isToday && hour === now.getHours() && minute < now.getMinutes())) {
        // 该分钟不可用，禁用所有秒
        disabledSecondsMap[key] = Array.from({ length: 60 }, (_, i) => i)
      } else if (isToday && hour === now.getHours() && minute === now.getMinutes()) {
        // 如果是当前分钟，禁用已过去的秒
        disabledSecondsMap[key] = []
        for (let second = 0; second <= now.getSeconds(); second++) {
          disabledSecondsMap[key].push(second)
        }
      } else {
        // 检查该秒是否在可用时间段内
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

onMounted(() => {
  fetchMyReservations()
})
</script>

<style scoped lang="scss">
.reservations-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .page-title {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: #333;
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

.table-card {
  border-radius: 8px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
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
