"""Initial migration

Revision ID: fa98e6e70c2d
Revises: add_reservation_desc
Create Date: 2026-01-04 10:49:16.412084

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa98e6e70c2d'
down_revision = 'add_reservation_desc'
branch_labels = None
depends_on = None


def upgrade():
    # 对于新数据库，外键约束已经在初始迁移中正确创建
    # 这个迁移原本是为了修复外键约束名称，但对于新数据库不需要
    # 保留空函数以保持迁移链的完整性
    pass


def downgrade():
    # 对于新数据库，不需要回滚操作
    pass
