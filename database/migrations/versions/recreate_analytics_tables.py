"""Recreate analytics tables to match updated models

Revision ID: recreate_analytics_tables
Revises: 3f692c91a138
Create Date: 2025-08-04 17:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'recreate_analytics_tables'
down_revision = '3f692c91a138'
branch_labels = None
depends_on = None

def upgrade():
    """
    Drop and recreate analytics tables to match the updated models perfectly.
    Since data can be recreated, this is the cleanest approach.
    """
    
    # Drop analytics tables (in dependency order)
    op.drop_table('attendance_analytics')
    op.drop_table('initiative_analytics') 
    op.drop_table('deputy_analytics')
    op.drop_table('deputy_timeline')
    op.drop_table('data_quality_metrics')
    
    # Recreate deputy_analytics with correct schema
    op.create_table('deputy_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deputado_id', sa.Integer(), nullable=False),
        sa.Column('legislatura_id', sa.Integer(), nullable=True),
        sa.Column('activity_score', sa.Integer(), nullable=True),
        sa.Column('attendance_score', sa.Integer(), nullable=True),
        sa.Column('initiative_score', sa.Integer(), nullable=True),
        sa.Column('intervention_score', sa.Integer(), nullable=True),
        sa.Column('engagement_score', sa.Integer(), nullable=True),
        sa.Column('total_sessions_scheduled', sa.Integer(), nullable=True),
        sa.Column('total_sessions_attended', sa.Integer(), nullable=True),
        sa.Column('attendance_percentage', sa.Integer(), nullable=True),
        sa.Column('consistency_score', sa.Integer(), nullable=True),
        sa.Column('total_initiatives_authored', sa.Integer(), nullable=True),
        sa.Column('total_initiatives_co_authored', sa.Integer(), nullable=True),
        sa.Column('initiatives_approved', sa.Integer(), nullable=True),
        sa.Column('initiatives_pending', sa.Integer(), nullable=True),
        sa.Column('initiatives_rejected', sa.Integer(), nullable=True),
        sa.Column('total_interventions', sa.Integer(), nullable=True),
        sa.Column('total_words_spoken', sa.Integer(), nullable=True),
        sa.Column('avg_intervention_length', sa.Integer(), nullable=True),
        sa.Column('approval_rate', sa.Integer(), nullable=True),
        sa.Column('productivity_trend', sa.String(length=20), nullable=True),
        sa.Column('avg_monthly_activity', sa.Integer(), nullable=True),
        sa.Column('peak_activity_month', sa.String(length=7), nullable=True),
        sa.Column('specialization_areas', sa.Text(), nullable=True),
        sa.Column('cross_party_collaboration', sa.Integer(), nullable=True),
        sa.Column('leadership_indicators', sa.Text(), nullable=True),
        sa.Column('last_calculated', sa.DateTime(), nullable=True),
        sa.Column('calculation_version', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['deputado_id'], ['deputados.id'], ),
        sa.ForeignKeyConstraint(['legislatura_id'], ['legislaturas.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('deputado_id', 'legislatura_id', name='unique_deputy_legislature_analytics')
    )
    
    # Recreate attendance_analytics with correct schema
    op.create_table('attendance_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deputado_id', sa.Integer(), nullable=False),
        sa.Column('legislatura_id', sa.Integer(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('sessions_scheduled', sa.Integer(), nullable=True),
        sa.Column('sessions_attended', sa.Integer(), nullable=True),
        sa.Column('sessions_absent', sa.Integer(), nullable=True),
        sa.Column('sessions_justified_absence', sa.Integer(), nullable=True),
        sa.Column('attendance_rate', sa.String(length=10), nullable=True),
        sa.Column('consistency_score', sa.Integer(), nullable=True),
        sa.Column('improvement_from_prev_month', sa.String(length=10), nullable=True),
        sa.Column('punctuality_score', sa.Integer(), nullable=True),
        sa.Column('meeting_types_attended', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['deputado_id'], ['deputados.id'], ),
        sa.ForeignKeyConstraint(['legislatura_id'], ['legislaturas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate initiative_analytics with correct schema
    op.create_table('initiative_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deputado_id', sa.Integer(), nullable=False),
        sa.Column('legislatura_id', sa.Integer(), nullable=True),
        sa.Column('total_initiatives_authored', sa.Integer(), nullable=True),
        sa.Column('total_initiatives_co_authored', sa.Integer(), nullable=True),
        sa.Column('initiatives_approved', sa.Integer(), nullable=True),
        sa.Column('initiatives_pending', sa.Integer(), nullable=True),
        sa.Column('initiatives_rejected', sa.Integer(), nullable=True),
        sa.Column('initiatives_withdrawn', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.String(length=10), nullable=True),
        sa.Column('impact_score', sa.Integer(), nullable=True),
        sa.Column('avg_initiatives_per_month', sa.String(length=10), nullable=True),
        sa.Column('most_productive_month', sa.String(length=7), nullable=True),
        sa.Column('productivity_trend', sa.String(length=20), nullable=True),
        sa.Column('collaboration_score', sa.Integer(), nullable=True),
        sa.Column('cross_party_initiatives', sa.Integer(), nullable=True),
        sa.Column('leadership_ratio', sa.String(length=10), nullable=True),
        sa.Column('amendment_rate', sa.String(length=10), nullable=True),
        sa.Column('thematic_focus', sa.Text(), nullable=True),
        sa.Column('initiative_complexity_avg', sa.Integer(), nullable=True),
        sa.Column('first_initiative_date', sa.Date(), nullable=True),
        sa.Column('latest_initiative_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['deputado_id'], ['deputados.id'], ),
        sa.ForeignKeyConstraint(['legislatura_id'], ['legislaturas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate deputy_timeline with id_cadastro (not deputado_id)
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
    
    # Recreate data_quality_metrics with correct schema
    op.create_table('data_quality_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('legislatura_id', sa.Integer(), nullable=True),
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=True),
        sa.Column('complete_records', sa.Integer(), nullable=True),
        sa.Column('incomplete_records', sa.Integer(), nullable=True),
        sa.Column('completeness_percentage', sa.String(length=10), nullable=True),
        sa.Column('consistency_score', sa.Integer(), nullable=True),
        sa.Column('data_freshness_days', sa.Integer(), nullable=True),
        sa.Column('newest_record_date', sa.Date(), nullable=True),
        sa.Column('data_span_days', sa.Integer(), nullable=True),
        sa.Column('last_update_lag_hours', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['legislatura_id'], ['legislaturas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    """Revert to original analytics tables"""
    # This would require recreating the original tables with their complex constraints
    # Since we can recreate data, it's simpler to just drop them
    op.drop_table('data_quality_metrics')
    op.drop_table('deputy_timeline')
    op.drop_table('initiative_analytics')
    op.drop_table('attendance_analytics')
    op.drop_table('deputy_analytics')