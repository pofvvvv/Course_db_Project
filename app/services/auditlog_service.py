"""
审计日志服务层
处理审计日志相关的业务逻辑
"""
from datetime import datetime
from app import db
from app.models.auditlog import AuditLog
from app.utils.exceptions import NotFoundError


def create_audit_log(operator_id, action_type, detail=None, ip_address=None):
    """
    创建审计日志记录
    
    Args:
        operator_id: 操作人ID
        action_type: 操作类型（如：create_equipment, update_equipment, delete_equipment, approve_reservation等）
        detail: 操作详情（JSON字符串或文本）
        ip_address: IP地址
    
    Returns:
        AuditLog: 创建的审计日志对象
    """
    audit_log = AuditLog(
        operator_id=operator_id,
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
        raise Exception(f'创建审计日志失败: {str(e)}')


def get_audit_log_list(operator_id=None, action_type=None, start_time=None, end_time=None, page=1, page_size=20):
    """
    获取审计日志列表（支持筛选和分页）
    
    Args:
        operator_id: 操作人ID筛选
        action_type: 操作类型筛选
        start_time: 开始时间（datetime对象）
        end_time: 结束时间（datetime对象）
        page: 页码（从1开始）
        page_size: 每页数量
    
    Returns:
        tuple: (日志列表, 总数)
    """
    query = AuditLog.query
    
    # 按操作人ID筛选
    if operator_id:
        query = query.filter(AuditLog.operator_id == operator_id)
    
    # 按操作类型筛选
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    
    # 按时间范围筛选
    if start_time:
        query = query.filter(AuditLog.action_time >= start_time)
    if end_time:
        query = query.filter(AuditLog.action_time <= end_time)
    
    # 按时间倒序排序（最新的在前）
    query = query.order_by(AuditLog.action_time.desc())
    
    # 获取总数（在分页之前）
    total = query.count()
    
    # 分页查询
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    return items, total


def get_audit_log_by_id(log_id):
    """
    根据 ID 查询审计日志详情
    
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
