"""add source_schema/target_schema to schema_relationships

Revision ID: b3d9f1a2c6e4
Revises: a7c2e0f4d8b1
Create Date: 2026-07-14 00:00:00.000000

Schema-qualifies relationships so tables of the same name in different
schemas on one connection don't get conflated (schema_tables already had
this via schema_name; schema_relationships never did). Existing rows are
backfilled to 'public' since that was the only schema this table ever
implicitly represented before this migration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3d9f1a2c6e4'
down_revision: Union[str, Sequence[str], None] = 'a7c2e0f4d8b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'schema_relationships',
        sa.Column('source_schema', sa.String(), nullable=False, server_default='public'),
    )
    op.add_column(
        'schema_relationships',
        sa.Column('target_schema', sa.String(), nullable=False, server_default='public'),
    )

    op.drop_constraint('uq_schema_relationship', 'schema_relationships', type_='unique')
    op.create_unique_constraint(
        'uq_schema_relationship',
        'schema_relationships',
        ['connection_id', 'source_schema', 'source_table', 'source_column',
         'target_schema', 'target_table', 'target_column'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_schema_relationship', 'schema_relationships', type_='unique')
    op.create_unique_constraint(
        'uq_schema_relationship',
        'schema_relationships',
        ['connection_id', 'source_table', 'source_column', 'target_table', 'target_column'],
    )

    op.drop_column('schema_relationships', 'target_schema')
    op.drop_column('schema_relationships', 'source_schema')
