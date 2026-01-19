"""
时间段服务层，处理时间段相关的业务逻辑
"""
from datetime import time, datetime, date, timedelta
from sqlalchemy import and_

from app import db
from app.models.equipment import Equipment
from app.models.timeslot import TimeSlot
from app.models.reservation import Reservation
from app.utils.exceptions import NotFoundError, ValidationError


def _normalize_time(value):
    """
    将字符串时间规范为 time 对象，支持 HH:MM 或 HH:MM:SS
    """
    if isinstance(value, time):
        return value

    if isinstance(value, str):
        parts = value.strip().split(':')
        if len(parts) == 2:
            parts.append('00')
        if len(parts) != 3:
            raise ValidationError('时间格式必须为 HH:MM:SS', payload={'field': 'time'})
        try:
            h, m, s = map(int, parts)
            return time(hour=h, minute=m, second=s)
        except Exception:
            raise ValidationError('时间格式必须为 HH:MM:SS', payload={'field': 'time'})

    raise ValidationError('时间格式必须为 HH:MM:SS', payload={'field': 'time'})


def _validate_time_range(start_time, end_time):
    """
    校验时间范围是否合法
    """
    if start_time >= end_time:
        raise ValidationError('开始时间必须早于结束时间', payload={'field': 'time_range'})


def _check_overlap(equip_id, start_time, end_time, exclude_slot_id=None):
    """
    检查同一设备下时间段是否与现有时间段重叠
    """
    query = TimeSlot.query.filter(TimeSlot.equip_id == equip_id)
    if exclude_slot_id:
        query = query.filter(TimeSlot.slot_id != exclude_slot_id)

    # 重叠条件：max(start1, start2) < min(end1, end2)
    conflict = query.filter(
        and_(TimeSlot.start_time < end_time, TimeSlot.end_time > start_time)
    ).first()

    if conflict:
        raise ValidationError('时间段与已有配置冲突', payload={'conflict_slot_id': conflict.slot_id})


def _check_equipment_exists(equip_id):
    equipment = Equipment.query.get(equip_id)
    if not equipment:
        raise NotFoundError('设备不存在', payload={'field': 'equip_id'})
    return equipment


def get_timeslots_by_equipment(equip_id, only_active=False):
    """
    获取设备的时间段列表
    """
    _check_equipment_exists(equip_id)
    query = TimeSlot.query.filter(TimeSlot.equip_id == equip_id)
    if only_active:
        query = query.filter(TimeSlot.is_active == 1)
    return query.order_by(TimeSlot.start_time.asc()).all()


def get_available_timeslots(equip_id, target_date=None):
    """
    获取设备可用时间段
    
    Args:
        equip_id: 设备ID
        target_date: 目标日期（可选），如果提供则排除该日期已被预约的时间段
    
    Returns:
        list: 可用时间段列表
    """
    _check_equipment_exists(equip_id)
    
    # 获取所有激活的时间段
    time_slots = get_timeslots_by_equipment(equip_id, only_active=True)
    
    # 如果没有指定日期，直接返回所有激活的时间段
    if not target_date:
        return time_slots
    
    # 如果指定了日期，需要排除已被预约的时间段
    if isinstance(target_date, str):
        try:
            target_date = datetime.fromisoformat(target_date).date()
        except:
            target_date = None
    
    if not target_date or not isinstance(target_date, date):
        # 日期格式无效，返回所有激活时间段
        return time_slots
    
    # 查询该日期上状态为待审(0)或已通过(1)的预约
    reservations = Reservation.query.filter(
        Reservation.equip_id == equip_id,
        Reservation.status.in_([0, 1]),
        Reservation.start_time.isnot(None),
        Reservation.end_time.isnot(None)
    ).all()
    
    # 过滤出该日期的预约
    date_reservations = []
    for res in reservations:
        if res.start_time and res.start_time.date() == target_date:
            date_reservations.append(res)
    
    # 如果没有该日期的预约，返回所有时间段
    if not date_reservations:
        return time_slots
    
    # 排除已被预约的时间段
    available_slots = []
    for slot in time_slots:
        is_available = True
        for res in date_reservations:
            # 检查时间段是否与预约冲突
            # 预约的开始时间和结束时间的时间部分
            res_start_time = res.start_time.time()
            res_end_time = res.end_time.time()
            
            # 如果时间段与预约时间有重叠，则不可用
            # 重叠条件：max(start1, start2) < min(end1, end2)
            if slot.start_time < res_end_time and slot.end_time > res_start_time:
                is_available = False
                break
        
        if is_available:
            available_slots.append(slot)
    
    return available_slots


def get_available_dates(equip_id, start_date=None, days=30):
    """
    获取设备的可用日期列表
    
    Args:
        equip_id: 设备ID
        start_date: 开始日期（可选），默认为今天
        days: 查询天数（默认30天）
    
    Returns:
        list: 可用日期列表（格式：YYYY-MM-DD）
    """
    _check_equipment_exists(equip_id)
    
    # 如果没有指定开始日期，使用今天
    if not start_date:
        start_date = datetime.now().date()
    elif isinstance(start_date, str):
        try:
            start_date = datetime.fromisoformat(start_date).date()
        except:
            start_date = datetime.now().date()
    
    # 获取所有激活的时间段
    time_slots = get_timeslots_by_equipment(equip_id, only_active=True)
    
    if not time_slots:
        # 如果没有配置时间段，返回空列表
        return []
    
    # 查询该设备在指定日期范围内的所有预约（待审或已通过）
    end_date = start_date + timedelta(days=days)
    reservations = Reservation.query.filter(
        Reservation.equip_id == equip_id,
        Reservation.status.in_([0, 1]),
        Reservation.start_time.isnot(None),
        Reservation.end_time.isnot(None),
        Reservation.start_time >= datetime.combine(start_date, datetime.min.time()),
        Reservation.start_time < datetime.combine(end_date, datetime.min.time())
    ).all()
    
    # 按日期组织预约
    date_reservations_map = {}
    for res in reservations:
        res_date = res.start_time.date()
        if res_date not in date_reservations_map:
            date_reservations_map[res_date] = []
        date_reservations_map[res_date].append(res)
    
    # 遍历日期范围，检查每天是否有可用时间段
    available_dates = []
    current_date = start_date
    
    while current_date < end_date:
        # 检查该日期是否有可用时间段
        date_reservations = date_reservations_map.get(current_date, [])
        
        if not date_reservations:
            # 如果该日期没有预约，说明所有时间段都可用
            available_dates.append(current_date.isoformat())
        else:
            # 检查是否有时间段没有被完全占用
            for slot in time_slots:
                is_slot_available = True
                for res in date_reservations:
                    res_start_time = res.start_time.time()
                    res_end_time = res.end_time.time()
                    
                    # 如果时间段与预约时间有重叠，则该时间段不可用
                    if slot.start_time < res_end_time and slot.end_time > res_start_time:
                        is_slot_available = False
                        break
                
                # 如果至少有一个时间段可用，该日期就可用
                if is_slot_available:
                    available_dates.append(current_date.isoformat())
                    break
        
        current_date += timedelta(days=1)
    
    return available_dates


def check_slot_usage(slot_id):
    """
    预留：检查时间段是否已有预约占用
    当前阶段返回 False，后续实现时用于阻止删除/修改时间范围
    """
    return False


def create_timeslot(data):
    """
    创建时间段
    """
    equip_id = data.get('equip_id')
    start_time = _normalize_time(data.get('start_time'))
    end_time = _normalize_time(data.get('end_time'))
    is_active = data.get('is_active', 1)

    _check_equipment_exists(equip_id)
    _validate_time_range(start_time, end_time)
    _check_overlap(equip_id, start_time, end_time)

    slot = TimeSlot(
        equip_id=equip_id,
        start_time=start_time,
        end_time=end_time,
        is_active=is_active
    )
    try:
        db.session.add(slot)
        db.session.commit()
        return slot
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f'创建时间段失败: {str(e)}')


def update_timeslot(slot_id, data):
    """
    更新时间段
    """
    slot = TimeSlot.query.get(slot_id)
    if not slot:
        raise NotFoundError('时间段不存在')

    # 预留占用检查
    if check_slot_usage(slot_id):
        raise ValidationError('该时间段已有关联预约，禁止修改时间范围', payload={'slot_id': slot_id})

    if 'equip_id' in data:
        equip_id = data.get('equip_id')
        _check_equipment_exists(equip_id)
        slot.equip_id = equip_id
    else:
        equip_id = slot.equip_id

    start_time = slot.start_time
    end_time = slot.end_time

    if 'start_time' in data:
        start_time = _normalize_time(data.get('start_time'))
    if 'end_time' in data:
        end_time = _normalize_time(data.get('end_time'))
    if start_time != slot.start_time or end_time != slot.end_time:
        _validate_time_range(start_time, end_time)
        _check_overlap(equip_id, start_time, end_time, exclude_slot_id=slot.slot_id)
        slot.start_time = start_time
        slot.end_time = end_time

    if 'is_active' in data:
        slot.is_active = data.get('is_active')

    try:
        db.session.commit()
        return slot
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f'更新时间段失败: {str(e)}')


def delete_timeslot(slot_id):
    """
    删除时间段
    """
    slot = TimeSlot.query.get(slot_id)
    if not slot:
        raise NotFoundError('时间段不存在')

    # 预留占用检查
    if check_slot_usage(slot_id):
        raise ValidationError('该时间段已有关联预约，禁止删除', payload={'slot_id': slot_id})

    try:
        equip_id = slot.equip_id
        db.session.delete(slot)
        db.session.commit()
        return equip_id
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f'删除时间段失败: {str(e)}')
