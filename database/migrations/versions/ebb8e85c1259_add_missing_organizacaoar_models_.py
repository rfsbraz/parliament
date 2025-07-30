"""Add missing OrganizacaoAR models: PermanentCommittee, SubCommittee, OrganMeeting, and DepNomeCompleto field

Revision ID: ebb8e85c1259
Revises: 57c6b0222e63
Create Date: 2025-07-30 16:01:20.568972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebb8e85c1259'
down_revision: Union[str, Sequence[str], None] = '57c6b0222e63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
