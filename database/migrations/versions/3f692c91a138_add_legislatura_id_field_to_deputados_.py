"""Add legislatura_id field to deputados table

Revision ID: 3f692c91a138
Revises: f6f59d95d49d
Create Date: 2025-08-04 15:45:16.446422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f692c91a138'
down_revision: Union[str, Sequence[str], None] = 'f6f59d95d49d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add legislatura_id field to deputados table."""
    # Add the legislatura_id column
    op.add_column('deputados', sa.Column('legislatura_id', sa.Integer(), nullable=False))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_deputados_legislatura_id', 
        'deputados', 
        'legislaturas', 
        ['legislatura_id'], 
        ['id']
    )
    
    # Add index for performance
    op.create_index('idx_deputados_legislatura', 'deputados', ['legislatura_id'])


def downgrade() -> None:
    """Remove legislatura_id field from deputados table."""
    op.drop_index('idx_deputados_legislatura', table_name='deputados')
    op.drop_constraint('fk_deputados_legislatura_id', 'deputados', type_='foreignkey')
    op.drop_column('deputados', 'legislatura_id')
