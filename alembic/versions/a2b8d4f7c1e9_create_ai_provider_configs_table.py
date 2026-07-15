"""create ai provider configs table

Revision ID: a2b8d4f7c1e9
Revises: f1a6c3e8b2d7
Create Date: 2026-07-15 00:00:00.000000

Phase 2, Step 1: stores user-registered LLM provider configs
(Anthropic/OpenAI/Gemini/Grok) with their own API key, Fernet-encrypted
the same way database_connections.password already is.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b8d4f7c1e9'
down_revision: Union[str, Sequence[str], None] = 'f1a6c3e8b2d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('ai_provider_configs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('provider', sa.String(), nullable=False),
    sa.Column('api_key', sa.String(), nullable=False),
    sa.Column('default_model', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_provider_configs_id'), 'ai_provider_configs', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_ai_provider_configs_id'), table_name='ai_provider_configs')
    op.drop_table('ai_provider_configs')
