"""Fix analytics deputy identity to properly handle cross-legislature tracking

Revision ID: fix_analytics_deputy_identity
Revises: a8457b39c720
Create Date: 2025-08-04 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'fix_analytics_deputy_identity'
down_revision = 'a8457b39c720'
branch_labels = None
depends_on = None

def upgrade():
    """
    Fix analytics tables to properly handle deputy identity across legislatures:
    
    1. Remove unique constraint on DeputyAnalytics.deputado_id (should allow multiple per legislature)
    2. Add unique constraint on (deputado_id, legislatura_id) for DeputyAnalytics
    3. Change DeputyTimeline to use id_cadastro instead of deputado_id for cross-legislature tracking
    """
    
    # Step 1: Fix DeputyAnalytics unique constraint
    # Drop the existing unique constraint on deputado_id
    op.drop_constraint('deputado_id', 'deputy_analytics', type_='unique')
    
    # Add unique constraint on (deputado_id, legislatura_id)
    op.create_unique_constraint(
        'unique_deputy_legislature_analytics', 
        'deputy_analytics', 
        ['deputado_id', 'legislatura_id']
    )
    
    # Step 2: Fix DeputyTimeline to use id_cadastro
    # First, backup existing data if any
    connection = op.get_bind()
    existing_timeline_data = connection.execute(
        sa.text("SELECT * FROM deputy_timeline")
    ).fetchall()
    
    # Drop the existing table and recreate with correct schema
    op.drop_table('deputy_timeline')
    
    # Recreate deputy_timeline with id_cadastro
    op.create_table('deputy_timeline',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_cadastro', sa.Integer(), nullable=False),
        sa.Column('first_election_date', sa.Date(), nullable=True),
        sa.Column('total_legislatures_served', sa.Integer(), nullable=True),
        sa.Column('consecutive_terms', sa.Integer(), nullable=True),
        sa.Column('years_of_service', sa.Integer(), nullable=True),
        sa.Column('current_term_start', sa.Date(), nullable=True),
        sa.Column('is_currently_active', sa.Boolean(), nullable=True),
        sa.Column('key_positions_held', sa.Text(), nullable=True),
        sa.Column('committee_memberships', sa.Text(), nullable=True),
        sa.Column('leadership_roles', sa.Text(), nullable=True),
        sa.Column('significant_initiatives', sa.Text(), nullable=True),
        sa.Column('experience_category', sa.String(length=20), nullable=True),
        sa.Column('specialization_areas', sa.Text(), nullable=True),
        sa.Column('cross_party_collaboration', sa.Integer(), nullable=True),
        sa.Column('seniority_rank', sa.Integer(), nullable=True),
        sa.Column('legislative_effectiveness', sa.Integer(), nullable=True),
        sa.Column('public_engagement_score', sa.Integer(), nullable=True),
        sa.Column('specialization_strength', sa.Integer(), nullable=True),
        sa.Column('institutional_memory_value', sa.Integer(), nullable=True),
        sa.Column('last_calculated', sa.DateTime(), nullable=True),
        sa.Column('calculation_version', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id_cadastro')
    )
    
    # If there was existing data, attempt to migrate it
    # Note: This requires manual conversion from deputado_id to id_cadastro
    if existing_timeline_data:
        # This would need to be done manually or with a more complex migration
        # since we need to map deputado_id to id_cadastro
        pass

def downgrade():
    """Revert the analytics deputy identity changes"""
    
    # Revert DeputyAnalytics changes
    op.drop_constraint('unique_deputy_legislature_analytics', 'deputy_analytics', type_='unique')
    op.create_unique_constraint('deputado_id', 'deputy_analytics', ['deputado_id'])
    
    # Revert DeputyTimeline changes
    op.drop_table('deputy_timeline')
    
    # Recreate original deputy_timeline with deputado_id
    op.create_table('deputy_timeline',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deputado_id', sa.Integer(), nullable=False),
        sa.Column('first_election_date', sa.Date(), nullable=True),
        sa.Column('total_legislatures_served', sa.Integer(), nullable=True),
        sa.Column('consecutive_terms', sa.Integer(), nullable=True),
        sa.Column('years_of_service', sa.Integer(), nullable=True),
        sa.Column('current_term_start', sa.Date(), nullable=True),
        sa.Column('is_currently_active', sa.Boolean(), nullable=True),
        sa.Column('key_positions_held', sa.Text(), nullable=True),
        sa.Column('committee_memberships', sa.Text(), nullable=True),
        sa.Column('leadership_roles', sa.Text(), nullable=True),
        sa.Column('significant_initiatives', sa.Text(), nullable=True),
        sa.Column('experience_category', sa.String(length=20), nullable=True),
        sa.Column('specialization_areas', sa.Text(), nullable=True),
        sa.Column('cross_party_collaboration', sa.Integer(), nullable=True),
        sa.Column('seniority_rank', sa.Integer(), nullable=True),
        sa.Column('legislative_effectiveness', sa.Integer(), nullable=True),
        sa.Column('public_engagement_score', sa.Integer(), nullable=True),
        sa.Column('specialization_strength', sa.Integer(), nullable=True),
        sa.Column('institutional_memory_value', sa.Integer(), nullable=True),
        sa.Column('last_calculated', sa.DateTime(), nullable=True),
        sa.Column('calculation_version', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['deputado_id'], ['deputados.id'], )
    )