"""Add recrawl_count and error_count tracking fields to ImportStatus

Revision ID: 434bcc563fa6
Revises: b421c8d61df5
Create Date: 2025-08-12 15:07:30.163447

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '434bcc563fa6'
down_revision: Union[str, Sequence[str], None] = 'b421c8d61df5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add recrawl_count and error_count tracking fields to ImportStatus."""
    # Add recrawl_count column
    op.add_column('import_status', sa.Column('recrawl_count', sa.Integer(), default=0, comment="Number of times URL has been recrawled"))
    # Add error_count column  
    op.add_column('import_status', sa.Column('error_count', sa.Integer(), default=0, comment="Number of import errors encountered"))


def downgrade() -> None:
    """Remove recrawl_count and error_count tracking fields from ImportStatus."""
    # Drop the added columns
    op.drop_column('import_status', 'error_count')
    op.drop_column('import_status', 'recrawl_count')
