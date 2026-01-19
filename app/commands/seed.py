"""
数据库初始化命令
用于初始化测试用户数据
"""
import click
import random
from werkzeug.security import generate_password_hash
from flask.cli import with_appcontext
from app import db
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.admin import Admin
from app.models.laboratory import Laboratory
from app.models.equipment import Equipment
from app.models.timeslot import TimeSlot
from datetime import time


@click.command('init-users')
@click.option('--password', default='123456', help='默认密码（默认：123456）')
@with_appcontext
def init_users(password):
    """
    初始化测试用户数据
    
    创建以下测试用户：
    - 学生: ID="2023001", Role="student", Lab="L1"
    - 导师: ID="T001", Role="teacher", Lab="L1"
    - 管理员: ID="admin", Role="admin"
    
    所有用户的默认密码为 123456（可通过 --password 参数修改）
    """
    try:
        click.echo('开始初始化测试用户...')
        
        # 确保实验室 L1 存在（ID=1）
        lab = Laboratory.query.filter_by(id=1).first()
        if not lab:
            click.echo('创建实验室 L1 (ID=1)...')
            lab = Laboratory(id=1, name='L1', location='实验室L1')
            db.session.add(lab)
            db.session.commit()
            click.echo('[OK] 实验室 L1 创建成功')
        else:
            click.echo('[OK] 实验室 L1 已存在')
        
        # 生成密码Hash
        password_hash = generate_password_hash(password)
        
        # 创建学生用户
        student = Student.query.filter_by(id='2023001').first()
        if not student:
            click.echo('创建学生用户: 2023001...')
            student = Student(
                id='2023001',
                name='测试学生',
                password_hash=password_hash,
                dept='计算机学院',
                lab_id=1,
                lab_name='L1'
            )
            db.session.add(student)
            click.echo('[OK] 学生用户创建成功')
        else:
            student.password_hash = password_hash
            click.echo('[OK] 学生用户已存在，已更新密码')
        
        # 创建导师用户
        teacher = Teacher.query.filter_by(id='T001').first()
        if not teacher:
            click.echo('创建导师用户: T001...')
            teacher = Teacher(
                id='T001',
                name='测试导师',
                password_hash=password_hash,
                dept='计算机学院',
                lab_id=1
            )
            db.session.add(teacher)
            click.echo('[OK] 导师用户创建成功')
        else:
            teacher.password_hash = password_hash
            click.echo('[OK] 导师用户已存在，已更新密码')
        
        # 创建管理员用户
        admin = Admin.query.filter_by(id='admin').first()
        if not admin:
            click.echo('创建管理员用户: admin...')
            admin = Admin(
                id='admin',
                name='系统管理员',
                password_hash=password_hash,
                manage_scope=1
            )
            db.session.add(admin)
            click.echo('[OK] 管理员用户创建成功')
        else:
            admin.password_hash = password_hash
            click.echo('[OK] 管理员用户已存在，已更新密码')
        
        # 提交事务
        db.session.commit()
        
        click.echo('\n[OK] 所有测试用户初始化完成！')
        click.echo(f'\n测试账号信息：')
        click.echo(f'  学生: 学号=2023001, 密码={password}')
        click.echo(f'  导师: 工号=T001, 密码={password}')
        click.echo(f'  管理员: ID=admin, 密码={password}')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'[ERROR] 初始化失败: {str(e)}', err=True)
        raise click.Abort()


@click.command('seed-data')
@click.option('--equipments', default=1000, help='生成设备数量（默认：1000）')
@click.option('--users', default=100, help='生成用户数量（默认：100，包括学生和教师）')
@click.option('--password', default='123456', help='默认密码（默认：123456）')
@with_appcontext
def seed_data(equipments, users, password):
    """
    生成并插入测试数据
    
    生成指定数量的设备和用户数据：
    - 设备数据：随机生成设备名称、实验室、类别、状态等，并自动为每个设备生成时间段
    - 用户数据：随机生成学生和教师（比例约 8:2）
    
    注意：每个设备会自动生成三个时间段（09:00-12:00、14:00-17:00 和 19:00-22:00）
    """
    try:
        click.echo(f'开始生成测试数据...')
        click.echo(f'  设备数量: {equipments}')
        click.echo(f'  用户数量: {users}')
        
        # 生成密码Hash
        password_hash = generate_password_hash(password)
        
        # 1. 确保有足够的实验室数据
        click.echo('\n[1/4] 检查实验室数据...')
        existing_labs = Laboratory.query.all()
        lab_count = len(existing_labs)
        
        if lab_count < 10:
            click.echo(f'  创建 {10 - lab_count} 个实验室...')
            for i in range(lab_count + 1, 11):
                lab = Laboratory(
                    id=i,
                    name=f'L{i}',
                    location=f'实验室L{i}'
                )
                db.session.add(lab)
            db.session.commit()
            click.echo(f'  [OK] 实验室数据准备完成（共10个）')
        else:
            click.echo(f'  [OK] 实验室数据已存在（共{lab_count}个）')
        
        # 获取所有实验室ID
        all_labs = Laboratory.query.all()
        lab_ids = [lab.id for lab in all_labs]
        
        # 记录生成前的设备数量，用于后续更新
        equipment_start_id = Equipment.query.count()
        
        # 2. 生成设备数据（包含时间段）
        click.echo(f'\n[2/4] 生成 {equipments} 条设备数据（含时间段）...')
        
        # 设备名称前缀列表
        equipment_prefixes = [
            '扫描电子显微镜', '透射电子显微镜', '原子力显微镜', '激光共聚焦显微镜',
            'X射线衍射仪', 'X射线光电子能谱仪', '拉曼光谱仪', '红外光谱仪',
            '紫外可见分光光度计', '荧光光谱仪', '核磁共振波谱仪', '质谱仪',
            '高效液相色谱仪', '气相色谱仪', '离子色谱仪', '电化学工作站',
            '材料试验机', '硬度计', '表面粗糙度仪', '三维测量仪',
            '激光切割机', '3D打印机', 'CNC加工中心', '精密磨床',
            '恒温恒湿箱', '高温炉', '真空干燥箱', '超低温冰箱',
            '离心机', '超声波清洗机', '纯水机', '超纯水系统'
        ]
        
        equipment_suffixes = ['-A', '-B', '-C', '-Pro', '-Plus', '-Max', '-Ultra', '-Elite']
        
        # 默认时间段配置
        default_slots = [
            {'start_time': '09:00:00', 'end_time': '12:00:00', 'is_active': 1},
            {'start_time': '14:00:00', 'end_time': '17:00:00', 'is_active': 1},
            {'start_time': '19:00:00', 'end_time': '22:00:00', 'is_active': 1},
        ]
        
        for i in range(equipments):
            # 生成设备名称
            prefix = random.choice(equipment_prefixes)
            suffix = random.choice(equipment_suffixes)
            number = random.randint(1, 999)
            name = f'{prefix}{suffix}-{number:03d}'
            
            # 随机分配实验室（70%概率有实验室，30%概率为None，表示学院设备）
            lab_id = random.choice(lab_ids) if random.random() < 0.7 else None
            
            # 随机类别（1:学院, 2:实验室）
            category = 1 if lab_id is None else random.choice([1, 2])
            
            # 随机状态（1:正常 70%, 2:使用中 15%, 3:维护中 10%, 0:已停用 5%）
            status_weights = [0.05, 0.70, 0.15, 0.10]
            status = random.choices([0, 1, 2, 3], weights=status_weights)[0]
            
            # 创建设备
            equipment = Equipment(
                name=name,
                lab_id=lab_id,
                category=category,
                status=status,
                next_avail_time=None
            )
            db.session.add(equipment)
            db.session.flush()  # 刷新以获取设备ID，但不提交
            
            # 为该设备生成时间段
            for slot_data in default_slots:
                slot = TimeSlot(
                    equip_id=equipment.id,
                    start_time=time.fromisoformat(slot_data['start_time']),
                    end_time=time.fromisoformat(slot_data['end_time']),
                    is_active=slot_data['is_active']
                )
                db.session.add(slot)
            
            # 每100条提交一次
            if (i + 1) % 100 == 0:
                db.session.commit()
                click.echo(f'  已生成 {i + 1}/{equipments} 条设备数据（含时间段）...', nl=False)
                click.echo('\r', nl=False)
        
        # 提交剩余数据
        db.session.commit()
        
        click.echo(f'\r  [OK] 设备数据生成完成（共 {equipments} 条，已包含时间段）')
        
        # 更新新生成设备的下次可用时间
        click.echo('  正在更新设备的下次可用时间...')
        try:
            from app.services.reservation_service import _update_equipment_next_avail_time
            # 只更新新生成的设备
            new_equipments = Equipment.query.filter(Equipment.id > equipment_start_id).all()
            updated_count = 0
            for equipment in new_equipments:
                try:
                    _update_equipment_next_avail_time(equipment.id)
                    updated_count += 1
                except Exception:
                    # 忽略单个设备的更新失败
                    pass
            click.echo(f'  [OK] 已更新 {updated_count} 个设备的下次可用时间')
        except Exception as e:
            click.echo(f'  [WARN] 更新下次可用时间时出错: {str(e)}')
        
        # 3. 生成用户数据（学生和教师）
        click.echo(f'\n[3/4] 生成 {users} 条用户数据...')
        
        # 学生和教师的比例（约 8:2）
        student_count = int(users * 0.8)
        teacher_count = users - student_count
        
        # 生成教师数据（先生成，因为学生需要关联教师）
        click.echo(f'  生成 {teacher_count} 条教师数据...')
        
        # 中文姓氏和名字
        surnames = ['王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴', '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗']
        given_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀兰', '霞', '平', '刚', '桂英']
        
        teacher_batch = []
        teacher_ids = []
        
        for i in range(teacher_count):
            teacher_id = f'T{1000 + i:04d}'
            teacher_ids.append(teacher_id)
            
            name = random.choice(surnames) + random.choice(given_names)
            dept = random.choice(['计算机学院', '电子工程学院', '机械工程学院', '材料科学学院', '化学化工学院', '物理学院', '数学学院'])
            lab_id = random.choice(lab_ids)
            
            teacher = Teacher(
                id=teacher_id,
                name=name,
                password_hash=password_hash,
                dept=dept,
                lab_id=lab_id
            )
            teacher_batch.append(teacher)
            
            # 批量插入
            if len(teacher_batch) >= 50:
                db.session.bulk_save_objects(teacher_batch)
                db.session.commit()
                teacher_batch = []
        
        if teacher_batch:
            db.session.bulk_save_objects(teacher_batch)
            db.session.commit()
        
        click.echo(f'  [OK] 教师数据生成完成（共 {teacher_count} 条）')
        
        # 生成学生数据
        click.echo(f'  生成 {student_count} 条学生数据...')
        
        student_batch = []
        used_student_ids = set()  # 用于跟踪已使用的学号
        
        for i in range(student_count):
            # 生成学号（格式：年份+序号），确保不重复
            max_attempts = 100
            student_id = None
            for _ in range(max_attempts):
                year = random.choice(['2021', '2022', '2023', '2024'])
                student_id = f'{year}{random.randint(1000, 9999)}'
                if student_id not in used_student_ids:
                    used_student_ids.add(student_id)
                    break
            
            if not student_id:
                # 如果无法生成唯一ID，使用序号
                student_id = f'2024{10000 + i:05d}'
                used_student_ids.add(student_id)
            
            name = random.choice(surnames) + random.choice(given_names)
            dept = random.choice(['计算机学院', '电子工程学院', '机械工程学院', '材料科学学院', '化学化工学院', '物理学院', '数学学院'])
            
            # 70%的学生有实验室，30%没有
            lab_id = random.choice(lab_ids) if random.random() < 0.7 else None
            lab = Laboratory.query.get(lab_id) if lab_id else None
            lab_name = lab.name if lab else None
            
            # 60%的学生有导师
            t_id = random.choice(teacher_ids) if random.random() < 0.6 and teacher_ids else None
            
            student = Student(
                id=student_id,
                name=name,
                password_hash=password_hash,
                dept=dept,
                lab_id=lab_id,
                lab_name=lab_name,
                t_id=t_id
            )
            student_batch.append(student)
            
            # 批量插入
            if len(student_batch) >= 50:
                db.session.bulk_save_objects(student_batch)
                db.session.commit()
                student_batch = []
                click.echo(f'    已生成 {i + 1}/{student_count} 条学生数据...', nl=False)
                click.echo('\r', nl=False)
        
        if student_batch:
            db.session.bulk_save_objects(student_batch)
            db.session.commit()
        
        click.echo(f'\r  [OK] 学生数据生成完成（共 {student_count} 条）')
        
        click.echo('\n[OK] 所有测试数据生成完成！')
        click.echo(f'\n数据统计：')
        click.echo(f'  设备: {equipments} 条')
        click.echo(f'  教师: {teacher_count} 条')
        click.echo(f'  学生: {student_count} 条')
        click.echo(f'  总计: {equipments + users} 条')
        click.echo(f'\n所有用户默认密码: {password}')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'\n[ERROR] 数据生成失败: {str(e)}', err=True)
        import traceback
        traceback.print_exc()
        raise click.Abort()


@click.command('seed-timeslots')
@click.option('--equipments', default=None, help='为指定数量的设备生成时间段（默认：所有设备）')
@with_appcontext
def seed_timeslots(equipments):
    """
    为已有设备生成时间段数据（补充命令）
    
    注意：seed-data 命令已自动为设备生成时间段，此命令仅用于为已有设备补充时间段。
    
    为指定数量的设备（或所有设备）生成默认的时间段配置：
    - 09:00-12:00
    - 14:00-17:00
    - 19:00-22:00
    """
    try:
        click.echo('开始为设备生成时间段数据...')
        
        # 获取所有设备
        if equipments:
            equipment_list = Equipment.query.limit(int(equipments)).all()
            click.echo(f'  将为 {len(equipment_list)} 个设备生成时间段...')
        else:
            equipment_list = Equipment.query.all()
            click.echo(f'  将为所有 {len(equipment_list)} 个设备生成时间段...')
        
        if not equipment_list:
            click.echo('  [WARN] 没有找到设备数据，请先运行 seed-data 命令生成设备数据')
            return
        
        # 默认时间段配置
        default_slots = [
            {'start_time': '09:00:00', 'end_time': '12:00:00', 'is_active': 1},
            {'start_time': '14:00:00', 'end_time': '17:00:00', 'is_active': 1},
            {'start_time': '19:00:00', 'end_time': '22:00:00', 'is_active': 1},
        ]
        
        created_count = 0
        skipped_count = 0
        
        for equipment in equipment_list:
            # 检查该设备是否已有时间段
            existing_slots = TimeSlot.query.filter_by(equip_id=equipment.id).count()
            if existing_slots > 0:
                skipped_count += 1
                continue
            
            # 为该设备创建时间段
            for slot_data in default_slots:
                slot = TimeSlot(
                    equip_id=equipment.id,
                    start_time=time.fromisoformat(slot_data['start_time']),
                    end_time=time.fromisoformat(slot_data['end_time']),
                    is_active=slot_data['is_active']
                )
                db.session.add(slot)
            
            created_count += 1
            
            # 每100个设备提交一次
            if created_count % 100 == 0:
                db.session.commit()
                click.echo(f'  已处理 {created_count}/{len(equipment_list)} 个设备...', nl=False)
                click.echo('\r', nl=False)
        
        # 提交剩余数据
        db.session.commit()
        
        click.echo(f'\r  [OK] 时间段数据生成完成！')
        click.echo(f'    已创建: {created_count} 个设备的时间段')
        click.echo(f'    已跳过: {skipped_count} 个设备（已有时间段）')
        click.echo(f'\n  每个设备默认配置了以下时间段：')
        for slot_data in default_slots:
            click.echo(f'    - {slot_data["start_time"]} ~ {slot_data["end_time"]}')
        
        # 更新所有设备的下次可用时间
        click.echo(f'\n  正在更新设备的下次可用时间...')
        try:
            from app.services.reservation_service import _update_equipment_next_avail_time
            updated_count = 0
            for equipment in equipment_list:
                try:
                    _update_equipment_next_avail_time(equipment.id)
                    updated_count += 1
                except Exception as e:
                    # 忽略单个设备的更新失败
                    pass
            click.echo(f'  [OK] 已更新 {updated_count} 个设备的下次可用时间')
        except Exception as e:
            click.echo(f'  [WARN] 更新下次可用时间时出错: {str(e)}')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'\n[ERROR] 时间段数据生成失败: {str(e)}', err=True)
        import traceback
        traceback.print_exc()
        raise click.Abort()


@click.command('clear-equipments')
@click.option('--confirm', is_flag=True, help='确认删除（必须提供此选项才会执行删除）')
@with_appcontext
def clear_equipments(confirm):
    """
    清空设备表的所有数据
    
    注意：此操作会删除所有设备、时间段和预约记录，且无法恢复！
    必须使用 --confirm 选项才会执行删除操作。
    """
    if not confirm:
        click.echo('[ERROR] 必须使用 --confirm 选项才能执行删除操作', err=True)
        click.echo('示例: flask clear-equipments --confirm')
        return
    
    try:
        from app.models.reservation import Reservation
        from app.models.timeslot import TimeSlot
        
        # 统计数据
        reservation_count = Reservation.query.count()
        equipment_count = Equipment.query.count()
        timeslot_count = TimeSlot.query.count()
        
        click.echo(f'\n准备删除以下数据：')
        click.echo(f'  预约记录: {reservation_count} 条')
        click.echo(f'  设备: {equipment_count} 个')
        click.echo(f'  时间段: {timeslot_count} 个')
        
        # 确认删除
        if not click.confirm('\n确定要删除所有设备数据吗？此操作无法恢复！'):
            click.echo('操作已取消')
            return
        
        # 删除预约记录
        if reservation_count > 0:
            click.echo(f'\n正在删除 {reservation_count} 条预约记录...')
            Reservation.query.delete()
            db.session.commit()
            click.echo('  [OK] 预约记录已删除')
        
        # 删除时间段（虽然会自动级联删除，但为了确保可以手动删除）
        if timeslot_count > 0:
            click.echo(f'正在删除 {timeslot_count} 个时间段...')
            TimeSlot.query.delete()
            db.session.commit()
            click.echo('  [OK] 时间段已删除')
        
        # 删除设备
        if equipment_count > 0:
            click.echo(f'正在删除 {equipment_count} 个设备...')
            Equipment.query.delete()
            db.session.commit()
            click.echo('  [OK] 设备已删除')
        
        # 验证删除结果
        remaining_equipment = Equipment.query.count()
        remaining_timeslot = TimeSlot.query.count()
        remaining_reservation = Reservation.query.count()
        
        click.echo(f'\n[OK] 删除完成！')
        click.echo(f'\n剩余数据统计：')
        click.echo(f'  设备: {remaining_equipment} 个')
        click.echo(f'  时间段: {remaining_timeslot} 个')
        click.echo(f'  预约记录: {remaining_reservation} 条')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'\n[ERROR] 删除失败: {str(e)}', err=True)
        import traceback
        traceback.print_exc()
        raise click.Abort()


def register_commands(app):
    """注册CLI命令到Flask应用"""
    app.cli.add_command(init_users)
    app.cli.add_command(seed_data)
    app.cli.add_command(seed_timeslots)
    app.cli.add_command(clear_equipments)

