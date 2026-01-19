<template>
  <div class="statistics-page">
    <!-- 页面标题 -->
    <div class="page-header animate__animated animate__fadeInDown">
      <div class="header-icon float">
        <el-icon :size="48"><DataAnalysis /></el-icon>
      </div>
      <div>
        <h2 class="page-title gradient-text">数据统计</h2>
        <p class="page-subtitle">系统运行数据概览与分析</p>
      </div>
      <el-button 
        type="primary" 
        :icon="Refresh" 
        circle 
        @click="fetchStatistics"
        :loading="loading"
        class="refresh-btn"
      />
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <!-- 设备统计 -->
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon equipment">
              <el-icon :size="32"><Box /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">设备总数</div>
              <div class="stat-value">{{ statistics.equipment?.total || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon available">
              <el-icon :size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">可用设备</div>
              <div class="stat-value">{{ statistics.equipment?.available || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon usage">
              <el-icon :size="32"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">使用率</div>
              <div class="stat-value">{{ statistics.equipment?.usage_rate || 0 }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon reservation">
              <el-icon :size="32"><Calendar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">总预约数</div>
              <div class="stat-value">{{ statistics.reservation?.total || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细统计区域 -->
    <el-row :gutter="20" class="detail-stats">
      <!-- 设备统计详情 -->
      <el-col :xs="24" :lg="12">
        <el-card class="detail-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><Box /></el-icon>
                设备统计
              </span>
            </div>
          </template>
          <div class="detail-content">
            <div class="stat-item">
              <span class="label">设备总数：</span>
              <span class="value">{{ statistics.equipment?.total || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">可用设备：</span>
              <span class="value success">{{ statistics.equipment?.available || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">不可用设备：</span>
              <span class="value danger">{{ statistics.equipment?.unavailable || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">使用率：</span>
              <span class="value">{{ statistics.equipment?.usage_rate || 0 }}%</span>
            </div>
            <div class="stat-item">
              <span class="label">有预约的设备：</span>
              <span class="value">{{ statistics.equipment?.equipment_with_reservations || 0 }}</span>
            </div>
          </div>
          <!-- 设备状态分布图表 -->
          <div class="chart-container">
            <v-chart 
              :option="equipmentStatusOption" 
              :loading="loading"
              style="height: 250px;"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 预约统计详情 -->
      <el-col :xs="24" :lg="12">
        <el-card class="detail-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><Calendar /></el-icon>
                预约统计
              </span>
            </div>
          </template>
          <div class="detail-content">
            <div class="stat-item">
              <span class="label">总预约数：</span>
              <span class="value">{{ statistics.reservation?.total || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">待审批：</span>
              <span class="value warning">{{ statistics.reservation?.pending || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">已通过：</span>
              <span class="value success">{{ statistics.reservation?.approved || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">已拒绝：</span>
              <span class="value danger">{{ statistics.reservation?.rejected || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">已取消：</span>
              <span class="value info">{{ statistics.reservation?.cancelled || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">通过率：</span>
              <span class="value">{{ statistics.reservation?.approval_rate || 0 }}%</span>
            </div>
            <div class="stat-item">
              <span class="label">拒绝率：</span>
              <span class="value">{{ statistics.reservation?.rejection_rate || 0 }}%</span>
            </div>
          </div>
          <!-- 预约状态分布图表 -->
          <div class="chart-container">
            <v-chart 
              :option="reservationStatusOption" 
              :loading="loading"
              style="height: 250px;"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 用户统计和趋势图 -->
    <el-row :gutter="20" class="detail-stats">
      <!-- 用户统计 -->
      <el-col :xs="24" :lg="8">
        <el-card class="detail-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><User /></el-icon>
                用户统计
              </span>
            </div>
          </template>
          <div class="detail-content">
            <div class="stat-item">
              <span class="label">总用户数：</span>
              <span class="value">{{ statistics.user?.total || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">学生：</span>
              <span class="value">{{ statistics.user?.students || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">教师：</span>
              <span class="value">{{ statistics.user?.teachers || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">管理员：</span>
              <span class="value">{{ statistics.user?.admins || 0 }}</span>
            </div>
          </div>
          <!-- 用户分布图表 -->
          <div class="chart-container">
            <v-chart 
              :option="userDistributionOption" 
              :loading="loading"
              style="height: 250px;"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 预约趋势图 -->
      <el-col :xs="24" :lg="16">
        <el-card class="detail-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><TrendCharts /></el-icon>
                预约趋势（最近30天）
              </span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart 
              :option="reservationTrendOption" 
              :loading="loading"
              style="height: 300px;"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  DataAnalysis, Box, CircleCheck, TrendCharts, Calendar, User, Refresh
} from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { getStatistics } from '@/api/statistics'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  PieChart,
  BarChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const router = useRouter()
const loading = ref(false)
const statistics = reactive({
  equipment: {},
  reservation: {},
  user: {}
})

// 设备状态分布图表配置
const equipmentStatusOption = computed(() => {
  const data = statistics.equipment?.status_distribution || {}
  const chartData = Object.entries(data).map(([status, count]) => ({
    value: count,
    name: getStatusName(status)
  }))
  
  // 如果没有数据，显示空状态
  if (chartData.length === 0) {
    chartData.push({ value: 0, name: '暂无数据' })
  }
  
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        name: '设备状态',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: chartData
      }
    ]
  }
})

// 预约状态分布图表配置
const reservationStatusOption = computed(() => {
  const data = {
    '待审批': statistics.reservation?.pending || 0,
    '已通过': statistics.reservation?.approved || 0,
    '已拒绝': statistics.reservation?.rejected || 0,
    '已取消': statistics.reservation?.cancelled || 0
  }
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        name: '预约状态',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: [
          { value: data['待审批'], name: '待审批', itemStyle: { color: '#E6A23C' } },
          { value: data['已通过'], name: '已通过', itemStyle: { color: '#67C23A' } },
          { value: data['已拒绝'], name: '已拒绝', itemStyle: { color: '#F56C6C' } },
          { value: data['已取消'], name: '已取消', itemStyle: { color: '#909399' } }
        ]
      }
    ]
  }
})

// 用户分布图表配置
const userDistributionOption = computed(() => {
  const data = {
    '学生': statistics.user?.students || 0,
    '教师': statistics.user?.teachers || 0,
    '管理员': statistics.user?.admins || 0
  }
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        name: '用户分布',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: [
          { value: data['学生'], name: '学生', itemStyle: { color: '#409EFF' } },
          { value: data['教师'], name: '教师', itemStyle: { color: '#67C23A' } },
          { value: data['管理员'], name: '管理员', itemStyle: { color: '#E6A23C' } }
        ]
      }
    ]
  }
})

// 预约趋势图配置
const reservationTrendOption = computed(() => {
  const trendData = statistics.reservation?.daily_trend || []
  const dates = trendData.map(item => item.date)
  const counts = trendData.map(item => item.count)
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['预约数量']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '预约数量',
        type: 'line',
        smooth: true,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
            ]
          }
        },
        itemStyle: {
          color: '#409EFF'
        },
        data: counts
      }
    ]
  }
})

// 获取状态名称
const getStatusName = (status) => {
  const statusMap = {
    '0': '待审批',
    '1': '正常/可用',
    '2': '已拒绝',
    '3': '已取消'
  }
  return statusMap[status] || `状态${status}`
}

// 获取统计数据
const fetchStatistics = async () => {
  loading.value = true
  try {
    const res = await getStatistics()
    if (res.code === 200) {
      Object.assign(statistics, res.data)
      ElMessage.success('数据刷新成功')
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStatistics()
})
</script>

<style scoped lang="scss">
.statistics-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  animation: slideInUp 0.6s ease-out;
}

/* 页面标题 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
  padding: 24px 32px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);

  .header-icon {
    width: 80px;
    height: 80px;
    border-radius: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  }

  .page-title {
    margin: 0 0 8px 0;
    font-size: 28px;
    font-weight: 700;
  }

  .page-subtitle {
    margin: 0;
    color: #666;
    font-size: 14px;
  }

  .refresh-btn {
    margin-left: auto;
  }
}

/* 统计卡片 */
.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  margin-bottom: 20px;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;

  &.equipment {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  &.available {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }

  &.usage {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  }

  &.reservation {
    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  }
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #333;
}

/* 详细统计卡片 */
.detail-stats {
  margin-bottom: 20px;
}

.detail-card {
  border-radius: 12px;
  margin-bottom: 20px;

  :deep(.el-card__header) {
    border-bottom: 2px solid rgba(102, 126, 234, 0.1);
    padding: 20px 24px;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  }

  :deep(.el-card__body) {
    padding: 24px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .card-title {
    font-size: 18px;
    font-weight: 600;
    color: #333;
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.detail-content {
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);

  &:last-child {
    border-bottom: none;
  }

  .label {
    font-size: 14px;
    color: #666;
  }

  .value {
    font-size: 16px;
    font-weight: 600;
    color: #333;

    &.success {
      color: #67C23A;
    }

    &.danger {
      color: #F56C6C;
    }

    &.warning {
      color: #E6A23C;
    }

    &.info {
      color: #909399;
    }
  }
}

.chart-container {
  margin-top: 20px;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    text-align: center;
  }

  .stat-content {
    flex-direction: column;
    text-align: center;
  }
}
</style>
