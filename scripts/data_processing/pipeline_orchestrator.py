#!/usr/bin/env python3
"""
Parliament Data Pipeline Orchestrator
====================================

Orchestrates the complete parliament data pipeline with parallel processing:
1. Discovery Service - Finds and catalogs file URLs
2. Download Manager - Downloads files on-demand
3. Import Processor - Processes downloaded files

Features:
- Rich terminal UI with live progress tracking
- Shared queue management between services
- Rate limiting for discovery and downloads
- Parallel execution with proper coordination
- Real-time status updates and statistics
"""

import argparse
import asyncio
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from typing import Dict, List, Optional

import requests
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress, TaskID, BarColumn, TextColumn, TimeElapsedColumn, 
    SpinnerColumn, MofNCompleteColumn
)
from rich.table import Table
from rich.text import Text

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from database.connection import DatabaseSession
from database.models import ImportStatus
from scripts.data_processing.discovery_service import DiscoveryService
from scripts.data_processing.unified_importer import UnifiedImporter


@dataclass
class DownloadInfo:
    """Information about a downloaded file"""
    file_name: str
    file_size: int
    timestamp: str
    status_id: int

@dataclass
class PipelineStats:
    """Pipeline statistics for UI display"""
    discovery_total: int = 0
    discovery_completed: int = 0
    download_queue_size: int = 0
    download_completed: int = 0
    download_failed: int = 0
    import_queue_size: int = 0
    import_completed: int = 0
    import_failed: int = 0
    total_records_imported: int = 0
    start_time: Optional[datetime] = None
    recent_messages: List[str] = None
    downloaded_files: List[DownloadInfo] = None
    
    def __post_init__(self):
        if self.recent_messages is None:
            self.recent_messages = []
        if self.downloaded_files is None:
            self.downloaded_files = []
    
    def add_message(self, message: str):
        """Add a message to recent messages (keep last 10)"""
        self.recent_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
        if len(self.recent_messages) > 10:
            self.recent_messages.pop(0)
    
    def add_download(self, file_name: str, file_size: int, status_id: int):
        """Add a downloaded file to the list (keep last 15)"""
        download_info = DownloadInfo(
            file_name=file_name,
            file_size=file_size,
            timestamp=datetime.now().strftime('%H:%M:%S'),
            status_id=status_id
        )
        self.downloaded_files.append(download_info)
        if len(self.downloaded_files) > 15:
            self.downloaded_files.pop(0)
    
    @property
    def elapsed_time(self) -> str:
        if not self.start_time:
            return "00:00:00"
        elapsed = datetime.now() - self.start_time
        # Only update every 5 seconds to reduce flashing
        total_seconds = int(elapsed.total_seconds())
        rounded_seconds = (total_seconds // 5) * 5
        hours, remainder = divmod(rounded_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class DownloadManager:
    """Manages file downloads from URLs in the database"""
    
    def __init__(self, rate_limit_delay: float = 0.3):
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.running = False
        
        # Create downloads directory
        self.downloads_dir = Path("E:/dev/parliament/scripts/data_processing/data/downloads")
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
    def start(self, download_queue: Queue, stats: PipelineStats, console: Console):
        """Start download processing"""
        self.running = True
        
        with DatabaseSession() as db_session:
            while self.running:
                try:
                    # Get files that need downloading
                    files_to_download = db_session.query(ImportStatus).filter(
                        ImportStatus.status.in_(['discovered', 'download_pending'])
                    ).limit(10).all()
                    
                    if not files_to_download:
                        time.sleep(1)
                        continue
                    
                    for import_record in files_to_download:
                        if not self.running:
                            break
                            
                        try:
                            # Update status to downloading
                            import_record.status = 'downloading'
                            db_session.commit()
                            
                            # Download file content
                            response = self.session.get(import_record.file_url, timeout=30)
                            response.raise_for_status()
                            
                            # Calculate file hash
                            import hashlib
                            file_hash = hashlib.sha1(response.content).hexdigest()
                            
                            # Save file to disk using ImportStatus ID as identifier
                            file_extension = Path(import_record.file_name).suffix or '.xml'
                            local_filename = f"{import_record.id}_{import_record.file_name}"
                            local_file_path = self.downloads_dir / local_filename
                            
                            # Write file to disk
                            with open(local_file_path, 'wb') as f:
                                f.write(response.content)
                            
                            # Update import record
                            import_record.file_path = str(local_file_path)
                            import_record.file_hash = file_hash
                            import_record.file_size = len(response.content)
                            import_record.status = 'pending'  # Ready for import
                            import_record.updated_at = datetime.now()
                            
                            db_session.commit()
                            stats.download_completed += 1
                            
                            # Add to import queue
                            download_queue.put(import_record.id)
                            
                            # Add to download tracking and message log
                            stats.add_download(import_record.file_name, import_record.file_size, import_record.id)
                            stats.add_message(f"Downloaded: {import_record.file_name} ({import_record.file_size:,} bytes)")
                            
                        except Exception as e:
                            import_record.status = 'failed'
                            import_record.error_message = f"Download error: {str(e)}"
                            db_session.commit()
                            stats.download_failed += 1
                            
                            stats.add_message(f"Download failed: {import_record.file_name} - {str(e)}")
                        
                        # Rate limiting
                        time.sleep(self.rate_limit_delay)
                        
                except Exception as e:
                    stats.add_message(f"Download manager error: {str(e)}")
                    time.sleep(1)
    
    def stop(self):
        """Stop download processing"""
        self.running = False


class ImportProcessor:
    """Processes downloaded files for import"""
    
    def __init__(self):
        self.running = False
        # Use the database-driven importer instead
        from scripts.data_processing.database_driven_importer import DatabaseDrivenImporter
        self.importer = DatabaseDrivenImporter()
        
    def start(self, download_queue: Queue, stats: PipelineStats, console: Console):
        """Start import processing"""
        self.running = True
        
        with DatabaseSession() as db_session:
            while self.running:
                try:
                    # First, check download queue for priority files
                    record_id = None
                    from_queue = False
                    
                    try:
                        record_id = download_queue.get(timeout=0.5)
                        from_queue = True
                    except Empty:
                        # If no files in download queue, check for any pending files
                        pending_files = db_session.query(ImportStatus).filter(
                            ImportStatus.status == 'pending'
                        ).limit(1).all()
                        
                        if pending_files:
                            record_id = pending_files[0].id
                            from_queue = False
                        else:
                            # No pending files, wait a bit
                            time.sleep(1)
                            continue
                        
                    # Get the import record
                    import_record = db_session.query(ImportStatus).get(record_id)
                    if not import_record or import_record.status not in ['pending', 'discovered', 'download_pending']:
                        continue
                    
                    try:
                        stats.add_message(f"Processing: {import_record.file_name}")
                        
                        # Use the actual database-driven importer
                        success = self.importer._process_single_import(db_session, import_record, strict_mode=False)
                        
                        if success:
                            stats.import_completed += 1
                            stats.total_records_imported += import_record.records_imported or 0
                            stats.add_message(f"SUCCESS: {import_record.file_name} ({import_record.records_imported or 0} records)")
                        else:
                            stats.import_failed += 1
                            error_msg = import_record.error_message or "Unknown error"
                            if len(error_msg) > 50:
                                error_msg = error_msg[:47] + "..."
                            stats.add_message(f"FAILED: {import_record.file_name} - {error_msg}")
                        
                    except Exception as e:
                        stats.import_failed += 1
                        error_msg = str(e)
                        if len(error_msg) > 50:
                            error_msg = error_msg[:47] + "..."
                        stats.add_message(f"ERROR: {import_record.file_name} - {error_msg}")
                        
                        # Update record status if not already updated
                        if import_record.status not in ['completed', 'failed']:
                            import_record.status = 'failed'
                            import_record.error_message = str(e)
                            import_record.processing_completed_at = datetime.now()
                            try:
                                db_session.commit()
                            except:
                                db_session.rollback()
                        
                    finally:
                        # Only mark task done if it came from download queue
                        if from_queue:
                            try:
                                download_queue.task_done()
                            except:
                                pass  # Ignore if task wasn't from queue
                        
                except Exception as e:
                    stats.add_message(f"Import processor error: {str(e)}")
                    time.sleep(1)
    
    def stop(self):
        """Stop import processing"""
        self.running = False


class PipelineOrchestrator:
    """Main orchestrator for the parliament data pipeline"""
    
    def __init__(self, discovery_rate_limit: float = 0.5, download_rate_limit: float = 0.3):
        self.console = Console()
        self.stats = PipelineStats()
        
        # Initialize services
        self.discovery_service = DiscoveryService(rate_limit_delay=discovery_rate_limit)
        self.download_manager = DownloadManager(rate_limit_delay=download_rate_limit)
        self.import_processor = ImportProcessor()
        
        # Shared queues
        self.download_queue = Queue()
        
        # Threading
        self.threads = []
        self.running = False
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                if unit == 'B':
                    return f"{size_bytes} {unit}"
                else:
                    return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        
        return f"{size_bytes:.1f} TB"
    
    def _get_pending_files(self, limit: int = 10) -> List:
        """Get pending files from ImportStatus table"""
        try:
            with DatabaseSession() as db_session:
                pending_files = db_session.query(ImportStatus).filter(
                    ImportStatus.status.in_(['discovered', 'download_pending', 'pending'])
                ).order_by(ImportStatus.discovered_at.desc()).limit(limit).all()
                
                return pending_files
        except Exception as e:
            self.stats.add_message(f"Error getting pending files: {str(e)}")
            return []
        
    def create_ui_layout(self) -> Layout:
        """Create Rich layout for the UI"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2)
        )
        
        # Split left panel into stats (top) and downloads (bottom)
        layout["left"].split_column(
            Layout(name="stats", ratio=1),
            Layout(name="downloads", ratio=1)
        )
        
        # Split right panel into pending files (top) and activity log (bottom)
        layout["right"].split_column(
            Layout(name="pending", ratio=1),
            Layout(name="activity", ratio=1)
        )
        
        return layout
        
    def update_layout(self, layout: Layout):
        """Update the Rich layout with current data"""
        # Header
        layout["header"].update(
            Panel(
                f"Parliament Data Pipeline Orchestrator - Runtime: {self.stats.elapsed_time}",
                style="bold blue"
            )
        )
        
        # Stats table
        stats_table = Table(title="Pipeline Statistics", show_header=True)
        stats_table.add_column("Stage", style="cyan")
        stats_table.add_column("Status", justify="right")
        
        stats_table.add_row(
            "Discovery",
            f"{self.stats.discovery_completed} files cataloged"
        )
        stats_table.add_row(
            "Downloads",
            f"OK: {self.stats.download_completed} | ERR: {self.stats.download_failed} | QUEUE: {self.download_queue.qsize()}"
        )
        stats_table.add_row(
            "Imports", 
            f"OK: {self.stats.import_completed} | ERR: {self.stats.import_failed} | RECORDS: {self.stats.total_records_imported}"
        )
        
        layout["stats"].update(Panel(stats_table, border_style="green"))
        
        # Downloaded files tracking
        if self.stats.downloaded_files:
            downloads_table = Table(show_header=True, header_style="bold magenta")
            downloads_table.add_column("Time", style="dim", width=8)
            downloads_table.add_column("File", style="cyan", width=25)
            downloads_table.add_column("Size", justify="right", width=10)
            downloads_table.add_column("ID", justify="right", width=6)
            
            # Show last 10 downloads
            for download in self.stats.downloaded_files[-10:]:
                file_display = download.file_name
                if len(file_display) > 22:
                    file_display = file_display[:19] + "..."
                
                # Format file size
                size_str = self._format_file_size(download.file_size)
                
                downloads_table.add_row(
                    download.timestamp,
                    file_display,
                    size_str,
                    str(download.status_id)
                )
                
            downloads_panel = Panel(downloads_table, title="Downloaded Files", border_style="blue")
        else:
            downloads_panel = Panel("No files downloaded yet", title="Downloaded Files", border_style="blue")
        
        layout["downloads"].update(downloads_panel)
        
        # Pending files for processing
        pending_files = self._get_pending_files(12)
        if pending_files:
            pending_table = Table(show_header=True, header_style="bold green")
            pending_table.add_column("Status", style="yellow", width=12)
            pending_table.add_column("File", style="cyan", width=30)
            pending_table.add_column("Category", style="magenta", width=20)
            pending_table.add_column("Legislature", width=10)
            
            for file_record in pending_files:
                file_display = file_record.file_name
                if len(file_display) > 27:
                    file_display = file_display[:24] + "..."
                    
                category_display = file_record.category or "Unknown"
                if len(category_display) > 17:
                    category_display = category_display[:14] + "..."
                
                # Color code status
                status_display = file_record.status
                if file_record.status == 'discovered':
                    status_display = "[blue]discovered[/blue]"
                elif file_record.status == 'download_pending':
                    status_display = "[yellow]dl_pending[/yellow]"
                elif file_record.status == 'pending':
                    status_display = "[green]ready[/green]"
                
                pending_table.add_row(
                    status_display,
                    file_display,
                    category_display,
                    file_record.legislatura or "N/A"
                )
                
            pending_panel = Panel(pending_table, title=f"Files Ready for Processing ({len(pending_files)})", border_style="green")
        else:
            pending_panel = Panel("No pending files found", title="Files Ready for Processing", border_style="green")
            
        layout["pending"].update(pending_panel)
        
        # Recent activity log  
        if self.stats.recent_messages:
            messages_text = "\n".join(self.stats.recent_messages[-10:])  # Show last 10 messages
        else:
            messages_text = "Waiting for activity..."
            
        activity_panel = Panel(
            messages_text,
            title="Processing Activity Log",
            border_style="yellow"
        )
        layout["activity"].update(activity_panel)
        
        # Footer
        layout["footer"].update(
            Panel(
                "Press Ctrl+C to stop gracefully",
                style="dim"
            )
        )
    
    def run_discovery(self, legislature_filter: str = None, category_filter: str = None):
        """Run discovery in background thread"""
        try:
            discovered_count = self.discovery_service.discover_all_files(
                legislature_filter=legislature_filter,
                category_filter=category_filter
            )
            self.stats.discovery_completed = discovered_count
            
        except Exception as e:
            self.console.print(f"❌ Discovery error: {e}")
    
    def start_pipeline(self, legislature_filter: str = None, category_filter: str = None):
        """Start the complete pipeline"""
        self.stats.start_time = datetime.now()
        self.running = True
        
        # Create UI layout
        layout = self.create_ui_layout()
        
        try:
            with Live(layout, refresh_per_second=2, screen=True):
                # Start discovery in background thread
                discovery_thread = threading.Thread(
                    target=self.run_discovery,
                    args=(legislature_filter, category_filter)
                )
                discovery_thread.daemon = True
                discovery_thread.start()
                self.threads.append(discovery_thread)
                
                # Start download manager
                download_thread = threading.Thread(
                    target=self.download_manager.start,
                    args=(self.download_queue, self.stats, self.console)
                )
                download_thread.daemon = True
                download_thread.start()
                self.threads.append(download_thread)
                
                # Start import processor
                import_thread = threading.Thread(
                    target=self.import_processor.start,
                    args=(self.download_queue, self.stats, self.console)
                )
                import_thread.daemon = True
                import_thread.start()
                self.threads.append(import_thread)
                
                # Main UI update loop
                while self.running:
                    self.update_layout(layout)
                    time.sleep(2.0)  # Reduced frequency to minimize flashing
                    
                    # Update queue sizes
                    with DatabaseSession() as db_session:
                        self.stats.download_queue_size = db_session.query(ImportStatus).filter(
                            ImportStatus.status.in_(['discovered', 'download_pending'])
                        ).count()
                        
                        self.stats.import_queue_size = db_session.query(ImportStatus).filter(
                            ImportStatus.status == 'pending'
                        ).count()
                    
        except KeyboardInterrupt:
            self.console.print("\n🛑 Shutdown requested...")
            self.stop_pipeline()
    
    def stop_pipeline(self):
        """Stop all pipeline components"""
        self.running = False
        self.download_manager.stop()
        self.import_processor.stop()
        
        # Wait for threads to complete
        for thread in self.threads:
            thread.join(timeout=2)
            
        self.console.print("✅ Pipeline stopped gracefully")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Parliament Data Pipeline Orchestrator")
    parser.add_argument('--legislature', type=str,
                       help='Filter by legislature (e.g., XVII, 17, Constituinte)')
    parser.add_argument('--category', type=str,
                       help='Filter by category (e.g., "Atividade Deputado")')
    parser.add_argument('--discovery-rate-limit', type=float, default=0.5,
                       help='Discovery rate limit delay (default: 0.5s)')
    parser.add_argument('--download-rate-limit', type=float, default=0.3,
                       help='Download rate limit delay (default: 0.3s)')
    
    args = parser.parse_args()
    
    # Create and start orchestrator
    orchestrator = PipelineOrchestrator(
        discovery_rate_limit=args.discovery_rate_limit,
        download_rate_limit=args.download_rate_limit
    )
    
    try:
        orchestrator.start_pipeline(
            legislature_filter=args.legislature,
            category_filter=args.category
        )
    except KeyboardInterrupt:
        orchestrator.stop_pipeline()


if __name__ == "__main__":
    main()