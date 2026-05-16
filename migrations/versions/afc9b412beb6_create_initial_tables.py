"""create initial tables

Revision ID: afc9b412beb6
Revises: 
Create Date: 2026-05-16 12:55:50.437852
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'afc9b412beb6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 MVP 所需的初始数据表和索引。"""
    op.create_table('image_assets',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('image_url', sa.String(length=1024), nullable=False),
    sa.Column('image_sha256', sa.String(length=128), nullable=False),
    sa.Column('width', sa.Integer(), nullable=False),
    sa.Column('height', sa.Integer(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_image_assets_image_sha256'), 'image_assets', ['image_sha256'], unique=True)
    op.create_table('users',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('openid', sa.String(length=128), nullable=False),
    sa.Column('nickname', sa.String(length=64), nullable=False),
    sa.Column('avatar_url', sa.String(length=512), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_openid'), 'users', ['openid'], unique=True)
    op.create_table('analyses',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=True),
    sa.Column('guest_id', sa.String(length=128), nullable=True),
    sa.Column('image_url', sa.String(length=1024), nullable=False),
    sa.Column('image_sha256', sa.String(length=128), nullable=False),
    sa.Column('pet_type', sa.String(length=16), nullable=False),
    sa.Column('pet_name', sa.String(length=40), nullable=False),
    sa.Column('score', sa.Integer(), nullable=False),
    sa.Column('risk_level', sa.String(length=16), nullable=False),
    sa.Column('risk_text', sa.String(length=16), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('observation_advice', sa.JSON(), nullable=False),
    sa.Column('diet_advice', sa.Text(), nullable=False),
    sa.Column('need_vet', sa.Boolean(), nullable=False),
    sa.Column('raw_ai_result', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analyses_guest_id'), 'analyses', ['guest_id'], unique=False)
    op.create_index(op.f('ix_analyses_image_sha256'), 'analyses', ['image_sha256'], unique=False)
    op.create_index(op.f('ix_analyses_user_id'), 'analyses', ['user_id'], unique=False)
    op.create_table('health_records',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('analysis_id', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'analysis_id', name='uq_record_user_analysis')
    )
    op.create_index(op.f('ix_health_records_analysis_id'), 'health_records', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_health_records_user_id'), 'health_records', ['user_id'], unique=False)


def downgrade() -> None:
    """回滚 MVP 初始数据表和索引。"""
    op.drop_index(op.f('ix_health_records_user_id'), table_name='health_records')
    op.drop_index(op.f('ix_health_records_analysis_id'), table_name='health_records')
    op.drop_table('health_records')
    op.drop_index(op.f('ix_analyses_user_id'), table_name='analyses')
    op.drop_index(op.f('ix_analyses_image_sha256'), table_name='analyses')
    op.drop_index(op.f('ix_analyses_guest_id'), table_name='analyses')
    op.drop_table('analyses')
    op.drop_index(op.f('ix_users_openid'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_image_assets_image_sha256'), table_name='image_assets')
    op.drop_table('image_assets')
