"""
审计日志 API 路由
实现审计日志的 RESTful API
"""
from flask import Blueprint, request
from flasgger import swag_from
from datetime import datetime

from app.services import auditlog_service
from app.api.v1.schemas.auditlog_schema import (
    AuditLogSchema, AuditLogQuerySchema
)
from app.utils.response import success, fail
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.auth import admin_required

# 创建蓝图
auditlog_bp = Blueprint('auditlog', __name__)

# 实例化 Schema
auditlog_schema = AuditLogSchema()
auditlog_query_schema = AuditLogQuerySchema()


@auditlog_bp.route('/', methods=['GET'])
@admin_required
@swag_from({
    'tags': ['审计日志'],
    'summary': '获取审计日志列表',
    'description': '获取审计日志列表，支持筛选和分页（需要管理员权限）',
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
            'description': '开始时间（ISO格式）'
        },
        {
            'in': 'query',
            'name': 'end_time',
            'type': 'string',
            'format': 'date-time',
            'required': False,
            'description': '结束时间（ISO格式）'
        },
        {
            'in': 'query',
            'name': 'page',
            'type': 'integer',
            'required': False,
            'description': '页码（默认1）'
        },
        {
            'in': 'query',
            'name': 'page_size',
            'type': 'integer',
            'required': False,
            'description': '每页数量（默认20，最大100）'
        }
    ],
    'responses': {
        200: {
            'description': '成功返回审计日志列表',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'items': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'id': {'type': 'integer', 'example': 1},
                                        'operator_id': {'type': 'string', 'example': 'admin'},
                                        'action_time': {'type': 'string', 'example': '2024-01-01T00:00:00'},
                                        'action_type': {'type': 'string', 'example': 'create_equipment'},
                                        'detail': {'type': 'string', 'example': '{"name": "设备名称"}'},
                                        'ip_address': {'type': 'string', 'example': '127.0.0.1'}
                                    }
                                }
                            },
                            'total': {'type': 'integer', 'example': 100}
                        }
                    }
                }
            }
        },
        403: {
            'description': '需要管理员权限'
        }
    }
})
def get_audit_logs():
    """获取审计日志列表"""
    try:
        # 获取查询参数
        query_params = {
            'operator_id': request.args.get('operator_id'),
            'action_type': request.args.get('action_type'),
            'page': request.args.get('page', 1, type=int),
            'page_size': request.args.get('page_size', 20, type=int)
        }
        
        # 处理时间参数
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        
        start_time = None
        end_time = None
        
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except ValueError:
                return fail(code=400, msg='开始时间格式错误，请使用ISO格式')
        
        if end_time_str:
            try:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            except ValueError:
                return fail(code=400, msg='结束时间格式错误，请使用ISO格式')
        
        # 验证查询参数
        errors = auditlog_query_schema.validate(query_params)
        if errors:
            return fail(code=422, msg='查询参数验证失败', data=errors)
        
        # 调用 Service 层获取日志列表
        logs, total = auditlog_service.get_audit_log_list(
            operator_id=query_params.get('operator_id'),
            action_type=query_params.get('action_type'),
            start_time=start_time,
            end_time=end_time,
            page=query_params['page'],
            page_size=query_params['page_size']
        )
        
        # 序列化返回
        data = {
            'items': auditlog_schema.dump(logs, many=True),
            'total': total
        }
        
        return success(data=data, msg='查询成功')
    except Exception as e:
        return fail(code=500, msg=f'查询失败: {str(e)}')


@auditlog_bp.route('/<int:log_id>', methods=['GET'])
@admin_required
@swag_from({
    'tags': ['审计日志'],
    'summary': '获取审计日志详情',
    'description': '根据ID获取审计日志详情（需要管理员权限）',
    'security': [{'Bearer': []}],
    'parameters': [{
        'in': 'path',
        'name': 'log_id',
        'type': 'integer',
        'required': True,
        'description': '日志ID'
    }],
    'responses': {
        200: {
            'description': '成功返回审计日志详情',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer', 'example': 1},
                            'operator_id': {'type': 'string', 'example': 'admin'},
                            'action_time': {'type': 'string', 'example': '2024-01-01T00:00:00'},
                            'action_type': {'type': 'string', 'example': 'create_equipment'},
                            'detail': {'type': 'string', 'example': '{"name": "设备名称"}'},
                            'ip_address': {'type': 'string', 'example': '127.0.0.1'}
                        }
                    }
                }
            }
        },
        404: {
            'description': '审计日志不存在'
        },
        403: {
            'description': '需要管理员权限'
        }
    }
})
def get_audit_log(log_id):
    """获取审计日志详情"""
    try:
        # 调用 Service 层获取日志详情
        log = auditlog_service.get_audit_log_by_id(log_id)
        
        # 序列化返回
        data = auditlog_schema.dump(log)
        
        return success(data=data, msg='查询成功')
    except NotFoundError as e:
        return fail(code=404, msg=e.message)
    except Exception as e:
        return fail(code=500, msg=f'查询失败: {str(e)}')
