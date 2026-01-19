"""
统计服务
提供数据统计相关的业务逻辑
"""
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app import db
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.admin import Admin


def get_equipment_statistics():
    """
    获取设备统计信息
    
    Returns:
        dict: 包含设备总数、可用数、使用率等统计信息
    """
    # 设备总数
    total_count = Equipment.query.count()
    
    # 可用设备数（status=1 表示正常/可用）
    available_count = Equipment.query.filter(Equipment.status == 1).count()
    
    # 计算使用率（有预约的设备数 / 总设备数）
    # 获取有预约的设备数量（去重）
    equipment_with_reservations = db.session.query(
        Reservation.equip_id
    ).filter(
        Reservation.status == 1  # 只统计已通过的预约
    ).distinct().count()
    
    usage_rate = 0.0
    if total_count > 0:
        usage_rate = round((equipment_with_reservations / total_count) * 100, 2)
    
    # 按状态统计
    status_stats = db.session.query(
        Equipment.status,
        func.count(Equipment.id).label('count')
    ).group_by(Equipment.status).all()
    
    status_distribution = {str(status): count for status, count in status_stats}
    
    # 按类别统计
    category_stats = db.session.query(
        Equipment.category,
        func.count(Equipment.id).label('count')
    ).group_by(Equipment.category).all()
    
    category_distribution = {
        '学院设备' if cat == 1 else '实验室设备': count 
        for cat, count in category_stats
    }
    
    return {
        'total': total_count,
        'available': available_count,
        'unavailable': total_count - available_count,
        'usage_rate': usage_rate,
        'equipment_with_reservations': equipment_with_reservations,
        'status_distribution': status_distribution,
        'category_distribution': category_distribution
    }


def get_reservation_statistics():
    """
    获取预约统计信息
    
    Returns:
        dict: 包含总预约数、通过率、拒绝率等统计信息
    """
    # 总预约数
    total_count = Reservation.query.count()
    
    # 按状态统计
    status_stats = db.session.query(
        Reservation.status,
        func.count(Reservation.id).label('count')
    ).group_by(Reservation.status).all()
    
    status_counts = {status: count for status, count in status_stats}
    
    # 待审批 (0)
    pending_count = status_counts.get(0, 0)
    # 已通过 (1)
    approved_count = status_counts.get(1, 0)
    # 已拒绝 (2)
    rejected_count = status_counts.get(2, 0)
    # 已取消 (3)
    cancelled_count = status_counts.get(3, 0)
    
    # 计算通过率和拒绝率（基于已处理的预约，不包括待审批和已取消）
    processed_count = approved_count + rejected_count
    approval_rate = 0.0
    rejection_rate = 0.0
    
    if processed_count > 0:
        approval_rate = round((approved_count / processed_count) * 100, 2)
        rejection_rate = round((rejected_count / processed_count) * 100, 2)
    
    # 最近30天的预约趋势（按日期统计）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_stats = db.session.query(
        func.date(Reservation.apply_time).label('date'),
        func.count(Reservation.id).label('count')
    ).filter(
        Reservation.apply_time >= thirty_days_ago
    ).group_by(
        func.date(Reservation.apply_time)
    ).order_by(
        func.date(Reservation.apply_time)
    ).all()
    
    daily_trend = [
        {
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        }
        for date, count in daily_stats
    ]
    
    return {
        'total': total_count,
        'pending': pending_count,
        'approved': approved_count,
        'rejected': rejected_count,
        'cancelled': cancelled_count,
        'approval_rate': approval_rate,
        'rejection_rate': rejection_rate,
        'daily_trend': daily_trend
    }


def get_user_statistics():
    """
    获取用户统计信息
    
    Returns:
        dict: 包含各角色人数等统计信息
    """
    # 学生总数
    student_count = Student.query.count()
    
    # 教师总数
    teacher_count = Teacher.query.count()
    
    # 管理员总数
    admin_count = Admin.query.count()
    
    # 总用户数
    total_count = student_count + teacher_count + admin_count
    
    return {
        'total': total_count,
        'students': student_count,
        'teachers': teacher_count,
        'admins': admin_count
    }


def get_top_equipment(time_range='week', limit=10):
    """
    获取热门设备排行
    
    Args:
        time_range: 时间范围，'week' 表示近一周，'month' 表示近一月
        limit: 返回数量限制
    
    Returns:
        list: 热门设备列表，包含设备ID、名称、预约次数
    """
    # 计算时间范围
    if time_range == 'week':
        start_date = datetime.utcnow() - timedelta(days=7)
    elif time_range == 'month':
        start_date = datetime.utcnow() - timedelta(days=30)
    else:
        start_date = datetime.utcnow() - timedelta(days=7)
    
    # 统计每个设备的预约次数（只统计已通过的预约）
    equipment_stats = db.session.query(
        Equipment.id,
        Equipment.name,
        func.count(Reservation.id).label('reservation_count')
    ).join(
        Reservation, Equipment.id == Reservation.equip_id
    ).filter(
        Reservation.status == 1,  # 只统计已通过的预约
        Reservation.apply_time >= start_date
    ).group_by(
        Equipment.id,
        Equipment.name
    ).order_by(
        func.count(Reservation.id).desc()
    ).limit(limit).all()
    
    # 转换为字典列表
    result = [
        {
            'id': equip_id,
            'name': name,
            'count': count
        }
        for equip_id, name, count in equipment_stats
    ]
    
    return result


def get_all_statistics():
    """
    获取所有统计信息
    
    Returns:
        dict: 包含设备、预约、用户的所有统计信息
    """
    return {
        'equipment': get_equipment_statistics(),
        'reservation': get_reservation_statistics(),
        'user': get_user_statistics(),
        'timestamp': datetime.utcnow().isoformat()
    }
