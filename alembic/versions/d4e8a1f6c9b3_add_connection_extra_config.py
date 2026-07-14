"""add extra_config to database_connections

Revision ID: d4e8a1f6c9b3
Revises: b3d9f1a2c6e4
Create Date: 2026-07-14 00:00:00.000000

Adds a flexible JSON column for source-specific config that doesn't fit
host/port/username/password/database (e.g. a future BigQuery connector's
service-account JSON + project id). Nullable and unused by the existing
PostgresConnector — this just avoids a second disruptive migration once a
non-Postgres source is actually implemented.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e8a1f6c9b3'
down_revision: Union[str, Sequence[str], None] = 'b3d9f1a2c6e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('database_connections', sa.Column('extra_config', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('database_connections', 'extra_config')
