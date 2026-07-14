"""create sync jobs table

Revision ID: e5f7b2a9d1c4
Revises: d4e8a1f6c9b3
Create Date: 2026-07-14 00:00:00.000000

Durable job-tracking table for async sync/refresh runs (see
docs/phase-1/step-13.md). Correlated to a Celery task via celery_task_id;
Celery's Redis result backend is TTL-based, this table is the durable
source of truth for job history.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f7b2a9d1c4'
down_revision: Union[str, Sequence[str], None] = 'd4e8a1f6c9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('sync_jobs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('connection_id', sa.Integer(), nullable=False),
    sa.Column('job_type', sa.String(), nullable=False),
    sa.Column('schema_name', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('celery_task_id', sa.String(), nullable=True),
    sa.Column('result_summary', sa.JSON(), nullable=True),
    sa.Column('error_message', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['connection_id'], ['database_connections.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sync_jobs_connection_id'), 'sync_jobs', ['connection_id'], unique=False)
    op.create_index(op.f('ix_sync_jobs_id'), 'sync_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_sync_jobs_celery_task_id'), 'sync_jobs', ['celery_task_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_sync_jobs_celery_task_id'), table_name='sync_jobs')
    op.drop_index(op.f('ix_sync_jobs_id'), table_name='sync_jobs')
    op.drop_index(op.f('ix_sync_jobs_connection_id'), table_name='sync_jobs')
    op.drop_table('sync_jobs')
