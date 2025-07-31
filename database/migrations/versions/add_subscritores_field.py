"""Add outros_subscritores field to AtividadeParlamentar

Revision ID: add_outros_subscritores_field
Revises: 75a9d5ce7f64
Create Date: 2025-07-30 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_outros_subscritores_field'
down_revision = '75a9d5ce7f64'
branch_labels = None
depends_on = None

def upgrade():
    # Add outros_subscritores field to atividade_parlamentar table
    op.add_column('atividade_parlamentar', sa.Column('outros_subscritores', sa.Text(), nullable=True))

def downgrade():
    # Remove outros_subscritores field from atividade_parlamentar table
    op.drop_column('atividade_parlamentar', 'outros_subscritores')