"""encrypt existing connection passwords at rest

Revision ID: a7c2e0f4d8b1
Revises: f3a1c9d5b6e2
Create Date: 2026-07-14 00:00:00.000000

Data migration: encrypts every existing plaintext password in
database_connections using the Fernet key from settings.SECRET_KEY
(see app/core/security.py). No schema change — the column stays a String,
it just now holds ciphertext instead of plaintext.

Requires SECRET_KEY to be set in the environment before running this
migration (it always must be, per app/core/config.py — there is no
insecure default).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.security import encrypt_password, decrypt_password


# revision identifiers, used by Alembic.
revision: str = 'a7c2e0f4d8b1'
down_revision: Union[str, Sequence[str], None] = 'f3a1c9d5b6e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


connections_table = sa.table(
    "database_connections",
    sa.column("id", sa.Integer),
    sa.column("password", sa.String),
)


def upgrade() -> None:
    """Encrypt every stored password in place."""
    bind = op.get_bind()
    rows = bind.execute(sa.select(connections_table.c.id, connections_table.c.password)).fetchall()
    for row in rows:
        bind.execute(
            connections_table.update()
            .where(connections_table.c.id == row.id)
            .values(password=encrypt_password(row.password))
        )


def downgrade() -> None:
    """Decrypt every stored password back to plaintext."""
    bind = op.get_bind()
    rows = bind.execute(sa.select(connections_table.c.id, connections_table.c.password)).fetchall()
    for row in rows:
        bind.execute(
            connections_table.update()
            .where(connections_table.c.id == row.id)
            .values(password=decrypt_password(row.password))
        )
