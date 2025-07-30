"""Create missing temas_parlamentares table to fix foreign key constraints

Revision ID: a7378e868b19
Revises: 741ccf31618e
Create Date: 2025-07-30 15:15:12.318570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7378e868b19'
down_revision: Union[str, Sequence[str], None] = '741ccf31618e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the missing temas_parlamentares table
    op.create_table('temas_parlamentares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_externo', sa.Integer(), nullable=True),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for better performance
    op.create_index('idx_temas_parlamentares_id_externo', 'temas_parlamentares', ['id_externo'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_temas_parlamentares_id_externo')
    op.drop_table('temas_parlamentares')
