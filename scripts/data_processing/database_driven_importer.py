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
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional

import requests
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
from scripts.data_processing.unified_importer import FileTypeResolver


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
            print(f"⚠️  Change detection error for {import_record.file_name}: {e}")
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
            print(f"⚠️  Metadata update error for {import_record.file_name}: {e}")
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
    
    def __init__(self):
        self.file_type_resolver = FileTypeResolver()
        self.change_detection = ChangeDetectionService()
        
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
        
        print(f"🔄 Starting database-driven import processing...")
        if file_type_filter:
            print(f"📂 Filtering for file type: {file_type_filter}")
        if legislatura_filter:
            print(f"🏛️  Filtering for legislatura: {legislatura_filter}")
        
        with DatabaseSession() as db_session:
            # Build query for files to process
            query = db_session.query(ImportStatus)
            
            if not force_reimport:
                # Only process files that haven't been completed
                query = query.filter(
                    ImportStatus.status.in_(['discovered', 'download_pending', 'pending'])
                )
            
            if file_type_filter:
                # Map file type filter to category patterns
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
            print(f"📋 Found {total_files} files to process")
            
            if not files_to_process:
                print("ℹ️  No files found matching criteria")
                return stats
            
            # Process each file
            for i, import_record in enumerate(files_to_process, 1):
                print(f"\n[{i}/{total_files}] Processing: {import_record.file_name}")
                
                try:
                    success = self._process_single_import(db_session, import_record, strict_mode)
                    
                    if success:
                        stats['succeeded'] += 1
                        stats['total_records'] += import_record.records_imported or 0
                        print(f"✅ Success: {import_record.records_imported or 0} records imported")
                    else:
                        stats['failed'] += 1
                        print(f"❌ Failed: {import_record.error_message or 'Unknown error'}")
                    
                    stats['processed'] += 1
                    
                    # Commit after each file
                    db_session.commit()
                    
                except Exception as e:
                    stats['failed'] += 1
                    print(f"❌ Unexpected error: {e}")
                    db_session.rollback()
                    
                    if strict_mode:
                        print("🛑 Strict mode: Stopping on error")
                        break
        
        print(f"\n📊 Processing complete:")
        print(f"   ✅ Succeeded: {stats['succeeded']}")
        print(f"   ❌ Failed: {stats['failed']}")
        print(f"   📊 Total records imported: {stats['total_records']}")
        
        return stats
    
    def _process_single_import(self, db_session, import_record: ImportStatus, strict_mode: bool = False) -> bool:
        """Process a single import record"""
        try:
            # Check if we need to download the file
            if not self._has_file_content(import_record):
                print(f"  ⬇️  Downloading file...")
                success = self._download_file(import_record)
                if not success:
                    return False
            
            # Check for changes if not forced
            if import_record.status == 'completed':
                if not self.change_detection.check_for_changes(import_record):
                    print(f"  ⏭️  No changes detected, skipping")
                    return True
                else:
                    print(f"  🔄 Changes detected, reprocessing")
            
            # Update status to processing
            import_record.status = 'processing'
            import_record.processing_started_at = datetime.now()
            import_record.updated_at = datetime.now()
            db_session.commit()
            
            # Resolve file type if not set
            if not import_record.category or import_record.category == 'Unknown':
                file_type = self.file_type_resolver.resolve_file_type(import_record.file_name)
                if file_type:
                    import_record.category = file_type.replace('_', ' ').title()
            
            # Get mapper for this file type
            mapper_key = self._get_mapper_key(import_record.category)
            if not mapper_key or mapper_key not in self.schema_mappers:
                error_msg = f"No mapper available for category: {import_record.category}"
                import_record.status = 'failed'
                import_record.error_message = error_msg
                import_record.processing_completed_at = datetime.now()
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
                import_record.status = 'failed'
                import_record.error_message = error_msg
                import_record.processing_completed_at = datetime.now()
                return False
            
            # Process with mapper
            try:
                from database.connection import DatabaseSession
                
                # Use separate session for mapper to avoid conflicts
                with DatabaseSession() as mapper_session:
                    mapper_class = self.schema_mappers[mapper_key]
                    mapper = mapper_class(mapper_session)
                    results = mapper.validate_and_map(xml_root, file_info, strict_mode)
                    
                    mapper_session.commit()
                    
                    # Update import record with results
                    import_record.status = 'completed'
                    import_record.processing_completed_at = datetime.now()
                    import_record.records_imported = results.get('records_imported', 0)
                    import_record.error_message = (
                        "; ".join(results.get('errors', []))
                        if results.get('errors')
                        else None
                    )
                    
                    return True
                    
            except Exception as e:
                error_msg = f"Processing error: {str(e)}"
                import_record.status = 'failed'
                import_record.error_message = error_msg
                import_record.processing_completed_at = datetime.now()
                return False
                
        except Exception as e:
            import_record.status = 'failed'
            import_record.error_message = f"Unexpected error: {str(e)}"
            import_record.processing_completed_at = datetime.now()
            return False
    
    def _download_file(self, import_record: ImportStatus) -> bool:
        """Download file content and update record"""
        try:
            print(f"    📡 Downloading from: {import_record.file_url}")
            
            response = requests.get(import_record.file_url, timeout=30)
            response.raise_for_status()
            
            # Calculate file hash
            file_hash = hashlib.sha1(response.content).hexdigest()
            
            # Store file metadata
            import_record.file_hash = file_hash
            import_record.file_size = len(response.content)
            import_record.status = 'pending'
            
            # Store content temporarily (in a real implementation, you might use Redis or file system)
            import_record._temp_content = response.content
            
            print(f"    ✅ Downloaded {len(response.content):,} bytes")
            return True
            
        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            import_record.status = 'failed'
            import_record.error_message = error_msg
            print(f"    ❌ Download failed: {error_msg}")
            return False
    
    def _has_file_content(self, import_record: ImportStatus) -> bool:
        """Check if file content is available"""
        return hasattr(import_record, '_temp_content') and import_record._temp_content
    
    def _get_file_content(self, import_record: ImportStatus) -> bytes:
        """Get file content for processing"""
        if hasattr(import_record, '_temp_content'):
            return import_record._temp_content
        else:
            # Re-download if content not available
            response = requests.get(import_record.file_url, timeout=30)
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
        elif 'composição' in category_lower:
            return 'composicao_orgaos'
        elif 'cooperação' in category_lower:
            return 'cooperacao'
        elif 'delegação' in category_lower and 'eventual' in category_lower:
            return 'delegacao_eventual'
        elif 'delegação' in category_lower and 'permanente' in category_lower:
            return 'delegacao_permanente'
        elif 'informação' in category_lower:
            return 'informacao_base'
        elif 'petições' in category_lower:
            return 'peticoes'
        elif 'perguntas' in category_lower:
            return 'perguntas_requerimentos'
        elif 'diplomas' in category_lower:
            return 'diplomas_aprovados'
        elif 'orçamento' in category_lower:
            return 'orcamento_estado'
        elif 'reuniões' in category_lower:
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


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database-Driven Parliament Data Importer")
    parser.add_argument('--file-type', type=str, help='Import only specific file type')
    parser.add_argument('--legislatura', type=str, help='Import only specific legislatura')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--force-reimport', action='store_true',
                       help='Force reimport of completed files')
    parser.add_argument('--strict-mode', action='store_true',
                       help='Exit on first error')
    
    args = parser.parse_args()
    
    # Create and run importer
    importer = DatabaseDrivenImporter()
    
    stats = importer.process_pending_imports(
        file_type_filter=args.file_type,
        legislatura_filter=args.legislatura,
        limit=args.limit,
        force_reimport=args.force_reimport,
        strict_mode=args.strict_mode
    )
    
    print(f"\n🏁 Import completed with {stats['succeeded']} successes, {stats['failed']} failures")


if __name__ == "__main__":
    main()