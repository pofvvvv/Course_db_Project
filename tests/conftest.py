"""
测试配置文件
提供 pytest fixtures 和测试工具函数
"""
import pytest
from datetime import datetime, timedelta, time
from unittest.mock import Mock, patch, MagicMock
from app import create_app, db
from app.models.equipment import Equipment
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.timeslot import TimeSlot
from app.models.reservation import Reservation


@pytest.fixture(scope='function')
def app():
    """创建测试应用实例"""
    app = create_app('testing')
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        yield app
        # 清理：删除所有表
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """提供数据库会话"""
    yield db.session
    db.session.rollback()


@pytest.fixture
def mock_redis():
    """模拟 Redis 客户端"""
    with patch('app.services.reservation_service.redis_client') as mock_redis:
        mock_client = MagicMock()
        mock_redis.get_client.return_value = mock_client
        mock_client.keys.return_value = []
        # 确保 delete 方法可以被调用
        mock_redis.delete = MagicMock(return_value=1)
        yield mock_redis


@pytest.fixture
def sample_equipment(db_session):
    """创建示例设备"""
    equipment = Equipment(
        id=1,
        name='测试设备',
        lab_id=1,
        category=1,
        status=1
    )
    db_session.add(equipment)
    db_session.commit()
    return equipment


@pytest.fixture
def sample_student(db_session):
    """创建示例学生"""
    student = Student(
        id='S001',
        name='测试学生',
        dept='计算机学院',
        lab_id=1
    )
    db_session.add(student)
    db_session.commit()
    return student


@pytest.fixture
def sample_teacher(db_session):
    """创建示例教师"""
    teacher = Teacher(
        id='T001',
        name='测试教师',
        dept='计算机学院',
        lab_id=1
    )
    db_session.add(teacher)
    db_session.commit()
    return teacher


@pytest.fixture
def sample_timeslot(db_session, sample_equipment):
    """创建示例时间段"""
    timeslot = TimeSlot(
        equip_id=sample_equipment.id,
        start_time=time(9, 0),  # 09:00
        end_time=time(17, 0),   # 17:00
        is_active=1
    )
    db_session.add(timeslot)
    db_session.commit()
    return timeslot


@pytest.fixture
def future_datetime():
    """返回未来的日期时间"""
    return datetime.utcnow() + timedelta(days=1)


@pytest.fixture
def sample_reservation_data(future_datetime):
    """示例预约数据"""
    return {
        'equip_id': 1,
        'start_time': future_datetime.replace(hour=10, minute=0),
        'end_time': future_datetime.replace(hour=11, minute=0),
        'description': '测试预约',
        'price': 100.00
    }


@pytest.fixture
def sample_current_user_student(sample_student):
    """示例学生用户信息"""
    return {
        'user_id': sample_student.id,
        'user_type': 'student'
    }


@pytest.fixture
def sample_current_user_teacher(sample_teacher):
    """示例教师用户信息"""
    return {
        'user_id': sample_teacher.id,
        'user_type': 'teacher'
    }
