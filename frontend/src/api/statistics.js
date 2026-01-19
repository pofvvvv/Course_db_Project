import request from './request'

/**
 * 统计 API
 */

/**
 * 获取统计数据
 */
export function getStatistics() {
  return request({
    url: '/admin/statistics',
    method: 'get'
  })
}
