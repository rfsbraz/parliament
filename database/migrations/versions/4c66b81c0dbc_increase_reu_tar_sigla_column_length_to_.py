"""Increase reu_tar_sigla column length to 50 characters

Revision ID: 4c66b81c0dbc
Revises: 4a64f05db651
Create Date: 2025-08-01 11:08:25.568889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c66b81c0dbc'
down_revision: Union[str, Sequence[str], None] = '4a64f05db651'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Increase reu_tar_sigla column length from 20 to 50 characters
    op.alter_column('organ_meetings', 'reu_tar_sigla',
                    existing_type=sa.String(20),
                    type_=sa.String(50),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert reu_tar_sigla column length back from 50 to 20 characters
    op.alter_column('organ_meetings', 'reu_tar_sigla',
                    existing_type=sa.String(50),
                    type_=sa.String(20),
                    existing_nullable=True)
