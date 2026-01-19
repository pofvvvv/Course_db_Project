"""
测试预约服务的更新预约状态功能
包括 update_reservation_status 函数的各种场景
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.services.reservation_service import update_reservation_status
from app.utils.exceptions import ValidationError, NotFoundError
from app.models.reservation import Reservation
from app.models.equipment import Equipment


class TestUpdateReservationStatus:
    """测试 update_reservation_status 函数"""
    
    def test_approve_pending_reservation(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试审批通过待审预约"""
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
        
        result = update_reservation_status(
            reservation.id,
            status=1,  # 通过
            approver_id='A001'
        )
        
        assert result.status == 1
        assert result.approver_id == 'A001'
        assert result.approve_time is not None
        
        # 验证设备状态更新为使用中
        equipment = Equipment.query.get(sample_equipment.id)
        assert equipment.status == 2  # 使用中
    
    def test_reject_pending_reservation(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试拒绝待审预约"""
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
        
        result = update_reservation_status(
            reservation.id,
            status=2,  # 拒绝
            approver_id='A001'
        )
        
        assert result.status == 2
        assert result.approver_id == 'A001'
        assert result.approve_time is not None
        
        # 设备状态不应该改变（因为预约被拒绝）
        equipment = Equipment.query.get(sample_equipment.id)
        assert equipment.status == 1  # 保持可用状态
    
    def test_cancel_pending_reservation(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试取消待审预约"""
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
        
        result = update_reservation_status(reservation.id, status=3)  # 取消
        
        assert result.status == 3
    
    def test_cancel_approved_reservation(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试取消已通过的预约"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,  # 已通过
            apply_time=datetime.utcnow(),
            approver_id='A001',
            approve_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        # 设置设备为使用中
        sample_equipment.status = 2
        db_session.commit()
        
        result = update_reservation_status(reservation.id, status=3)  # 取消
        
        assert result.status == 3
        
        # 验证设备状态恢复为可用
        equipment = Equipment.query.get(sample_equipment.id)
        assert equipment.status == 1  # 可用
    
    def test_invalid_status_transition_pending_to_rejected(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试无效的状态流转：待审 -> 已拒绝 -> 已通过（不允许）"""
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
        
        # 先拒绝
        update_reservation_status(reservation.id, status=2, approver_id='A001')
        
        # 尝试从已拒绝状态改为已通过（不允许）
        with pytest.raises(ValidationError) as exc_info:
            update_reservation_status(reservation.id, status=1)
        
        assert '无效的状态流转' in exc_info.value.message
    
    def test_invalid_status_transition_approved_to_pending(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试无效的状态流转：已通过 -> 待审（不允许）"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,  # 已通过
            apply_time=datetime.utcnow(),
            approver_id='A001',
            approve_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        with pytest.raises(ValidationError) as exc_info:
            update_reservation_status(reservation.id, status=0)
        
        assert '无效的状态流转' in exc_info.value.message
    
    def test_invalid_status_transition_cancelled_to_approved(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试无效的状态流转：已取消 -> 已通过（不允许）"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=3,  # 已取消
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        with pytest.raises(ValidationError) as exc_info:
            update_reservation_status(reservation.id, status=1)
        
        assert '无效的状态流转' in exc_info.value.message
    
    def test_update_nonexistent_reservation(self, app, db_session, mock_redis):
        """测试更新不存在的预约"""
        with pytest.raises(NotFoundError) as exc_info:
            update_reservation_status(99999, status=1)
        
        assert '预约不存在' in exc_info.value.message
    
    def test_update_without_approver_id(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试更新状态时不提供审批人ID"""
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
        
        result = update_reservation_status(reservation.id, status=1)
        
        assert result.status == 1
        assert result.approver_id is None
    
    def test_update_status_updates_equipment_next_avail_time(
        self, app, db_session, sample_equipment, sample_student, sample_timeslot, future_datetime, mock_redis
    ):
        """测试更新状态时更新设备的下次可用时间"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,  # 待审
            apply_time=datetime.utcnow(),
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 审批通过
        with patch('app.services.reservation_service._update_equipment_next_avail_time') as mock_update:
            update_reservation_status(reservation.id, status=1, approver_id='A001')
            
            # 验证更新可用时间的函数被调用
            mock_update.assert_called_once_with(sample_equipment.id)
    
    def test_update_status_clears_cache(
        self, app, db_session, sample_equipment, sample_student, future_datetime, mock_redis
    ):
        """测试更新状态时清除缓存"""
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
        
        update_reservation_status(reservation.id, status=1, approver_id='A001')
        
        # 验证缓存清除方法被调用
        assert mock_redis.delete.called
    
    def test_update_status_db_rollback_on_error(
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
                update_reservation_status(reservation.id, status=1)
            
            assert '更新预约状态失败' in exc_info.value.message
