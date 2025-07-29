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
"""

import os
import sys
import json
import argparse
import hashlib
import sqlite3
import xml.etree.ElementTree as ET
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import re
import logging

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


from mappers import SchemaMapper, SchemaError, RegistoBiograficoMapper, InitiativasMapper, IntervencoesMapper


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
    
    def __init__(self, db_path: str = "../../parlamento.db"):
        self.db_path = db_path
        self.data_roots = [
            "../../data/raw/downloads",
            "../../data/raw/parliament_data"
        ]
        self.file_type_resolver = FileTypeResolver()
        self.init_database()
        
        # Schema mappers registry
        self.schema_mappers = {
            'registo_biografico': RegistoBiograficoMapper,
            'iniciativas': InitiativasMapper,
            'intervencoes': IntervencoesMapper,
        }
    
    def init_database(self):
        """Initialize database with import_status table"""
        with sqlite3.connect(self.db_path) as conn:
            # Read and execute the migration
            migration_path = Path("../../database/migrations/create_import_status.sql")
            if migration_path.exists():
                with open(migration_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
                logger.info("Import status table initialized")
            else:
                logger.error("Migration file not found")
    
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
    
    def scan_all_files(self):
        """Discover and queue all files for processing"""
        logger.info("Starting file discovery...")
        total_files = 0
        queued_files = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for data_root in self.data_roots:
                if not os.path.exists(data_root):
                    logger.warning(f"Data root not found: {data_root}")
                    continue
                
                logger.info(f"Scanning data root: {data_root}")
                
                for root, dirs, files in os.walk(data_root):
                    for file in files:
                        if file.endswith(('.xml', '.json')) or file.endswith('_json.txt'):
                            file_path = os.path.join(root, file)
                            total_files += 1
                            
                            if self._should_queue_file(cursor, file_path):
                                self._queue_file(cursor, file_path)
                                queued_files += 1
                                
                                if queued_files % 100 == 0:
                                    logger.info(f"Queued {queued_files} files so far...")
            
            conn.commit()
        
        logger.info(f"File discovery complete: {total_files} files found, {queued_files} queued for processing")
    
    def _should_queue_file(self, cursor, file_path: str) -> bool:
        """Check if file should be queued (not already processed with same hash)"""
        file_hash = self.calculate_file_hash(file_path)
        if not file_hash:
            return False
        
        cursor.execute("""
            SELECT status FROM import_status 
            WHERE file_path = ? AND file_hash = ? AND status = 'completed'
        """, (file_path, file_hash))
        
        return cursor.fetchone() is None
    
    def _queue_file(self, cursor, file_path: str):
        """Queue file for processing"""
        file_hash = self.calculate_file_hash(file_path)
        file_name = os.path.basename(file_path)
        file_type = self.file_type_resolver.resolve_file_type(file_path)
        legislatura = self.file_type_resolver.extract_legislatura(file_path)
        
        # Determine category from file type
        category = file_type.replace('_', ' ').title() if file_type else 'Unknown'
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO import_status 
                (file_url, file_path, file_name, file_type, category, legislatura, 
                 file_hash, file_size, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """, (
                file_path,  # Using file_path as URL for local files
                file_path,
                file_name,
                file_type or 'unknown',
                category,
                legislatura,
                file_hash,
                os.path.getsize(file_path),
                datetime.now(),
                datetime.now()
            ))
        except Exception as e:
            logger.error(f"Error queuing file {file_path}: {e}")
    
    def import_pending_files(self, file_type_filter: Optional[str] = None, limit: Optional[int] = None):
        """Import all pending files"""
        logger.info("Starting import of pending files...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM import_status WHERE status = 'pending'"
            params = []
            
            if file_type_filter:
                query += " AND file_type LIKE ?"
                params.append(f"%{file_type_filter}%")
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            pending_files = cursor.fetchall()
        
        if not pending_files:
            logger.info("No pending files found")
            return
        
        logger.info(f"Found {len(pending_files)} pending files to process")
        
        processed = 0
        successful = 0
        
        for file_record in pending_files:
            try:
                success = self._process_single_file(file_record)
                if success:
                    successful += 1
                processed += 1
                
                if processed % 10 == 0:
                    logger.info(f"Processed {processed}/{len(pending_files)} files, {successful} successful")
                    
            except Exception as e:
                logger.error(f"Error processing file {file_record[2]}: {e}")
                processed += 1
        
        logger.info(f"Import complete: {processed} processed, {successful} successful")
    
    def _process_single_file(self, file_record: Tuple) -> bool:
        """Process a single file"""
        file_id = file_record[0]
        file_path = file_record[2]
        file_type = file_record[4]
        
        logger.info(f"Processing {file_type}: {os.path.basename(file_path)}")
        
        # Skip files we don't have mappers for yet
        if file_type not in self.schema_mappers:
            logger.warning(f"No schema mapper found for file type: {file_type}")
            self._update_file_status(file_id, 'failed', f"No mapper for type: {file_type}")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update status to processing
                self._update_file_status(file_id, 'processing', processing_started_at=datetime.now())
                
                # Load and parse XML
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Remove BOM if present
                if content.startswith(b'\\xef\\xbb\\xbf'):
                    content = content[3:]
                
                xml_root = ET.fromstring(content.decode('utf-8'))
                
                # Get appropriate schema mapper
                mapper_class = self.schema_mappers[file_type]
                mapper = mapper_class(conn)
                
                # Process file with schema validation
                file_info = {
                    'file_id': file_id,
                    'file_path': file_path,
                    'file_type': file_type
                }
                
                results = mapper.validate_and_map(xml_root, file_info)
                
                # Update status to completed
                self._update_file_status(
                    file_id, 'completed', 
                    records_imported=results['records_imported'],
                    processing_completed_at=datetime.now()
                )
                
                logger.info(f"Successfully processed {results['records_imported']} records")
                return True
                
        except SchemaError as e:
            logger.error(f"Schema validation failed: {e}")
            self._update_file_status(file_id, 'schema_mismatch', str(e))
            return False
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            self._update_file_status(file_id, 'failed', str(e))
            return False
    
    def _update_file_status(self, file_id: int, status: str, error_message: str = None, 
                           records_imported: int = 0, processing_started_at: datetime = None,
                           processing_completed_at: datetime = None):
        """Update file processing status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            update_fields = ["status = ?"]
            params = [status]
            
            if error_message:
                update_fields.append("error_message = ?")  
                params.append(error_message)
            
            if records_imported > 0:
                update_fields.append("records_imported = ?")
                params.append(records_imported)
            
            if processing_started_at:
                update_fields.append("processing_started_at = ?")
                params.append(processing_started_at)
            
            if processing_completed_at:
                update_fields.append("processing_completed_at = ?")
                params.append(processing_completed_at)
            
            update_fields.append("updated_at = ?")
            params.append(datetime.now())
            params.append(file_id)
            
            query = f"UPDATE import_status SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
    
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


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Unified Parliament Data Importer')
    parser.add_argument('--scan-all', action='store_true', 
                       help='Discover and queue all files for processing')
    parser.add_argument('--import-pending', action='store_true',
                       help='Import all pending files')
    parser.add_argument('--force-reimport', action='store_true',
                       help='Force reimport of all files (ignore SHA1)')
    parser.add_argument('--file-type', type=str,
                       help='Import only specific file type')
    parser.add_argument('--limit', type=int,
                       help='Limit number of files to process')
    parser.add_argument('--validate-schema', action='store_true',
                       help='Validate schema mapping coverage')
    parser.add_argument('--status', action='store_true',
                       help='Show import status summary')
    
    args = parser.parse_args()
    
    importer = UnifiedImporter()
    
    if args.scan_all:
        importer.scan_all_files()
    elif args.import_pending:
        importer.import_pending_files(file_type_filter=args.file_type, limit=args.limit)
    elif args.status:
        importer.show_status()
    elif args.validate_schema:
        importer.validate_schema_coverage(args.file_type)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()