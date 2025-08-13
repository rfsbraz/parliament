#!/usr/bin/env python3
"""
Database-Driven Parliament Data Importer
=========================================

A database-driven importer that processes files based on ImportStatus table records.
Works with the discovery service and download manager to process files on-demand.

Features:
- Database-driven processing (no directory scanning)
- On-demand file downloading during import
- HTTP HEAD request change detection
- Integration with pipeline orchestrator
- Maintains all existing mapper functionality
"""

import hashlib
import logging
import os
import signal
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, List, Optional

import requests
from http_retry_utils import safe_request_get
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError, Timeout

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from database.connection import DatabaseSession
from database.models import ImportStatus
from scripts.data_processing.mappers import (
    AgendaParlamentarMapper,
    AtividadeDeputadosMapper,
    AtividadesMapper,
    ComposicaoOrgaosMapper,
    CooperacaoMapper,
    DelegacaoEventualMapper,
    DelegacaoPermanenteMapper,
    DiplomasAprovadosMapper,
    InformacaoBaseMapper,
    InitiativasMapper,
    IntervencoesMapper,
    OrcamentoEstadoMapper,
    PerguntasRequerimentosMapper,
    PeticoesMapper,
    RegistoBiograficoMapper,
    RegistoInteressesMapper,
    ReunioesNacionaisMapper,
)
from scripts.data_processing.file_type_resolver import FileTypeResolver

# Configure logging with Unicode-safe console handler
from utils.unicode_safe_logging import UnicodeSafeHandler

# Initialize logger (will be configured in main() for CLI usage)
logger = logging.getLogger(__name__)


class ChangeDetectionService:
    """Service for detecting file changes using HTTP HEAD requests"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def check_for_changes(self, import_record: ImportStatus) -> bool:
        """Check if a file has changed since last discovery/download"""
        try:
            response = self.session.head(import_record.file_url, timeout=10)
            response.raise_for_status()
            
            # Compare Last-Modified
            if 'Last-Modified' in response.headers:
                from email.utils import parsedate_to_datetime
                try:
                    server_modified = parsedate_to_datetime(response.headers['Last-Modified'])
                    if import_record.last_modified and server_modified != import_record.last_modified:
                        return True
                except:
                    pass
            
            # Compare Content-Length
            if 'Content-Length' in response.headers:
                try:
                    server_length = int(response.headers['Content-Length'])
                    if import_record.content_length and server_length != import_record.content_length:
                        return True
                except:
                    pass
            
            # Compare ETag
            if 'ETag' in response.headers:
                server_etag = response.headers['ETag']
                if import_record.etag and server_etag != import_record.etag:
                    return True
            
            return False
            
        except Exception as e:
            self._print(f"   Change detection error for {import_record.file_name}: {e}")
            return False  # Assume no change on error
    
    def update_metadata(self, import_record: ImportStatus) -> bool:
        """Update HTTP metadata for an import record"""
        try:
            response = self.session.head(import_record.file_url, timeout=10)
            response.raise_for_status()
            
            updated = False
            
            # Update Last-Modified
            if 'Last-Modified' in response.headers:
                from email.utils import parsedate_to_datetime
                try:
                    server_modified = parsedate_to_datetime(response.headers['Last-Modified'])
                    if server_modified != import_record.last_modified:
                        import_record.last_modified = server_modified
                        updated = True
                except:
                    pass
            
            # Update Content-Length
            if 'Content-Length' in response.headers:
                try:
                    server_length = int(response.headers['Content-Length'])
                    if server_length != import_record.content_length:
                        import_record.content_length = server_length
                        updated = True
                except:
                    pass
            
            # Update ETag
            if 'ETag' in response.headers:
                server_etag = response.headers['ETag']
                if server_etag != import_record.etag:
                    import_record.etag = server_etag
                    updated = True
            
            if updated:
                import_record.updated_at = datetime.now()
            
            return updated
            
        except Exception as e:
            self._print(f"   Metadata update error for {import_record.file_name}: {e}")
            return False


class DatabaseDrivenImporter:
    """Main database-driven importer class"""
    
    # Import order respecting foreign key dependencies (same as unified_importer)
    IMPORT_ORDER = [
        "atividade_deputados",
        "atividades", 
        "composicao_orgaos",
        "informacao_base",
        "registo_biografico",
        "agenda_parlamentar",
        "orcamento_estado",
        "iniciativas",
        "intervencoes",
        "peticoes",
        "perguntas_requerimentos",
        "diplomas_aprovados",
        "cooperacao",
        "delegacao_eventual",
        "delegacao_permanente",
        "registo_interesses",
    ]
    
    def __init__(self, allowed_file_types: List[str] = None, quiet: bool = False, orchestrator_mode: bool = False):
        self.file_type_resolver = FileTypeResolver()
        self.change_detection = ChangeDetectionService()
        self.allowed_file_types = allowed_file_types or ['XML']  # Default to XML only
        self.shutdown_requested = False
        self.quiet = quiet  # Suppress console output when True
        self.orchestrator_mode = orchestrator_mode  # Modify behavior for orchestrator integration
        
        # Configure logging for standalone mode
        if not self.orchestrator_mode and not self.quiet:
            self._setup_console_logging()
        
        # Retry configuration for exponential backoff
        self.min_retry_delay = 300  # 5 minutes minimum
        self.max_retry_delay = 86400  # 24 hours maximum
        self.retry_backoff_factor = 2.0  # Double delay each time
        
        # Schema mappers registry (same as unified_importer)
        self.schema_mappers = {
            "registo_biografico": RegistoBiograficoMapper,
            "iniciativas": InitiativasMapper,
            "intervencoes": IntervencoesMapper,
            "registo_interesses": RegistoInteressesMapper,
            "atividade_deputados": AtividadeDeputadosMapper,
            "agenda_parlamentar": AgendaParlamentarMapper,
            "atividades": AtividadesMapper,
            "composicao_orgaos": ComposicaoOrgaosMapper,
            "cooperacao": CooperacaoMapper,
            "delegacao_eventual": DelegacaoEventualMapper,
            "delegacao_permanente": DelegacaoPermanenteMapper,
            "informacao_base": InformacaoBaseMapper,
            "peticoes": PeticoesMapper,
            "perguntas_requerimentos": PerguntasRequerimentosMapper,
            "diplomas_aprovados": DiplomasAprovadosMapper,
            "orcamento_estado": OrcamentoEstadoMapper,
            "reunioes_visitas": ReunioesNacionaisMapper,
        }
    
    def _setup_console_logging(self):
        """Setup console logging for standalone mode"""
        # Only configure if not already configured
        if not logger.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler("database_driven_importer.log", encoding="utf-8"),
                    UnicodeSafeHandler(),  # Console handler with Unicode safety
                ],
            )
            logger.info("Database-driven importer logging configured for standalone mode")
    
    def _print(self, *args, **kwargs):
        """Print only if not in quiet mode"""
        if not self.quiet:
            print(*args, **kwargs)
    
    def set_shutdown_requested(self, value: bool):
        """Set shutdown request flag (for orchestrator integration)"""
        self.shutdown_requested = value
    
    def is_running(self) -> bool:
        """Check if importer should continue running"""
        return not self.shutdown_requested
    
    def get_import_statistics(self) -> Dict[str, int]:
        """Get import statistics for orchestrator integration"""
        with DatabaseSession() as db_session:
            from sqlalchemy import func
            
            # Query import statistics based on allowed file types
            query = db_session.query(ImportStatus)
            if self.allowed_file_types:
                query = query.filter(ImportStatus.file_type.in_(self.allowed_file_types))
            
            # Count by status
            completed = query.filter(ImportStatus.status == 'completed').count()
            failed = query.filter(ImportStatus.status.in_(['import_error', 'failed'])).count()
            pending = query.filter(ImportStatus.status.in_(['pending', 'discovered', 'download_pending'])).count()
            
            # Sum total records imported
            total_records = (
                query.filter(ImportStatus.status == 'completed')
                .with_entities(func.coalesce(func.sum(ImportStatus.records_imported), 0))
                .scalar() or 0
            )
            
            return {
                'completed': completed,
                'failed': failed,
                'pending': pending,
                'total_records': total_records
            }
    
    def _calculate_retry_time(self, error_count: int) -> datetime:
        """Calculate next retry time using exponential backoff"""
        # Calculate delay: min_delay * (backoff_factor ^ (error_count - 1))
        delay_seconds = self.min_retry_delay * (self.retry_backoff_factor ** (error_count - 1))
        
        # Cap at maximum delay
        delay_seconds = min(delay_seconds, self.max_retry_delay)
        
        # Add some jitter (±10%) to avoid thundering herd
        import random
        jitter = random.uniform(-0.1, 0.1)
        delay_seconds = delay_seconds * (1 + jitter)
        
        return datetime.now() + timedelta(seconds=int(delay_seconds))
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self._print(f"\n>> Received shutdown signal ({signal.Signals(signum).name})")
            self._print("   Finishing current file processing and shutting down gracefully...")
            self._print("   Press Ctrl+C again to force shutdown (not recommended)")
            self.shutdown_requested = True
        
        # Handle both SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    def process_pending_imports(self, 
                               file_type_filter: str = None,
                               legislatura_filter: str = None,
                               limit: int = None,
                               force_reimport: bool = False,
                               strict_mode: bool = False) -> Dict[str, int]:
        """Process all pending imports from the database"""
        stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'skipped': 0,
            'total_records': 0
        }
        
        self._print(f">> Starting database-driven import processing...")
        logger.info("Starting database-driven import processing")
        if not self.orchestrator_mode:
            self._print("   Press Ctrl+C to shutdown gracefully after current file completes")
        
        # Setup signal handlers for graceful shutdown (only in standalone mode)
        if not self.orchestrator_mode:
            self._setup_signal_handlers()
        
        # Show active file type filter
        if self.allowed_file_types:
            file_types_str = ", ".join(self.allowed_file_types)
            self._print(f"   Processing file types: {file_types_str}")
        else:
            self._print(f"   Processing all file types")
        
        if file_type_filter:
            self._print(f"   Additional category filter: {file_type_filter}")
        if legislatura_filter:
            self._print(f"   Filtering for legislatura: {legislatura_filter}")
        
        with DatabaseSession() as db_session:
            # Build query for files to process
            query = db_session.query(ImportStatus)
            
            if not force_reimport:
                # Only process files that haven't been completed or are ready for retry
                current_time = datetime.now()
                query = query.filter(
                    (ImportStatus.status.in_(['discovered', 'download_pending', 'pending'])) |
                    (ImportStatus.status == 'import_error') & 
                    ((ImportStatus.retry_at.is_(None)) | (ImportStatus.retry_at <= current_time))
                )
            
            # Apply class-level file type filter
            if self.allowed_file_types:
                query = query.filter(ImportStatus.file_type.in_(self.allowed_file_types))
            
            if file_type_filter:
                # Legacy filter support - map file type filter to category patterns
                category_pattern = self._get_category_pattern(file_type_filter)
                if category_pattern:
                    query = query.filter(ImportStatus.category.like(f"%{category_pattern}%"))
            
            if legislatura_filter:
                query = query.filter(ImportStatus.legislatura == legislatura_filter)
            
            # Order by import dependency order
            files_to_process = query.all()
            
            # Sort by import order
            if not file_type_filter:
                files_to_process = self._sort_by_import_order(files_to_process)
            
            if limit:
                files_to_process = files_to_process[:limit]
            
            total_files = len(files_to_process)
            self._print(f"   Found {total_files} files to process")
            logger.info(f"Found {total_files} files to process")
            
            if not files_to_process:
                self._print("   No files found matching criteria")
                logger.info("No files found matching criteria")
                return stats
            
            # Process each file
            for i, import_record in enumerate(files_to_process, 1):
                # Check for graceful shutdown request
                if self.shutdown_requested:
                    self._print(f"\n>> Shutdown requested. Stopping after processing {i-1}/{total_files} files.")
                    break
                
                self._print(f"\n[{i}/{total_files}] Processing: {import_record.file_name}")
                logger.info(f"Processing file {i}/{total_files}: {import_record.file_name}")
                
                try:
                    success = self._process_single_import(db_session, import_record, strict_mode)
                    
                    if success:
                        stats['succeeded'] += 1
                        stats['total_records'] += import_record.records_imported or 0
                        self._print(f"   Success: {import_record.records_imported or 0} records imported")
                        logger.info(f"Successfully processed {import_record.file_name}: {import_record.records_imported or 0} records imported")
                    else:
                        stats['failed'] += 1
                        self._print(f"   Failed: {import_record.error_message or 'Unknown error'}")
                        logger.error(f"Failed to process {import_record.file_name}: {import_record.error_message or 'Unknown error'}")
                    
                    stats['processed'] += 1
                    
                    # Commit after each file
                    db_session.commit()
                    
                except Exception as e:
                    stats['failed'] += 1
                    self._print(f"   Unexpected error: {e}")
                    logger.error(f"Unexpected error processing {import_record.file_name}: {e}")
                    db_session.rollback()
                    
                    if strict_mode:
                        self._print("   Strict mode: Stopping on error")
                        logger.warning("Strict mode: Stopping on error")
                        break
        
        self._print(f"\n>> Processing complete:")
        self._print(f"   Succeeded: {stats['succeeded']}")
        self._print(f"   Failed: {stats['failed']}")
        self._print(f"   Total records imported: {stats['total_records']}")
        
        logger.info(f"Processing complete: {stats['succeeded']} succeeded, {stats['failed']} failed, {stats['total_records']} total records imported")
        
        return stats
    
    def _process_single_import(self, db_session, import_record: ImportStatus, strict_mode: bool = False) -> bool:
        """Process a single import record"""
        try:
            # Check for shutdown request before starting
            if self.shutdown_requested:
                self._print(f"     Shutdown requested, skipping file")
                return False
            
            # Reset status from import_error to pending if retrying
            if import_record.status == 'import_error':
                self._print(f"     Retrying after error (attempt {import_record.error_count + 1})")
                import_record.status = 'pending'
                import_record.retry_at = None  # Clear retry timestamp
                
            # Check if we need to download the file
            if not self._has_file_content(import_record):
                self._print(f"     Downloading file...")
                logger.info(f"Downloading file: {import_record.file_name}")
                success = self._download_file(import_record)
                if not success:
                    logger.error(f"Failed to download file: {import_record.file_name}")
                    return False
            
            # Check for changes if not forced
            if import_record.status == 'completed':
                if not self.change_detection.check_for_changes(import_record):
                    self._print(f"     No changes detected, skipping")
                    return True
                else:
                    self._print(f"     Changes detected, reprocessing")
            
            # Update status to processing
            import_record.status = 'processing'
            import_record.processing_started_at = datetime.now()
            import_record.updated_at = datetime.now()
            db_session.commit()
            
            # Check for shutdown request after committing processing status
            if self.shutdown_requested:
                self._print(f"     Shutdown requested during processing, reverting to pending status")
                import_record.status = 'pending'
                import_record.processing_started_at = None
                import_record.updated_at = datetime.now()
                db_session.commit()
                return False
            
            # Resolve file type if not set
            if not import_record.category or import_record.category == 'Unknown':
                file_type = self.file_type_resolver.resolve_file_type(import_record.file_name)
                if file_type:
                    import_record.category = file_type.replace('_', ' ').title()
            
            # Get mapper for this file type
            mapper_key = self._get_mapper_key(import_record.category)
            if not mapper_key or mapper_key not in self.schema_mappers:
                error_msg = f"No mapper available for category: {import_record.category}"
                logger.error(f"No mapper available for category '{import_record.category}' in file: {import_record.file_name}")
                import_record.status = 'import_error'
                import_record.error_message = error_msg
                import_record.error_count = (import_record.error_count or 0) + 1
                import_record.retry_at = self._calculate_retry_time(import_record.error_count)
                import_record.processing_completed_at = datetime.now()
                import_record.updated_at = datetime.now()
                
                # Explicitly flush the error record updates to the database
                db_session.flush()
                return False
            
            # Parse XML content
            try:
                xml_content = self._get_file_content(import_record)
                xml_root = self._parse_xml_with_bom_handling(xml_content)
                
                file_info = {
                    "file_path": import_record.file_name,  # Use file name since we don't have local path
                    "file_type": mapper_key,
                    "file_hash": import_record.file_hash,
                    "skip_video_processing": True,  # Skip video processing for performance
                }
                
            except Exception as e:
                error_msg = f"XML parsing error: {str(e)}"
                logger.error(f"XML parsing error for {import_record.file_name}: {error_msg}")
                import_record.status = 'import_error'
                import_record.error_message = error_msg
                import_record.error_count = (import_record.error_count or 0) + 1
                import_record.retry_at = self._calculate_retry_time(import_record.error_count)
                import_record.processing_completed_at = datetime.now()
                return False
            
            # Process with mapper using the same session for transaction-per-file
            try:
                mapper_class = self.schema_mappers[mapper_key]
                mapper = mapper_class(db_session)  # Use the same session for transaction control
                results = mapper.validate_and_map(xml_root, file_info, strict_mode)
                
                # Update import record with results  
                import_record.status = 'completed'
                import_record.processing_completed_at = datetime.now()
                import_record.records_imported = results.get('records_imported', 0)
                import_record.error_message = (
                    "; ".join(results.get('errors', []))
                    if results.get('errors')
                    else None
                )
                import_record.updated_at = datetime.now()
                
                # Commit the entire transaction (mapper data + import status) together
                db_session.commit()
                
                return True
                    
            except Exception as e:
                # Rollback the failed transaction (both mapper data and import status changes)
                db_session.rollback()
                
                error_msg = f"Processing error: {str(e)}"
                import_record.status = 'import_error'
                import_record.error_message = error_msg
                import_record.error_count = (import_record.error_count or 0) + 1
                import_record.retry_at = self._calculate_retry_time(import_record.error_count)
                import_record.processing_completed_at = datetime.now()
                import_record.updated_at = datetime.now()
                
                # Commit only the error record (not the failed mapper data)
                db_session.commit()
                return False
                
        except Exception as e:
            # Rollback any changes from the outer try block
            db_session.rollback()
            
            import_record.status = 'import_error'
            import_record.error_message = f"Unexpected error: {str(e)}"
            import_record.error_count = (import_record.error_count or 0) + 1
            import_record.retry_at = self._calculate_retry_time(import_record.error_count)
            import_record.processing_completed_at = datetime.now()
            import_record.updated_at = datetime.now()
            
            # Commit only the error record
            db_session.commit()
            return False
    
    def _download_file(self, import_record: ImportStatus) -> bool:
        """Download file content and update record"""
        try:
            self._print(f"        Downloading from: {import_record.file_url}")
            
            response = safe_request_get(import_record.file_url)
            response.raise_for_status()
            
            # Calculate file hash
            file_hash = hashlib.sha1(response.content).hexdigest()
            
            # Store file metadata
            import_record.file_hash = file_hash
            import_record.file_size = len(response.content)
            import_record.status = 'pending'
            
            # Store content temporarily (in a real implementation, you might use Redis or file system)
            import_record._temp_content = response.content
            
            self._print(f"        Downloaded {len(response.content):,} bytes")
            return True
            
        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            import_record.status = 'import_error'
            import_record.error_message = error_msg
            import_record.error_count = (import_record.error_count or 0) + 1
            self._print(f"        Download failed: {error_msg}")
            return False
    
    def _has_file_content(self, import_record: ImportStatus) -> bool:
        """Check if file content is available"""
        # Check if file exists on disk
        if import_record.file_path and os.path.exists(import_record.file_path):
            return True
        # Check if content is in memory (for backward compatibility)
        return hasattr(import_record, '_temp_content') and import_record._temp_content
    
    def _get_file_content(self, import_record: ImportStatus) -> bytes:
        """Get file content for processing"""
        # Try to read from disk first
        if import_record.file_path and os.path.exists(import_record.file_path):
            with open(import_record.file_path, 'rb') as f:
                return f.read()
        
        # Fall back to memory content
        if hasattr(import_record, '_temp_content'):
            return import_record._temp_content
        
        # Last resort: re-download
        response = safe_request_get(import_record.file_url)
        response.raise_for_status()
        return response.content
    
    def _parse_xml_with_bom_handling(self, content: bytes) -> ET.Element:
        """Parse XML content with BOM handling (same logic as unified_importer)"""
        # Remove UTF-8 BOM if present
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
        elif content.startswith(b'\xfe\xff'):
            content = content[2:]
        elif content.startswith(b'\xff\xfe'):
            content = content[2:]
        
        # Remove non-ASCII characters before '<'
        while content and content[0:1] != b'<' and content[0] > 127:
            content = content[1:]
        
        # Try different encodings
        try:
            decoded_content = content.decode('utf-8')
            return ET.fromstring(decoded_content)
        except UnicodeDecodeError:
            try:
                decoded_content = content.decode('utf-16')
                return ET.fromstring(decoded_content)
            except UnicodeDecodeError:
                try:
                    decoded_content = content.decode('windows-1252')
                    return ET.fromstring(decoded_content)
                except UnicodeDecodeError:
                    decoded_content = content.decode('latin-1')
                    return ET.fromstring(decoded_content)
    
    def _get_category_pattern(self, file_type_filter: str) -> Optional[str]:
        """Map file type filter to category pattern"""
        mapping = {
            'biografico': 'Registo Biográfico',
            'iniciativas': 'Iniciativas',
            'intervencoes': 'Intervenções',
            'interesses': 'Registo',
            'deputados': 'Atividade Deputado',
            'agenda': 'Agenda',
            'atividades': 'Atividades',
            'orgaos': 'Composição',
            'cooperacao': 'Cooperação',
            'delegacao': 'Delegação',
            'informacao': 'Informação',
            'peticoes': 'Petições',
            'perguntas': 'Perguntas',
            'diplomas': 'Diplomas',
            'orcamento': 'Orçamento',
            'reunioes': 'Reuniões',
        }
        return mapping.get(file_type_filter.lower())
    
    def _get_mapper_key(self, category: str) -> Optional[str]:
        """Map category to mapper key"""
        if not category:
            return None
            
        category_lower = category.lower()
        
        if 'registo' in category_lower and 'biográfico' in category_lower:
            return 'registo_biografico'
        elif 'iniciativas' in category_lower:
            return 'iniciativas'
        elif 'intervenções' in category_lower:
            return 'intervencoes'
        elif 'registo' in category_lower and 'interesse' in category_lower:
            return 'registo_interesses'
        elif 'atividade' in category_lower and 'deputado' in category_lower:
            return 'atividade_deputados'
        elif 'agenda' in category_lower:
            return 'agenda_parlamentar'
        elif 'atividades' in category_lower:
            return 'atividades'
        elif 'composição' in category_lower or 'composicao' in category_lower:
            return 'composicao_orgaos'
        elif 'cooperação' in category_lower or 'cooperacao' in category_lower:
            return 'cooperacao'
        elif ('delegação' in category_lower or 'delegacao' in category_lower or 'delegacoes' in category_lower) and ('eventual' in category_lower or 'eventuais' in category_lower):
            return 'delegacao_eventual'
        elif ('delegação' in category_lower or 'delegacao' in category_lower or 'delegacoes' in category_lower) and ('permanente' in category_lower or 'permanentes' in category_lower):
            return 'delegacao_permanente'
        elif 'informação' in category_lower or 'informacao' in category_lower:
            return 'informacao_base'
        elif 'petições' in category_lower or 'peticoes' in category_lower:
            return 'peticoes'
        elif 'perguntas' in category_lower:
            return 'perguntas_requerimentos'
        elif 'diplomas' in category_lower:
            return 'diplomas_aprovados'
        elif 'orçamento' in category_lower or 'orcamento' in category_lower:
            return 'orcamento_estado'
        elif 'reuniões' in category_lower or 'reunioes' in category_lower:
            return 'reunioes_visitas'
        
        return None
    
    def _sort_by_import_order(self, import_records: List[ImportStatus]) -> List[ImportStatus]:
        """Sort import records by dependency order"""
        def get_order_index(record):
            mapper_key = self._get_mapper_key(record.category)
            if mapper_key in self.IMPORT_ORDER:
                return self.IMPORT_ORDER.index(mapper_key)
            return len(self.IMPORT_ORDER)  # Put unknown types at the end
        
        return sorted(import_records, key=get_order_index)

    def cleanup_database(self):
        """Drop all tables except ImportStatus and reset ImportStatus to 'discovered'"""
        try:
            logger.info("Starting database cleanup...")

            from sqlalchemy import text
            from database.connection import get_engine

            # Use centralized database connection
            engine = get_engine()
            connection = engine.connect()

            try:
                # Disable foreign key checks for MySQL
                connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

                # Get all table names
                result = connection.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result.fetchall()]

                logger.info(f"Found {len(tables)} tables")

                # Reset ImportStatus instead of dropping it
                if 'import_status' in tables:
                    logger.info("Resetting ImportStatus records to 'discovered' status...")
                    
                    # Count records before reset
                    count_result = connection.execute(text("SELECT COUNT(*) FROM import_status"))
                    total_records = count_result.fetchone()[0]
                    
                    # Reset all ImportStatus records to discovered state
                    reset_query = text("""
                        UPDATE import_status 
                        SET 
                            status = 'discovered',
                            processing_started_at = NULL,
                            processing_completed_at = NULL,
                            error_message = NULL,
                            records_imported = 0,
                            error_count = 0,
                            retry_at = NULL,
                            updated_at = NOW()
                        WHERE status != 'discovered'
                    """)
                    
                    reset_result = connection.execute(reset_query)
                    reset_count = reset_result.rowcount
                    
                    logger.info(f"Reset {reset_count} ImportStatus records out of {total_records} total records to 'discovered' status")

                # Drop all other tables except ImportStatus and alembic_version
                tables_to_preserve = {'import_status', 'alembic_version'}
                tables_to_drop = [table for table in tables if table not in tables_to_preserve]
                
                logger.info(f"Dropping {len(tables_to_drop)} tables (preserving ImportStatus and alembic_version)")

                for table_name in tables_to_drop:
                    connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                    logger.info(f"Dropped table: {table_name}")

                # Re-enable foreign key checks
                connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

                connection.commit()
                logger.info(
                    f"Database cleanup completed successfully. Dropped {len(tables_to_drop)} tables, preserved and reset ImportStatus"
                )

            finally:
                connection.close()

        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            raise

    def full_cleanup_database(self):
        """Drop ALL tables including ImportStatus (original cleanup behavior)"""
        try:
            logger.info("Starting FULL database cleanup (including ImportStatus)...")

            from sqlalchemy import text
            from database.connection import get_engine

            # Use centralized database connection
            engine = get_engine()
            connection = engine.connect()

            try:
                # Disable foreign key checks for MySQL
                connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

                # Get all table names
                result = connection.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result.fetchall()]

                logger.info(f"Found {len(tables)} tables to drop")

                # Drop all tables except alembic_version
                tables_to_drop = [table for table in tables if table != 'alembic_version']
                
                for table_name in tables_to_drop:
                    connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                    logger.info(f"Dropped table: {table_name}")

                # Re-enable foreign key checks
                connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

                connection.commit()
                logger.info(
                    f"FULL database cleanup completed successfully. Dropped {len(tables_to_drop)} tables"
                )

            finally:
                connection.close()

        except Exception as e:
            logger.error(f"FULL database cleanup failed: {e}")
            raise

    def show_status(self):
        """Show import status summary"""
        from sqlalchemy import case, func
        from database.connection import DatabaseSession
        from database.models import ImportStatus

        with DatabaseSession() as session:
            # Overall status summary
            status_summary = (
                session.query(
                    ImportStatus.status,
                    func.count().label("count"),
                    func.coalesce(func.sum(ImportStatus.records_imported), 0).label(
                        "total_imported"
                    ),
                )
                .group_by(ImportStatus.status)
                .order_by(func.count().desc())
                .all()
            )

            print("\\n" + "=" * 80)
            print("IMPORT STATUS SUMMARY")
            print("=" * 80)

            for status, count, imported in status_summary:
                print(f"{status.upper():20} {count:>8} files    {imported:>10} records")

            # File type breakdown
            file_type_summary = (
                session.query(
                    ImportStatus.file_type,
                    func.count().label("count"),
                    func.sum(
                        case((ImportStatus.status == "completed", 1), else_=0)
                    ).label("completed"),
                )
                .group_by(ImportStatus.file_type)
                .order_by(func.count().desc())
                .all()
            )

            print("\\n" + "-" * 80)
            print("FILE TYPE BREAKDOWN")
            print("-" * 80)

            for file_type, total, completed in file_type_summary:
                completion_rate = (completed / total * 100) if total > 0 else 0
                print(
                    f"{file_type:25} {total:>6} total    {completed:>6} done    {completion_rate:>5.1f}%"
                )

            # Enhanced statistics for retries and errors
            error_summary = (
                session.query(
                    func.count(case((ImportStatus.error_count > 0, 1))).label("files_with_errors"),
                    func.avg(case((ImportStatus.error_count > 0, ImportStatus.error_count))).label("avg_error_count"),
                    func.max(ImportStatus.error_count).label("max_error_count"),
                    func.count(case((ImportStatus.retry_at.isnot(None), 1))).label("files_pending_retry")
                )
                .first()
            )

            print("\\n" + "-" * 80)
            print("ERROR AND RETRY STATISTICS")
            print("-" * 80)
            
            print(f"Files with errors:     {error_summary.files_with_errors:>6}")
            print(f"Files pending retry:   {error_summary.files_pending_retry:>6}")
            print(f"Average error count:   {error_summary.avg_error_count:>6.1f}" if error_summary.avg_error_count else "Average error count:      0.0")
            print(f"Maximum error count:   {error_summary.max_error_count:>6}")


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database-Driven Parliament Data Importer")
    parser.add_argument('--file-type', type=str, help='Import only specific file type (legacy)')
    parser.add_argument('--file-types', nargs='*', 
                       choices=['XML', 'JSON', 'PDF', 'Archive', 'XSD'], 
                       default=['XML'],
                       help='File types to process (default: XML only)')
    parser.add_argument('--all-file-types', action='store_true',
                       help='Process all file types (overrides --file-types)')
    parser.add_argument('--legislatura', type=str, help='Import only specific legislatura')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--force-reimport', action='store_true',
                       help='Force reimport of completed files')
    parser.add_argument('--strict-mode', action='store_true',
                       help='Exit on first error')
    parser.add_argument('--watch', action='store_true',
                       help='Continuous mode: wait for new files instead of exiting')
    parser.add_argument('--watch-interval', type=int, default=10,
                       help='Seconds between checks for new files in watch mode (default: 10)')
    parser.add_argument('--log-level', type=str,
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       default='INFO',
                       help='Set logging level (default: INFO)')
    parser.add_argument('--status', action='store_true',
                       help='Show import status summary')
    parser.add_argument('--cleanup', action='store_true',
                       help='Drop all data tables (preserves ImportStatus and resets to "discovered")')
    parser.add_argument('--full-cleanup', action='store_true',
                       help='Drop ALL tables including ImportStatus (original cleanup behavior)')
    
    args = parser.parse_args()
    
    # Determine file types to process
    if args.all_file_types:
        allowed_file_types = None  # Process all file types
    elif args.file_type:  # Legacy support
        allowed_file_types = [args.file_type.upper()]
    else:
        allowed_file_types = args.file_types
    
    # Configure logging level for CLI usage
    log_level = getattr(logging, args.log_level.upper())
    logging.getLogger().setLevel(log_level)
    
    # Also update any existing handlers
    for handler in logging.getLogger().handlers:
        handler.setLevel(log_level)
    
    # Create and run importer with file type filter
    importer = DatabaseDrivenImporter(allowed_file_types=allowed_file_types)
    
    # Handle status, cleanup, and full-cleanup commands
    if args.status:
        importer.show_status()
        return
    elif args.cleanup:
        # Confirm cleanup action (preserves ImportStatus)
        print("WARNING: This will drop all data tables but preserve ImportStatus records!")
        print("All ImportStatus records will be reset to 'discovered' status for reprocessing.")
        confirmation = input("Are you sure you want to continue? (yes/no): ")
        if confirmation.lower() == "yes":
            importer.cleanup_database()
            print("Database cleanup completed successfully.")
        else:
            print("Cleanup cancelled.")
        return
    elif args.full_cleanup:
        # Confirm full cleanup action (drops everything)
        print("WARNING: This will drop ALL database tables including ImportStatus!")
        print("You will need to run discovery again to find files.")
        confirmation = input("Are you sure you want to continue? (yes/no): ")
        if confirmation.lower() == "yes":
            importer.full_cleanup_database()
            print("Full database cleanup completed successfully.")
        else:
            print("Full cleanup cancelled.")
        return
    
    if args.watch:
        # Continuous mode - watch for new files
        print(f">> Starting continuous import mode...")
        print(f"   File types: {', '.join(allowed_file_types) if allowed_file_types else 'ALL'}")
        if args.legislatura:
            print(f"   Legislature filter: {args.legislatura}")
        print(f"   Check interval: {args.watch_interval} seconds")
        print(f"   Press Ctrl+C to stop")
        
        import time
        import signal
        
        # Handle graceful shutdown
        def signal_handler(signum, frame):
            print(f"\n>> Received shutdown signal. Finishing current processing...")
            importer.set_shutdown_requested(True)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        total_stats = {'succeeded': 0, 'failed': 0, 'total_records': 0, 'processed': 0}
        
        try:
            while importer.is_running():
                # Process pending files
                stats = importer.process_pending_imports(
                    file_type_filter=args.file_type if args.file_type else None,
                    legislatura_filter=args.legislatura,
                    limit=args.limit,
                    force_reimport=args.force_reimport,
                    strict_mode=args.strict_mode
                )
                
                # Accumulate stats
                if stats['processed'] > 0:
                    total_stats['succeeded'] += stats['succeeded']
                    total_stats['failed'] += stats['failed'] 
                    total_stats['total_records'] += stats['total_records']
                    total_stats['processed'] += stats['processed']
                    
                    print(f">> Batch complete: {stats['succeeded']} successes, {stats['failed']} failures, {stats['total_records']} records")
                    print(f">> Session totals: {total_stats['succeeded']} successes, {total_stats['failed']} failures, {total_stats['total_records']} records")
                else:
                    print(f">> No pending files found, waiting {args.watch_interval} seconds...")
                
                # Wait before next check
                time.sleep(args.watch_interval)
                
        except KeyboardInterrupt:
            print(f"\n>> Keyboard interrupt received")
        finally:
            print(f"\n>> Watch mode completed:")
            print(f"   >> Total successes: {total_stats['succeeded']}")
            print(f"   >> Total failures: {total_stats['failed']}")
            print(f"   >> Total records imported: {total_stats['total_records']}")
    else:
        # Single run mode (original behavior)
        stats = importer.process_pending_imports(
            file_type_filter=args.file_type if args.file_type else None,  # Legacy support only
            legislatura_filter=args.legislatura,
            limit=args.limit,
            force_reimport=args.force_reimport,
            strict_mode=args.strict_mode
        )
        
        print(f"\n>> Import completed with {stats['succeeded']} successes, {stats['failed']} failures")


if __name__ == "__main__":
    main()