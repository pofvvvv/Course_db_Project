"""
审计日志装饰器
自动记录操作日志的装饰器
"""
from functools import wraps
from flask import g
from app.services.auditlog_service import create_audit_log
from app.utils.auth import get_current_user


def audit_log(action_type, detail_template=None):
    """
    审计日志装饰器
    自动记录操作日志
    
    Args:
        action_type: 操作类型（如 'CREATE_EQUIPMENT', 'UPDATE_EQUIPMENT'）
        detail_template: 详情模板，支持格式化字符串（可选）
    
    Usage:
        @audit_log('CREATE_EQUIPMENT', '创建设备: {name}')
        def create_equipment_api():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行原函数
            result = f(*args, **kwargs)
            
            # 记录审计日志（在函数执行成功后）
            try:
                # 获取当前用户
                current_user = get_current_user()
                operator_id = current_user.get('user_id')
                
                # 构建详情信息
                detail = None
                if detail_template:
                    # 尝试从 g 对象获取参数（通常在函数中设置）
                    format_params = getattr(g, 'audit_params', {})
                    
                    # 如果没有设置参数，尝试从 kwargs 获取
                    if not format_params and kwargs:
                        format_params = kwargs
                    
                    # 格式化详情
                    if format_params:
                        try:
                            detail = detail_template.format(**format_params)
                        except (KeyError, ValueError):
                            detail = detail_template
                    else:
                        detail = detail_template
                
                # 创建审计日志
                create_audit_log(
                    operator_id=operator_id,
                    action_type=action_type,
                    detail=detail
                )
                
            except Exception as e:
                # 审计日志记录失败不应该影响主要功能
                print(f"[WARNING] 审计日志记录失败: {str(e)}")
            
            return result
        
        return decorated_function
    return decorator


def set_audit_params(**params):
    """
    设置审计日志参数
    在被装饰的函数中调用，用于设置详情格式化参数
    
    Args:
        **params: 参数字典
    
    Usage:
        @audit_log('CREATE_EQUIPMENT', '创建设备: {name}')
        def create_equipment():
            # 业务逻辑
            equipment = Equipment(name='新设备')
            
            # 设置审计参数
            set_audit_params(name=equipment.name)
            
            return equipment
    """
    g.audit_params = params


def audit_login(user_id, user_type, success=True):
    """
    记录登录日志
    
    Args:
        user_id: 用户ID
        user_type: 用户类型
        success: 登录是否成功
    """
    try:
        action_type = 'LOGIN' if success else 'LOGIN_FAILED'
        detail = f'用户类型: {user_type}, 登录{"成功" if success else "失败"}'
        
        create_audit_log(
            operator_id=str(user_id),
            action_type=action_type,
            detail=detail
        )
    except Exception as e:
        print(f"[WARNING] 登录审计日志记录失败: {str(e)}")


def audit_logout(user_id, user_type):
    """
    记录登出日志
    
    Args:
        user_id: 用户ID
        user_type: 用户类型
    """
    try:
        create_audit_log(
            operator_id=str(user_id),
            action_type='LOGOUT',
            detail=f'用户类型: {user_type}'
        )
    except Exception as e:
        print(f"[WARNING] 登出审计日志记录失败: {str(e)}")


def audit_operation(operator_id, action_type, detail=None):
    """
    手动记录操作日志
    
    Args:
        operator_id: 操作人ID
        action_type: 操作类型
        detail: 操作详情
    """
    try:
        create_audit_log(
            operator_id=str(operator_id),
            action_type=action_type,
            detail=detail
        )
    except Exception as e:
        print(f"[WARNING] 手动审计日志记录失败: {str(e)}")


# 常用的操作类型常量
class AuditActionType:
    """审计操作类型常量"""
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    LOGIN_FAILED = 'LOGIN_FAILED'
    
    # 设备相关
    CREATE_EQUIPMENT = 'CREATE_EQUIPMENT'
    UPDATE_EQUIPMENT = 'UPDATE_EQUIPMENT'
    DELETE_EQUIPMENT = 'DELETE_EQUIPMENT'
    
    # 实验室相关
    CREATE_LAB = 'CREATE_LAB'
    UPDATE_LAB = 'UPDATE_LAB'
    DELETE_LAB = 'DELETE_LAB'
    
    # 预约相关
    CREATE_RESERVATION = 'CREATE_RESERVATION'
    APPROVE_RESERVATION = 'APPROVE_RESERVATION'
    REJECT_RESERVATION = 'REJECT_RESERVATION'
    CANCEL_RESERVATION = 'CANCEL_RESERVATION'
    
    # 时间段相关
    CREATE_TIMESLOT = 'CREATE_TIMESLOT'
    UPDATE_TIMESLOT = 'UPDATE_TIMESLOT'
    DELETE_TIMESLOT = 'DELETE_TIMESLOT'
    
    # 用户相关
    CREATE_USER = 'CREATE_USER'
    UPDATE_USER = 'UPDATE_USER'
    DELETE_USER = 'DELETE_USER'
