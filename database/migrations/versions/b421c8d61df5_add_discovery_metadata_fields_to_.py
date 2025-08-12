"""Add discovery metadata fields to ImportStatus

Revision ID: b421c8d61df5
Revises: 7e1fc7095557
Create Date: 2025-08-12 14:30:55.107965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b421c8d61df5'
down_revision: Union[str, Sequence[str], None] = '7e1fc7095557'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new discovery metadata fields to import_status table
    op.add_column('import_status', sa.Column('source_page_url', sa.String(length=1000), comment='URL of the page where the link was found'))
    op.add_column('import_status', sa.Column('anchor_text', sa.String(length=500), comment='Text content of the link anchor element'))
    op.add_column('import_status', sa.Column('url_pattern', sa.String(length=200), comment='Heuristic pattern for URL token refresh (e.g., doc.xml?path=...&fich=...)'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the added discovery metadata fields
    op.drop_column('import_status', 'url_pattern')
    op.drop_column('import_status', 'anchor_text') 
    op.drop_column('import_status', 'source_page_url')
