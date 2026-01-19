"""
审计日志装饰器
自动记录操作日志的装饰器
"""
import json
from functools import wraps
from flask import request, g
from app.utils.auth import get_current_user
from app.services import auditlog_service


def audit_log(action_type, detail_func=None):
    """
    审计日志装饰器
    自动记录操作日志
    
    Args:
        action_type: 操作类型（如：'create_equipment', 'update_equipment', 'delete_equipment', 'approve_reservation'等）
        detail_func: 可选的详情生成函数，接收 (func, *args, **kwargs) 参数，返回详情字符串或字典
    
    Usage:
        @audit_log('create_equipment')
        def create_equipment():
            ...
        
        @audit_log('update_equipment', detail_func=lambda f, *a, **k: f'更新设备ID: {a[0]}')
        def update_equipment(equip_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行原函数
            result = f(*args, **kwargs)
            
            # 检查响应状态码，只有成功响应（200-299）才记录日志
            # Flask 响应对象有 status_code 属性，如果是字典则检查 code 字段
            should_log = True
            if hasattr(result, 'status_code'):
                should_log = 200 <= result.status_code < 300
            elif isinstance(result, dict) and 'code' in result:
                should_log = result.get('code') == 200
            
            if not should_log:
                return result
            
            try:
                # 获取当前用户信息
                user = get_current_user()
                operator_id = user.get('user_id')
                
                # 获取IP地址
                ip_address = request.remote_addr
                if request.headers.get('X-Forwarded-For'):
                    ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
                
                # 生成操作详情
                detail = None
                if detail_func:
                    try:
                        detail_data = detail_func(f, *args, **kwargs)
                        if detail_data:
                            if isinstance(detail_data, dict):
                                detail = json.dumps(detail_data, ensure_ascii=False)
                            else:
                                detail = str(detail_data)
                    except Exception as e:
                        detail = f'生成详情失败: {str(e)}'
                else:
                    # 默认详情：记录请求参数
                    try:
                        request_data = {}
                        if request.json:
                            request_data['body'] = request.json
                        if request.args:
                            request_data['query'] = dict(request.args)
                        if args:
                            request_data['args'] = [str(arg) for arg in args]
                        if kwargs:
                            request_data['kwargs'] = {k: str(v) for k, v in kwargs.items()}
                        if request_data:
                            detail = json.dumps(request_data, ensure_ascii=False)
                    except Exception:
                        pass
                
                # 创建审计日志
                auditlog_service.create_audit_log(
                    operator_id=operator_id,
                    action_type=action_type,
                    detail=detail,
                    ip_address=ip_address
                )
            except Exception as e:
                # 审计日志记录失败不应该影响主业务逻辑
                # 只记录错误，不抛出异常
                print(f'[WARNING] 审计日志记录失败: {str(e)}')
            
            return result
        return decorated_function
    return decorator
