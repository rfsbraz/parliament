"""Add critical performance indexes for high-volume tables

Revision ID: 9cb2036b4e70
Revises: 6d4e12845f07
Create Date: 2025-08-04 08:38:10.101807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9cb2036b4e70'
down_revision: Union[str, Sequence[str], None] = '6d4e12845f07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with critical performance indexes for high-volume tables."""
    
    # Phase 1A: meeting_attendances table indexes (848k+ rows)
    # Primary lookup patterns: by dep_id, by meeting date, by presence status
    # Corrected field names based on actual schema
    op.create_index(
        'idx_meeting_attendances_dep_lookup',
        'meeting_attendances',
        ['dep_id', 'dt_reuniao']
    )
    
    op.create_index(
        'idx_meeting_attendances_presence_status',
        'meeting_attendances', 
        ['pres_tipo', 'dt_reuniao'],
        mysql_length={'pres_tipo': 50}
    )
    
    op.create_index(
        'idx_meeting_attendances_session_performance',
        'meeting_attendances',
        ['dt_reuniao', 'dep_id', 'pres_tipo'],
        mysql_length={'pres_tipo': 50}
    )
    
    # Phase 1B: iniciativas_detalhadas table indexes (1.1M+ rows)
    # Primary lookup patterns: by legislature, by initiative type, by dates
    # Corrected field names based on actual schema
    op.create_index(
        'idx_iniciativas_legislatura_tipo',
        'iniciativas_detalhadas',
        ['legislatura_id', 'ini_tipo'],
        mysql_length={'ini_tipo': 100}
    )
    
    op.create_index(
        'idx_iniciativas_data_periodo', 
        'iniciativas_detalhadas',
        ['data_inicio_leg', 'data_fim_leg']
    )
    
    op.create_index(
        'idx_iniciativas_leg_periodo',
        'iniciativas_detalhadas', 
        ['ini_leg', 'legislatura_id'],
        mysql_length={'ini_leg': 20}
    )
    
    op.create_index(
        'idx_iniciativas_number_leg',
        'iniciativas_detalhadas',
        ['ini_nr', 'ini_leg', 'ini_tipo'],
        mysql_length={'ini_leg': 20, 'ini_tipo': 100}
    )
    
    # Phase 1C: deputados table optimization indexes 
    # Primary lookup patterns: active deputies, by name, biographical data
    # Note: schema shows 'ativo' field (tinyint) and no separate legislature/party/mandate fields
    op.create_index(
        'idx_deputados_active_lookup',
        'deputados',
        ['ativo', 'nome'],
        mysql_length={'nome': 200}
    )
    
    op.create_index(
        'idx_deputados_biographical',
        'deputados',
        ['data_nascimento', 'naturalidade'],
        mysql_length={'naturalidade': 100}
    )
    
    # Phase 1D: intervencao_parlamentar table indexes (149k+ rows) 
    # Primary lookup patterns: by date, by type, by session
    # Corrected field names based on actual schema
    op.create_index(
        'idx_intervencao_data_tipo',
        'intervencao_parlamentar',
        ['data_reuniao_plenaria', 'tipo_intervencao'],
        mysql_length={'tipo_intervencao': 200}
    )
    
    op.create_index(
        'idx_intervencao_sessao_legislatura',
        'intervencao_parlamentar',
        ['sessao_numero', 'legislatura_id'],
        mysql_length={'sessao_numero': 50}
    )
    
    op.create_index(
        'idx_intervencao_legislatura_data',
        'intervencao_parlamentar',
        ['legislatura_id', 'data_reuniao_plenaria', 'tipo_intervencao'],
        mysql_length={'tipo_intervencao': 200}
    )
    
    # Phase 1E: Interest registry performance indexes
    # For registo_interesses and registo_interesses_v2 tables
    # Field names confirmed from actual schema
    op.create_index(
        'idx_registo_interesses_deputado_lookup',
        'registo_interesses',
        ['deputado_id', 'cad_id']
    )
    
    op.create_index(
        'idx_registo_interesses_v2_deputado_lookup', 
        'registo_interesses_v2',
        ['deputado_id', 'cad_id']
    )


def downgrade() -> None:
    """Downgrade schema by removing performance indexes."""
    
    # Remove in reverse order for safety
    op.drop_index('idx_registo_interesses_v2_deputado_lookup', table_name='registo_interesses_v2')
    op.drop_index('idx_registo_interesses_deputado_lookup', table_name='registo_interesses')
    
    op.drop_index('idx_intervencao_legislatura_data', table_name='intervencao_parlamentar')
    op.drop_index('idx_intervencao_sessao_legislatura', table_name='intervencao_parlamentar')
    op.drop_index('idx_intervencao_data_tipo', table_name='intervencao_parlamentar')
    
    op.drop_index('idx_deputados_biographical', table_name='deputados')
    op.drop_index('idx_deputados_active_lookup', table_name='deputados')
    
    op.drop_index('idx_iniciativas_number_leg', table_name='iniciativas_detalhadas')
    op.drop_index('idx_iniciativas_leg_periodo', table_name='iniciativas_detalhadas')
    op.drop_index('idx_iniciativas_data_periodo', table_name='iniciativas_detalhadas')
    op.drop_index('idx_iniciativas_legislatura_tipo', table_name='iniciativas_detalhadas')
    
    op.drop_index('idx_meeting_attendances_session_performance', table_name='meeting_attendances')
    op.drop_index('idx_meeting_attendances_presence_status', table_name='meeting_attendances')
    op.drop_index('idx_meeting_attendances_dep_lookup', table_name='meeting_attendances')
