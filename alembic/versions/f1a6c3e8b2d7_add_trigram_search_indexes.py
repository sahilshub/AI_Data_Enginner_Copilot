"""add pg_trgm indexes for ILIKE search

Revision ID: f1a6c3e8b2d7
Revises: e5f7b2a9d1c4
Create Date: 2026-07-14 00:00:00.000000

search_repository.py filters with ILIKE '%term%' (wildcard on both sides).
A leading wildcard makes a plain B-tree index (already present on
table_name/source_table/target_table) unusable — Postgres always falls back
to a sequential scan for this query shape, regardless of B-tree indexing.
This is invisible on a small catalog and becomes the actual bottleneck as
more connections/tables get synced. pg_trgm's GIN trigram index is the
standard fix for substring search in Postgres. Existing B-tree indexes are
left in place — they're still the right structure for the exact-match
lookups elsewhere (e.g. MetadataRepository.get_table_by_name).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f1a6c3e8b2d7'
down_revision: Union[str, Sequence[str], None] = 'e5f7b2a9d1c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        "CREATE INDEX ix_schema_tables_table_name_trgm "
        "ON schema_tables USING gin (table_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_schema_columns_column_name_trgm "
        "ON schema_columns USING gin (column_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_schema_columns_data_type_trgm "
        "ON schema_columns USING gin (data_type gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_schema_relationships_source_table_trgm "
        "ON schema_relationships USING gin (source_table gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_schema_relationships_target_table_trgm "
        "ON schema_relationships USING gin (target_table gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_schema_relationships_source_column_trgm "
        "ON schema_relationships USING gin (source_column gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_schema_relationships_target_column_trgm "
        "ON schema_relationships USING gin (target_column gin_trgm_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_schema_relationships_target_column_trgm")
    op.execute("DROP INDEX IF EXISTS ix_schema_relationships_source_column_trgm")
    op.execute("DROP INDEX IF EXISTS ix_schema_relationships_target_table_trgm")
    op.execute("DROP INDEX IF EXISTS ix_schema_relationships_source_table_trgm")
    op.execute("DROP INDEX IF EXISTS ix_schema_columns_data_type_trgm")
    op.execute("DROP INDEX IF EXISTS ix_schema_columns_column_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_schema_tables_table_name_trgm")
    # Not dropping the pg_trgm extension itself — other objects/migrations
    # created after this one may come to depend on it.
