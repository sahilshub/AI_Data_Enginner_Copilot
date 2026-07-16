"""add is_active to ai_provider_configs

Revision ID: b7d3e9a1f4c6
Revises: a2b8d4f7c1e9
Create Date: 2026-07-15 00:00:00.000000

Phase 2, Step 3: exactly one AIProviderConfig row can be active at a time
— the provider every AI task uses. Enforced at the application layer
(AIProviderRepository.set_active()) and, here, at the DB level via a
partial unique index — defense in depth against an application bug ever
leaving two rows active simultaneously.

If any provider rows already exist from before this migration, the most
recently created one is activated so AI features keep working without
requiring a manual activation step immediately after upgrading.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d3e9a1f4c6'
down_revision: Union[str, Sequence[str], None] = 'a2b8d4f7c1e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'ai_provider_configs',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # Activate the most recently created existing row, if any, so upgrading
    # doesn't silently disable AI features that were already configured.
    op.execute("""
        UPDATE ai_provider_configs
        SET is_active = true
        WHERE id = (SELECT id FROM ai_provider_configs ORDER BY created_at DESC LIMIT 1)
    """)

    op.execute(
        "CREATE UNIQUE INDEX ix_ai_provider_configs_one_active "
        "ON ai_provider_configs (is_active) WHERE is_active = true"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_ai_provider_configs_one_active")
    op.drop_column('ai_provider_configs', 'is_active')
