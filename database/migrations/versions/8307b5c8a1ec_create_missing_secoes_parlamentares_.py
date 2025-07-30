"""Create missing secoes_parlamentares table to complete sync fix

Revision ID: 8307b5c8a1ec
Revises: a7378e868b19
Create Date: 2025-07-30 15:19:40.457785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8307b5c8a1ec'
down_revision: Union[str, Sequence[str], None] = 'a7378e868b19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the missing secoes_parlamentares table
    op.create_table('secoes_parlamentares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_externo', sa.Integer(), nullable=True),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for better performance
    op.create_index('idx_secoes_parlamentares_id_externo', 'secoes_parlamentares', ['id_externo'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_secoes_parlamentares_id_externo')
    op.drop_table('secoes_parlamentares')
