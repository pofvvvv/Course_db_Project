"""
审计日志服务层
处理审计日志相关的业务逻辑
"""
from datetime import datetime
from flask import request
from app import db
from app.models.auditlog import AuditLog
from app.utils.exceptions import NotFoundError, ValidationError


def create_audit_log(operator_id, action_type, detail=None):
    """
    创建审计日志记录
    
    Args:
        operator_id: 操作人ID
        action_type: 操作类型
        detail: 操作详情（可选）
    
    Returns:
        AuditLog: 创建的审计日志对象
    """
    # 获取客户端IP地址
    ip_address = get_client_ip()
    
    audit_log = AuditLog(
        operator_id=str(operator_id),
        action_type=action_type,
        detail=detail,
        ip_address=ip_address,
        action_time=datetime.utcnow()
    )
    
    try:
        db.session.add(audit_log)
        db.session.commit()
        return audit_log
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f'创建审计日志失败: {str(e)}')


def get_audit_log_list(operator_id=None, action_type=None, start_time=None, end_time=None, page=1, per_page=20):
    """
    查询审计日志列表（支持筛选和分页）
    
    Args:
        operator_id: 操作人ID筛选
        action_type: 操作类型筛选
        start_time: 开始时间筛选
        end_time: 结束时间筛选
        page: 页码
        per_page: 每页数量
    
    Returns:
        dict: 包含日志列表、总数、分页信息
    """
    query = AuditLog.query
    
    # 按操作人ID筛选
    if operator_id:
        query = query.filter(AuditLog.operator_id == str(operator_id))
    
    # 按操作类型筛选
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    
    # 按时间范围筛选
    if start_time:
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        query = query.filter(AuditLog.action_time >= start_time)
    
    if end_time:
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        query = query.filter(AuditLog.action_time <= end_time)
    
    # 按时间降序排序（最新的在前）
    query = query.order_by(AuditLog.action_time.desc())
    
    # 分页查询
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return {
        'logs': pagination.items,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }


def get_audit_log_by_id(log_id):
    """
    根据ID查询审计日志详情
    
    Args:
        log_id: 日志ID
    
    Returns:
        AuditLog: 审计日志对象
    
    Raises:
        NotFoundError: 日志不存在
    """
    audit_log = AuditLog.query.get(log_id)
    if not audit_log:
        raise NotFoundError('审计日志不存在')
    return audit_log


def get_action_types():
    """
    获取所有操作类型列表
    
    Returns:
        list: 操作类型列表
    """
    return [
        'LOGIN',           # 登录
        'LOGOUT',          # 登出
        'CREATE_EQUIPMENT', # 创建设备
        'UPDATE_EQUIPMENT', # 更新设备
        'DELETE_EQUIPMENT', # 删除设备
        'CREATE_LAB',      # 创建实验室
        'UPDATE_LAB',      # 更新实验室
        'DELETE_LAB',      # 删除实验室
        'CREATE_RESERVATION', # 创建预约
        'APPROVE_RESERVATION', # 审批通过预约
        'REJECT_RESERVATION',  # 拒绝预约
        'CANCEL_RESERVATION',  # 取消预约
        'CREATE_TIMESLOT',     # 创建时间段
        'UPDATE_TIMESLOT',     # 更新时间段
        'DELETE_TIMESLOT',     # 删除时间段
        'CREATE_USER',         # 创建用户
        'UPDATE_USER',         # 更新用户
        'DELETE_USER',         # 删除用户
    ]


def get_client_ip():
    """
    获取客户端IP地址
    
    Returns:
        str: IP地址
    """
    # 考虑代理服务器的情况
    if request.headers.get('X-Forwarded-For'):
        # 如果有多个IP，取第一个
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    
    return ip or 'unknown'


def get_audit_statistics():
    """
    获取审计日志统计信息
    
    Returns:
        dict: 统计信息
    """
    try:
        # 总日志数
        total_logs = AuditLog.query.count()
        
        # 今日日志数
        today = datetime.utcnow().date()
        today_logs = AuditLog.query.filter(
            db.func.date(AuditLog.action_time) == today
        ).count()
        
        # 按操作类型统计
        action_stats = db.session.query(
            AuditLog.action_type,
            db.func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.action_type).all()
        
        # 按操作人统计（前10名）
        operator_stats = db.session.query(
            AuditLog.operator_id,
            db.func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.operator_id).order_by(
            db.func.count(AuditLog.id).desc()
        ).limit(10).all()
        
        return {
            'total_logs': total_logs,
            'today_logs': today_logs,
            'action_stats': [{'action_type': item[0], 'count': item[1]} for item in action_stats],
            'operator_stats': [{'operator_id': item[0], 'count': item[1]} for item in operator_stats]
        }
    except Exception as e:
        raise ValidationError(f'获取统计信息失败: {str(e)}')
