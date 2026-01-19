# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建完整的测试数据
"""
from app import create_app, db
from app.models.laboratory import Laboratory
from app.models.equipment import Equipment
from app.models.timeslot import TimeSlot
from app.models.admin import Admin
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.reservation import Reservation
from app.models.auditlog import AuditLog
from werkzeug.security import generate_password_hash
from datetime import datetime, time, timedelta

def init_database():
    app = create_app()
    with app.app_context():
        print("=== 开始初始化数据库 ===")
        
        # 清空所有表（按外键顺序）
        print("清空现有数据...")
        db.session.query(AuditLog).delete()
        db.session.query(Reservation).delete()
        db.session.query(TimeSlot).delete()
        db.session.query(Equipment).delete()
        db.session.query(Student).delete()
        db.session.query(Teacher).delete()
        db.session.query(Admin).delete()
        db.session.query(Laboratory).delete()
        db.session.commit()
        
        # 1. 创建实验室
        print("创建实验室...")
        labs = [
            Laboratory(id=1, name='计算机科学实验室', location='理工楼A101'),
            Laboratory(id=2, name='人工智能实验室', location='理工楼A201'),
            Laboratory(id=3, name='网络安全实验室', location='理工楼B101'),
            Laboratory(id=4, name='大数据分析实验室', location='理工楼B201'),
            Laboratory(id=5, name='物联网实验室', location='理工楼C101'),
        ]
        db.session.add_all(labs)
        db.session.commit()
        
        # 2. 创建管理员
        print("创建管理员...")
        admins = [
            Admin(id='admin001', name='系统管理员', password_hash=generate_password_hash('123456'), manage_scope=1),
            Admin(id='admin002', name='设备管理员', password_hash=generate_password_hash('123456'), manage_scope=2),
        ]
        db.session.add_all(admins)
        db.session.commit()
        
        # 3. 创建教师
        print("创建教师...")
        teachers = [
            Teacher(id='T001', name='张教授', password_hash=generate_password_hash('123456'), dept='计算机学院', lab_id=1),
            Teacher(id='T002', name='李教授', password_hash=generate_password_hash('123456'), dept='计算机学院', lab_id=2),
            Teacher(id='T003', name='王教授', password_hash=generate_password_hash('123456'), dept='信息学院', lab_id=3),
            Teacher(id='T004', name='刘教授', password_hash=generate_password_hash('123456'), dept='信息学院', lab_id=4),
            Teacher(id='T005', name='陈教授', password_hash=generate_password_hash('123456'), dept='电子学院', lab_id=5),
        ]
        db.session.add_all(teachers)
        db.session.commit()
        
        # 4. 创建学生
        print("创建学生...")
        students = [
            Student(id='S001', name='学生小明', password_hash=generate_password_hash('123456'), dept='计算机学院', lab_id=1, t_id='T001', lab_name='计算机科学实验室'),
            Student(id='S002', name='学生小红', password_hash=generate_password_hash('123456'), dept='计算机学院', lab_id=1, t_id='T001', lab_name='计算机科学实验室'),
            Student(id='S003', name='学生小华', password_hash=generate_password_hash('123456'), dept='计算机学院', lab_id=2, t_id='T002', lab_name='人工智能实验室'),
            Student(id='S004', name='学生小李', password_hash=generate_password_hash('123456'), dept='信息学院', lab_id=3, t_id='T003', lab_name='网络安全实验室'),
            Student(id='S005', name='学生小张', password_hash=generate_password_hash('123456'), dept='信息学院', lab_id=4, t_id='T004', lab_name='大数据分析实验室'),
        ]
        db.session.add_all(students)
        db.session.commit()
        
        # 5. 创建设备
        print("创建设备...")
        equipments = [
            # 计算机科学实验室设备
            Equipment(name='高性能服务器A', lab_id=1, category=2, status=1),
            Equipment(name='GPU计算集群', lab_id=1, category=2, status=1),
            Equipment(name='网络分析仪', lab_id=1, category=2, status=1),
            # 人工智能实验室设备
            Equipment(name='深度学习工作站', lab_id=2, category=2, status=1),
            Equipment(name='NVIDIA DGX服务器', lab_id=2, category=2, status=1),
            Equipment(name='机器人臂', lab_id=2, category=2, status=1),
            # 网络安全实验室设备
            Equipment(name='渗透测试平台', lab_id=3, category=2, status=1),
            Equipment(name='防火墙设备', lab_id=3, category=2, status=1),
            Equipment(name='入侵检测系统', lab_id=3, category=2, status=1),
            # 大数据分析实验室设备
            Equipment(name='Hadoop集群', lab_id=4, category=2, status=1),
            Equipment(name='Spark计算平台', lab_id=4, category=2, status=1),
            Equipment(name='数据可视化大屏', lab_id=4, category=2, status=1),
            # 物联网实验室设备
            Equipment(name='物联网网关', lab_id=5, category=2, status=1),
            Equipment(name='传感器套件', lab_id=5, category=2, status=1),
            Equipment(name='边缘计算节点', lab_id=5, category=2, status=1),
            # 学院级设备（全院共享）
            Equipment(name='3D打印机', lab_id=1, category=1, status=1),
            Equipment(name='激光切割机', lab_id=1, category=1, status=1),
            Equipment(name='示波器', lab_id=1, category=1, status=1),
        ]
        db.session.add_all(equipments)
        db.session.commit()
        
        # 获取设备ID
        equip_list = Equipment.query.all()
        
        # 6. 创建时间段
        print("创建时间段...")
        timeslots = []
        for equip in equip_list:
            # 每个设备创建多个时间段
            slots = [
                TimeSlot(equip_id=equip.id, start_time=time(8, 0), end_time=time(10, 0), is_active=1),
                TimeSlot(equip_id=equip.id, start_time=time(10, 0), end_time=time(12, 0), is_active=1),
                TimeSlot(equip_id=equip.id, start_time=time(14, 0), end_time=time(16, 0), is_active=1),
                TimeSlot(equip_id=equip.id, start_time=time(16, 0), end_time=time(18, 0), is_active=1),
            ]
            timeslots.extend(slots)
        db.session.add_all(timeslots)
        db.session.commit()
        
        # 7. 创建一些预约记录
        print("创建预约记录...")
        now = datetime.now()
        reservations = [
            Reservation(
                student_id='S001', 
                equip_id=1, 
                status=1,  # 已通过
                apply_time=now - timedelta(days=2),
                approver_id='admin001',
                approve_time=now - timedelta(days=1),
                user_name='学生小明',
                equip_name='高性能服务器A',
                start_time=now + timedelta(days=1, hours=8),
                end_time=now + timedelta(days=1, hours=10),
            ),
            Reservation(
                student_id='S002', 
                equip_id=4, 
                status=0,  # 待审批
                apply_time=now - timedelta(hours=5),
                user_name='学生小红',
                equip_name='深度学习工作站',
                start_time=now + timedelta(days=2, hours=14),
                end_time=now + timedelta(days=2, hours=16),
            ),
            Reservation(
                teacher_id='T001', 
                equip_id=2, 
                status=1,  # 已通过
                apply_time=now - timedelta(days=3),
                approver_id='admin001',
                approve_time=now - timedelta(days=2),
                user_name='张教授',
                equip_name='GPU计算集群',
                start_time=now + timedelta(days=3, hours=10),
                end_time=now + timedelta(days=3, hours=12),
            ),
            Reservation(
                student_id='S003', 
                equip_id=5, 
                status=2,  # 已拒绝
                apply_time=now - timedelta(days=4),
                approver_id='admin002',
                approve_time=now - timedelta(days=3),
                user_name='学生小华',
                equip_name='NVIDIA DGX服务器',
                start_time=now + timedelta(days=1, hours=16),
                end_time=now + timedelta(days=1, hours=18),
            ),
        ]
        db.session.add_all(reservations)
        db.session.commit()
        
        # 8. 创建审计日志
        print("创建审计日志...")
        audit_logs = [
            AuditLog(operator_id='admin001', action_type='LOGIN', detail='管理员登录系统', ip_address='127.0.0.1'),
            AuditLog(operator_id='admin001', action_type='CREATE_EQUIPMENT', detail='创建设备: 高性能服务器A', ip_address='127.0.0.1'),
            AuditLog(operator_id='T001', action_type='LOGIN', detail='教师登录系统', ip_address='127.0.0.1'),
            AuditLog(operator_id='S001', action_type='LOGIN', detail='学生登录系统', ip_address='127.0.0.1'),
            AuditLog(operator_id='S001', action_type='CREATE_RESERVATION', detail='创建预约: 高性能服务器A', ip_address='127.0.0.1'),
            AuditLog(operator_id='admin001', action_type='APPROVE_RESERVATION', detail='审批通过预约', ip_address='127.0.0.1'),
        ]
        db.session.add_all(audit_logs)
        db.session.commit()
        
        print("\n=== 数据库初始化完成 ===")
        print(f"实验室: 5个")
        print(f"管理员: 2个")
        print(f"教师: 5个")
        print(f"学生: 5个")
        print(f"设备: {len(equip_list)}个")
        print(f"时间段: {len(timeslots)}个")
        print(f"预约: 4条")
        print(f"审计日志: 6条")
        print("\n=== 测试账户 ===")
        print("管理员: admin001 / 123456")
        print("管理员: admin002 / 123456")
        print("教师: T001-T005 / 123456")
        print("学生: S001-S005 / 123456")

if __name__ == '__main__':
    init_database()
