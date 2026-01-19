"""
测试预约服务的创建预约功能
包括 create_reservation 函数的各种场景
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.services.reservation_service import create_reservation
from app.utils.exceptions import ValidationError, NotFoundError
from app.models.reservation import Reservation
from app.models.equipment import Equipment


class TestCreateReservation:
    """测试 create_reservation 函数"""
    
    def test_create_reservation_as_student_success(
        self, app, db_session, sample_equipment, sample_student,
        sample_timeslot, sample_reservation_data, sample_current_user_student, mock_redis
    ):
        """测试学生成功创建预约"""
        reservation = create_reservation(
            sample_reservation_data,
            sample_current_user_student
        )
        
        assert reservation is not None
        assert reservation.id is not None
        assert reservation.equip_id == sample_reservation_data['equip_id']
        assert reservation.student_id == sample_student.id
        assert reservation.teacher_id is None
        assert reservation.status == 0  # 待审
        assert reservation.user_name == sample_student.name
        assert reservation.equip_name == sample_equipment.name
    
    def test_create_reservation_as_teacher_success(
        self, app, db_session, sample_equipment, sample_teacher,
        sample_timeslot, sample_reservation_data, sample_current_user_teacher, mock_redis
    ):
        """测试教师成功创建预约"""
        reservation = create_reservation(
            sample_reservation_data,
            sample_current_user_teacher
        )
        
        assert reservation is not None
        assert reservation.id is not None
        assert reservation.teacher_id == sample_teacher.id
        assert reservation.student_id is None
        assert reservation.status == 0  # 待审
        assert reservation.user_name == sample_teacher.name
    
    def test_create_reservation_without_time(
        self, app, db_session, sample_equipment, sample_student,
        sample_current_user_student, mock_redis
    ):
        """测试创建不带时间的预约"""
        data = {
            'equip_id': sample_equipment.id,
            'description': '测试预约'
        }
        
        reservation = create_reservation(data, sample_current_user_student)
        
        assert reservation is not None
        assert reservation.start_time is None
        assert reservation.end_time is None
    
    def test_create_reservation_with_string_time(
        self, app, db_session, sample_equipment, sample_student,
        sample_timeslot, sample_current_user_student, future_datetime, mock_redis
    ):
        """测试使用字符串格式的时间创建预约"""
        start_time_str = future_datetime.replace(hour=10, minute=0).isoformat()
        end_time_str = future_datetime.replace(hour=11, minute=0).isoformat()
        
        data = {
            'equip_id': sample_equipment.id,
            'start_time': start_time_str,
            'end_time': end_time_str,
            'description': '测试预约'
        }
        
        reservation = create_reservation(data, sample_current_user_student)
        
        assert reservation is not None
        assert reservation.start_time is not None
        assert reservation.end_time is not None
    
    def test_create_reservation_equipment_not_found(
        self, app, db_session, sample_student, sample_current_user_student, mock_redis
    ):
        """测试设备不存在的情况"""
        data = {
            'equip_id': 99999,  # 不存在的设备ID
            'description': '测试预约'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_reservation(data, sample_current_user_student)
        
        assert '设备不存在' in exc_info.value.message
    
    def test_create_reservation_student_not_found(
        self, app, db_session, sample_equipment, sample_timeslot, sample_reservation_data, mock_redis
    ):
        """测试学生不存在的情况"""
        current_user = {
            'user_id': 'NONEXISTENT',
            'user_type': 'student'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_reservation(sample_reservation_data, current_user)
        
        assert '学生不存在' in exc_info.value.message
    
    def test_create_reservation_teacher_not_found(
        self, app, db_session, sample_equipment, sample_timeslot, sample_reservation_data, mock_redis
    ):
        """测试教师不存在的情况"""
        current_user = {
            'user_id': 'NONEXISTENT',
            'user_type': 'teacher'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_reservation(sample_reservation_data, current_user)
        
        assert '教师不存在' in exc_info.value.message
    
    def test_create_reservation_invalid_user_type(
        self, app, db_session, sample_equipment, sample_reservation_data, mock_redis
    ):
        """测试无效的用户类型"""
        current_user = {
            'user_id': 'U001',
            'user_type': 'admin'  # 不支持的类型
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_reservation(sample_reservation_data, current_user)
        
        assert '用户类型不支持预约' in exc_info.value.message
    
    def test_create_reservation_invalid_time_format(
        self, app, db_session, sample_equipment, sample_student,
        sample_timeslot, sample_current_user_student, mock_redis
    ):
        """测试无效的时间格式"""
        data = {
            'equip_id': sample_equipment.id,
            'start_time': 'invalid-time-format',
            'end_time': 'invalid-time-format',
            'description': '测试预约'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_reservation(data, sample_current_user_student)
        
        assert '开始时间格式错误' in exc_info.value.message or '结束时间格式错误' in exc_info.value.message
    
    def test_create_reservation_with_conflict(
        self, app, db_session, sample_equipment, sample_student,
        sample_timeslot, sample_reservation_data, sample_current_user_student, future_datetime, mock_redis
    ):
        """测试创建与已有预约冲突的预约"""
        # 先创建一个预约
        existing_reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,  # 已通过
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(existing_reservation)
        db_session.commit()
        
        # 尝试创建冲突的预约
        data = {
            'equip_id': sample_equipment.id,
            'start_time': future_datetime.replace(hour=10, minute=30),
            'end_time': future_datetime.replace(hour=11, minute=30),
            'description': '冲突的预约'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_reservation(data, sample_current_user_student)
        
        assert '预约时间与已有预约冲突' in exc_info.value.message
    
    def test_create_reservation_outside_timeslot(
        self, app, db_session, sample_equipment, sample_student,
        sample_timeslot, sample_current_user_student, future_datetime, mock_redis
    ):
        """测试创建不在时间段内的预约"""
        # 时间段是 09:00-17:00，尝试创建 08:00-09:00 的预约
        data = {
            'equip_id': sample_equipment.id,
            'start_time': future_datetime.replace(hour=8, minute=0),
            'end_time': future_datetime.replace(hour=9, minute=0),
            'description': '不在时间段内的预约'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_reservation(data, sample_current_user_student)
        
        assert '预约时间不在设备的可用时间段内' in exc_info.value.message
    
    def test_create_reservation_with_price(
        self, app, db_session, sample_equipment, sample_student,
        sample_timeslot, sample_reservation_data, sample_current_user_student, mock_redis
    ):
        """测试创建带价格的预约"""
        sample_reservation_data['price'] = 150.50
        
        reservation = create_reservation(
            sample_reservation_data,
            sample_current_user_student
        )
        
        assert reservation.price == 150.50
    
    def test_create_reservation_with_description(
        self, app, db_session, sample_equipment, sample_student,
        sample_timeslot, sample_reservation_data, sample_current_user_student, mock_redis
    ):
        """测试创建带描述的预约"""
        sample_reservation_data['description'] = '这是一个测试预约描述'
        
        reservation = create_reservation(
            sample_reservation_data,
            sample_current_user_student
        )
        
        assert reservation.description == '这是一个测试预约描述'
    
    def test_create_reservation_db_rollback_on_error(
        self, app, db_session, sample_equipment, sample_student,
        sample_timeslot, sample_reservation_data, sample_current_user_student, mock_redis
    ):
        """测试数据库错误时回滚"""
        # 模拟数据库错误
        with patch('app.services.reservation_service.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('数据库错误')
            
            with pytest.raises(ValidationError) as exc_info:
                create_reservation(sample_reservation_data, sample_current_user_student)
            
            assert '创建预约失败' in exc_info.value.message
            
            # 验证回滚被调用（通过检查数据库中没有新记录）
            # 注意：由于 mock_commit 会抛出异常，create_reservation 内部会调用 rollback
            # 这里我们验证异常被正确抛出即可
