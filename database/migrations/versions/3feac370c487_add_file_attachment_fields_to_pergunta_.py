"""Add file attachment fields to pergunta_requerimento_respostas table

Revision ID: 3feac370c487
Revises: 36c3f1a90419
Create Date: 2025-08-13 10:16:27.702831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3feac370c487'
down_revision: Union[str, Sequence[str], None] = '36c3f1a90419'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add file attachment fields to pergunta_requerimento_respostas table."""
    # Add new columns for file attachment information
    op.add_column('pergunta_requerimento_respostas', sa.Column('ficheiro_url', sa.Text(), nullable=True, comment='File attachment URL (XML: ficheiroComTipo.url)'))
    op.add_column('pergunta_requerimento_respostas', sa.Column('ficheiro_tipo', sa.String(length=50), nullable=True, comment='File attachment type (XML: ficheiroComTipo.tipo)'))


def downgrade() -> None:
    """Remove file attachment fields from pergunta_requerimento_respostas table."""
    # Remove the added columns
    op.drop_column('pergunta_requerimento_respostas', 'ficheiro_tipo')
    op.drop_column('pergunta_requerimento_respostas', 'ficheiro_url')
