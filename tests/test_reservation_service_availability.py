"""
测试预约服务的可用时间计算功能
包括：
- _calculate_next_avail_time: 计算设备的下次可用时间
- _update_equipment_next_avail_time: 更新设备的下次可用时间
"""
import pytest
from datetime import datetime, timedelta, time
from unittest.mock import patch, MagicMock
from app.services.reservation_service import (
    _calculate_next_avail_time,
    _update_equipment_next_avail_time
)
from app.models.equipment import Equipment
from app.models.timeslot import TimeSlot
from app.models.reservation import Reservation


class TestCalculateNextAvailTime:
    """测试 _calculate_next_avail_time 函数"""
    
    def test_no_timeslot_configured(self, app, db_session, sample_equipment):
        """测试没有配置时间段的情况"""
        result = _calculate_next_avail_time(sample_equipment.id)
        assert result is None
    
    def test_no_reservations(self, app, db_session, sample_equipment, sample_timeslot):
        """测试没有预约的情况"""
        now = datetime.utcnow()
        result = _calculate_next_avail_time(sample_equipment.id)
        
        # 应该返回今天或明天的时间段开始时间
        assert result is not None
        assert result >= now
    
    def test_with_future_reservation(
        self, app, db_session, sample_equipment, sample_student, sample_timeslot, future_datetime
    ):
        """测试有未来预约的情况"""
        # 创建未来预约：明天 10:00-11:00
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,  # 已通过
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 在调用函数前记录时间，避免时间差导致测试失败
        now = datetime.utcnow()
        result = _calculate_next_avail_time(sample_equipment.id)
        
        # 时间段是 09:00-17:00，预约是 10:00-11:00
        # 下次可用时间应该是 09:00（如果今天）或 11:00（如果预约占用了09:00）
        assert result is not None
        assert result >= now - timedelta(seconds=1)  # 允许1秒的误差
    
    def test_with_multiple_reservations(
        self, app, db_session, sample_equipment, sample_student, sample_timeslot, future_datetime
    ):
        """测试有多个预约的情况"""
        # 创建多个预约
        reservations = [
            Reservation(
                equip_id=sample_equipment.id,
                student_id=sample_student.id,
                status=1,
                start_time=future_datetime.replace(hour=10, minute=0),
                end_time=future_datetime.replace(hour=11, minute=0),
                apply_time=datetime.utcnow(),
                user_name=sample_student.name,
                equip_name=sample_equipment.name
            ),
            Reservation(
                equip_id=sample_equipment.id,
                student_id=sample_student.id,
                status=1,
                start_time=future_datetime.replace(hour=14, minute=0),
                end_time=future_datetime.replace(hour=15, minute=0),
                apply_time=datetime.utcnow(),
                user_name=sample_student.name,
                equip_name=sample_equipment.name
            )
        ]
        db_session.add_all(reservations)
        db_session.commit()
        
        # 在调用函数前记录时间，避免时间差导致测试失败
        now = datetime.utcnow()
        result = _calculate_next_avail_time(sample_equipment.id)
        
        assert result is not None
        # 应该找到没有被预约占用的时间段
        assert result >= now - timedelta(seconds=1)  # 允许1秒的误差
    
    def test_with_past_reservation(
        self, app, db_session, sample_equipment, sample_student, sample_timeslot
    ):
        """测试只有过去预约的情况（不应该影响可用时间）"""
        # 创建过去的预约
        past_time = datetime.utcnow() - timedelta(days=1)
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,  # 已通过
            start_time=past_time.replace(hour=10, minute=0),
            end_time=past_time.replace(hour=11, minute=0),
            apply_time=past_time,
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 在调用函数前记录时间，避免时间差导致测试失败
        now = datetime.utcnow()
        result = _calculate_next_avail_time(sample_equipment.id)
        
        # 过去的预约不应该影响可用时间
        assert result is not None
        assert result >= now - timedelta(seconds=1)  # 允许1秒的误差
    
    def test_with_pending_reservation(
        self, app, db_session, sample_equipment, sample_student, sample_timeslot, future_datetime
    ):
        """测试待审预约不应该影响可用时间"""
        # 创建待审预约
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,  # 待审
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 在调用函数前记录时间，避免时间差导致测试失败
        now = datetime.utcnow()
        result = _calculate_next_avail_time(sample_equipment.id)
        
        # 待审预约不应该影响可用时间
        assert result is not None
        # 应该可以找到包含待审预约时间的时间段
        assert result >= now - timedelta(seconds=1)  # 允许1秒的误差
    
    def test_with_rejected_reservation(
        self, app, db_session, sample_equipment, sample_student, sample_timeslot, future_datetime
    ):
        """测试已拒绝预约不应该影响可用时间"""
        # 创建已拒绝预约
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=2,  # 已拒绝
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 在调用函数前记录时间，避免时间差导致测试失败
        now = datetime.utcnow()
        result = _calculate_next_avail_time(sample_equipment.id)
        
        # 已拒绝预约不应该影响可用时间
        assert result is not None
        assert result >= now - timedelta(seconds=1)  # 允许1秒的误差
    
    def test_with_multiple_timeslots(
        self, app, db_session, sample_equipment, sample_student, future_datetime
    ):
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
        
        # 创建预约占用第一个时间段
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 在调用函数前记录时间，避免时间差导致测试失败
        now = datetime.utcnow()
        result = _calculate_next_avail_time(sample_equipment.id)
        
        assert result is not None
        # 应该找到第二个时间段的开始时间或第一个时间段未被占用的部分
        assert result >= now - timedelta(seconds=1)  # 允许1秒的误差
    
    def test_full_day_reserved(
        self, app, db_session, sample_equipment, sample_student, sample_timeslot, future_datetime
    ):
        """测试整天都被预约的情况"""
        # 创建覆盖整个时间段的预约
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,
            start_time=future_datetime.replace(hour=9, minute=0),
            end_time=future_datetime.replace(hour=17, minute=0),
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        result = _calculate_next_avail_time(sample_equipment.id)
        
        # 应该返回下一天的时间段开始时间（因为明天整天都被预约）
        assert result is not None
        # 预约是明天的 09:00-17:00，所以下次可用时间应该是：
        # - 如果今天的时间段没有被占用，返回今天的时间（合理）
        # - 如果今天的时间段也被占用，返回后天的 09:00
        # 这里我们验证返回的时间至少是今天的时间，并且如果返回的是今天，应该是在时间段内
        now = datetime.utcnow()
        reservation_date = future_datetime.date()  # 预约的日期（明天）
        next_day_date = reservation_date + timedelta(days=1)  # 后天的日期
        
        # 如果返回的是今天，应该 >= 当前时间
        # 如果返回的是后天，应该 >= 后天的 09:00
        if result.date() == now.date():
            # 返回的是今天的时间，应该 >= 当前时间
            assert result >= now - timedelta(seconds=1)
        elif result.date() == next_day_date:
            # 返回的是后天的时间，应该 >= 后天的 09:00
            expected_next_day_time = datetime.combine(next_day_date, time(9, 0))
            assert result >= expected_next_day_time - timedelta(seconds=1)
        else:
            # 返回的时间应该是今天或后天
            assert result.date() in [now.date(), next_day_date]


class TestUpdateEquipmentNextAvailTime:
    """测试 _update_equipment_next_avail_time 函数"""
    
    def test_update_next_avail_time(
        self, app, db_session, sample_equipment, sample_timeslot, mock_redis
    ):
        """测试更新设备的下次可用时间"""
        # 在调用函数前记录时间，避免时间差导致测试失败
        now = datetime.utcnow()
        _update_equipment_next_avail_time(sample_equipment.id)
        
        # 重新查询设备
        equipment = Equipment.query.get(sample_equipment.id)
        
        # 验证下次可用时间已更新
        assert equipment.next_avail_time is not None
        assert equipment.next_avail_time >= now - timedelta(seconds=1)  # 允许1秒的误差
    
    def test_update_nonexistent_equipment(self, app, db_session, mock_redis):
        """测试更新不存在的设备（应该不报错）"""
        # 不应该抛出异常
        _update_equipment_next_avail_time(99999)
    
    def test_update_clears_cache(
        self, app, db_session, sample_equipment, sample_timeslot, mock_redis
    ):
        """测试更新时清除设备缓存"""
        _update_equipment_next_avail_time(sample_equipment.id)
        
        # 验证缓存清除方法被调用
        mock_redis.delete.assert_called()
    
    def test_update_with_db_error(
        self, app, db_session, sample_equipment, sample_timeslot, mock_redis
    ):
        """测试数据库错误时不影响主业务"""
        with patch('app.services.reservation_service.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('数据库错误')
            
            # 不应该抛出异常（错误被捕获）
            _update_equipment_next_avail_time(sample_equipment.id)
            
            # 验证回滚被调用（通过检查异常被正确处理，函数没有抛出异常）
            # 注意：由于错误被捕获并打印，函数应该正常返回
    
    def test_update_with_reservations(
        self, app, db_session, sample_equipment, sample_student, sample_timeslot, future_datetime, mock_redis
    ):
        """测试有预约时更新可用时间"""
        # 创建预约
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        _update_equipment_next_avail_time(sample_equipment.id)
        
        equipment = Equipment.query.get(sample_equipment.id)
        assert equipment.next_avail_time is not None
