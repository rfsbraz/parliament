"""Add IniciativaEventoAnexo model for IX Legislature phase attachments

Revision ID: 61b194ad744c
Revises: 4c66b81c0dbc
Create Date: 2025-08-01 12:27:39.789321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61b194ad744c'
down_revision: Union[str, Sequence[str], None] = '4c66b81c0dbc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create table for initiative event attachments (IX Legislature phase attachments)
    op.create_table('iniciativas_eventos_anexos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evento_id', sa.Integer(), nullable=False),
        sa.Column('anexo_id', sa.Integer(), nullable=True),
        sa.Column('anexo_nome', sa.Text(), nullable=True),
        sa.Column('anexo_fich', sa.Text(), nullable=True),
        sa.Column('link', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['evento_id'], ['iniciativas_eventos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the initiative event attachments table
    op.drop_table('iniciativas_eventos_anexos')
