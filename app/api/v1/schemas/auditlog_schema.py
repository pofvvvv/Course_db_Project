"""
审计日志 Schema 定义
用于数据验证和序列化
"""
from marshmallow import fields, validate
from app.utils.schemas import BaseSchema


class AuditLogSchema(BaseSchema):
    """审计日志 Schema（用于响应）"""
    id = fields.Integer(dump_only=True, description='日志ID')
    operator_id = fields.String(required=True, description='操作人ID')
    action_time = fields.DateTime(dump_only=True, format='iso', description='操作时间')
    action_type = fields.String(required=True, description='操作类型')
    detail = fields.String(allow_none=True, description='操作详情')
    ip_address = fields.String(allow_none=True, description='IP地址')


class AuditLogQuerySchema(BaseSchema):
    """审计日志查询 Schema（用于 GET 请求参数）"""
    operator_id = fields.String(allow_none=True, description='操作人ID筛选')
    action_type = fields.String(
        allow_none=True,
        validate=validate.OneOf([
            'LOGIN', 'LOGOUT', 
            'CREATE_EQUIPMENT', 'UPDATE_EQUIPMENT', 'DELETE_EQUIPMENT',
            'CREATE_LAB', 'UPDATE_LAB', 'DELETE_LAB',
            'CREATE_RESERVATION', 'APPROVE_RESERVATION', 'REJECT_RESERVATION', 'CANCEL_RESERVATION',
            'CREATE_TIMESLOT', 'UPDATE_TIMESLOT', 'DELETE_TIMESLOT',
            'CREATE_USER', 'UPDATE_USER', 'DELETE_USER'
        ]),
        description='操作类型筛选'
    )
    start_time = fields.DateTime(
        allow_none=True, 
        format='iso', 
        description='开始时间筛选（ISO格式）'
    )
    end_time = fields.DateTime(
        allow_none=True, 
        format='iso', 
        description='结束时间筛选（ISO格式）'
    )
    page = fields.Integer(
        missing=1, 
        validate=validate.Range(min=1), 
        description='页码'
    )
    per_page = fields.Integer(
        missing=20, 
        validate=validate.Range(min=1, max=100), 
        description='每页数量'
    )


class AuditLogStatsSchema(BaseSchema):
    """审计日志统计 Schema"""
    total_logs = fields.Integer(description='总日志数')
    today_logs = fields.Integer(description='今日日志数')
    action_stats = fields.List(
        fields.Dict(keys=fields.String(), values=fields.Integer()),
        description='按操作类型统计'
    )
    operator_stats = fields.List(
        fields.Dict(keys=fields.String(), values=fields.Integer()),
        description='按操作人统计'
    )
