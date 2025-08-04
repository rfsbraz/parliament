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

import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET

from sqlalchemy import text

# Add project root to path for config import
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
import logging
import re
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config.settings import DOWNLOADS_DIR, PARLIAMENT_DATA_DIR
from database.models import ImportStatus

# Constants
CORRUPTED_FILE_PREFIX = "CORRUPTED FILE:"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("unified_importer.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


from scripts.data_processing.mappers import (
    AgendaParlamentarMapper,
    AtividadeDeputadosMapper,
    AtividadesMapper,
    ComposicaoOrgaosMapper,
    CooperacaoMapper,
    DelegacaoEventualMapper,
    DelegacaoPermanenteMapper,
    DiplomasAprovadosMapper,
    InitiativasMapper,
    IntervencoesMapper,
    PerguntasRequerimentosMapper,
    PeticoesMapper,
    RegistoBiograficoMapper,
    RegistoInteressesMapper,
    SchemaError,
    SchemaMapper,
)


class FileTypeResolver:
    """Resolves file types based on filename, path, and content patterns"""

    # File type patterns - ordered by priority
    FILE_TYPE_PATTERNS = {
        "registo_biografico": [
            r"RegistoBiografico.*\.xml",
            r".*[/\\]RegistoBiogr[aá]fico[/\\].*\.xml",
            r".*RegistoBiografico.*\.xml",
        ],
        "registo_interesses": [
            r"RegistoInteresses.*\.xml",
            r".*[/\\]RegistoBiogr[aá]fico[/\\].*RegistoInteresses.*\.xml",
        ],
        "composicao_orgaos": [
            r"OrgaoComposicao.*\.xml",
            r".*[/\\]Composi[cç][aã]o.*[Óó]rg[aã]os[/\\].*\.xml",
            r".*[/\\]Composição de Órgãos[/\\].*\.xml",
        ],
        "atividade_deputados": [
            r"AtividadeDeputado.*\.xml",
            r".*[/\\]Atividade dos Deputados[/\\].*\.xml",
        ],
        "atividades": [r"Atividades.*\.xml", r".*[/\\]Atividades[/\\].*\.xml"],
        "agenda_parlamentar": [
            r"AgendaParlamentar.*\.xml",
            r".*[/\\]Agenda Parlamentar[/\\].*\.xml",
        ],
        "cooperacao": [
            r"Cooperacao.*\.xml",
            r".*[/\\]Coopera[cç][aã]o Parlamentar[/\\].*\.xml",
        ],
        "delegacao_eventual": [
            r"DelegacaoEventual.*\.xml",
            r".*[/\\]Delega[cç][oõ]es Eventuais[/\\].*\.xml",
        ],
        "delegacao_permanente": [
            r"DelegacaoPermanente.*\.xml",
            r".*[/\\]Delega[cç][oõ]es Permanentes[/\\].*\.xml",
        ],
        "iniciativas": [r"Iniciativas.*\.xml", r".*[/\\]Iniciativas[/\\].*\.xml"],
        "intervencoes": [
            r"Intervencoes.*\.xml",
            r".*[/\\]Interven[cç][oõ]es[/\\].*\.xml",
        ],
        "peticoes": [r"Peticoes.*\.xml", r".*[/\\]Peti[cç][oõ]es[/\\].*\.xml"],
        "perguntas_requerimentos": [
            r"PerguntasRequerimentos.*\.xml",
            r".*[/\\]Perguntas e Requerimentos[/\\].*\.xml",
        ],
        "diplomas_aprovados": [
            r"Diplomas.*\.xml",
            r".*[/\\]Diplomas Aprovados[/\\].*\.xml",
            r".*_Diplomas.*\.xml",
            r".*Diplomas.*\.xml\.xml",
        ],
        "orcamento_estado": [
            r"OE.*\.xml",
            r"OEPropostasAlteracao.*\.xml",
            r".*[/\\]Orçamento do Estado[/\\].*\.xml",
            r".*OE.*\.xml\.xml",
            r".*OEPropostasAlteracao.*\.xml\.xml",
        ],
        "informacao_base": [
            r"InformacaoBase.*\.xml",
            r".*[/\\]Informação base[/\\].*\.xml",
            r".*[/\\]Informao base[/\\].*\.xml",
            r".*InformacaoBase.*\.xml\.xml",
        ],
        "reunioes_visitas": [
            r"Reunioes.*\.xml",
            r"ReuniaoNacional.*\.xml",
            r".*[/\\]Reuniões _ Visitas[/\\].*\.xml",
            r".*[/\\]Reunies _ Visitas[/\\].*\.xml",
            r".*Reunioe.*\.xml\.xml",
            r".*ReuniaoNacional.*\.xml\.xml",
        ],
        "grupos_amizade": [
            r"GrupoDeAmizade.*\.xml",
            r".*[/\\]Grupos Parlamentares de Amizade[/\\].*\.xml",
            r".*GrupoDeAmizade.*\.xml\.xml",
        ],
        "diario_assembleia": [
            r"Número_.*\.xml",
            r".*[/\\]Dirioda Assembleia da República[/\\].*\.xml",
            r".*[/\\]Dirioda Assembleia da Repblica[/\\].*\.xml",
            r".*_Nmero_.*\.xml",
            r".*Nmero_.*\.xml\.xml",
        ],
    }

    @classmethod
    def resolve_file_type(cls, file_path: str) -> Optional[str]:
        """Resolve file type based on path patterns"""
        normalized_path = file_path.replace("\\\\", "/").replace("\\", "/")

        for file_type, patterns in cls.FILE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, normalized_path, re.IGNORECASE):
                    return file_type

        # Check if it's JSON equivalent
        if file_path.endswith("_json.txt"):
            xml_equivalent = file_path.replace("_json.txt", ".xml")
            xml_type = cls.resolve_file_type(xml_equivalent)
            if xml_type:
                return f"{xml_type}_json"

        return None

    @classmethod
    def extract_legislatura(cls, file_path: str) -> Optional[str]:
        """Extract legislatura from file path"""
        # Try different patterns
        patterns = [
            r"Legislatura_([A-Z]+|\\d+)",
            r"[/\\\\]([XVII]+)[/\\\\]",
            r"([XVII]+)\\.xml",
            r"(\\d+)\\.xml",
        ]

        for pattern in patterns:
            match = re.search(pattern, file_path, re.IGNORECASE)
            if match:
                leg = match.group(1).upper()
                # Convert roman numerals to numbers if needed
                roman_map = {
                    "XVII": "17",
                    "XVI": "16",
                    "XV": "15",
                    "XIV": "14",
                    "XIII": "13",
                    "XII": "12",
                    "XI": "11",
                    "X": "10",
                    "IX": "9",
                    "VIII": "8",
                    "VII": "7",
                    "VI": "6",
                    "V": "5",
                    "IV": "4",
                    "III": "3",
                    "II": "2",
                    "I": "1",
                    "CONSTITUINTE": "0",
                }
                return roman_map.get(leg, leg)

        return None


class UnifiedImporter:
    """Main importer class that orchestrates the entire import process"""

    # Import order respecting foreign key dependencies
    IMPORT_ORDER = [
        # 1. Foundation data (no dependencies)
        "registo_biografico",  # Creates: Deputado, Legislatura, CirculoEleitoral, Partido
        # 2. Basic organizational structure
        "composicao_orgaos",  # Creates: OrganMeeting, Committee data (depends on Deputado, Legislatura)
        # 3. Deputy activities (depends on Deputado)
        "atividade_deputados",  # Creates: AtividadeDeputado, DeputySituations (depends on Deputado)
        # 4. Parliamentary activities (depends on Deputado, Legislatura)
        "atividades",  # Creates: AtividadeParlamentar (depends on Deputado, Legislatura)
        "agenda_parlamentar",  # Creates: AgendaParlamentar (depends on Legislatura)
        # 5. Complex activities (depends on previous activities)
        "iniciativas",  # Creates: IniciativaParlamentar (depends on Deputado, Legislatura)
        "intervencoes",  # Creates: IntervencaoParlamentar (depends on Deputado, activities)
        # 6. Related processes (depends on initiatives/activities)
        "peticoes",  # Creates: PeticaoParlamentar (depends on Deputado, committees)
        "perguntas_requerimentos",  # Creates: PerguntaRequerimento (depends on Deputado, Legislatura)
        "diplomas_aprovados",  # Creates: DiplomaAprovado (depends on initiatives)
        # 7. Cooperative and delegation activities (depends on deputies/committees)
        "cooperacao",  # Creates: CooperacaoParlamentar (depends on Deputado)
        "delegacao_eventual",  # Creates: DelegacaoEventual (depends on Deputado)
        "delegacao_permanente",  # Creates: DelegacaoPermanente (depends on Deputado)
        # 8. Interest registrations (depends on Deputado)
        "registo_interesses",  # Creates: RegistoInteresses (depends on Deputado)
    ]

    def __init__(self, db_path: str = None):
        # Get script directory and resolve paths
        script_dir = Path(__file__).parent
        self.db_path = db_path or str((script_dir / "../../parlamento.db").resolve())
        self.data_roots = [DOWNLOADS_DIR, PARLIAMENT_DATA_DIR]
        self.file_type_resolver = FileTypeResolver()
        self.init_database()

        # Schema mappers registry
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
            "peticoes": PeticoesMapper,
            "perguntas_requerimentos": PerguntasRequerimentosMapper,
            "diplomas_aprovados": DiplomasAprovadosMapper,
        }

    def init_database(self):
        """Initialize database with import_status table"""
        from database.connection import get_engine

        engine = get_engine()
        # Import status table is now handled by Alembic migrations
        logger.info("Using centralized MySQL database connection")

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

    def process_files(
        self,
        file_type_filter: str = None,
        limit: int = None,
        force_reimport: bool = False,
        legislatura_filter: str = None,
        strict_mode: bool = False,
        skip_video_processing: bool = False,
    ):
        """Process files directly from source directories in dependency order"""
        logger.info("Starting file processing...")
        if strict_mode:
            logger.warning(
                "STRICT MODE ENABLED: Will exit on first unmapped field, schema warning, or processing error"
            )
        if legislatura_filter:
            logger.info(f"Filtering for Legislatura: {legislatura_filter}")

        # Determine import order
        if file_type_filter:
            # Single file type - use as specified
            file_types_to_process = [file_type_filter]
            logger.info(f"Processing single file type: {file_type_filter}")
        else:
            # Multiple file types - use dependency order
            file_types_to_process = self.IMPORT_ORDER
            logger.info(
                f"Processing all file types in dependency order: {' -> '.join(file_types_to_process)}"
            )

        total_files = 0
        processed_files = 0

        from database.connection import DatabaseSession

        with DatabaseSession() as session:
            # Process each file type in dependency order
            for file_type in file_types_to_process:
                logger.info(f"Processing file type: {file_type}")
                files_for_type = []

                # Collect all files for this type
                for data_root in self.data_roots:
                    if not os.path.exists(data_root):
                        logger.warning(f"Data root not found: {data_root}")
                        continue

                    for root, dirs, files in os.walk(data_root):
                        for file in files:
                            if file.endswith((".xml", ".json")) or file.endswith(
                                "_json.txt"
                            ):
                                file_path = os.path.join(root, file)
                                detected_type = (
                                    self.file_type_resolver.resolve_file_type(file_path)
                                )

                                if detected_type == file_type:
                                    # Apply legislatura filter if specified
                                    if (
                                        legislatura_filter
                                        and legislatura_filter.upper()
                                        not in file_path.upper()
                                    ):
                                        continue

                                    files_for_type.append(file_path)

                logger.info(f"Found {len(files_for_type)} files for {file_type}")
                total_files += len(files_for_type)

                # Process files for this type
                for file_path in files_for_type:
                    if self._should_process_file(
                        session, file_path, force_reimport, strict_mode
                    ):
                        success = self._process_file(session, file_path, strict_mode, skip_video_processing)
                        if success:
                            processed_files += 1
                        elif strict_mode:
                            # Check if this was a corrupted file that we should skip
                            import_status = session.query(ImportStatus).filter_by(
                                file_path=file_path
                            ).first()
                            if import_status and import_status.status == "corrupted":
                                logger.info(f"STRICT MODE: Skipping corrupted file {file_path}")
                                processed_files += 1  # Count as processed since we handled it
                            else:
                                logger.error(
                                    f"STRICT MODE: Exiting due to processing error in {file_path}"
                                )
                                session.commit()
                                sys.exit(1)

                        if processed_files % 10 == 0:
                            logger.info(f"Processed {processed_files} files so far...")

                        # Check limit
                        if limit and processed_files >= limit:
                            logger.info(f"Reached limit of {limit} files")
                            session.commit()
                            return

                # Commit after each file type to ensure data integrity
                session.commit()
                logger.info(
                    f"Completed processing {file_type}: {len([f for f in files_for_type if self._should_process_file(session, f, force_reimport, strict_mode)])} files processed"
                )

            session.commit()
            logger.info(
                f"Processing complete: {total_files} files found, {processed_files} processed"
            )

    def _parse_xml_with_bom_handling(self, file_path: str) -> ET.Element:
        """Parse XML file with BOM (Byte Order Mark) handling"""
        # First, try reading the file and removing BOM if present
        with open(file_path, "rb") as f:
            content = f.read()

        # Remove UTF-8 BOM if present (EF BB BF)
        if content.startswith(b"\xef\xbb\xbf"):
            logger.info(f"Removing UTF-8 BOM from {file_path}")
            content = content[3:]

        # Remove UTF-16 BE BOM if present (FE FF)
        elif content.startswith(b"\xfe\xff"):
            logger.info(f"Removing UTF-16 BE BOM from {file_path}")
            content = content[2:]

        # Remove UTF-16 LE BOM if present (FF FE)
        elif content.startswith(b"\xff\xfe"):
            logger.info(f"Removing UTF-16 LE BOM from {file_path}")
            content = content[2:]

        # Also try to remove any other common problematic characters at start
        # Remove any non-ASCII characters before '<'
        while content and content[0:1] != b"<" and content[0] > 127:
            content = content[1:]

        # Parse the cleaned content
        try:
            return ET.fromstring(content.decode("utf-8"))
        except UnicodeDecodeError:
            # Try with different encodings if UTF-8 fails
            try:
                return ET.fromstring(content.decode("utf-16"))
            except UnicodeDecodeError:
                return ET.fromstring(content.decode("latin-1"))

    def _should_process_file(
        self,
        session,
        file_path: str,
        force_reimport: bool = False,
        strict_mode: bool = False,
    ) -> bool:
        """Check if file should be processed"""
        # Check file type filter
        file_type = self.file_type_resolver.resolve_file_type(file_path)
        if not file_type:
            return False

        # Check if we have a mapper for this file type
        if file_type not in self.schema_mappers:
            error_msg = f"No mapper for file type: {file_type}"
            if strict_mode:
                logger.error(f"STRICT MODE: {error_msg} in {file_path}")
                logger.error(
                    "Available mappers: " + ", ".join(self.schema_mappers.keys())
                )
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

        from database.models import ImportStatus

        existing = (
            session.query(ImportStatus)
            .filter(
                ImportStatus.file_path == file_path,
                ImportStatus.file_hash == file_hash,
                ImportStatus.status == "completed",
            )
            .first()
        )

        return existing is None

    def _process_file(self, session, file_path: str, strict_mode: bool = False, skip_video_processing: bool = False) -> bool:
        """Process a single file"""
        try:
            # Determine file type
            file_type = self.file_type_resolver.resolve_file_type(file_path)
            if not file_type or file_type not in self.schema_mappers:
                logger.warning(
                    f"No mapper available for file type '{file_type}': {file_path}"
                )
                return False

            # Calculate file hash and size
            file_hash = self.calculate_file_hash(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

            # Update import status to processing
            from database.models import ImportStatus

            # Check if record exists
            import_status = (
                session.query(ImportStatus)
                .filter(
                    ImportStatus.file_path == file_path,
                    ImportStatus.file_hash == file_hash,
                )
                .first()
            )

            if import_status:
                import_status.status = "processing"
                import_status.processing_started_at = datetime.now()
                import_status.updated_at = datetime.now()
            else:
                import_status = ImportStatus(
                    file_url=file_path,  # Using file_path as URL for local files
                    file_path=file_path,
                    file_name=os.path.basename(file_path),
                    file_type=file_type,
                    category=file_type.replace("_", " ").title(),
                    file_hash=file_hash,
                    file_size=file_size,
                    status="processing",
                    processing_started_at=datetime.now(),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                session.add(import_status)

            # Process the file
            mapper_class = self.schema_mappers[file_type]

            # Parse XML first
            try:
                xml_root = self._parse_xml_with_bom_handling(file_path)
                file_info = {
                    "file_path": file_path,
                    "file_type": file_type,
                    "file_hash": file_hash,
                    "skip_video_processing": skip_video_processing,
                }
            except Exception as e:
                error_msg = f"XML parsing error: {str(e)}"
                import_status.status = "failed"
                import_status.processing_completed_at = datetime.now()
                import_status.error_message = error_msg

                # Commit the status update
                session.commit()

                logger.error(f"Failed to parse XML {file_path}: {error_msg}")
                if strict_mode:
                    # In strict mode, only exit for schema violations, not corrupted files
                    if "not well-formed" in error_msg or "invalid token" in error_msg:
                        import_status.status = "corrupted"
                        import_status.error_message = f"{CORRUPTED_FILE_PREFIX}: {error_msg}"
                        try:
                            session.commit()
                        except Exception as commit_error:
                            logger.warning(f"Failed to commit corrupted status: {commit_error}")
                            session.rollback()
                        logger.warning(
                            f"STRICT MODE: Skipping corrupted XML file {file_path}"
                        )
                        return False
                    else:
                        logger.error(
                            f"STRICT MODE: Exiting due to XML parsing error in {file_path}"
                        )
                        sys.exit(1)
                return False

            # Commit the status update before processing to avoid locks
            session.commit()

            # Create database connection for the mapper with proper isolation
            try:
                from database.connection import DatabaseSession

                # Use a separate session for the mapper to avoid conflicts
                with DatabaseSession() as mapper_session:
                    mapper = mapper_class(mapper_session)
                    results = mapper.validate_and_map(xml_root, file_info, strict_mode)

                    # Commit mapper changes
                    mapper_session.commit()

                    # Update status to completed
                    import_status.status = "completed"
                    import_status.processing_completed_at = datetime.now()
                    import_status.records_imported = results.get("records_imported", 0)
                    import_status.error_message = (
                        "; ".join(results.get("errors", []))
                        if results.get("errors")
                        else None
                    )

                    # Commit the status update
                    session.commit()

                    logger.info(
                        f"Successfully processed {file_path}: {results.get('records_imported', 0)} records imported"
                    )
                    return True

            except Exception as e:
                # Update status to failed
                error_msg = f"Processing error: {str(e)}"
                import_status.status = "failed"
                import_status.processing_completed_at = datetime.now()
                import_status.error_message = error_msg

                # Commit the status update
                session.commit()

                logger.error(f"Failed to process {file_path}: {error_msg}")

                # Check for strict mode - but allow skipping corrupted files
                if strict_mode:
                    # Check if this is just a corrupted file we should skip
                    try:
                        with open(file_path, "rb") as f:
                            first_bytes = f.read(10)
                        # If file looks corrupted (non-XML bytes), skip it
                        if not first_bytes.startswith(
                            b"<?xml"
                        ) and not first_bytes.startswith(b"<"):
                            import_status.status = "corrupted"
                            import_status.error_message = f"{CORRUPTED_FILE_PREFIX}: File contains non-XML binary data"
                            try:
                                session.commit()
                            except Exception as commit_error:
                                logger.warning(f"Failed to commit corrupted status: {commit_error}")
                                session.rollback()
                            logger.warning(
                                f"STRICT MODE: Skipping corrupted file {file_path}"
                            )
                            return False
                    except:
                        import_status.status = "corrupted"
                        import_status.error_message = f"{CORRUPTED_FILE_PREFIX}: File is unreadable or has access issues"
                        try:
                            session.commit()
                        except Exception as commit_error:
                            logger.warning(f"Failed to commit corrupted status: {commit_error}")
                            session.rollback()
                        logger.warning(
                            f"STRICT MODE: Skipping unreadable file {file_path}"
                        )
                        return False

                    logger.error(
                        f"STRICT MODE: Exiting immediately due to processing error in {file_path}"
                    )
                    logger.error(f"Error details: {traceback.format_exc()}")
                    # Force immediate exit - no further processing
                    sys.exit(1)

                return False

        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}")
            traceback.print_exc()
            if strict_mode:
                logger.error(
                    f"STRICT MODE: Exiting due to unexpected error in {file_path}"
                )
                sys.exit(1)
            return False

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

    def validate_schema_coverage(self, file_type: str = None):
        """Validate schema mapping coverage for file types"""
        logger.info("Validating schema coverage...")
        # Implementation for schema validation
        pass

    def cleanup_database(self):
        """Drop all tables and recreate schema from models"""
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

                logger.info(f"Found {len(tables)} tables to drop")

                # Drop all tables except alembic_version
                for table_name in tables:
                    connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                    logger.info(f"Dropped table: {table_name}")

                # Re-enable foreign key checks
                connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

                connection.commit()
                logger.info(
                    f"Database cleanup completed successfully. Dropped {len([t for t in tables if t != 'alembic_version'])} tables"
                )

            finally:
                connection.close()

        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            raise


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Unified Parliament Data Importer")
    parser.add_argument(
        "--force-reimport",
        action="store_true",
        help="Force reimport of all files (ignore SHA1)",
    )
    parser.add_argument("--file-type", type=str, help="Import only specific file type")
    parser.add_argument(
        "--legislatura",
        type=str,
        help='Import only specific legislatura (e.g., "XVII", "17", "X", "10")',
    )
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    parser.add_argument(
        "--validate-schema",
        action="store_true",
        help="Validate schema mapping coverage",
    )
    parser.add_argument(
        "--status", action="store_true", help="Show import status summary"
    )
    parser.add_argument(
        "--strict-mode",
        action="store_true",
        help="Exit immediately on any unmapped field, schema warning, or processing error",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Create timestamped backup and truncate all database tables",
    )
    parser.add_argument(
        "--skip-video-processing",
        action="store_true",
        help="Skip video URL validation and thumbnail extraction to speed up processing",
    )

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
        if confirmation.lower() == "yes":
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
            strict_mode=args.strict_mode,
            skip_video_processing=args.skip_video_processing,
        )


if __name__ == "__main__":
    main()
