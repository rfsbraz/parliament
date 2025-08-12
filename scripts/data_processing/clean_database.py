#!/usr/bin/env python
"""
Clean all data from the database to prepare for a fresh import
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from database.connection import DatabaseSession
from database.models import (
    Deputado, DeputadoMandatoLegislativo, Legislatura,
    Partido, Coligacao, ColigacaoPartido,
    DeputadoHabilitacao, DeputadoCargoFuncao,
    DeputadoTitulo, DeputadoCondecoracao,
    DeputadoObraPublicada, IntervencaoParlamentar,
    IntervencaoDeputado, IniciativaParlamentar,
    IniciativaAutorDeputado, IniciativaEvento,
    IniciativaEventoVotacao, AtividadeParlamentarVotacao,
    OrcamentoEstadoVotacao, OrcamentoEstadoGrupoParlamentarVoto,
    RegistoInteressesUnified, CirculoEleitoral,
    AtividadeDeputado, AtividadeParlamentar,
    ImportStatus
)
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_all_data():
    """Delete all data from the database"""
    
    with DatabaseSession() as session:
        try:
            logger.info("Starting database cleanup...")
            
            # Delete in reverse order of dependencies
            tables_to_clean = [
                # Voting and activity records
                OrcamentoEstadoGrupoParlamentarVoto,
                OrcamentoEstadoVotacao,
                AtividadeParlamentarVotacao,
                IniciativaEventoVotacao,
                IniciativaEvento,
                IniciativaAutorDeputado,
                IniciativaParlamentar,
                IntervencaoDeputado,
                IntervencaoParlamentar,
                
                # Deputy related data
                DeputadoObraPublicada,
                DeputadoCondecoracao,
                DeputadoTitulo,
                DeputadoCargoFuncao,
                DeputadoHabilitacao,
                DeputadoMandatoLegislativo,
                RegistoInteressesUnified,
                
                # Activity records
                AtividadeParlamentar,
                AtividadeDeputado,
                
                # Core entities
                ColigacaoPartido,
                Coligacao,
                Partido,
                Deputado,
                CirculoEleitoral,
                Legislatura,
                
                # Import tracking
                ImportStatus
            ]
            
            for table_class in tables_to_clean:
                count = session.query(table_class).count()
                if count > 0:
                    logger.info(f"Deleting {count} records from {table_class.__tablename__}...")
                    session.query(table_class).delete()
                    session.commit()
                    logger.info(f"  Deleted {count} records from {table_class.__tablename__}")
                else:
                    logger.info(f"  {table_class.__tablename__} is already empty")
            
            # Reset auto-increment counters (PostgreSQL specific)
            logger.info("Resetting auto-increment sequences...")
            for table_class in tables_to_clean:
                table_name = table_class.__tablename__
                # Find primary key column
                pk_cols = [col.name for col in table_class.__table__.primary_key.columns]
                if pk_cols:
                    pk_col = pk_cols[0]
                    sequence_name = f"{table_name}_{pk_col}_seq"
                    try:
                        session.execute(text(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1"))
                        logger.info(f"  Reset sequence {sequence_name}")
                    except Exception as e:
                        # Sequence might not exist for all tables
                        pass
            
            session.commit()
            logger.info("Database cleanup completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            session.rollback()
            raise

if __name__ == "__main__":
    response = input("WARNING: This will delete ALL data from the database. Are you sure? (yes/no): ")
    if response.lower() == 'yes':
        clean_all_data()
    else:
        logger.info("Cleanup cancelled.")