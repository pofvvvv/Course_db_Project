"""
预约服务层
处理预约相关的业务逻辑
"""
from datetime import datetime, timedelta, date, time
from sqlalchemy import and_
from app import db
from app.models.reservation import Reservation
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.equipment import Equipment
from app.models.timeslot import TimeSlot
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.redis_client import redis_client


def _validate_time_range(start_time, end_time):
    """
    验证时间范围是否合理
    
    Args:
        start_time: 开始时间（datetime）
        end_time: 结束时间（datetime）
    
    Raises:
        ValidationError: 时间范围无效
    """
    if not start_time or not end_time:
        raise ValidationError('开始时间和结束时间不能为空', payload={'field': 'time_range'})
    
    if start_time >= end_time:
        raise ValidationError('开始时间必须早于结束时间', payload={'field': 'time_range'})
    
    # 检查预约时间不能是过去的时间
    if start_time < datetime.utcnow():
        raise ValidationError('预约时间不能是过去的时间', payload={'field': 'start_time'})


def _check_timeslot_availability(equip_id, start_time, end_time):
    """
    检查预约时间是否在设备的可用时间段内
    
    Args:
        equip_id: 设备ID
        start_time: 预约开始时间（datetime）
        end_time: 预约结束时间（datetime）
    
    Raises:
        ValidationError: 不在可用时间段内
    """
    # 获取设备的激活时间段
    time_slots = TimeSlot.query.filter(
        TimeSlot.equip_id == equip_id,
        TimeSlot.is_active == 1
    ).all()
    
    if not time_slots:
        raise ValidationError('该设备没有配置可用时间段', payload={'field': 'equip_id'})
    
    # 提取预约时间的日期和时间部分
    start_date = start_time.date()
    end_date = end_time.date()
    start_time_only = start_time.time()
    end_time_only = end_time.time()
    
    # 检查预约的开始时间和结束时间必须在同一天
    if start_date != end_date:
        raise ValidationError('预约的开始时间和结束时间必须在同一天', payload={'field': 'time_range'})
    
    # 检查预约时间是否在某个时间段内
    # 注意：时间段是每天重复的，所以只需要检查时间部分
    found_valid_slot = False
    for slot in time_slots:
        # 检查预约的开始时间和结束时间是否都在该时间段内
        # 修复：允许开始时间等于 slot.start_time，结束时间等于 slot.end_time（边界情况）
        # 同时处理秒和微秒的差异：如果结束时间只差几秒/微秒（小时和分钟相同），也认为是边界情况
        if slot.start_time <= start_time_only < slot.end_time:
            # 检查结束时间：允许等于 slot.end_time，或者只差几秒/微秒（边界情况）
            # 情况1：正常情况，结束时间在时间段内
            normal_case = slot.start_time < end_time_only <= slot.end_time
            # 情况2：边界情况，结束时间正好等于 slot.end_time
            exact_boundary = end_time_only == slot.end_time
            # 情况3：边界情况，结束时间超过 slot.end_time 但小时和分钟相同（只有秒/微秒不同）
            near_boundary = (end_time_only > slot.end_time and 
                            end_time_only.hour == slot.end_time.hour and 
                            end_time_only.minute == slot.end_time.minute)
            
            end_time_match = normal_case or exact_boundary or near_boundary
            
            if end_time_match:
                found_valid_slot = True
                break
    
    if not found_valid_slot:
        raise ValidationError(
            '预约时间不在设备的可用时间段内',
            payload={'field': 'time_range', 'available_slots': [
                {'start': str(slot.start_time), 'end': str(slot.end_time)}
                for slot in time_slots
            ]}
        )


def _check_reservation_conflict(equip_id, start_time, end_time, exclude_reservation_id=None):
    """
    检查预约时间是否与其他预约冲突
    
    Args:
        equip_id: 设备ID
        start_time: 预约开始时间（datetime）
        end_time: 预约结束时间（datetime）
        exclude_reservation_id: 排除的预约ID（用于更新预约时排除自己）
    
    Raises:
        ValidationError: 时间冲突
    """
    # 查询同一设备上状态为待审(0)或已通过(1)的预约
    query = Reservation.query.filter(
        Reservation.equip_id == equip_id,
        Reservation.status.in_([0, 1])  # 待审或已通过
    )
    
    if exclude_reservation_id:
        query = query.filter(Reservation.id != exclude_reservation_id)
    
    # 检查时间冲突：max(start1, start2) < min(end1, end2)
    conflicting_reservations = query.filter(
        and_(
            Reservation.start_time < end_time,
            Reservation.end_time > start_time
        )
    ).all()
    
    if conflicting_reservations:
        conflict_info = [
            {
                'id': r.id,
                'start_time': r.start_time.isoformat() if r.start_time else None,
                'end_time': r.end_time.isoformat() if r.end_time else None,
                'status': r.status
            }
            for r in conflicting_reservations
        ]
        raise ValidationError(
            '预约时间与已有预约冲突',
            payload={'field': 'time_range', 'conflicts': conflict_info}
        )


def create_reservation(data, current_user):
    """
    创建预约（学生/教师）
    
    Args:
        data: 预约数据字典
        current_user: 当前用户信息
    
    Returns:
        Reservation: 创建的预约对象
    
    Raises:
        ValidationError: 数据验证失败
    """
    # 验证设备是否存在
    equipment = Equipment.query.get(data.get('equip_id'))
    if not equipment:
        raise ValidationError('设备不存在', payload={'field': 'equip_id'})
    
    # 先检查用户类型（在检查时间段之前，确保错误消息正确）
    user_id = current_user['user_id']
    user_type = current_user['user_type']
    
    # 填充冗余字段
    user_name = None
    if user_type == 'student':
        student = Student.query.get(user_id)
        if not student:
            raise ValidationError('学生不存在')
        user_name = student.name
        data['student_id'] = user_id
        data['teacher_id'] = None
    elif user_type == 'teacher':
        teacher = Teacher.query.get(user_id)
        if not teacher:
            raise ValidationError('教师不存在')
        user_name = teacher.name
        data['student_id'] = None
        data['teacher_id'] = user_id
    else:
        raise ValidationError('用户类型不支持预约')
    
    # 获取预约时间
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    # 如果提供了时间，进行验证
    if start_time and end_time:
        # 确保是 datetime 对象
        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except:
                raise ValidationError('开始时间格式错误', payload={'field': 'start_time'})
        if isinstance(end_time, str):
            try:
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except:
                raise ValidationError('结束时间格式错误', payload={'field': 'end_time'})
        
        # 1. 验证时间范围
        _validate_time_range(start_time, end_time)
        
        # 2. 检查是否在可用时间段内
        _check_timeslot_availability(data.get('equip_id'), start_time, end_time)
        
        # 3. 检查是否与其他预约冲突
        _check_reservation_conflict(data.get('equip_id'), start_time, end_time)
    
    # 创建预约
    reservation = Reservation(
        equip_id=data['equip_id'],
        student_id=data.get('student_id'),
        teacher_id=data.get('teacher_id'),
        status=0,  # 待审
        apply_time=datetime.utcnow(),
        user_name=user_name,
        equip_name=equipment.name,
        price=data.get('price'),
        start_time=start_time,
        end_time=end_time,
        description=data.get('description')
    )
    
    try:
        db.session.add(reservation)
        db.session.commit()
        
        # 清除相关缓存
        _clear_reservation_cache()
        
        # 注意：创建预约时不需要更新 next_avail_time，因为状态是待审(0)
        # 只有审批通过后才会影响可用时间
        
        return reservation
    except ValidationError:
        # 重新抛出验证错误
        raise
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f'创建预约失败: {str(e)}')


def get_reservation_list(user_id=None, equip_id=None, status=None, user_type=None):
    """
    获取预约列表（支持筛选）
    
    Args:
        user_id: 用户ID筛选
        equip_id: 设备ID筛选
        status: 状态筛选
        user_type: 用户类型（student/teacher）
    
    Returns:
        list: 预约列表
    """
    query = Reservation.query
    
    # 按用户ID筛选
    if user_id and user_type:
        if user_type == 'student':
            query = query.filter(Reservation.student_id == user_id)
        elif user_type == 'teacher':
            query = query.filter(Reservation.teacher_id == user_id)
    
    # 按设备ID筛选
    if equip_id is not None:
        query = query.filter(Reservation.equip_id == equip_id)
    
    # 按状态筛选
    if status is not None:
        query = query.filter(Reservation.status == status)
    
    # 按申请时间倒序排列
    query = query.order_by(Reservation.apply_time.desc())
    
    return query.all()


def get_reservation_by_id(reservation_id):
    """
    根据 ID 查询预约详情
    
    Args:
        reservation_id: 预约ID
    
    Returns:
        Reservation: 预约对象
    
    Raises:
        NotFoundError: 预约不存在
    """
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        raise NotFoundError('预约不存在')
    return reservation


def update_reservation_status(reservation_id, status, approver_id=None):
    """
    更新预约状态（审批）
    
    Args:
        reservation_id: 预约ID
        status: 新状态
        approver_id: 审批人ID
    
    Returns:
        Reservation: 更新后的预约对象
    
    Raises:
        NotFoundError: 预约不存在
        ValidationError: 状态更新失败
    """
    reservation = get_reservation_by_id(reservation_id)
    
    # 验证状态流转
    valid_transitions = {
        0: [1, 2, 3],  # 待审 → 通过/拒绝/取消
        1: [3],        # 通过 → 取消
        2: [],         # 拒绝 → 无
        3: []          # 取消 → 无
    }
    
    old_status = reservation.status
    if status not in valid_transitions.get(reservation.status, []):
        raise ValidationError(f'无效的状态流转: {reservation.status} -> {status}')
    
    # 更新状态
    reservation.status = status
    if status in [1, 2]:  # 审批通过或拒绝
        reservation.approver_id = approver_id
        reservation.approve_time = datetime.utcnow()
        
    # 更新设备状态
    equipment = Equipment.query.get(reservation.equip_id)
    if equipment:
        # 如果审批通过，将设备设为使用中 (2)
        if status == 1 and old_status == 0:
            equipment.status = 2
        # 如果已通过的预约被取消，将设备设为可用 (1)
        elif status == 3 and old_status == 1:
            equipment.status = 1
    
    try:
        db.session.commit()
        
        # 更新设备的下次可用时间
        # 当预约状态变化时（通过/取消），需要重新计算可用时间
        if equipment and status in [1, 3]:  # 审批通过或取消
            _update_equipment_next_avail_time(equipment.id)
        
        # 清除设备缓存，确保前端设备详情页能看到最新状态
        if equipment:
            redis_client.delete(f'api:equipment:detail:{equipment.id}')
            
            # 清除设备列表缓存，确保设备列表页状态同步更新
            try:
                client = redis_client.get_client()
                keys = client.keys('api:equipment:list:*')
                if keys:
                    redis_client.delete(*keys)
            except Exception as e:
                print(f"Clear equipment list cache failed: {e}")
            
        # 清除相关缓存
        _clear_reservation_cache(reservation_id=reservation_id)
        
        return reservation
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f'更新预约状态失败: {str(e)}')


def delete_reservation(reservation_id):
    """
    删除预约
    
    Args:
        reservation_id: 预约ID
    
    Returns:
        bool: 删除成功返回 True
    
    Raises:
        NotFoundError: 预约不存在
        ValidationError: 删除失败
    """
    reservation = get_reservation_by_id(reservation_id)
    equip_id = reservation.equip_id
    
    try:
        db.session.delete(reservation)
        db.session.commit()
        
        # 如果删除的是已通过的预约，需要更新设备的下次可用时间
        if reservation.status == 1:
            _update_equipment_next_avail_time(equip_id)
        
        # 清除相关缓存
        _clear_reservation_cache(reservation_id=reservation_id)
        
        return True
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f'删除预约失败: {str(e)}')


def _calculate_next_avail_time(equip_id):
    """
    计算设备的下次可用时间
    
    算法：
    1. 获取设备的所有激活时间段
    2. 获取设备的所有已通过预约（status=1），按开始时间排序
    3. 从当前时间开始，查找第一个没有被预约占用的时间段
    
    Args:
        equip_id: 设备ID
    
    Returns:
        datetime: 下次可用时间，如果没有可用时间则返回 None
    """
    # 获取设备的激活时间段
    time_slots = TimeSlot.query.filter(
        TimeSlot.equip_id == equip_id,
        TimeSlot.is_active == 1
    ).order_by(TimeSlot.start_time).all()
    
    if not time_slots:
        # 如果没有配置时间段，返回 None
        return None
    
    # 获取设备的所有已通过预约（status=1），按开始时间排序
    active_reservations = Reservation.query.filter(
        Reservation.equip_id == equip_id,
        Reservation.status == 1,  # 已通过
        Reservation.start_time.isnot(None),
        Reservation.end_time.isnot(None),
        Reservation.end_time >= datetime.utcnow()  # 只考虑未来的预约
    ).order_by(Reservation.start_time).all()
    
    now = datetime.utcnow()
    today = now.date()
    current_time = now.time()
    
    # 查找未来30天内的可用时间
    for day_offset in range(30):
        check_date = today + timedelta(days=day_offset)
        
        # 如果是今天，从当前时间开始查找；否则从当天的第一个时间段开始
        for slot in time_slots:
            slot_start_datetime = datetime.combine(check_date, slot.start_time)
            slot_end_datetime = datetime.combine(check_date, slot.end_time)
            
            # 如果是今天且时间段已过，跳过
            if day_offset == 0 and slot_end_datetime <= now:
                continue
            
            # 检查这个时间段是否被预约占用
            is_occupied = False
            for reservation in active_reservations:
                # 检查时间段是否与预约冲突
                if reservation.start_time and reservation.end_time:
                    # 时间段冲突：max(start1, start2) < min(end1, end2)
                    if max(slot_start_datetime, reservation.start_time) < \
                       min(slot_end_datetime, reservation.end_time):
                        is_occupied = True
                        break
            
            # 如果时间段没有被占用，这就是下次可用时间
            if not is_occupied:
                # 如果是今天且开始时间已过，返回当前时间；否则返回时间段开始时间
                if day_offset == 0 and slot_start_datetime < now:
                    return now
                return slot_start_datetime
    
    # 如果30天内都没有可用时间，返回 None
    return None


def _update_equipment_next_avail_time(equip_id):
    """
    更新设备的下次可用时间
    
    Args:
        equip_id: 设备ID
    """
    equipment = Equipment.query.get(equip_id)
    if not equipment:
        return
    
    next_avail_time = _calculate_next_avail_time(equip_id)
    equipment.next_avail_time = next_avail_time
    
    try:
        db.session.commit()
        # 清除设备缓存
        redis_client.delete(f'api:equipment:detail:{equip_id}')
    except Exception as e:
        # 避免更新失败影响主业务
        print(f"Update next_avail_time failed: {e}")
        db.session.rollback()


def _clear_reservation_cache(reservation_id=None):
    """
    清除预约相关缓存
    
    Args:
        reservation_id: 预约ID，如果提供则清除该预约的详情缓存
    """
    # 清除详情缓存
    if reservation_id:
        redis_client.delete(f'api:reservation:detail:{reservation_id}')
    
    # 清除列表缓存
    try:
        client = redis_client.get_client()
        # 清除用户预约列表缓存
        keys = client.keys('api:reservation:list:*')
        if keys:
            redis_client.delete(*keys)
        # 清除管理员预约列表缓存
        admin_keys = client.keys('api:admin:reservation:list:*')
        if admin_keys:
            redis_client.delete(*admin_keys)
    except Exception as e:
        # 避免缓存操作失败影响主业务
        print(f"Clear cache failed: {e}")