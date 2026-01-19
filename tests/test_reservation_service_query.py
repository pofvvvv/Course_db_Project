"""
测试预约服务的查询功能
包括：
- get_reservation_list: 获取预约列表
- get_reservation_by_id: 根据ID查询预约
"""
import pytest
from datetime import datetime, timedelta
from app.services.reservation_service import get_reservation_list, get_reservation_by_id
from app.utils.exceptions import NotFoundError
from app.models.reservation import Reservation


class TestGetReservationList:
    """测试 get_reservation_list 函数"""
    
    def test_get_all_reservations(
        self, app, db_session, sample_equipment, sample_student, sample_teacher, future_datetime
    ):
        """测试获取所有预约"""
        # 创建多个预约
        reservations = [
            Reservation(
                equip_id=sample_equipment.id,
                student_id=sample_student.id,
                status=0,
                apply_time=datetime.utcnow() - timedelta(hours=1),
                user_name=sample_student.name,
                equip_name=sample_equipment.name
            ),
            Reservation(
                equip_id=sample_equipment.id,
                teacher_id=sample_teacher.id,
                status=1,
                apply_time=datetime.utcnow() - timedelta(hours=2),
                user_name=sample_teacher.name,
                equip_name=sample_equipment.name
            ),
            Reservation(
                equip_id=sample_equipment.id,
                student_id=sample_student.id,
                status=2,
                apply_time=datetime.utcnow() - timedelta(hours=3),
                user_name=sample_student.name,
                equip_name=sample_equipment.name
            )
        ]
        db_session.add_all(reservations)
        db_session.commit()
        
        result = get_reservation_list()
        
        assert len(result) == 3
        # 应该按申请时间倒序排列
        assert result[0].apply_time > result[1].apply_time
        assert result[1].apply_time > result[2].apply_time
    
    def test_get_reservations_by_student_id(
        self, app, db_session, sample_equipment, sample_student, sample_teacher, future_datetime
    ):
        """测试按学生ID筛选预约"""
        # 创建学生的预约
        student_reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        # 创建教师的预约
        teacher_reservation = Reservation(
            equip_id=sample_equipment.id,
            teacher_id=sample_teacher.id,
            status=0,
            apply_time=datetime.utcnow(),
            user_name=sample_teacher.name,
            equip_name=sample_equipment.name
        )
        db_session.add_all([student_reservation, teacher_reservation])
        db_session.commit()
        
        result = get_reservation_list(
            user_id=sample_student.id,
            user_type='student'
        )
        
        assert len(result) == 1
        assert result[0].student_id == sample_student.id
        assert result[0].teacher_id is None
    
    def test_get_reservations_by_teacher_id(
        self, app, db_session, sample_equipment, sample_student, sample_teacher, future_datetime
    ):
        """测试按教师ID筛选预约"""
        # 创建学生的预约
        student_reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        # 创建教师的预约
        teacher_reservation = Reservation(
            equip_id=sample_equipment.id,
            teacher_id=sample_teacher.id,
            status=0,
            apply_time=datetime.utcnow(),
            user_name=sample_teacher.name,
            equip_name=sample_equipment.name
        )
        db_session.add_all([student_reservation, teacher_reservation])
        db_session.commit()
        
        result = get_reservation_list(
            user_id=sample_teacher.id,
            user_type='teacher'
        )
        
        assert len(result) == 1
        assert result[0].teacher_id == sample_teacher.id
        assert result[0].student_id is None
    
    def test_get_reservations_by_equip_id(
        self, app, db_session, sample_equipment, sample_student, future_datetime
    ):
        """测试按设备ID筛选预约"""
        from app.models.equipment import Equipment
        
        # 创建另一个设备
        equipment2 = Equipment(
            id=2,
            name='设备2',
            lab_id=1,
            category=1,
            status=1
        )
        db_session.add(equipment2)
        db_session.commit()
        
        # 创建不同设备的预约
        reservation1 = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        reservation2 = Reservation(
            equip_id=equipment2.id,
            student_id=sample_student.id,
            status=0,
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=equipment2.name
        )
        db_session.add_all([reservation1, reservation2])
        db_session.commit()
        
        result = get_reservation_list(equip_id=sample_equipment.id)
        
        assert len(result) == 1
        assert result[0].equip_id == sample_equipment.id
    
    def test_get_reservations_by_status(
        self, app, db_session, sample_equipment, sample_student, future_datetime
    ):
        """测试按状态筛选预约"""
        # 创建不同状态的预约
        reservations = [
            Reservation(
                equip_id=sample_equipment.id,
                student_id=sample_student.id,
                status=0,  # 待审
                apply_time=datetime.utcnow(),
                user_name=sample_student.name,
                equip_name=sample_equipment.name
            ),
            Reservation(
                equip_id=sample_equipment.id,
                student_id=sample_student.id,
                status=1,  # 已通过
                apply_time=datetime.utcnow(),
                user_name=sample_student.name,
                equip_name=sample_equipment.name
            ),
            Reservation(
                equip_id=sample_equipment.id,
                student_id=sample_student.id,
                status=2,  # 已拒绝
                apply_time=datetime.utcnow(),
                user_name=sample_student.name,
                equip_name=sample_equipment.name
            )
        ]
        db_session.add_all(reservations)
        db_session.commit()
        
        # 测试筛选待审状态
        result = get_reservation_list(status=0)
        assert len(result) == 1
        assert result[0].status == 0
        
        # 测试筛选已通过状态
        result = get_reservation_list(status=1)
        assert len(result) == 1
        assert result[0].status == 1
        
        # 测试筛选已拒绝状态
        result = get_reservation_list(status=2)
        assert len(result) == 1
        assert result[0].status == 2
    
    def test_get_reservations_with_multiple_filters(
        self, app, db_session, sample_equipment, sample_student, future_datetime
    ):
        """测试组合多个筛选条件"""
        # 创建多个预约
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
                user_name=sample_student.name,
                equip_name=sample_equipment.name
            )
        ]
        db_session.add_all(reservations)
        db_session.commit()
        
        # 组合筛选：学生ID + 状态
        result = get_reservation_list(
            user_id=sample_student.id,
            user_type='student',
            status=0
        )
        
        assert len(result) == 1
        assert result[0].student_id == sample_student.id
        assert result[0].status == 0
    
    def test_get_empty_reservation_list(self, app, db_session):
        """测试获取空列表"""
        result = get_reservation_list()
        assert len(result) == 0


class TestGetReservationById:
    """测试 get_reservation_by_id 函数"""
    
    def test_get_existing_reservation(
        self, app, db_session, sample_equipment, sample_student, future_datetime
    ):
        """测试获取存在的预约"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=0,
            apply_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name
        )
        db_session.add(reservation)
        db_session.commit()
        
        result = get_reservation_by_id(reservation.id)
        
        assert result is not None
        assert result.id == reservation.id
        assert result.equip_id == sample_equipment.id
        assert result.student_id == sample_student.id
    
    def test_get_nonexistent_reservation(self, app, db_session):
        """测试获取不存在的预约"""
        with pytest.raises(NotFoundError) as exc_info:
            get_reservation_by_id(99999)
        
        assert '预约不存在' in exc_info.value.message
    
    def test_get_reservation_with_all_fields(
        self, app, db_session, sample_equipment, sample_student, future_datetime
    ):
        """测试获取包含所有字段的预约"""
        reservation = Reservation(
            equip_id=sample_equipment.id,
            student_id=sample_student.id,
            status=1,
            apply_time=datetime.utcnow(),
            approver_id='A001',
            approve_time=datetime.utcnow(),
            user_name=sample_student.name,
            equip_name=sample_equipment.name,
            price=100.50,
            start_time=future_datetime.replace(hour=10, minute=0),
            end_time=future_datetime.replace(hour=11, minute=0),
            description='测试描述'
        )
        db_session.add(reservation)
        db_session.commit()
        
        result = get_reservation_by_id(reservation.id)
        
        assert result.status == 1
        assert result.approver_id == 'A001'
        assert result.approve_time is not None
        assert result.price == 100.50
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.description == '测试描述'
