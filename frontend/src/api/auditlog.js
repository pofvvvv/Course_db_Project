import request from './request'

/**
 * 审计日志 API
 */

/**
 * 获取审计日志列表
 * @param {object} params - 查询参数
 * @param {string} params.operator_id - 操作人ID（可选）
 * @param {string} params.action_type - 操作类型（可选）
 * @param {string} params.start_time - 开始时间（可选）
 * @param {string} params.end_time - 结束时间（可选）
 * @param {number} params.page - 页码（可选，默认1）
 * @param {number} params.per_page - 每页数量（可选，默认20）
 */
export function getAuditLogList(params = {}) {
  return request({
    url: '/auditlogs/',
    method: 'get',
    params
  })
}

/**
 * 获取审计日志详情
 * @param {number} id - 日志ID
 */
export function getAuditLogById(id) {
  return request({
    url: `/auditlogs/${id}`,
    method: 'get'
  })
}

/**
 * 获取操作类型列表
 */
export function getActionTypes() {
  return request({
    url: '/auditlogs/action-types',
    method: 'get'
  })
}

/**
 * 获取审计日志统计信息
 */
export function getAuditStatistics() {
  return request({
    url: '/auditlogs/statistics',
    method: 'get'
  })
}

/**
 * 操作类型常量
 */
export const ACTION_TYPES = {
  LOGIN: 'LOGIN',
  LOGOUT: 'LOGOUT',
  LOGIN_FAILED: 'LOGIN_FAILED',
  
  // 设备相关
  CREATE_EQUIPMENT: 'CREATE_EQUIPMENT',
  UPDATE_EQUIPMENT: 'UPDATE_EQUIPMENT',
  DELETE_EQUIPMENT: 'DELETE_EQUIPMENT',
  
  // 实验室相关
  CREATE_LAB: 'CREATE_LAB',
  UPDATE_LAB: 'UPDATE_LAB',
  DELETE_LAB: 'DELETE_LAB',
  
  // 预约相关
  CREATE_RESERVATION: 'CREATE_RESERVATION',
  APPROVE_RESERVATION: 'APPROVE_RESERVATION',
  REJECT_RESERVATION: 'REJECT_RESERVATION',
  CANCEL_RESERVATION: 'CANCEL_RESERVATION',
  
  // 时间段相关
  CREATE_TIMESLOT: 'CREATE_TIMESLOT',
  UPDATE_TIMESLOT: 'UPDATE_TIMESLOT',
  DELETE_TIMESLOT: 'DELETE_TIMESLOT',
  
  // 用户相关
  CREATE_USER: 'CREATE_USER',
  UPDATE_USER: 'UPDATE_USER',
  DELETE_USER: 'DELETE_USER'
}

/**
 * 操作类型中文映射
 */
export const ACTION_TYPE_LABELS = {
  LOGIN: '登录',
  LOGOUT: '登出',
  LOGIN_FAILED: '登录失败',
  
  CREATE_EQUIPMENT: '创建设备',
  UPDATE_EQUIPMENT: '更新设备',
  DELETE_EQUIPMENT: '删除设备',
  
  CREATE_LAB: '创建实验室',
  UPDATE_LAB: '更新实验室',
  DELETE_LAB: '删除实验室',
  
  CREATE_RESERVATION: '创建预约',
  APPROVE_RESERVATION: '审批通过预约',
  REJECT_RESERVATION: '拒绝预约',
  CANCEL_RESERVATION: '取消预约',
  
  CREATE_TIMESLOT: '创建时间段',
  UPDATE_TIMESLOT: '更新时间段',
  DELETE_TIMESLOT: '删除时间段',
  
  CREATE_USER: '创建用户',
  UPDATE_USER: '更新用户',
  DELETE_USER: '删除用户'
}
