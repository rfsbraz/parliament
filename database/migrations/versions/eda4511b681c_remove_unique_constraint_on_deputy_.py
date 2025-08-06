"""Remove unique constraint on deputy cadastro per legislature

Revision ID: eda4511b681c
Revises: b3e6e29740ad
Create Date: 2025-08-06 22:10:58.119093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eda4511b681c'
down_revision: Union[str, Sequence[str], None] = 'b3e6e29740ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unique constraint on deputy cadastro per legislature."""
    # Drop the unique constraint that prevented multiple deputies with same cadastral ID per legislature
    op.drop_constraint('uq_deputy_cadastro_legislature', 'deputados', type_='unique')


def downgrade() -> None:
    """Restore unique constraint on deputy cadastro per legislature."""
    # Restore the unique constraint (note: this may fail if duplicate data exists)
    op.create_unique_constraint('uq_deputy_cadastro_legislature', 'deputados', ['id_cadastro', 'legislatura_id'])
