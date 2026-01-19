<template>
  <div class="audit-log-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon><Document /></el-icon>
        审计日志
      </h2>
      <div class="header-actions">
        <el-button type="info" @click="showStatsDialog = true">
          <el-icon><PieChart /></el-icon>
          统计信息
        </el-button>
        <el-button type="primary" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选区域 -->
    <el-card class="filter-card" shadow="hover">
      <el-form :model="filterForm" inline>
        <el-form-item label="操作人ID">
          <el-input
            v-model="filterForm.operator_id"
            placeholder="请输入操作人ID"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select 
            v-model="filterForm.action_type" 
            placeholder="请选择操作类型" 
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="type in actionTypes"
              :key="type"
              :label="getActionTypeLabel(type)"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 360px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志列表 -->
    <el-card class="table-card" shadow="hover">
      <div class="table-header">
        <div class="table-info">
          <span>共 {{ total }} 条记录</span>
        </div>
      </div>
      
      <el-table 
        :data="auditLogs" 
        v-loading="loading"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="id" label="日志ID" width="80" />
        <el-table-column prop="operator_id" label="操作人ID" width="120" />
        <el-table-column prop="action_type" label="操作类型" width="140">
          <template #default="scope">
            <el-tag :type="getActionTypeColor(scope.row.action_type)">
              {{ getActionTypeLabel(scope.row.action_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="操作详情" min-width="200">
          <template #default="scope">
            <span :title="scope.row.detail">
              {{ scope.row.detail || '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="130" />
        <el-table-column prop="action_time" label="操作时间" width="160">
          <template #default="scope">
            {{ formatTime(scope.row.action_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="handleViewDetail(scope.row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="审计日志详情"
      width="600px"
    >
      <div v-if="currentLog" class="log-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="日志ID">
            {{ currentLog.id }}
          </el-descriptions-item>
          <el-descriptions-item label="操作人ID">
            {{ currentLog.operator_id }}
          </el-descriptions-item>
          <el-descriptions-item label="操作类型">
            <el-tag :type="getActionTypeColor(currentLog.action_type)">
              {{ getActionTypeLabel(currentLog.action_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作详情">
            {{ currentLog.detail || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ currentLog.ip_address || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="操作时间">
            {{ formatTime(currentLog.action_time) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 统计信息对话框 -->
    <el-dialog
      v-model="showStatsDialog"
      title="审计日志统计"
      width="800px"
    >
      <div v-if="statistics" class="stats-content">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>基础统计</span>
              </template>
              <el-statistic title="总日志数" :value="statistics.total_logs" />
              <el-divider />
              <el-statistic title="今日日志数" :value="statistics.today_logs" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>操作类型统计</span>
              </template>
              <div class="action-stats">
                <div 
                  v-for="item in statistics.action_stats" 
                  :key="item.action_type"
                  class="stat-item"
                >
                  <span class="stat-label">{{ getActionTypeLabel(item.action_type) }}:</span>
                  <span class="stat-value">{{ item.count }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="24">
            <el-card shadow="hover">
              <template #header>
                <span>活跃操作人统计（TOP 10）</span>
              </template>
              <div class="operator-stats">
                <div 
                  v-for="item in statistics.operator_stats" 
                  :key="item.operator_id"
                  class="stat-item"
                >
                  <span class="stat-label">{{ item.operator_id }}:</span>
                  <span class="stat-value">{{ item.count }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      <template #footer>
        <el-button @click="showStatsDialog = false">关闭</el-button>
        <el-button type="primary" @click="loadStatistics">刷新统计</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, PieChart, Refresh, Search, RefreshLeft } from '@element-plus/icons-vue'
import { getAuditLogList, getAuditLogById, getActionTypes, getAuditStatistics, ACTION_TYPE_LABELS } from '@/api/auditlog'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 响应式数据
const auditLogs = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const actionTypes = ref([])
const timeRange = ref([])
const statistics = ref(null)

// 对话框状态
const showDetailDialog = ref(false)
const showStatsDialog = ref(false)
const currentLog = ref(null)

// 筛选表单
const filterForm = reactive({
  operator_id: '',
  action_type: ''
})

// 加载数据
const loadAuditLogs = async () => {
  try {
    loading.value = true
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      ...filterForm
    }
    
    // 处理时间范围
    if (timeRange.value && timeRange.value.length === 2) {
      params.start_time = timeRange.value[0]
      params.end_time = timeRange.value[1]
    }
    
    const response = await getAuditLogList(params)
    if (response.code === 200) {
      auditLogs.value = response.data.logs
      total.value = response.data.total
    } else {
      ElMessage.error(response.msg || '获取审计日志失败')
    }
  } catch (error) {
    console.error('加载审计日志失败:', error)
    ElMessage.error('网络错误，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 加载操作类型
const loadActionTypes = async () => {
  try {
    const response = await getActionTypes()
    if (response.code === 200) {
      actionTypes.value = response.data
    }
  } catch (error) {
    console.error('加载操作类型失败:', error)
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const response = await getAuditStatistics()
    if (response.code === 200) {
      statistics.value = response.data
    } else {
      ElMessage.error(response.msg || '获取统计信息失败')
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
    ElMessage.error('网络错误，请稍后重试')
  }
}

// 处理函数
const handleSearch = () => {
  currentPage.value = 1
  loadAuditLogs()
}

const handleReset = () => {
  filterForm.operator_id = ''
  filterForm.action_type = ''
  timeRange.value = []
  handleSearch()
}

const handleRefresh = () => {
  loadAuditLogs()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadAuditLogs()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadAuditLogs()
}

const handleViewDetail = async (row) => {
  try {
    const response = await getAuditLogById(row.id)
    if (response.code === 200) {
      currentLog.value = response.data
      showDetailDialog.value = true
    } else {
      ElMessage.error(response.msg || '获取日志详情失败')
    }
  } catch (error) {
    console.error('获取日志详情失败:', error)
    ElMessage.error('网络错误，请稍后重试')
  }
}

// 工具函数
const getActionTypeLabel = (type) => {
  return ACTION_TYPE_LABELS[type] || type
}

const getActionTypeColor = (type) => {
  const colorMap = {
    LOGIN: 'success',
    LOGOUT: 'info',
    LOGIN_FAILED: 'danger',
    CREATE_EQUIPMENT: 'success',
    UPDATE_EQUIPMENT: 'warning',
    DELETE_EQUIPMENT: 'danger',
    CREATE_LAB: 'success',
    UPDATE_LAB: 'warning',
    DELETE_LAB: 'danger',
    CREATE_RESERVATION: 'success',
    APPROVE_RESERVATION: 'success',
    REJECT_RESERVATION: 'warning',
    CANCEL_RESERVATION: 'info',
    CREATE_TIMESLOT: 'success',
    UPDATE_TIMESLOT: 'warning',
    DELETE_TIMESLOT: 'danger',
    CREATE_USER: 'success',
    UPDATE_USER: 'warning',
    DELETE_USER: 'danger'
  }
  return colorMap[type] || 'info'
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 监听统计对话框打开
watch(showStatsDialog, (newVal) => {
  if (newVal && !statistics.value) {
    loadStatistics()
  }
})

// 页面加载时初始化
onMounted(() => {
  if (!userStore.isAdmin) {
    ElMessage.error('权限不足，仅管理员可访问')
    return
  }
  
  loadActionTypes()
  loadAuditLogs()
})
</script>

<style scoped>
.audit-log-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.table-info {
  color: #606266;
  font-size: 14px;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.log-detail {
  padding: 10px 0;
}

.stats-content {
  padding: 10px 0;
}

.action-stats,
.operator-stats {
  max-height: 200px;
  overflow-y: auto;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.stat-value {
  font-weight: bold;
  color: #409eff;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
}

:deep(.el-card__header) {
  background-color: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
}
</style>
