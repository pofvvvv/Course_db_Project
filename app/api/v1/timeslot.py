"""
时间段 API 路由
"""
from flask import Blueprint, request
from flasgger import swag_from

from app.services import timeslot_service
from app.api.v1.schemas.timeslot_schema import TimeSlotSchema
from app.utils.response import success, fail
from app.utils.auth import login_required
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.redis_client import redis_client

timeslot_bp = Blueprint('timeslot', __name__)

timeslot_schema = TimeSlotSchema()


@timeslot_bp.route('/equipment/<int:equip_id>', methods=['GET'])
@login_required
@swag_from({
    'tags': ['时间段管理'],
    'summary': '获取设备时间段列表',
    'description': '返回指定设备的全部时间段，支持 only_active 过滤；默认包含禁用时间段，按开始时间升序。',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'in': 'path',
            'name': 'equip_id',
            'required': True,
            'type': 'integer',
            'description': '设备ID'
        },
        {
            'in': 'query',
            'name': 'only_active',
            'required': False,
            'type': 'boolean',
            'description': '是否仅返回激活的时间段（true/false）'
        }
    ],
    'responses': {
        200: {
            'description': '成功返回时间段列表',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'slot_id': {'type': 'integer', 'example': 1},
                                'equip_id': {'type': 'integer', 'example': 1},
                                'start_time': {'type': 'string', 'example': '09:00:00'},
                                'end_time': {'type': 'string', 'example': '10:00:00'},
                                'is_active': {'type': 'integer', 'example': 1}
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_timeslots(equip_id):
    try:
        only_active = str(request.args.get('only_active', '')).lower() in ('true', '1')

        # 仅对完整列表做缓存，only_active 时不使用缓存以避免歧义
        cache_key = f'timeslot:list:{equip_id}'
        if not only_active:
            cached_data = redis_client.get(cache_key)
            if cached_data is not None:
                return success(data=cached_data, msg='查询成功')

        slots = timeslot_service.get_timeslots_by_equipment(equip_id, only_active=only_active)
        data = timeslot_schema.dump(slots, many=True)

        if not only_active:
            redis_client.set(cache_key, data, ex=3600)

        return success(data=data, msg='查询成功')
    except NotFoundError as e:
        return fail(code=404, msg=e.message, data=e.payload)
    except ValidationError as e:
        return fail(code=422, msg=e.message, data=e.payload)
    except Exception as e:
        return fail(code=500, msg=f'查询失败: {str(e)}')


@timeslot_bp.route('/equipment/<int:equip_id>/available', methods=['GET'])
@login_required
@swag_from({
    'tags': ['时间段管理'],
    'summary': '获取设备可用时间段',
    'description': '返回设备可用时间段。如果不提供日期参数，返回所有激活的时间段；如果提供日期参数，会排除该日期已被预约的时间段。',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'in': 'path',
            'name': 'equip_id',
            'required': True,
            'type': 'integer',
            'description': '设备ID'
        },
        {
            'in': 'query',
            'name': 'date',
            'required': False,
            'type': 'string',
            'format': 'date',
            'description': '目标日期（格式：YYYY-MM-DD），可选。如果提供，会排除该日期已被预约的时间段'
        }
    ],
    'responses': {
        200: {
            'description': '成功返回可用时间段列表',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'slot_id': {'type': 'integer', 'example': 1},
                                'equip_id': {'type': 'integer', 'example': 1},
                                'start_time': {'type': 'string', 'example': '09:00:00'},
                                'end_time': {'type': 'string', 'example': '10:00:00'},
                                'is_active': {'type': 'integer', 'example': 1}
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_available_timeslots(equip_id):
    try:
        # 获取可选的日期参数
        target_date = request.args.get('date')
        
        slots = timeslot_service.get_available_timeslots(equip_id, target_date=target_date)
        data = timeslot_schema.dump(slots, many=True)
        return success(data=data, msg='查询成功')
    except NotFoundError as e:
        return fail(code=404, msg=e.message, data=e.payload)
    except ValidationError as e:
        return fail(code=422, msg=e.message, data=e.payload)
    except Exception as e:
        return fail(code=500, msg=f'查询失败: {str(e)}')


@timeslot_bp.route('/equipment/<int:equip_id>/available-dates', methods=['GET'])
@login_required
@swag_from({
    'tags': ['时间段管理'],
    'summary': '获取设备可用日期列表',
    'description': '返回设备在未来一段时间内的可用日期列表（有可用时间段的日期）。',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'in': 'path',
            'name': 'equip_id',
            'required': True,
            'type': 'integer',
            'description': '设备ID'
        },
        {
            'in': 'query',
            'name': 'start_date',
            'required': False,
            'type': 'string',
            'format': 'date',
            'description': '开始日期（格式：YYYY-MM-DD），可选，默认为今天'
        },
        {
            'in': 'query',
            'name': 'days',
            'required': False,
            'type': 'integer',
            'description': '查询天数（默认30天）'
        }
    ],
    'responses': {
        200: {
            'description': '成功返回可用日期列表',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'format': 'date',
                            'example': '2024-01-15'
                        }
                    }
                }
            }
        }
    }
})
def get_available_dates(equip_id):
    try:
        # 获取可选的查询参数
        start_date = request.args.get('start_date')
        days = request.args.get('days', type=int, default=30)
        
        dates = timeslot_service.get_available_dates(equip_id, start_date=start_date, days=days)
        return success(data=dates, msg='查询成功')
    except NotFoundError as e:
        return fail(code=404, msg=e.message, data=e.payload)
    except ValidationError as e:
        return fail(code=422, msg=e.message, data=e.payload)
    except Exception as e:
        return fail(code=500, msg=f'查询失败: {str(e)}')
