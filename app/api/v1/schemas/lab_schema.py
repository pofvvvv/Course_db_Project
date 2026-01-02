"""
实验室 Schema 定义
用于数据验证和序列化
"""
from marshmallow import fields, validate
from app.utils.schemas import BaseCreateSchema, BaseUpdateSchema, BaseSchema


class LaboratorySchema(BaseSchema):
    """
    实验室 Schema（用于响应数据的序列化）
    
    用途：
        - 将数据库查询的 ORM 对象序列化为字典，用于 API 响应
        - 主要用于 GET 请求返回数据时的序列化
    
    特点：
        - id 字段设置为 dump_only=True，表示只在序列化时使用，不会用于验证
        - 继承自 BaseSchema，自动过滤 None 值
        - 严格模式（unknown=RAISE），遇到未知字段会抛出异常
    
    使用示例：
        lab = lab_service.get_lab_by_id(1)
        data = lab_schema.dump(lab)  # 将 ORM 对象转为字典
        # 结果: {'id': 1, 'name': '计算机实验室', 'location': '教学楼A101'}
    """
    id = fields.Integer(dump_only=True, description='实验室ID')
    name = fields.String(required=True, validate=validate.Length(min=1, max=50), description='实验室名称')
    location = fields.String(allow_none=True, validate=validate.Length(max=100), description='实验室位置')


class LaboratoryCreateSchema(BaseCreateSchema):
    """
    创建实验室 Schema（用于 POST 请求的数据验证）
    
    用途：
        - 验证创建实验室时的请求数据
        - 将 JSON 数据转换为验证后的字典，用于创建数据库记录
    
    特点：
        - 继承自 BaseCreateSchema，严格模式（unknown=RAISE）
        - 遇到未知字段会抛出异常，确保数据安全
        - name 字段为必填项（required=True）
        - location 字段可选（allow_none=True）
    
    使用示例：
        json_data = {'name': '计算机实验室', 'location': '教学楼A101'}
        errors = lab_create_schema.validate(json_data)  # 验证数据
        if errors:
            return fail(code=422, msg='数据验证失败', data=errors)
        validated_data = lab_create_schema.load(json_data)  # 加载并验证
        lab = lab_service.create_lab(validated_data)  # 创建实验室
    """
    name = fields.String(required=True, validate=validate.Length(min=1, max=50), error_messages={
        'required': '实验室名称不能为空',
        'invalid': '实验室名称格式错误'
    }, description='实验室名称')
    location = fields.String(allow_none=True, validate=validate.Length(max=100), error_messages={
        'invalid': '实验室位置长度不能超过100个字符'
    }, description='实验室位置')


class LaboratoryUpdateSchema(BaseUpdateSchema):
    """
    更新实验室 Schema（用于 PUT/PATCH 请求的数据验证）
    
    用途：
        - 验证更新实验室时的请求数据
        - 将 JSON 数据转换为验证后的字典，用于更新数据库记录
    
    特点：
        - 继承自 BaseUpdateSchema，宽松模式（unknown=EXCLUDE）
        - 忽略未知字段，允许部分更新（只更新提供的字段）
        - 所有字段都是可选的（不设置 required=True），支持部分更新
        - 适合 PUT 和 PATCH 请求
    
    使用示例：
        json_data = {'name': '新实验室名称'}  # 只更新名称
        errors = lab_update_schema.validate(json_data)  # 验证数据
        if errors:
            return fail(code=422, msg='数据验证失败', data=errors)
        validated_data = lab_update_schema.load(json_data)  # 加载并验证
        lab = lab_service.update_lab(lab_id, validated_data)  # 更新实验室
    """
    name = fields.String(validate=validate.Length(min=1, max=50), error_messages={
        'invalid': '实验室名称格式错误'
    }, description='实验室名称')
    location = fields.String(allow_none=True, validate=validate.Length(max=100), error_messages={
        'invalid': '实验室位置长度不能超过100个字符'
    }, description='实验室位置')