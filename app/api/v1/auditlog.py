"""
审计日志 API 路由
实现审计日志的查询功能（仅管理员可访问）
"""
from flask import Blueprint, request
from flasgger import swag_from
from app.services import auditlog_service
from app.api.v1.schemas.auditlog_schema import AuditLogSchema, AuditLogQuerySchema, AuditLogStatsSchema
from app.utils.response import success, fail
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.auth import admin_required
from app.utils.redis_client import redis_client

# 创建蓝图
auditlog_bp = Blueprint('auditlog', __name__)

# 实例化 Schema
auditlog_schema = AuditLogSchema()
auditlog_query_schema = AuditLogQuerySchema()
auditlog_stats_schema = AuditLogStatsSchema()


@auditlog_bp.route('/', methods=['GET'])
@auditlog_bp.route('', methods=['GET'])
@admin_required
@swag_from({
    'tags': ['审计日志管理'],
    'summary': '获取审计日志列表',
    'description': '获取审计日志列表，支持多种筛选条件和分页（仅管理员可访问）',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'in': 'query',
            'name': 'operator_id',
            'type': 'string',
            'required': False,
            'description': '操作人ID筛选'
        },
        {
            'in': 'query',
            'name': 'action_type',
            'type': 'string',
            'required': False,
            'description': '操作类型筛选'
        },
        {
            'in': 'query',
            'name': 'start_time',
            'type': 'string',
            'format': 'date-time',
            'required': False,
            'description': '开始时间筛选（ISO格式）'
        },
        {
            'in': 'query',
            'name': 'end_time',
            'type': 'string',
            'format': 'date-time',
            'required': False,
            'description': '结束时间筛选（ISO格式）'
        },
        {
            'in': 'query',
            'name': 'page',
            'type': 'integer',
            'required': False,
            'default': 1,
            'description': '页码'
        },
        {
            'in': 'query',
            'name': 'per_page',
            'type': 'integer',
            'required': False,
            'default': 20,
            'description': '每页数量'
        }
    ],
    'responses': {
        200: {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': '获取成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'logs': {
                                'type': 'array',
                                'items': {'$ref': '#/definitions/AuditLog'}
                            },
                            'total': {'type': 'integer'},
                            'page': {'type': 'integer'},
                            'per_page': {'type': 'integer'},
                            'pages': {'type': 'integer'},
                            'has_next': {'type': 'boolean'},
                            'has_prev': {'type': 'boolean'}
                        }
                    }
                }
            }
        },
        401: {
            'description': '未授权访问',
            'schema': {'$ref': '#/definitions/Error'}
        },
        403: {
            'description': '权限不足',
            'schema': {'$ref': '#/definitions/Error'}
        }
    }
})
def get_audit_logs():
    """获取审计日志列表"""
    try:
        # 验证查询参数
        args = auditlog_query_schema.load(request.args)
        
        # 检查 Redis 缓存
        cache_key = f"audit_logs:{hash(str(sorted(args.items())))}"
        cached_result = redis_client.get_json(cache_key)
        if cached_result:
            return success(data=cached_result, msg='获取成功（缓存）')
        
        # 查询审计日志
        result = auditlog_service.get_audit_log_list(**args)
        
        # 序列化数据
        serialized_logs = auditlog_schema.dump(result['logs'], many=True)
        result['logs'] = serialized_logs
        
        # 缓存结果（5分钟）
        redis_client.set_json(cache_key, result, expire=300)
        
        return success(data=result, msg='获取成功')
        
    except ValidationError as e:
        return fail(code=400, msg=f'参数验证失败: {e.message}')
    except Exception as e:
        return fail(code=500, msg=f'服务器内部错误: {str(e)}')


@auditlog_bp.route('/<int:log_id>', methods=['GET'])
@admin_required
@swag_from({
    'tags': ['审计日志管理'],
    'summary': '获取审计日志详情',
    'description': '根据ID获取单个审计日志的详细信息（仅管理员可访问）',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'in': 'path',
            'name': 'log_id',
            'type': 'integer',
            'required': True,
            'description': '审计日志ID'
        }
    ],
    'responses': {
        200: {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': '获取成功'},
                    'data': {'$ref': '#/definitions/AuditLog'}
                }
            }
        },
        404: {
            'description': '审计日志不存在',
            'schema': {'$ref': '#/definitions/Error'}
        },
        401: {
            'description': '未授权访问',
            'schema': {'$ref': '#/definitions/Error'}
        },
        403: {
            'description': '权限不足',
            'schema': {'$ref': '#/definitions/Error'}
        }
    }
})
def get_audit_log_detail(log_id):
    """获取审计日志详情"""
    try:
        # 检查 Redis 缓存
        cache_key = f"audit_log:{log_id}"
        cached_result = redis_client.get_json(cache_key)
        if cached_result:
            return success(data=cached_result, msg='获取成功（缓存）')
        
        # 查询审计日志
        audit_log = auditlog_service.get_audit_log_by_id(log_id)
        
        # 序列化数据
        result = auditlog_schema.dump(audit_log)
        
        # 缓存结果（10分钟）
        redis_client.set_json(cache_key, result, expire=600)
        
        return success(data=result, msg='获取成功')
        
    except NotFoundError as e:
        return fail(code=404, msg=e.message)
    except Exception as e:
        return fail(code=500, msg=f'服务器内部错误: {str(e)}')


@auditlog_bp.route('/action-types', methods=['GET'])
@admin_required
@swag_from({
    'tags': ['审计日志管理'],
    'summary': '获取操作类型列表',
    'description': '获取所有可用的操作类型列表（仅管理员可访问）',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': '获取成功'},
                    'data': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'example': ['LOGIN', 'CREATE_EQUIPMENT', 'UPDATE_EQUIPMENT']
                    }
                }
            }
        },
        401: {
            'description': '未授权访问',
            'schema': {'$ref': '#/definitions/Error'}
        },
        403: {
            'description': '权限不足',
            'schema': {'$ref': '#/definitions/Error'}
        }
    }
})
def get_action_types():
    """获取操作类型列表"""
    try:
        # 检查 Redis 缓存
        cache_key = "audit_action_types"
        cached_result = redis_client.get_json(cache_key)
        if cached_result:
            return success(data=cached_result, msg='获取成功（缓存）')
        
        # 获取操作类型
        action_types = auditlog_service.get_action_types()
        
        # 缓存结果（1小时）
        redis_client.set_json(cache_key, action_types, expire=3600)
        
        return success(data=action_types, msg='获取成功')
        
    except Exception as e:
        return fail(code=500, msg=f'服务器内部错误: {str(e)}')


@auditlog_bp.route('/statistics', methods=['GET'])
@admin_required
@swag_from({
    'tags': ['审计日志管理'],
    'summary': '获取审计日志统计信息',
    'description': '获取审计日志的统计信息，包括总数、今日数量、操作类型统计等（仅管理员可访问）',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': '获取成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'total_logs': {'type': 'integer', 'example': 1000},
                            'today_logs': {'type': 'integer', 'example': 50},
                            'action_stats': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'action_type': {'type': 'string'},
                                        'count': {'type': 'integer'}
                                    }
                                }
                            },
                            'operator_stats': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'operator_id': {'type': 'string'},
                                        'count': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        401: {
            'description': '未授权访问',
            'schema': {'$ref': '#/definitions/Error'}
        },
        403: {
            'description': '权限不足',
            'schema': {'$ref': '#/definitions/Error'}
        }
    }
})
def get_audit_statistics():
    """获取审计日志统计信息"""
    try:
        # 检查 Redis 缓存
        cache_key = "audit_statistics"
        cached_result = redis_client.get_json(cache_key)
        if cached_result:
            return success(data=cached_result, msg='获取成功（缓存）')
        
        # 获取统计信息
        stats = auditlog_service.get_audit_statistics()
        
        # 序列化数据
        result = auditlog_stats_schema.dump(stats)
        
        # 缓存结果（15分钟）
        redis_client.set_json(cache_key, result, expire=900)
        
        return success(data=result, msg='获取成功')
        
    except ValidationError as e:
        return fail(code=400, msg=f'统计失败: {e.message}')
    except Exception as e:
        return fail(code=500, msg=f'服务器内部错误: {str(e)}')
