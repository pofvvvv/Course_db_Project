# 预约服务测试说明

本目录包含 `reservation_service.py` 的完整测试套件，测试脚本按功能模块分为多个文件。

## 测试文件结构

```
tests/
├── __init__.py                              # 测试模块初始化
├── conftest.py                              # pytest 配置和 fixtures
├── test_reservation_service_validation.py   # 验证函数测试
├── test_reservation_service_create.py       # 创建预约测试
├── test_reservation_service_query.py        # 查询预约测试
├── test_reservation_service_update.py       # 更新预约状态测试
├── test_reservation_service_delete.py       # 删除预约测试
└── test_reservation_service_availability.py # 可用时间计算测试
```

## 测试覆盖范围

### 1. 验证函数测试 (`test_reservation_service_validation.py`)
- ✅ `_validate_time_range`: 时间范围验证
  - 有效时间范围
  - 开始时间等于/晚于结束时间
  - 空值检查
  - 过去时间检查

- ✅ `_check_timeslot_availability`: 时间段可用性检查
  - 有效时间段
  - 无时间段配置
  - 时间段外的时间
  - 跨天预约
  - 多个时间段

- ✅ `_check_reservation_conflict`: 预约冲突检查
  - 无冲突情况
  - 与待审/已通过预约冲突
  - 与已拒绝预约不冲突
  - 排除指定预约ID
  - 相邻时间不冲突
  - 重叠时间冲突

### 2. 创建预约测试 (`test_reservation_service_create.py`)
- ✅ 学生/教师成功创建预约
- ✅ 创建不带时间的预约
- ✅ 字符串格式时间处理
- ✅ 设备/学生/教师不存在的情况
- ✅ 无效用户类型
- ✅ 无效时间格式
- ✅ 预约冲突检查
- ✅ 时间段外预约
- ✅ 价格和描述字段

### 3. 查询预约测试 (`test_reservation_service_query.py`)
- ✅ `get_reservation_list`: 获取预约列表
  - 获取所有预约
  - 按学生ID筛选
  - 按教师ID筛选
  - 按设备ID筛选
  - 按状态筛选
  - 组合筛选条件
  - 空列表

- ✅ `get_reservation_by_id`: 根据ID查询
  - 获取存在的预约
  - 获取不存在的预约
  - 获取包含所有字段的预约

### 4. 更新预约状态测试 (`test_reservation_service_update.py`)
- ✅ 审批通过待审预约
- ✅ 拒绝待审预约
- ✅ 取消待审/已通过预约
- ✅ 无效状态流转
- ✅ 更新不存在的预约
- ✅ 设备状态更新
- ✅ 可用时间更新
- ✅ 缓存清除

### 5. 删除预约测试 (`test_reservation_service_delete.py`)
- ✅ 删除存在的预约
- ✅ 删除不存在的预约
- ✅ 删除已通过预约时更新设备
- ✅ 删除待审预约不更新设备
- ✅ 缓存清除
- ✅ 数据库错误回滚

### 6. 可用时间计算测试 (`test_reservation_service_availability.py`)
- ✅ `_calculate_next_avail_time`: 计算下次可用时间
  - 无时间段配置
  - 无预约情况
  - 有未来预约
  - 多个预约
  - 过去预约不影响
  - 待审/已拒绝预约不影响
  - 多个时间段
  - 整天被预约

- ✅ `_update_equipment_next_avail_time`: 更新设备可用时间
  - 更新存在的设备
  - 更新不存在的设备
  - 缓存清除
  - 数据库错误处理

## 运行测试

### 安装依赖

首先确保已安装 pytest：

```bash
pip install pytest pytest-cov
```

### 运行所有测试

**注意**：如果遇到 `无法将"pytest"项识别为 cmdlet` 错误，请使用 `python -m pytest` 代替 `pytest`。

```bash
# 在项目根目录运行（推荐方式）
python -m pytest tests/

# 或使用详细输出
python -m pytest tests/ -v

# 显示覆盖率
python -m pytest tests/ --cov=app.services.reservation_service --cov-report=html

# 如果虚拟环境已激活，也可以直接使用
pytest tests/ -v
```

**遇到问题？** 请查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 获取详细的问题排查指南。

### 运行特定测试文件

```bash
# 只运行验证函数测试
python -m pytest tests/test_reservation_service_validation.py -v

# 只运行创建预约测试
python -m pytest tests/test_reservation_service_create.py -v
```

### 运行特定测试类或测试方法

```bash
# 运行特定测试类
python -m pytest tests/test_reservation_service_validation.py::TestValidateTimeRange -v

# 运行特定测试方法
python -m pytest tests/test_reservation_service_validation.py::TestValidateTimeRange::test_valid_time_range -v
```

## 测试配置

测试使用内存数据库（SQLite）进行，配置在 `conftest.py` 中：

- 使用 `TestingConfig` 配置
- 每个测试函数都会创建新的数据库表
- 测试结束后自动清理

## Fixtures 说明

`conftest.py` 提供了以下 fixtures：

- `app`: Flask 应用实例
- `client`: 测试客户端
- `db_session`: 数据库会话
- `mock_redis`: 模拟 Redis 客户端
- `sample_equipment`: 示例设备
- `sample_student`: 示例学生
- `sample_teacher`: 示例教师
- `sample_timeslot`: 示例时间段
- `future_datetime`: 未来日期时间
- `sample_reservation_data`: 示例预约数据
- `sample_current_user_student`: 示例学生用户信息
- `sample_current_user_teacher`: 示例教师用户信息

## 注意事项

1. **时间相关测试**: 某些测试依赖于当前时间，如果测试时间接近边界值（如午夜），可能需要调整测试数据。

2. **数据库隔离**: 每个测试函数都使用独立的数据库会话，测试之间不会相互影响。

3. **Mock Redis**: Redis 操作被 mock，不会实际连接 Redis 服务器。

4. **时区问题**: 测试使用 `datetime.utcnow()`，确保时间一致性。

## 扩展测试

如果需要添加新的测试用例：

1. 在相应的测试文件中添加新的测试类或测试方法
2. 使用 `pytest` 的装饰器标记测试（如 `@pytest.mark.skip` 跳过测试）
3. 遵循现有的测试命名规范：`test_功能描述`

## 测试覆盖率目标

建议保持测试覆盖率在 80% 以上，重点关注：
- 边界条件
- 错误处理
- 业务逻辑分支
- 数据库操作
