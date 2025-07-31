"""Merge multiple heads

Revision ID: aa85ab68585d
Revises: ebb8e85c1259, f9b31f8a0531
Create Date: 2025-07-31 06:51:47.533557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa85ab68585d'
down_revision: Union[str, Sequence[str], None] = ('ebb8e85c1259', 'f9b31f8a0531')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
