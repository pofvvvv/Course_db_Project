<template>
  <div class="rules-page">
    <!-- 页面标题 -->
    <div class="page-header animate__animated animate__fadeInDown">
      <div class="header-icon float">
        <el-icon :size="48"><Document /></el-icon>
      </div>
      <div>
        <h2 class="page-title gradient-text">规章制度</h2>
        <p class="page-subtitle">设备使用相关规定与制度</p>
      </div>
    </div>

    <!-- 规章制度内容 -->
    <div class="rules-content">
      <el-card class="rule-card" shadow="hover" v-for="(rule, index) in rules" :key="index">
        <template #header>
          <div class="rule-header">
            <el-icon class="rule-icon"><component :is="rule.icon" /></el-icon>
            <h3 class="rule-title">{{ rule.title }}</h3>
          </div>
        </template>
        <div class="rule-body">
          <div class="rule-section" v-for="(section, sIndex) in rule.sections" :key="sIndex">
            <h4 class="section-title">{{ section.title }}</h4>
            <ul class="section-list">
              <li v-for="(item, iIndex) in section.items" :key="iIndex">{{ item }}</li>
            </ul>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Document, Warning, CircleCheck, InfoFilled } from '@element-plus/icons-vue'

const rules = ref([
  {
    title: '设备使用基本规定',
    icon: Document,
    sections: [
      {
        title: '使用资格',
        items: [
          '本校师生均可申请使用共享设备',
          '学生需经导师同意后方可预约',
          '校外人员需经实验室主任审批',
          '使用前需完成安全培训并通过考核'
        ]
      },
      {
        title: '预约要求',
        items: [
          '至少提前3个工作日提交预约申请',
          '预约时间不得超过连续7天',
          '同一设备同一时间段只能被一人预约',
          '取消预约需提前24小时通知'
        ]
      },
      {
        title: '使用规范',
        items: [
          '严格按照设备操作规程使用',
          '不得擅自拆卸、改装设备',
          '使用过程中发现问题及时报告',
          '使用完毕后及时清理并恢复原状'
        ]
      }
    ]
  },
  {
    title: '安全管理制度',
    icon: Warning,
    sections: [
      {
        title: '安全责任',
        items: [
          '使用者对设备安全负直接责任',
          '使用前检查设备状态是否正常',
          '发现安全隐患立即停止使用并报告',
          '因违规操作造成损失需承担相应责任'
        ]
      },
      {
        title: '应急处理',
        items: [
          '发生事故立即切断电源',
          '及时通知实验室管理员',
          '保护现场，不得擅自处理',
          '配合事故调查和处理'
        ]
      },
      {
        title: '防护措施',
        items: [
          '使用危险设备需佩戴防护用品',
          '遵守实验室安全标识要求',
          '禁止在实验室内饮食',
          '保持实验环境整洁有序'
        ]
      }
    ]
  },
  {
    title: '费用管理规定',
    icon: CircleCheck,
    sections: [
      {
        title: '收费标准',
        items: [
          '校内师生使用按成本价收费',
          '校外人员按市场价收费',
          '科研项目可申请优惠价格',
          '具体收费标准见设备详情页'
        ]
      },
      {
        title: '缴费方式',
        items: [
          '预约时需缴纳押金',
          '使用结束后按实际使用时间结算',
          '支持校内转账和在线支付',
          '发票可在系统内申请开具'
        ]
      },
      {
        title: '退费政策',
        items: [
          '因设备故障无法使用可全额退费',
          '提前取消预约可退还部分费用',
          '违规使用造成的损失从押金中扣除',
          '退费申请需在7个工作日内处理'
        ]
      }
    ]
  },
  {
    title: '违规处理办法',
    icon: InfoFilled,
    sections: [
      {
        title: '违规行为',
        items: [
          '未经授权擅自使用设备',
          '超时使用或未按时归还',
          '损坏设备未及时报告',
          '违反安全操作规程'
        ]
      },
      {
        title: '处理措施',
        items: [
          '首次违规给予警告并记录',
          '严重违规暂停使用权限3-6个月',
          '造成损失需照价赔偿',
          '情节严重者移交学校处理'
        ]
      },
      {
        title: '申诉渠道',
        items: [
          '对处理结果有异议可申请申诉',
          '申诉需在收到通知后7日内提交',
          '申诉材料需详细说明情况',
          '实验室将在15个工作日内给予答复'
        ]
      }
    ]
  }
])
</script>

<style scoped lang="scss">
.rules-page {
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

.rules-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.rule-card {
  border-radius: 12px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }

  :deep(.el-card__header) {
    border-bottom: 2px solid rgba(102, 126, 234, 0.1);
    padding: 20px 24px;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  }

  :deep(.el-card__body) {
    padding: 24px;
  }
}

.rule-header {
  display: flex;
  align-items: center;
  gap: 12px;

  .rule-icon {
    font-size: 24px;
    color: #667eea;
  }

  .rule-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #333;
  }
}

.rule-body {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.rule-section {
  .section-title {
    margin: 0 0 12px 0;
    font-size: 16px;
    font-weight: 600;
    color: #667eea;
    padding-bottom: 8px;
    border-bottom: 2px solid rgba(102, 126, 234, 0.2);
  }

  .section-list {
    margin: 0;
    padding-left: 24px;
    list-style: none;

    li {
      position: relative;
      padding: 8px 0;
      padding-left: 24px;
      line-height: 1.8;
      color: #666;

      &::before {
        content: '•';
        position: absolute;
        left: 0;
        color: #667eea;
        font-weight: bold;
        font-size: 18px;
      }

      &:hover {
        color: #333;
      }
    }
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    text-align: center;
  }
}
</style>
