"""
测试预约服务的验证函数部分
包括：
- _validate_time_range: 验证时间范围
- _check_timeslot_availability: 检查时间段可用性
- _check_reservation_conflict: 检查预约冲突
"""
import pytest
from datetime import datetime, timedelta, time
from app.services.reservation_service import (
    _validate_time_range,
    _check_timeslot_availability,
    _check_reservation_conflict
)
from app.utils.exceptions import ValidationError
from app.models.equipment import Equipment
from app.models.timeslot import TimeSlot
from app.models.reservation import Reservation


class TestValidateTimeRange:
    """测试 _validate_time_range 函数"""
    
    def test_valid_time_range(self, app, future_datetime):
        """测试有效的时间范围"""
        start_time = future_datetime.replace(hour=10, minute=0)
        end_time = future_datetime.replace(hour=11, minute=0)
        
        # 不应该抛出异常
        _validate_time_range(start_time, end_time)
    
    def test_start_time_equals_end_time(self, app, future_datetime):
        """测试开始时间等于结束时间"""
        start_time = future_datetime.replace(hour=10, minute=0)
        end_time = start_time
        
        with pytest.raises(ValidationError) as exc_info:
            _validate_time_range(start_time, end_time)
        
        assert '开始时间必须早于结束时间' in exc_info.value.message
    
    def test_start_time_after_end_time(self, app, future_datetime):
        """测试开始时间晚于结束时间"""
        start_time = future_datetime.replace(hour=11, minute=0)
        end_time = future_datetime.replace(hour=10, minute=0)
        
        with pytest.raises(ValidationError) as exc_info:
            _validate_time_range(start_time, end_time)
        
        assert '开始时间必须早于结束时间' in exc_info.value.message
    
    def test_start_time_is_none(self, app, future_datetime):
        """测试开始时间为 None"""
        end_time = future_datetime.replace(hour=11, minute=0)
        
        with pytest.raises(ValidationError) as exc_info:
            _validate_time_range(None, end_time)
        
        assert '开始时间和结束时间不能为空' in exc_info.value.message
    
    def test_end_time_is_none(self, app, future_datetime):
        """测试结束时间为 None"""
        start_time = future_datetime.replace(hour=10, minute=0)
        
        with pytest.raises(ValidationError) as exc_info:
            _validate_time_range(start_time, None)
        
        assert '开始时间和结束时间不能为空' in exc_info.value.message
    
    def test_past_time(self, app):
        """测试过去的时间"""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow() - timedelta(minutes=30)
        
        with pytest.raises(ValidationError) as exc_info:
            _validate_time_range(start_time, end_time)
        
        assert '预约时间不能是过去的时间' in exc_info.value.message


class TestCheckTimeslotAvailability:
    """测试 _check_timeslot_availability 函数"""
    
    def test_valid_timeslot(self, app, db_session, sample_equipment, sample_timeslot, future_datetime):
        """测试有效的时间段"""
        start_time = future_datetime.replace(hour=10, minute=0)
        end_time = future_datetime.replace(hour=11, minute=0)
        
        # 不应该抛出异常
        _check_timeslot_availability(sample_equipment.id, start_time, end_time)
    
    def test_no_timeslot_configured(self, app, db_session, sample_equipment, future_datetime):
        """测试设备没有配置时间段"""
        start_time = future_datetime.replace(hour=10, minute=0)
        end_time = future_datetime.replace(hour=11, minute=0)
        
        with pytest.raises(ValidationError) as exc_info:
            _check_timeslot_availability(sample_equipment.id, start_time, end_time)
        
        assert '该设备没有配置可用时间段' in exc_info.value.message
    
    def test_time_outside_timeslot(self, app, db_session, sample_equipment, sample_timeslot, future_datetime):
        """测试预约时间不在时间段内"""
        # 时间段是 09:00-17:00，预约时间是 08:00-09:00
        start_time = future_datetime.replace(hour=8, minute=0)
        end_time = future_datetime.replace(hour=9, minute=0)
        
        with pytest.raises(ValidationError) as exc_info:
            _check_timeslot_availability(sample_equipment.id, start_time, end_time)
        
        assert '预约时间不在设备的可用时间段内' in exc_info.value.message
    
    def test_time_spanning_multiple_days(self, app, db_session, sample_equipment, sample_timeslot, future_datetime):
        """测试跨天的预约时间"""
        start_time = future_datetime.replace(hour=10, minute=0)
        end_time = (future_datetime + timedelta(days=1)).replace(hour=11, minute=0)
        
        with pytest.raises(ValidationError) as exc_info:
            _check_timeslot_availability(sample_equipment.id, start_time, end_time)
        
        assert '预约的开始时间和结束时间必须在同一天' in exc_info.value.message
    
    def test_time_partially_outside_timeslot(self, app, db_session, sample_equipment, sample_timeslot, future_datetime):
        """测试预约时间部分在时间段外"""
        # 时间段是 09:00-17:00，预约时间是 16:00-18:00
        start_time = future_datetime.replace(hour=16, minute=0)
        end_time = future_datetime.replace(hour=18, minute=0)
        
        with pytest.raises(ValidationError) as exc_info:
            _check_timeslot_availability(sample_equipment.id, start_time, end_time)
        
        assert '预约时间不在设备的可用时间段内' in exc_info.value.message
    
    def test_time_at_timeslot_boundary(self, app, db_session, sample_equipment, sample_timeslot, future_datetime):
        """测试预约时间正好在时间段边界"""
        # 时间段是 09:00-17:00，预约时间是 09:00-17:00
        start_time = future_datetime.replace(hour=9, minute=0)
        end_time = future_datetime.replace(hour=17, minute=0)
        
        # 应该通过验证
        _check_timeslot_availability(sample_equipment.id, start_time, end_time)
    
    def test_multiple_timeslots(self, app, db_session, sample_equipment, future_datetime):
        """测试多个时间段的情况"""
        # 创建两个时间段：09:00-12:00 和 14:00-17:00
        timeslot1 = TimeSlot(
            equip_id=sample_equipment.id,
            start_time=time(9, 0),
            end_time=time(12, 0),
            is_active=1
        )
        timeslot2 = TimeSlot(
            equip_id=sample_equipment.id,
            start_time=time(14, 0),
            end_time=time(17, 0),
            is_active=1
        )
        db_session.add_all([timeslot1, timeslot2])
        db_session.commit()
        
        # 测试在第一个时间段内
        start_time = future_datetime.replace(hour=10, minute=0)
        end_time = future_datetime.replace(hour=11, minute=0)
        _check_timeslot_availability(sample_equipment.id, start_time, end_time)
        
        # 测试在第二个时间段内
        start_time = future_datetime.replace(hour=15, minute=0)
        end_time = future_datetime.replace(hour=16, minute=0)
        _check_timeslot_availability(sample_equipment.id, start_time, end_time)
        
        # 测试在两个时间段之间的时间（应该失败）
        start_time = future_datetime.replace(hour=12, minute=30)
        end_time = future_datetime.replace(hour=13, minute=30)
        with pytest.raises(ValidationError):
            _check_timeslot_availability(sample_equipment.id, start_time, end_time)


class TestCheckReservationConflict:
    """测试 _check_reservation_conflict 函数"""
    
    def test_no_conflict(self, app, db_session, sample_equipment, future_datetime):
        """测试没有冲突的情况"""
        start_time = future_datetime.replace(hour=10, minute=0)
        end_time = future_datetime.replace(hour=11, minute=0)
        
        # 不应该抛出异常
        _check_reservation_conflict(sample_equipment.id, start_time, end_time)
    
    def test_conflict_with_pending_reservation(self, app, db_session, sample_equipment, sample_student, future_datetime):
        """测试与待审预约冲突"""
        # 创建一个待审预约：10:00-11:00
        existing_reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,  # 待审
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow()
        )
        db_session.add(existing_reservation)
        db_session.commit()
        
        # 尝试创建冲突的预约：10:30-11:30
        start_time = future_datetime.replace(hour=10, minute=30)
        end_time = future_datetime.replace(hour=11, minute=30)
        
        with pytest.raises(ValidationError) as exc_info:
            _check_reservation_conflict(sample_equipment.id, start_time, end_time)
        
        assert '预约时间与已有预约冲突' in exc_info.value.message
        assert 'conflicts' in exc_info.value.payload
    
    def test_conflict_with_approved_reservation(self, app, db_session, sample_equipment, sample_student, future_datetime):
        """测试与已通过预约冲突"""
        # 创建一个已通过预约：10:00-11:00
        existing_reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,  # 已通过
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow()
        )
        db_session.add(existing_reservation)
        db_session.commit()
        
        # 尝试创建冲突的预约：09:30-10:30
        start_time = future_datetime.replace(hour=9, minute=30)
        end_time = future_datetime.replace(hour=10, minute=30)
        
        with pytest.raises(ValidationError) as exc_info:
            _check_reservation_conflict(sample_equipment.id, start_time, end_time)
        
        assert '预约时间与已有预约冲突' in exc_info.value.message
    
    def test_no_conflict_with_rejected_reservation(self, app, db_session, sample_equipment, sample_student, future_datetime):
        """测试与已拒绝预约不冲突"""
        # 创建一个已拒绝预约：10:00-11:00
        existing_reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=2,  # 已拒绝
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow()
        )
        db_session.add(existing_reservation)
        db_session.commit()
        
        # 创建相同时间的预约应该不冲突
        start_time = future_datetime.replace(hour=10, minute=0)
        end_time = future_datetime.replace(hour=11, minute=0)
        
        # 不应该抛出异常
        _check_reservation_conflict(sample_equipment.id, start_time, end_time)
    
    def test_exclude_reservation_id(self, app, db_session, sample_equipment, sample_student, future_datetime):
        """测试排除指定预约ID（用于更新预约时）"""
        # 创建一个待审预约：10:00-11:00
        existing_reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,  # 待审
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow()
        )
        db_session.add(existing_reservation)
        db_session.commit()
        
        # 更新同一个预约的时间（排除自己）应该不冲突
        start_time = future_datetime.replace(hour=10, minute=30)
        end_time = future_datetime.replace(hour=11, minute=30)
        
        # 不应该抛出异常
        _check_reservation_conflict(
            sample_equipment.id,
            start_time,
            end_time,
            exclude_reservation_id=existing_reservation.id
        )
    
    def test_adjacent_times_no_conflict(self, app, db_session, sample_equipment, sample_student, future_datetime):
        """测试相邻时间不冲突"""
        # 创建一个预约：10:00-11:00
        existing_reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,  # 已通过
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow()
        )
        db_session.add(existing_reservation)
        db_session.commit()
        
        # 创建相邻的预约：11:00-12:00（不冲突）
        start_time = future_datetime.replace(hour=11, minute=0)
        end_time = future_datetime.replace(hour=12, minute=0)
        
        # 不应该抛出异常
        _check_reservation_conflict(sample_equipment.id, start_time, end_time)
    
    def test_overlapping_times_conflict(self, app, db_session, sample_equipment, sample_student, future_datetime):
        """测试重叠时间冲突"""
        # 创建一个预约：10:00-12:00
        existing_reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,  # 已通过
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=12, minute=0),
            apply_time=datetime.utcnow()
        )
        db_session.add(existing_reservation)
        db_session.commit()
        
        # 测试各种重叠情况
        conflict_cases = [
            (9, 0, 11, 0),   # 09:00-11:00（部分重叠）
            (11, 0, 13, 0),  # 11:00-13:00（部分重叠）
            (9, 0, 13, 0),   # 09:00-13:00（完全包含）
            (10, 30, 11, 30), # 10:30-11:30（完全被包含）
        ]
        
        for start_hour, start_min, end_hour, end_min in conflict_cases:
            start_time = future_datetime.replace(hour=start_hour, minute=start_min)
            end_time = future_datetime.replace(hour=end_hour, minute=end_min)
            
            with pytest.raises(ValidationError):
                _check_reservation_conflict(sample_equipment.id, start_time, end_time)
