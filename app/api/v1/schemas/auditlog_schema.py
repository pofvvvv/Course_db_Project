"""
审计日志 Schema 定义
用于数据验证和序列化
"""
from marshmallow import fields, validate
from app.utils.schemas import BaseSchema, BaseQuerySchema


class AuditLogSchema(BaseSchema):
    """审计日志 Schema（用于响应）"""
    id = fields.Integer(dump_only=True, description='日志ID')
    operator_id = fields.String(required=True, description='操作人ID')
    action_time = fields.DateTime(format='iso', description='操作时间')
    action_type = fields.String(required=True, description='操作类型')
    detail = fields.String(allow_none=True, description='操作详情')
    ip_address = fields.String(allow_none=True, description='IP地址')


class AuditLogQuerySchema(BaseQuerySchema):
    """审计日志查询 Schema（用于 GET 请求参数）"""
    operator_id = fields.String(allow_none=True, description='操作人ID筛选')
    action_type = fields.String(allow_none=True, description='操作类型筛选')
    start_time = fields.DateTime(allow_none=True, format='iso', description='开始时间')
    end_time = fields.DateTime(allow_none=True, format='iso', description='结束时间')
    page = fields.Integer(missing=1, validate=lambda x: x > 0, description='页码')
    page_size = fields.Integer(missing=20, validate=lambda x: 0 < x <= 100, description='每页数量')
