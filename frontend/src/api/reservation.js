import request from './request'

/**
 * 预约 API
 */

/**
 * 创建预约
 * @param {object} data - 预约数据
 */
export function createReservation(data) {
  return request({
    url: '/reservations/',
    method: 'post',
    data
  })
}

/**
 * 获取预约列表
 * @param {object} params - 查询参数 (page, page_size, status, equipment_id, etc.)
 */
export function getReservationList(params = {}) {
  return request({
    url: '/reservations/',
    method: 'get',
    params
  })
}

/**
 * 获取预约详情
 * @param {number} id - 预约ID
 */
export function getReservationById(id) {
  return request({
    url: `/reservations/${id}`,
    method: 'get'
  })
}

/**
 * 取消预约
 * @param {number} id - 预约ID
 */
export function cancelReservation(id) {
  return request({
    url: `/reservations/${id}/cancel`,
    method: 'put'
  })
}

/**
 * 审批通过（管理员）
 * @param {number} id - 预约ID
 * @param {object} data - 审批数据 (可选)
 */
export function approveReservation(id, data = {}) {
  return request({
    url: `/admin/reservations/${id}/approve`,
    method: 'put',
    data
  })
}

/**
 * 审批拒绝（管理员）
 * @param {number} id - 预约ID
 * @param {object} data - 审批数据 (包含拒绝理由)
 */
export function rejectReservation(id, data = {}) {
  return request({
    url: `/admin/reservations/${id}/reject`,
    method: 'put',
    data
  })
}