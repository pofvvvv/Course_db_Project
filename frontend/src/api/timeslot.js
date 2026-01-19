import request from './request'

/**
 * 时间段 API
 */

/**
 * 获取设备的可用时间段
 * @param {number} equipId - 设备ID
 * @param {string} date - 目标日期（可选，格式：YYYY-MM-DD）
 */
export function getAvailableTimeslots(equipId, date = null) {
  const params = {}
  if (date) {
    params.date = date
  }
  return request({
    url: `/timeslots/equipment/${equipId}/available`,
    method: 'get',
    params
  })
}

/**
 * 获取设备的时间段列表
 * @param {number} equipId - 设备ID
 * @param {boolean} onlyActive - 是否仅返回激活的时间段
 */
export function getTimeslots(equipId, onlyActive = false) {
  const params = {}
  if (onlyActive) {
    params.only_active = true
  }
  return request({
    url: `/timeslots/equipment/${equipId}`,
    method: 'get',
    params
  })
}

/**
 * 获取设备的可用日期列表
 * @param {number} equipId - 设备ID
 * @param {string} startDate - 开始日期（可选，格式：YYYY-MM-DD），默认为今天
 * @param {number} days - 查询天数（可选，默认30天）
 */
export function getAvailableDates(equipId, startDate = null, days = 30) {
  const params = { days }
  if (startDate) {
    params.start_date = startDate
  }
  return request({
    url: `/timeslots/equipment/${equipId}/available-dates`,
    method: 'get',
    params
  })
}
