"""Add OrganizacaoAR parliamentary organization models for full XML mapping

Revision ID: 57c6b0222e63
Revises: 8307b5c8a1ec
Create Date: 2025-07-30 15:39:02.903534

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57c6b0222e63'
down_revision: Union[str, Sequence[str], None] = '8307b5c8a1ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
