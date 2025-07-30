"""Add artigo field to DebateParlamentar

Revision ID: add_artigo_field_to_debates
Revises: add_outros_subscritores_field
Create Date: 2025-07-30 22:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_artigo_field_to_debates'
down_revision = 'add_outros_subscritores_field'
branch_labels = None
depends_on = None

def upgrade():
    # Add artigo field to debate_parlamentar table
    op.add_column('debate_parlamentar', sa.Column('artigo', sa.Text(), nullable=True))

def downgrade():
    # Remove artigo field from debate_parlamentar table
    op.drop_column('debate_parlamentar', 'artigo')