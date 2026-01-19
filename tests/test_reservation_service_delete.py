"""
测试预约服务的删除预约功能
包括 delete_reservation 函数的各种场景
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.services.reservation_service import delete_reservation, get_reservation_by_id
from app.utils.exceptions import NotFoundError, ValidationError
from app.models.reservation import Reservation


class TestDeleteReservation:
    """测试 delete_reservation 函数"""
    
    def test_delete_existing_reservation(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试删除存在的预约"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,  # 待审
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        reservation_id = reservation.id
        
        result = delete_reservation(reservation_id)
        
        assert result is True
        
        # 验证预约已被删除
        with pytest.raises(NotFoundError):
            get_reservation_by_id(reservation_id)
    
    def test_delete_nonexistent_reservation(self, app, db_session, mock_redis):
        """测试删除不存在的预约"""
        with pytest.raises(NotFoundError) as exc_info:
            delete_reservation(99999)
        
        assert '预约不存在' in exc_info.value.message
    
    def test_delete_approved_reservation_updates_equipment(
        self, app, db_session, sample_equipment, sample_student, sample_timeslot, future_datetime, mock_redis
    ):
        """测试删除已通过的预约时更新设备可用时间"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,  # 已通过
            apply_time=datetime.utcnow(),
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            approver_id='A001',
            approve_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 删除预约
        with patch('app.services.reservation_service._update_equipment_next_avail_time') as mock_update:
            delete_reservation(reservation.id)
            
            # 验证更新可用时间的函数被调用
            mock_update.assert_called_once_with(sample_equipment.id)
    
    def test_delete_pending_reservation_no_update(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试删除待审预约时不更新设备可用时间"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,  # 待审
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 删除预约
        with patch('app.services.reservation_service._update_equipment_next_avail_time') as mock_update:
            delete_reservation(reservation.id)
            
            # 验证更新可用时间的函数没有被调用（因为状态是待审）
            mock_update.assert_not_called()
    
    def test_delete_reservation_clears_cache(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试删除预约时清除缓存"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,  # 待审
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        delete_reservation(reservation.id)
        
        # 验证缓存清除方法被调用
        assert mock_redis.delete.called
    
    def test_delete_reservation_db_rollback_on_error(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试数据库错误时回滚"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,  # 待审
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 模拟数据库错误
        with patch('app.services.reservation_service.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('数据库错误')
            
            with pytest.raises(ValidationError) as exc_info:
                delete_reservation(reservation.id)
            
            assert '删除预约失败' in exc_info.value.message
            
            # 验证预约仍然存在（因为回滚了）
            result = get_reservation_by_id(reservation.id)
            assert result is not None
    
    def test_delete_multiple_reservations(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试删除多个预约"""
        reservations = [
            Reservation(
                equip_id=sample_equipment.id,
                student_id=sample_student.id,
                status=0,
                apply_time=datetime.utcnow(),
                user_name=sample_student.name,
                equip_name=sample_equipment.name
            ),
            Reservation(
                equip_id=sample_equipment.id,
                student_id=sample_student.id,
                status=1,
                apply_time=datetime.utcnow(),
                approver_id='A001',
                approve_time=datetime.utcnow(),
                user_name=sample_student.name,
                equip_name=sample_equipment.name
            )
        ]
        db_session.add_all(reservations)
        db_session.commit()
        
        reservation_ids = [r.id for r in reservations]
        
        # 删除第一个预约
        delete_reservation(reservation_ids[0])
        with pytest.raises(NotFoundError):
            get_reservation_by_id(reservation_ids[0])
        
        # 第二个预约应该仍然存在
        result = get_reservation_by_id(reservation_ids[1])
        assert result is not None
        
        # 删除第二个预约
        delete_reservation(reservation_ids[1])
        with pytest.raises(NotFoundError):
            get_reservation_by_id(reservation_ids[1])
