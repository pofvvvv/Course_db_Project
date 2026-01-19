import request from './request'

/**
 * 审计日志 API
 */

/**
 * 获取审计日志列表
 * @param {object} params - 查询参数
 * @param {string} params.operator_id - 操作人ID（可选）
 * @param {string} params.action_type - 操作类型（可选）
 * @param {string} params.start_time - 开始时间（ISO格式，可选）
 * @param {string} params.end_time - 结束时间（ISO格式，可选）
 * @param {number} params.page - 页码（可选）
 * @param {number} params.page_size - 每页数量（可选）
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
