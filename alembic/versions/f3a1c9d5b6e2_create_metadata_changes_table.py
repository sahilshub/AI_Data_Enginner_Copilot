"""create metadata changes table

Revision ID: f3a1c9d5b6e2
Revises: 21783c690530
Create Date: 2026-07-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a1c9d5b6e2'
down_revision: Union[str, Sequence[str], None] = '21783c690530'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('metadata_changes',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('connection_id', sa.Integer(), nullable=False),
    sa.Column('change_type', sa.String(), nullable=False),
    sa.Column('object_type', sa.String(), nullable=False),
    sa.Column('object_name', sa.String(), nullable=False),
    sa.Column('previous_value', sa.String(), nullable=True),
    sa.Column('new_value', sa.String(), nullable=True),
    sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['connection_id'], ['database_connections.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_metadata_changes_connection_id'), 'metadata_changes', ['connection_id'], unique=False)
    op.create_index(op.f('ix_metadata_changes_id'), 'metadata_changes', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_metadata_changes_id'), table_name='metadata_changes')
    op.drop_index(op.f('ix_metadata_changes_connection_id'), table_name='metadata_changes')
    op.drop_table('metadata_changes')
