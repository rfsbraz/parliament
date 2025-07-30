"""Add RelatorioParlamentarIniciativaConjunta table

Revision ID: add_relatorio_iniciativas_conjuntas
Revises: add_artigo_field_to_debates
Create Date: 2025-07-30 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_relatorio_iniciativas_conjuntas'
down_revision = 'add_artigo_field_to_debates'
branch_labels = None
depends_on = None

def upgrade():
    # Create relatorio_parlamentar_iniciativas_conjuntas table
    op.create_table('relatorio_parlamentar_iniciativas_conjuntas',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('relatorio_id', sa.Integer(), sa.ForeignKey('relatorio_parlamentar.id'), nullable=False),
        sa.Column('iniciativa_id', sa.Integer(), nullable=True),
        sa.Column('tipo', sa.String(200), nullable=True),
        sa.Column('desc_tipo', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_relatorio_iniciativas_conjuntas_relatorio', 'relatorio_parlamentar_iniciativas_conjuntas', ['relatorio_id'])
    op.create_index('idx_relatorio_iniciativas_conjuntas_iniciativa', 'relatorio_parlamentar_iniciativas_conjuntas', ['iniciativa_id'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_relatorio_iniciativas_conjuntas_iniciativa', 'relatorio_parlamentar_iniciativas_conjuntas')
    op.drop_index('idx_relatorio_iniciativas_conjuntas_relatorio', 'relatorio_parlamentar_iniciativas_conjuntas')
    
    # Drop table
    op.drop_table('relatorio_parlamentar_iniciativas_conjuntas')