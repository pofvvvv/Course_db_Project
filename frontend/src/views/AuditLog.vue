<template>
  <div class="auditlog-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon><Document /></el-icon>
        审计日志
      </h2>
      <el-button :icon="Refresh" circle @click="fetchAuditLogs" />
    </div>

    <!-- 筛选区域 -->
    <el-card class="filter-card" shadow="hover">
      <el-form :model="filterForm" inline>
        <el-form-item label="操作人ID">
          <el-input
            v-model="filterForm.operator_id"
            placeholder="请输入操作人ID"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select 
            v-model="filterForm.action_type" 
            placeholder="请选择操作类型" 
            clearable
            style="width: 200px"
          >
            <el-option label="创建设备" value="create_equipment" />
            <el-option label="更新设备" value="update_equipment" />
            <el-option label="删除设备" value="delete_equipment" />
            <el-option label="创建时间段" value="create_timeslot" />
            <el-option label="更新时间段" value="update_timeslot" />
            <el-option label="删除时间段" value="delete_timeslot" />
            <el-option label="审批通过预约" value="approve_reservation" />
            <el-option label="审批拒绝预约" value="reject_reservation" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filterForm.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 400px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志列表 -->
    <el-card class="list-card" shadow="hover">
      <el-empty v-if="!loading && auditLogList.length === 0" description="暂无审计日志" />
      <el-skeleton v-else-if="loading" :rows="10" animated />
      <el-table v-else :data="auditLogList" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="日志ID" width="100" />
        <el-table-column prop="operator_id" label="操作人ID" width="120" />
        <el-table-column prop="action_type" label="操作类型" width="180">
          <template #default="{ row }">
            <el-tag>{{ getActionTypeText(row.action_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action_time" label="操作时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.action_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="150" />
        <el-table-column prop="detail" label="操作详情" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.detail">{{ formatDetail(row.detail) }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="审计日志详情"
      width="600px"
    >
      <el-descriptions :column="1" border v-if="currentLog">
        <el-descriptions-item label="日志ID">{{ currentLog.id }}</el-descriptions-item>
        <el-descriptions-item label="操作人ID">{{ currentLog.operator_id }}</el-descriptions-item>
        <el-descriptions-item label="操作类型">
          <el-tag>{{ getActionTypeText(currentLog.action_type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="操作时间">{{ formatDateTime(currentLog.action_time) }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog.ip_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="操作详情">
          <pre v-if="currentLog.detail" class="detail-pre">{{ formatDetail(currentLog.detail) }}</pre>
          <span v-else class="text-gray">-</span>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Refresh, Search } from '@element-plus/icons-vue'
import { getAuditLogList, getAuditLogById } from '@/api/auditlog'

// 数据
const auditLogList = ref([])
const loading = ref(false)
const total = ref(0)

// 筛选表单
const filterForm = reactive({
  operator_id: '',
  action_type: '',
  timeRange: null
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20
})

// 详情对话框
const showDetailDialog = ref(false)
const currentLog = ref(null)

// 操作类型映射
const actionTypeMap = {
  'create_equipment': '创建设备',
  'update_equipment': '更新设备',
  'delete_equipment': '删除设备',
  'create_timeslot': '创建时间段',
  'update_timeslot': '更新时间段',
  'delete_timeslot': '删除时间段',
  'approve_reservation': '审批通过预约',
  'reject_reservation': '审批拒绝预约'
}

// 获取操作类型文本
const getActionTypeText = (actionType) => {
  return actionTypeMap[actionType] || actionType
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化详情
const formatDetail = (detail) => {
  if (!detail) return '-'
  try {
    const parsed = JSON.parse(detail)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return detail
  }
}

// 获取审计日志列表
const fetchAuditLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      operator_id: filterForm.operator_id || undefined,
      action_type: filterForm.action_type || undefined
    }

    // 处理时间范围
    if (filterForm.timeRange && filterForm.timeRange.length === 2) {
      params.start_time = filterForm.timeRange[0]
      params.end_time = filterForm.timeRange[1]
    }

    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === '') {
        delete params[key]
      }
    })

    const response = await getAuditLogList(params)
    if (response.code === 200) {
      auditLogList.value = response.data.items || []
      total.value = response.data.total || 0
    }
  } catch (error) {
    console.error('获取审计日志列表失败:', error)
    ElMessage.error('获取审计日志列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchAuditLogs()
}

// 重置
const handleReset = () => {
  filterForm.operator_id = ''
  filterForm.action_type = ''
  filterForm.timeRange = null
  handleSearch()
}

// 查看详情
const handleViewDetail = async (row) => {
  try {
    const response = await getAuditLogById(row.id)
    if (response.code === 200) {
      currentLog.value = response.data
      showDetailDialog.value = true
    }
  } catch (error) {
    console.error('获取审计日志详情失败:', error)
    ElMessage.error('获取审计日志详情失败')
  }
}

// 分页变化
const handleSizeChange = () => {
  fetchAuditLogs()
}

const handlePageChange = () => {
  fetchAuditLogs()
}

// 初始化
onMounted(() => {
  fetchAuditLogs()
})
</script>

<style scoped lang="scss">
.auditlog-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .page-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: #333;
  }
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.list-card {
  border-radius: 8px;
}

.pagination {
  margin-top: 20px;
  justify-content: center;
}

.text-gray {
  color: #999;
}

.detail-pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
