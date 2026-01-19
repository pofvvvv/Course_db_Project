# 删除设备表数据的方法

## ⚠️ 注意事项
设备表与以下表有关联：
- **reservation（预约表）**：设备被预约后会有预约记录
- **timeslot（时间段表）**：设备的时间段配置（会自动级联删除）

删除前请确保：
1. 已备份重要数据
2. 了解删除后无法恢复

---

## 方法1：使用 Flask Shell（推荐，安全）

### 步骤1：先删除所有预约记录
```bash
# 进入 Flask shell
flask shell
```

在 Flask shell 中执行：
```python
from app import db
from app.models.reservation import Reservation
from app.models.equipment import Equipment
from app.models.timeslot import TimeSlot

# 删除所有预约记录
reservation_count = Reservation.query.count()
print(f'准备删除 {reservation_count} 条预约记录...')
Reservation.query.delete()
db.session.commit()
print('预约记录已删除')

# 删除所有设备（时间段会自动删除）
equipment_count = Equipment.query.count()
print(f'准备删除 {equipment_count} 个设备...')
Equipment.query.delete()
db.session.commit()
print('设备数据已删除')

# 验证删除结果
print(f'剩余设备数量: {Equipment.query.count()}')
print(f'剩余时间段数量: {TimeSlot.query.count()}')
```

---

## 方法2：使用 SQL 命令（快速，但需谨慎）

### 如果使用 MySQL/TiDB：
```sql
-- 先删除预约记录
DELETE FROM reservation;

-- 删除时间段（会自动删除，但为了确保可以手动删除）
DELETE FROM timeslot;

-- 删除设备
DELETE FROM equipment;
```

### 如果使用 SQLite：
```sql
-- 先删除预约记录
DELETE FROM reservation;

-- 删除时间段
DELETE FROM timeslot;

-- 删除设备
DELETE FROM equipment;
```

---

## 方法3：使用 CLI 命令（最方便，已创建）

我已经为你创建了一个 Flask CLI 命令，可以直接使用：

```bash
# 删除所有设备数据（包括关联的预约和时间段）
flask clear-equipments --confirm
```

**命令说明：**
- `--confirm`：必须提供此选项才会执行删除，防止误操作
- 会先删除预约记录，再删除时间段，最后删除设备
- 删除前会显示统计信息并要求确认
- 删除后会显示剩余数据统计

**示例输出：**
```
准备删除以下数据：
  预约记录: 150 条
  设备: 1000 个
  时间段: 3000 个

确定要删除所有设备数据吗？此操作无法恢复！ [y/N]: y

正在删除 150 条预约记录...
  [OK] 预约记录已删除
正在删除 3000 个时间段...
  [OK] 时间段已删除
正在删除 1000 个设备...
  [OK] 设备已删除

[OK] 删除完成！

剩余数据统计：
  设备: 0 个
  时间段: 0 个
  预约记录: 0 条
```
