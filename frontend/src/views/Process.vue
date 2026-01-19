<template>
  <div class="process-page">
    <!-- 页面标题 -->
    <div class="page-header animate__animated animate__fadeInDown">
      <div class="header-icon float">
        <el-icon :size="48"><InfoFilled /></el-icon>
      </div>
      <div>
        <h2 class="page-title gradient-text">开放流程</h2>
        <p class="page-subtitle">设备预约使用流程指南</p>
      </div>
    </div>

    <!-- 流程步骤 -->
    <div class="process-content">
      <el-card class="process-card" shadow="never">
        <div class="process-steps">
          <div 
            class="process-step" 
            v-for="(step, index) in steps" 
            :key="index"
            :class="{ 'is-active': true }"
          >
            <div class="step-number">
              <span>{{ index + 1 }}</span>
            </div>
            <div class="step-content">
              <h3 class="step-title">
                <el-icon class="step-icon"><component :is="step.icon" /></el-icon>
                {{ step.title }}
              </h3>
              <p class="step-description">{{ step.description }}</p>
              <div class="step-details" v-if="step.details">
                <div class="detail-item" v-for="(detail, dIndex) in step.details" :key="dIndex">
                  <el-icon class="detail-icon"><CircleCheck /></el-icon>
                  <span>{{ detail }}</span>
                </div>
              </div>
            </div>
            <div class="step-arrow" v-if="index < steps.length - 1">
              <el-icon :size="24"><ArrowDown /></el-icon>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 注意事项 -->
      <el-card class="notice-card" shadow="hover">
        <template #header>
          <div class="notice-header">
            <el-icon><Warning /></el-icon>
            <span>注意事项</span>
          </div>
        </template>
        <ul class="notice-list">
          <li v-for="(notice, index) in notices" :key="index">{{ notice }}</li>
        </ul>
      </el-card>

      <!-- 常见问题 -->
      <el-card class="faq-card" shadow="hover">
        <template #header>
          <div class="faq-header">
            <el-icon><QuestionFilled /></el-icon>
            <span>常见问题</span>
          </div>
        </template>
        <el-collapse v-model="activeFaq">
          <el-collapse-item 
            v-for="(faq, index) in faqs" 
            :key="index"
            :title="faq.question"
            :name="index"
          >
            <div class="faq-answer">{{ faq.answer }}</div>
          </el-collapse-item>
        </el-collapse>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { 
  InfoFilled, User, Search, Calendar, Document, CircleCheck, 
  ArrowDown, Warning, QuestionFilled, Check
} from '@element-plus/icons-vue'

const steps = ref([
  {
    title: '注册登录',
    description: '使用学号/工号注册账号并完成登录',
    icon: User,
    details: [
      '学生使用学号注册',
      '教师使用工号注册',
      '首次登录需完善个人信息',
      '完成安全培训考核'
    ]
  },
  {
    title: '浏览设备',
    description: '在设备目录中查找所需设备',
    icon: Search,
    details: [
      '可按实验室、类别筛选设备',
      '查看设备详细信息和状态',
      '了解设备使用要求和费用',
      '查看设备可用时间段'
    ]
  },
  {
    title: '提交预约',
    description: '选择设备和时间段提交预约申请',
    icon: Calendar,
    details: [
      '选择设备并查看可用时间',
      '填写预约用途说明',
      '确认预约时间范围',
      '提交预约申请等待审批'
    ]
  },
  {
    title: '等待审批',
    description: '管理员审核预约申请',
    icon: Document,
    details: [
      '管理员会在1-2个工作日内审核',
      '可通过系统查看审批状态',
      '审批通过后收到通知',
      '如被拒绝可查看拒绝理由'
    ]
  },
  {
    title: '使用设备',
    description: '按预约时间到实验室使用设备',
    icon: Check,
    details: [
      '按时到达指定实验室',
      '向管理员出示预约凭证',
      '按照操作规程使用设备',
      '使用完毕后及时归还'
    ]
  },
  {
    title: '完成结算',
    description: '确认使用时间并完成费用结算',
    icon: CircleCheck,
    details: [
      '系统自动记录使用时间',
      '确认费用明细',
      '完成费用支付',
      '对使用体验进行评价'
    ]
  }
])

const notices = ref([
  '预约申请需至少提前3个工作日提交',
  '预约成功后请按时使用，迟到超过30分钟视为自动取消',
  '如需取消预约，请提前24小时在系统中操作',
  '使用设备前请仔细阅读设备使用说明和安全规范',
  '使用过程中如遇问题，请及时联系实验室管理员',
  '设备使用完毕后请及时清理并恢复原状',
  '违规使用设备将影响后续预约权限'
])

const faqs = ref([
  {
    question: '如何查看设备的可用时间段？',
    answer: '在设备详情页面可以查看该设备的所有可用时间段，系统会自动排除已被预约的时间段。您也可以选择特定日期查看该日期的可用时间段。'
  },
  {
    question: '预约被拒绝后可以重新申请吗？',
    answer: '可以的。如果预约被拒绝，您可以查看拒绝理由，修改预约信息后重新提交申请。建议在重新申请前先与管理员沟通了解具体情况。'
  },
  {
    question: '可以同时预约多台设备吗？',
    answer: '可以。只要时间段不冲突，您可以同时预约多台设备。但请注意合理安排时间，确保能够按时使用所有预约的设备。'
  },
  {
    question: '预约后可以修改时间吗？',
    answer: '预约提交后，在管理员审批前可以取消并重新提交。如果已经审批通过，需要先取消当前预约，然后重新提交新的预约申请。'
  },
  {
    question: '设备使用费用如何计算？',
    answer: '设备使用费用按照实际使用时间计算，具体收费标准可在设备详情页面查看。系统会在使用结束后自动计算费用，您可以在预约管理页面查看费用明细。'
  },
  {
    question: '如果设备出现故障怎么办？',
    answer: '如果使用过程中发现设备故障，请立即停止使用并通知实验室管理员。因设备故障导致无法正常使用的，可以申请全额退费或重新安排使用时间。'
  }
])

const activeFaq = ref([0])
</script>

<style scoped lang="scss">
.process-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  animation: slideInUp 0.6s ease-out;
}

/* 页面标题 */
.page-header {
  display: flex;
  align-items: center;
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
}

.process-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.process-card {
  border-radius: 12px;

  :deep(.el-card__body) {
    padding: 40px;
  }
}

.process-steps {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.process-step {
  display: flex;
  align-items: flex-start;
  gap: 24px;
  position: relative;

  &.is-active {
    .step-number {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
  }
}

.step-number {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: #666;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.step-content {
  flex: 1;
}

.step-title {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;

  .step-icon {
    color: #667eea;
    font-size: 24px;
  }
}

.step-description {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #666;
  line-height: 1.8;
}

.step-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;

  .detail-icon {
    color: #67C23A;
    font-size: 16px;
  }
}

.step-arrow {
  position: absolute;
  left: 24px;
  top: 64px;
  color: #ddd;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(10px);
  }
}

.notice-card,
.faq-card {
  border-radius: 12px;

  :deep(.el-card__header) {
    border-bottom: 2px solid rgba(102, 126, 234, 0.1);
    padding: 20px 24px;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  }

  :deep(.el-card__body) {
    padding: 24px;
  }
}

.notice-header,
.faq-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #333;

  .el-icon {
    color: #E6A23C;
    font-size: 20px;
  }
}

.notice-list {
  margin: 0;
  padding-left: 24px;
  list-style: none;

  li {
    position: relative;
    padding: 12px 0;
    padding-left: 24px;
    line-height: 1.8;
    color: #666;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);

    &:last-child {
      border-bottom: none;
    }

    &::before {
      content: '⚠';
      position: absolute;
      left: 0;
      color: #E6A23C;
      font-size: 16px;
    }

    &:hover {
      color: #333;
    }
  }
}

.faq-answer {
  padding: 16px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 8px;
  line-height: 1.8;
  color: #666;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    text-align: center;
  }

  .process-step {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .step-arrow {
    position: static;
    margin: 16px 0;
    transform: rotate(90deg);
  }
}
</style>
