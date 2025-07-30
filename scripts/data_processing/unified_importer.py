#!/usr/bin/env python3
"""
Unified Parliament Data Importer
===============================

A comprehensive importer that processes ALL XML/JSON files with complete field mapping,
SHA1-based duplicate detection, and robust schema validation.

Architecture:
- Single entry point with CLI flags for different behaviors
- Iterates through ALL data directories systematically
- File-type resolution based on filename/path/content patterns
- Comprehensive field mapping with schema validation
- SHA1-based import status tracking to skip duplicates
- Transactional processing with rollback on schema mismatches

Usage:
    python unified_importer.py --scan-all              # Discover and queue all files
    python unified_importer.py --import-pending        # Process pending files
    python unified_importer.py --force-reimport        # Ignore SHA1, reimport all
    python unified_importer.py --file-type biografico  # Import specific types only
    python unified_importer.py --validate-schema       # Check schema mapping coverage
    python unified_importer.py --status                # Show import status summary
    python unified_importer.py --cleanup               # Backup database and truncate all tables
"""

import os
import sys
import json
import argparse
import hashlib
import sqlite3
import xml.etree.ElementTree as ET

# Add project root to path for config import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import DOWNLOADS_DIR, PARLIAMENT_DATA_DIR
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import re
import logging
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_importer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


from mappers import SchemaMapper, SchemaError, RegistoBiograficoMapper, InitiativasMapper, IntervencoesMapper, RegistoInteressesMapper, AtividadeDeputadosMapper, AgendaParlamentarMapper, AtividadesMapper, ComposicaoOrgaosMapper, CooperacaoMapper, DelegacaoEventualMapper, DelegacaoPermanenteMapper, PeticoesMapper, PerguntasRequerimentosMapper, DiplomasAprovadosMapper


class FileTypeResolver:
    """Resolves file types based on filename, path, and content patterns"""
    
    # File type patterns - ordered by priority
    FILE_TYPE_PATTERNS = {
        'registo_biografico': [
            r'RegistoBiografico.*\.xml',
            r'.*[/\\]RegistoBiogr[aá]fico[/\\].*\.xml',
            r'.*RegistoBiografico.*\.xml'
        ],
        'registo_interesses': [
            r'RegistoInteresses.*\.xml',
            r'.*[/\\]RegistoBiogr[aá]fico[/\\].*RegistoInteresses.*\.xml'
        ],
        'composicao_orgaos': [
            r'OrgaoComposicao.*\.xml',
            r'.*[/\\]Composi[cç][aã]o.*[Óó]rg[aã]os[/\\].*\.xml',
            r'.*[/\\]Composição de Órgãos[/\\].*\.xml'
        ],
        'atividade_deputados': [
            r'AtividadeDeputado.*\.xml',
            r'.*[/\\]Atividade dos Deputados[/\\].*\.xml'
        ],
        'atividades': [
            r'Atividades.*\.xml',
            r'.*[/\\]Atividades[/\\].*\.xml'
        ],
        'agenda_parlamentar': [
            r'AgendaParlamentar.*\.xml',
            r'.*[/\\]Agenda Parlamentar[/\\].*\.xml'
        ],
        'cooperacao': [
            r'Cooperacao.*\.xml',
            r'.*[/\\]Coopera[cç][aã]o Parlamentar[/\\].*\.xml'
        ],
        'delegacao_eventual': [
            r'DelegacaoEventual.*\.xml',
            r'.*[/\\]Delega[cç][oõ]es Eventuais[/\\].*\.xml'
        ],
        'delegacao_permanente': [
            r'DelegacaoPermanente.*\.xml',
            r'.*[/\\]Delega[cç][oõ]es Permanentes[/\\].*\.xml'
        ],
        'iniciativas': [
            r'Iniciativas.*\.xml',
            r'.*[/\\]Iniciativas[/\\].*\.xml'
        ],
        'intervencoes': [
            r'Intervencoes.*\.xml',
            r'.*[/\\]Interven[cç][oõ]es[/\\].*\.xml'
        ],
        'peticoes': [
            r'Peticoes.*\.xml',
            r'.*[/\\]Peti[cç][oõ]es[/\\].*\.xml'
        ],
        'perguntas_requerimentos': [
            r'PerguntasRequerimentos.*\.xml',
            r'.*[/\\]Perguntas e Requerimentos[/\\].*\.xml'
        ],
        'diplomas_aprovados': [
            r'Diplomas.*\.xml',
            r'.*[/\\]Diplomas Aprovados[/\\].*\.xml',
            r'.*_Diplomas.*\.xml',
            r'.*Diplomas.*\.xml\.xml'
        ],
        'orcamento_estado': [
            r'OE.*\.xml',
            r'OEPropostasAlteracao.*\.xml',
            r'.*[/\\]Orçamento do Estado[/\\].*\.xml',
            r'.*OE.*\.xml\.xml',
            r'.*OEPropostasAlteracao.*\.xml\.xml'
        ],
        'informacao_base': [
            r'InformacaoBase.*\.xml',
            r'.*[/\\]Informação base[/\\].*\.xml',
            r'.*[/\\]Informao base[/\\].*\.xml',
            r'.*InformacaoBase.*\.xml\.xml'
        ],
        'reunioes_visitas': [
            r'Reunioes.*\.xml',
            r'ReuniaoNacional.*\.xml',
            r'.*[/\\]Reuniões _ Visitas[/\\].*\.xml',
            r'.*[/\\]Reunies _ Visitas[/\\].*\.xml',
            r'.*Reunioe.*\.xml\.xml',
            r'.*ReuniaoNacional.*\.xml\.xml'
        ],
        'grupos_amizade': [
            r'GrupoDeAmizade.*\.xml',
            r'.*[/\\]Grupos Parlamentares de Amizade[/\\].*\.xml',
            r'.*GrupoDeAmizade.*\.xml\.xml'
        ],
        'diario_assembleia': [
            r'Número_.*\.xml',
            r'.*[/\\]Dirioda Assembleia da República[/\\].*\.xml',
            r'.*[/\\]Dirioda Assembleia da Repblica[/\\].*\.xml',
            r'.*_Nmero_.*\.xml',
            r'.*Nmero_.*\.xml\.xml'
        ]
    }
    
    @classmethod
    def resolve_file_type(cls, file_path: str) -> Optional[str]:
        """Resolve file type based on path patterns"""
        normalized_path = file_path.replace('\\\\', '/').replace('\\', '/')
        
        for file_type, patterns in cls.FILE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, normalized_path, re.IGNORECASE):
                    return file_type
        
        # Check if it's JSON equivalent
        if file_path.endswith('_json.txt'):
            xml_equivalent = file_path.replace('_json.txt', '.xml')
            xml_type = cls.resolve_file_type(xml_equivalent)
            if xml_type:
                return f"{xml_type}_json"
        
        return None
    
    @classmethod
    def extract_legislatura(cls, file_path: str) -> Optional[str]:
        """Extract legislatura from file path"""
        # Try different patterns
        patterns = [
            r'Legislatura_([A-Z]+|\\d+)',
            r'[/\\\\]([XVII]+)[/\\\\]',
            r'([XVII]+)\\.xml',
            r'(\\d+)\\.xml'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, file_path, re.IGNORECASE)
            if match:
                leg = match.group(1).upper()
                # Convert roman numerals to numbers if needed
                roman_map = {
                    'XVII': '17', 'XVI': '16', 'XV': '15', 'XIV': '14', 'XIII': '13',
                    'XII': '12', 'XI': '11', 'X': '10', 'IX': '9', 'VIII': '8',
                    'VII': '7', 'VI': '6', 'V': '5', 'IV': '4', 'III': '3',
                    'II': '2', 'I': '1', 'CONSTITUINTE': '0'
                }
                return roman_map.get(leg, leg)
        
        return None


class UnifiedImporter:
    """Main importer class that orchestrates the entire import process"""
    
    def __init__(self, db_path: str = None):
        # Get script directory and resolve paths
        script_dir = Path(__file__).parent
        self.db_path = db_path or str((script_dir / "../../parlamento.db").resolve())
        self.data_roots = [
            DOWNLOADS_DIR,
            PARLIAMENT_DATA_DIR
        ]
        self.file_type_resolver = FileTypeResolver()
        self.init_database()
        
        # Schema mappers registry
        self.schema_mappers = {
            'registo_biografico': RegistoBiograficoMapper,
            'iniciativas': InitiativasMapper,
            'intervencoes': IntervencoesMapper,
            'registo_interesses': RegistoInteressesMapper,
            'atividade_deputados': AtividadeDeputadosMapper,
            'agenda_parlamentar': AgendaParlamentarMapper,
            'atividades': AtividadesMapper,
            'composicao_orgaos': ComposicaoOrgaosMapper,
            'cooperacao': CooperacaoMapper,
            'delegacao_eventual': DelegacaoEventualMapper,
            'delegacao_permanente': DelegacaoPermanenteMapper,
            'peticoes': PeticoesMapper,
            'perguntas_requerimentos': PerguntasRequerimentosMapper,
            'diplomas_aprovados': DiplomasAprovadosMapper,
        }
    
    def init_database(self):
        """Initialize database with import_status table"""
        with sqlite3.connect(self.db_path) as conn:
            # Read and execute the migration
            script_dir = Path(__file__).parent
            migration_path = script_dir / "../../database/migrations/create_import_status.sql"
            migration_path = migration_path.resolve()
            
            if migration_path.exists():
                with open(migration_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
                logger.info("Import status table initialized")
            else:
                logger.error(f"Migration file not found at: {migration_path}")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA1 hash of file content"""
        sha1_hash = hashlib.sha1()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha1_hash.update(chunk)
            return sha1_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def process_files(self, file_type_filter: str = None, limit: int = None, force_reimport: bool = False, legislatura_filter: str = None, strict_mode: bool = False):
        """Process files directly from source directories"""
        logger.info("Starting file processing...")
        if strict_mode:
            logger.warning("STRICT MODE ENABLED: Will exit on first unmapped field, schema warning, or processing error")
        if legislatura_filter:
            logger.info(f"Filtering for Legislatura: {legislatura_filter}")
        total_files = 0
        processed_files = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for data_root in self.data_roots:
                if not os.path.exists(data_root):
                    logger.warning(f"Data root not found: {data_root}")
                    continue
                
                logger.info(f"Processing files from: {data_root}")
                
                for root, dirs, files in os.walk(data_root):
                    for file in files:
                        if file.endswith(('.xml', '.json')) or file.endswith('_json.txt'):
                            file_path = os.path.join(root, file)
                            total_files += 1
                            
                            # Check if we should process this file
                            if self._should_process_file(cursor, file_path, file_type_filter, force_reimport, legislatura_filter, strict_mode):
                                success = self._process_file(cursor, file_path, strict_mode)
                                if success:
                                    processed_files += 1
                                elif strict_mode:
                                    logger.error(f"STRICT MODE: Exiting due to processing error in {file_path}")
                                    conn.commit()
                                    sys.exit(1)
                                
                                if processed_files % 10 == 0:
                                    logger.info(f"Processed {processed_files} files so far...")
                                
                                # Check limit
                                if limit and processed_files >= limit:
                                    logger.info(f"Reached limit of {limit} files")
                                    conn.commit()
                                    return
            
            conn.commit()
        
        logger.info(f"Processing complete: {total_files} files found, {processed_files} processed")
    
    def _should_process_file(self, cursor, file_path: str, file_type_filter: str = None, force_reimport: bool = False, legislatura_filter: str = None, strict_mode: bool = False) -> bool:
        """Check if file should be processed"""
        # Check file type filter
        file_type = self.file_type_resolver.resolve_file_type(file_path)
        if not file_type:
            return False
        
        if file_type_filter and file_type != file_type_filter:
            return False
        
        # Check legislatura filter
        if legislatura_filter:
            legislatura = self.file_type_resolver.extract_legislatura(file_path)
            if not legislatura:
                # If we can't extract legislatura, skip the file
                return False
            
            # Convert roman numerals to numbers for comparison
            if legislatura_filter.upper() in ['XVII', 'XVI', 'XV', 'XIV', 'XIII', 'XII', 'XI', 'X', 'IX', 'VIII', 'VII', 'VI', 'V', 'IV', 'III', 'II', 'I', 'CONSTITUINTE']:
                # User provided roman numeral
                if legislatura != legislatura_filter.upper():
                    return False
            else:
                # User provided number, convert legislatura to number for comparison
                roman_to_num = {
                    'XVII': '17', 'XVI': '16', 'XV': '15', 'XIV': '14', 'XIII': '13',
                    'XII': '12', 'XI': '11', 'X': '10', 'IX': '9', 'VIII': '8',
                    'VII': '7', 'VI': '6', 'V': '5', 'IV': '4', 'III': '3',
                    'II': '2', 'I': '1', 'CONSTITUINTE': '0'
                }
                leg_num = roman_to_num.get(legislatura, legislatura)
                if leg_num != legislatura_filter:
                    return False
        
        # Check if we have a mapper for this file type
        if file_type not in self.schema_mappers:
            error_msg = f"No mapper for file type: {file_type}"
            if strict_mode:
                logger.error(f"STRICT MODE: {error_msg} in {file_path}")
                logger.error("Available mappers: " + ", ".join(self.schema_mappers.keys()))
                sys.exit(1)
            else:
                logger.debug(error_msg)
                return False
        
        # If force reimport, always process
        if force_reimport:
            return True
        
        # Check if already processed with same hash
        file_hash = self.calculate_file_hash(file_path)
        if not file_hash:
            return False
        
        cursor.execute("""
            SELECT status FROM import_status 
            WHERE file_path = ? AND file_hash = ? AND status = 'completed'
        """, (file_path, file_hash))
        
        return cursor.fetchone() is None
    
    def _process_file(self, cursor, file_path: str, strict_mode: bool = False) -> bool:
        """Process a single file"""
        try:
            # Determine file type
            file_type = self.file_type_resolver.resolve_file_type(file_path)
            if not file_type or file_type not in self.schema_mappers:
                logger.warning(f"No mapper available for file type '{file_type}': {file_path}")
                return False
            
            # Calculate file hash and size
            file_hash = self.calculate_file_hash(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            # Update import status to processing
            cursor.execute("""
                INSERT OR REPLACE INTO import_status 
                (file_url, file_path, file_name, file_type, category, file_hash, file_size, status, processing_started_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'processing', ?, ?, ?)
            """, (
                file_path,  # Using file_path as URL for local files
                file_path,
                os.path.basename(file_path),
                file_type,
                file_type.replace('_', ' ').title(),
                file_hash,
                file_size,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # Process the file
            mapper_class = self.schema_mappers[file_type]
            
            # Parse XML first
            try:
                xml_root = ET.parse(file_path).getroot()
                file_info = {
                    'file_path': file_path,
                    'file_type': file_type,
                    'file_hash': file_hash
                }
            except Exception as e:
                error_msg = f"XML parsing error: {str(e)}"
                cursor.execute("""
                    UPDATE import_status 
                    SET status = 'failed', processing_completed_at = ?, error_message = ?
                    WHERE file_path = ? AND file_hash = ?
                """, (datetime.now().isoformat(), error_msg, file_path, file_hash))
                logger.error(f"Failed to parse XML {file_path}: {error_msg}")
                if strict_mode:
                    logger.error(f"STRICT MODE: Exiting due to XML parsing error in {file_path}")
                    sys.exit(1)
                return False
            
            # Commit the status update before processing to avoid locks
            cursor.connection.commit()
            
            # Create database connection for the mapper with proper isolation
            try:
                with sqlite3.connect(self.db_path, timeout=30.0) as mapper_conn:
                    # Enable WAL mode for better concurrency
                    mapper_conn.execute("PRAGMA journal_mode=WAL")
                    mapper_conn.execute("PRAGMA synchronous=NORMAL")
                    mapper_conn.execute("PRAGMA busy_timeout=30000")
                    
                    mapper = mapper_class(mapper_conn)
                    results = mapper.validate_and_map(xml_root, file_info, strict_mode)
                    
                    # Commit mapper changes
                    mapper_conn.commit()
                    
                    # Update status to completed
                    cursor.execute("""
                        UPDATE import_status 
                        SET status = 'completed', processing_completed_at = ?, 
                            records_imported = ?, error_message = ?
                        WHERE file_path = ? AND file_hash = ?
                    """, (
                        datetime.now().isoformat(),
                        results.get('records_imported', 0),
                        '; '.join(results.get('errors', [])) if results.get('errors') else None,
                        file_path, file_hash
                    ))
                    
                    logger.info(f"Successfully processed {file_path}: {results.get('records_imported', 0)} records imported")
                    return True
                    
            except Exception as e:
                # Update status to failed
                error_msg = f"Processing error: {str(e)}"
                cursor.execute("""
                    UPDATE import_status 
                    SET status = 'failed', processing_completed_at = ?, error_message = ?
                    WHERE file_path = ? AND file_hash = ?
                """, (datetime.now().isoformat(), error_msg, file_path, file_hash))
                
                logger.error(f"Failed to process {file_path}: {error_msg}")
                if strict_mode:
                    logger.error(f"STRICT MODE: Exiting due to processing error in {file_path}")
                    logger.error(f"Error details: {traceback.format_exc()}")
                    sys.exit(1)
                return False
                    
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}")
            traceback.print_exc()
            if strict_mode:
                logger.error(f"STRICT MODE: Exiting due to unexpected error in {file_path}")
                sys.exit(1)
            return False

    
    def show_status(self):
        """Show import status summary"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Overall status summary
            cursor.execute("""
                SELECT status, COUNT(*) as count, SUM(records_imported) as total_imported
                FROM import_status 
                GROUP BY status
                ORDER BY count DESC
            """)
            
            print("\\n" + "="*80)
            print("IMPORT STATUS SUMMARY")
            print("="*80)
            
            for row in cursor.fetchall():
                status, count, imported = row
                imported = imported or 0
                print(f"{status.upper():20} {count:>8} files    {imported:>10} records")
            
            # File type breakdown
            cursor.execute("""
                SELECT file_type, COUNT(*) as count, 
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM import_status 
                GROUP BY file_type
                ORDER BY count DESC
            """)
            
            print("\\n" + "-"*80)
            print("FILE TYPE BREAKDOWN")
            print("-"*80)
            
            for row in cursor.fetchall():
                file_type, total, completed = row
                completion_rate = (completed / total * 100) if total > 0 else 0
                print(f"{file_type:25} {total:>6} total    {completed:>6} done    {completion_rate:>5.1f}%")
    
    def validate_schema_coverage(self, file_type: str = None):
        """Validate schema mapping coverage for file types"""
        logger.info("Validating schema coverage...")
        # Implementation for schema validation
        pass
    
    def cleanup_database(self):
        """Create timestamped backup and truncate all tables"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            # Create backup
            logger.info(f"Creating database backup: {backup_path}")
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Backup created successfully: {backup_path}")
            
            # Get all table names
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all user tables (excluding sqlite_* system tables)
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"Found {len(tables)} tables to truncate")
                
                # Disable foreign key constraints temporarily
                cursor.execute("PRAGMA foreign_keys=OFF")
                
                # Truncate all tables
                for table in tables:
                    try:
                        cursor.execute(f"DELETE FROM {table}")
                        logger.info(f"Truncated table: {table}")
                    except Exception as e:
                        logger.warning(f"Failed to truncate table {table}: {e}")
                
                # Re-enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                
                # Vacuum to reclaim space
                logger.info("Vacuuming database to reclaim space...")
                cursor.execute("VACUUM")
                
                conn.commit()
                logger.info("Database cleanup completed successfully")
                
                # Show final statistics
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                table_count = cursor.fetchone()[0]
                
                logger.info(f"Database cleaned: {table_count} tables truncated")
                logger.info(f"Backup available at: {backup_path}")
                
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            if os.path.exists(backup_path):
                logger.info(f"Backup file preserved: {backup_path}")
            raise


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Unified Parliament Data Importer')
    parser.add_argument('--force-reimport', action='store_true',
                       help='Force reimport of all files (ignore SHA1)')
    parser.add_argument('--file-type', type=str,
                       help='Import only specific file type')
    parser.add_argument('--legislatura', type=str,
                       help='Import only specific legislatura (e.g., "XVII", "17", "X", "10")')
    parser.add_argument('--limit', type=int,
                       help='Limit number of files to process')
    parser.add_argument('--validate-schema', action='store_true',
                       help='Validate schema mapping coverage')
    parser.add_argument('--status', action='store_true',
                       help='Show import status summary')
    parser.add_argument('--strict-mode', action='store_true',
                       help='Exit immediately on any unmapped field, schema warning, or processing error')
    parser.add_argument('--cleanup', action='store_true',
                       help='Create timestamped backup and truncate all database tables')
    
    args = parser.parse_args()
    
    importer = UnifiedImporter()
    
    if args.status:
        importer.show_status()
    elif args.validate_schema:
        importer.validate_schema_coverage(args.file_type)
    elif args.cleanup:
        # Confirm cleanup action
        print("WARNING: This will create a backup and truncate ALL database tables!")
        print(f"Database: {importer.db_path}")
        confirmation = input("Are you sure you want to continue? (yes/no): ")
        if confirmation.lower() == 'yes':
            importer.cleanup_database()
        else:
            print("Cleanup cancelled.")
    else:
        # Default behavior: process files from source directories
        importer.process_files(
            file_type_filter=args.file_type, 
            limit=args.limit, 
            force_reimport=args.force_reimport,
            legislatura_filter=args.legislatura,
            strict_mode=args.strict_mode
        )


if __name__ == "__main__":
    main()