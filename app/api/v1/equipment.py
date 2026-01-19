"""
设备 API 路由
实现设备的 RESTful API（读写分离：普通用户读，管理员写）
"""
from flask import Blueprint, request
from flasgger import swag_from
from app.services import equipment_service
from app.api.v1.schemas.equipment_schema import EquipmentSchema
from app.utils.response import success, fail
from app.utils.exceptions import NotFoundError
from app.utils.auth import login_required
from app.utils.redis_client import redis_client
from app.services import statistics_service

# 创建蓝图
equipment_bp = Blueprint('equipment', __name__)

# 实例化 Schema
equipment_schema = EquipmentSchema()


@equipment_bp.route('/', methods=['GET'])
@equipment_bp.route('', methods=['GET'])  # 同时支持带斜杠和不带斜杠的 URL
@login_required
@swag_from({
    'tags': ['设备管理'],
    'summary': '获取设备列表',
    'description': '获取设备列表，支持按实验室ID和关键词筛选，支持分页（普通用户可访问）',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'in': 'query',
            'name': 'lab_id',
            'type': 'integer',
            'required': False,
            'description': '实验室ID筛选'
        },
        {
            'in': 'query',
            'name': 'keyword',
            'type': 'string',
            'required': False,
            'description': '关键词搜索（设备名称）'
        },
        {
            'in': 'query',
            'name': 'category',
            'type': 'integer',
            'required': False,
            'description': '设备类别筛选 (1:学院, 2:实验室)'
        },
        {
            'in': 'query',
            'name': 'status',
            'type': 'integer',
            'required': False,
            'description': '设备状态筛选'
        },
        {
            'in': 'query',
            'name': 'page',
            'type': 'integer',
            'required': False,
            'description': '页码（从1开始，默认1）',
            'default': 1
        },
        {
            'in': 'query',
            'name': 'page_size',
            'type': 'integer',
            'required': False,
            'description': '每页数量（默认10，最大100）',
            'default': 10
        }
    ],
    'responses': {
        200: {
            'description': '成功返回设备列表',
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
                                        'name': {'type': 'string', 'example': '扫描电子显微镜'},
                                        'lab_id': {'type': 'integer', 'example': 1},
                                        'lab_name': {'type': 'string', 'example': '材料实验室'},
                                        'category': {'type': 'integer', 'example': 2},
                                        'status': {'type': 'integer', 'example': 1}
                                    }
                                }
                            },
                            'total': {'type': 'integer', 'example': 100}
                        }
                    }
                }
            }
        },
        401: {
            'description': '未授权'
        }
    }
})
def get_equipments():
    """获取设备列表（支持筛选和分页）"""
    try:
        # 获取查询参数
        lab_id = request.args.get('lab_id', type=int)
        keyword = request.args.get('keyword', type=str)
        category = request.args.get('category', type=int)
        status = request.args.get('status', type=int)
        page = request.args.get('page', type=int, default=1)
        page_size = request.args.get('page_size', type=int, default=9)
        
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 9
        elif page_size > 100:
            page_size = 100  # 限制每页最大数量
        
        # 构建缓存键（包含所有筛选条件和分页参数）
        cache_key = f'api:equipment:list:lab_{lab_id}:kw_{keyword}:cat_{category}:st_{status}:p_{page}:ps_{page_size}'
        
        # 尝试从缓存获取
        cached_data = redis_client.get(cache_key)
        if cached_data is not None:
            return success(data=cached_data, msg='查询成功')
        
        # 查询设备列表
        equipments, total = equipment_service.get_equipment_list(
            lab_id=lab_id,
            keyword=keyword,
            category=category,
            status=status,
            page=page,
            page_size=page_size
        )
        
        # 序列化
        items = equipment_schema.dump(equipments, many=True)
        
        # 构建返回数据
        data = {
            'items': items,
            'total': total
        }
        
        # 存入缓存（5分钟过期）
        redis_client.set(cache_key, data, ex=300)
        
        return success(data=data, msg='查询成功')
    except Exception as e:
        return fail(code=500, msg=f'查询失败: {str(e)}')


@equipment_bp.route('/<int:equip_id>', methods=['GET'])
@login_required
@swag_from({
    'tags': ['设备管理'],
    'summary': '获取设备详情',
    'description': '获取指定设备的详细信息（普通用户可访问）',
    'security': [{'Bearer': []}],
    'parameters': [{
        'in': 'path',
        'name': 'equip_id',
        'type': 'integer',
        'required': True,
        'description': '设备ID'
    }],
    'responses': {
        200: {
            'description': '成功返回设备详情',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer', 'example': 1},
                            'name': {'type': 'string', 'example': '扫描电子显微镜'},
                            'lab_id': {'type': 'integer', 'example': 1},
                            'category': {'type': 'integer', 'example': 2},
                            'status': {'type': 'integer', 'example': 1}
                        }
                    }
                }
            }
        },
        404: {
            'description': '设备不存在'
        }
    }
})
def get_equipment(equip_id):
    """获取设备详情"""
    try:
        # 尝试从缓存获取
        cache_key = f'api:equipment:detail:{equip_id}'
        cached_data = redis_client.get(cache_key)
        if cached_data is not None:
            return success(data=cached_data, msg='查询成功')
        
        # 查询设备
        equipment = equipment_service.get_equipment_by_id(equip_id)
        
        # 序列化
        data = equipment_schema.dump(equipment)
        
        # 存入缓存（10分钟过期）
        redis_client.set(cache_key, data, ex=600)
        
        return success(data=data, msg='查询成功')
    except NotFoundError as e:
        return fail(code=404, msg=e.message)
    except Exception as e:
        return fail(code=500, msg=f'查询失败: {str(e)}')


@equipment_bp.route('/top', methods=['GET'])
@swag_from({
    'tags': ['设备管理'],
    'summary': '获取热门设备排行',
    'description': '获取热门设备预约排行（按时间段统计，不需要登录）',
    'parameters': [
        {
            'in': 'query',
            'name': 'time_range',
            'type': 'string',
            'required': False,
            'enum': ['week', 'month'],
            'description': '时间范围：week（近一周）或 month（近一月）',
            'default': 'week'
        },
        {
            'in': 'query',
            'name': 'limit',
            'type': 'integer',
            'required': False,
            'description': '返回数量限制（默认10）',
            'default': 10
        }
    ],
    'responses': {
        200: {
            'description': '成功返回热门设备列表',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': '查询成功'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer', 'example': 1},
                                'name': {'type': 'string', 'example': '扫描电子显微镜'},
                                'count': {'type': 'integer', 'example': 156}
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_top_equipments():
    """获取热门设备排行"""
    try:
        # 获取查询参数
        time_range = request.args.get('time_range', 'week')
        limit = request.args.get('limit', type=int, default=10)
        
        # 验证参数
        if time_range not in ['week', 'month']:
            time_range = 'week'
        if limit < 1 or limit > 50:
            limit = 10
        
        # 构建缓存键
        cache_key = f'api:equipment:top:{time_range}:{limit}'
        
        # 尝试从缓存获取（10分钟过期）
        cached_data = redis_client.get(cache_key)
        if cached_data is not None:
            return success(data=cached_data, msg='查询成功')
        
        # 获取热门设备数据
        top_equipments = statistics_service.get_top_equipment(
            time_range=time_range,
            limit=limit
        )
        
        # 存入缓存（10分钟过期）
        redis_client.set(cache_key, top_equipments, ex=600)
        
        return success(data=top_equipments, msg='查询成功')
    except Exception as e:
        return fail(code=500, msg=f'查询失败: {str(e)}')



