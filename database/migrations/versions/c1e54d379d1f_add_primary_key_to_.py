"""Add primary key to RegistoInteressesUnified and create RegistoInteressesFactoDeclaracao model

Revision ID: c1e54d379d1f
Revises: 5f1535c04191
Create Date: 2025-08-10 15:15:04.813633

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "c1e54d379d1f"
down_revision: Union[str, Sequence[str], None] = "5f1535c04191"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the new RegistoInteressesFactoDeclaracao table
    op.create_table(
        "registo_interesses_facto_declaracao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("registo_id", sa.Integer(), nullable=False),
        sa.Column(
            "declaracao_id",
            sa.String(length=50),
            nullable=True,
            comment="Declaration ID from XML (XML: Id)",
        ),
        sa.Column(
            "cargo_funcao",
            sa.String(length=200),
            nullable=True,
            comment="Function/position title (XML: CargoFuncao)",
        ),
        sa.Column(
            "chk_declaracao",
            sa.String(length=10),
            nullable=True,
            comment="Declaration check flag (XML: ChkDeclaracao)",
        ),
        sa.Column(
            "txt_declaracao",
            sa.Text(),
            nullable=True,
            comment="Declaration text content (XML: TxtDeclaracao)",
        ),
        sa.Column(
            "data_inicio_funcao",
            sa.Date(),
            nullable=True,
            comment="Function start date (XML: DataInicioFuncao)",
        ),
        sa.Column(
            "data_alteracao_funcao",
            sa.Date(),
            nullable=True,
            comment="Function change date (XML: DataAlteracaoFuncao)",
        ),
        sa.Column(
            "data_cessacao_funcao",
            sa.Date(),
            nullable=True,
            comment="Function end date (XML: DataCessacaoFuncao)",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["registo_id"], ["registo_interesses_unified.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("registo_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the new RegistoInteressesFactoDeclaracao table
    op.drop_table("registo_interesses_facto_declaracao")

    # Note: We don't downgrade the primary key addition for registo_interesses_unified
    # as it would break existing foreign key relationships
    # If needed, this should be done manually with careful consideration of data integrity
