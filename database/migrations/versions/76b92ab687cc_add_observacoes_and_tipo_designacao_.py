"""Add observacoes and tipo_designacao columns to reunioes_nacionais table

Revision ID: 76b92ab687cc
Revises: 3feac370c487
Create Date: 2025-08-13 10:28:04.355442

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76b92ab687cc'
down_revision: Union[str, Sequence[str], None] = '3feac370c487'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns to reunioes_nacionais table."""
    # Add missing columns that are used by the mapper but don't exist in the model
    op.add_column('reunioes_nacionais', sa.Column('observacoes', sa.Text(), nullable=True, comment='Meeting observations/notes (XML: observacoes)'))
    op.add_column('reunioes_nacionais', sa.Column('tipo_designacao', sa.String(length=100), nullable=True, comment='Meeting type designation (XML: tipoDesignacao)'))


def downgrade() -> None:
    """Remove added columns from reunioes_nacionais table."""
    # Remove the added columns
    op.drop_column('reunioes_nacionais', 'tipo_designacao')
    op.drop_column('reunioes_nacionais', 'observacoes')
