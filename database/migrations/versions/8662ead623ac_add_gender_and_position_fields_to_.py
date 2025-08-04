"""Add gender and position fields to registo_interesses_unified

Revision ID: 8662ead623ac
Revises: d0f14597c3d5
Create Date: 2025-08-04 20:49:39.766061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8662ead623ac'
down_revision: Union[str, Sequence[str], None] = 'd0f14597c3d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing gender and position fields to registo_interesses_unified table."""
    
    # Add gender field for V5 GenDadosPessoais.Sexo
    op.add_column('registo_interesses_unified', 
                  sa.Column('gender', sa.String(10), nullable=True))
    
    # Add position-related fields for V3 RecordInterests structure
    op.add_column('registo_interesses_unified', 
                  sa.Column('position_begin_date', sa.Date, nullable=True))
    
    op.add_column('registo_interesses_unified', 
                  sa.Column('position_end_date', sa.Date, nullable=True))
    
    op.add_column('registo_interesses_unified', 
                  sa.Column('position_changed_date', sa.Date, nullable=True))
    
    op.add_column('registo_interesses_unified', 
                  sa.Column('position_designation', sa.String(200), nullable=True))


def downgrade() -> None:
    """Remove the added fields."""
    op.drop_column('registo_interesses_unified', 'position_designation')
    op.drop_column('registo_interesses_unified', 'position_changed_date')
    op.drop_column('registo_interesses_unified', 'position_end_date')
    op.drop_column('registo_interesses_unified', 'position_begin_date')
    op.drop_column('registo_interesses_unified', 'gender')
