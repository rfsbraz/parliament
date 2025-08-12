#!/usr/bin/env python3
"""
Parliament Data Discovery Service
================================

Discovers and catalogs all parliament data files without downloading them.
Stores metadata in ImportStatus table for later processing by the import pipeline.

Features:
- URL discovery through parliament website crawling
- HTTP HEAD requests for change detection metadata
- Legislatura, category, and file type extraction from URLs
- Database-driven file tracking without local storage

Usage:
    python discovery_service.py --discover-all
    python discovery_service.py --legislature XVII
    python discovery_service.py --category "Atividade Deputado"
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError, Timeout

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from database.connection import DatabaseSession
from database.models import ImportStatus


class ParliamentURLExtractor:
    """Extracts metadata from parliament URLs and file paths"""
    
    # Category mapping from URL patterns to human-readable categories
    CATEGORY_PATTERNS = {
        r"atividade[_\s]*deputado": "Atividade Deputado",
        r"composicao[_\s]*orgaos": "Composição Órgãos", 
        r"boletim[_\s]*informativo": "Agenda Parlamentar",
        r"atividades": "Atividades",
        r"cooperacao[_\s]*parlamentar": "Cooperação Parlamentar",
        r"delegacoes[_\s]*eventuais": "Delegações Eventuais",
        r"delegacoes[_\s]*permanentes": "Delegações Permanentes",
        r"informacao[_\s]*base": "Informação Base",
        r"registo[_\s]*biografico": "Registo Biográfico",
        r"iniciativas": "Iniciativas",
        r"intervencoes": "Intervenções",
        r"peticoes": "Petições",
        r"perguntas[_\s]*requerimentos": "Perguntas Requerimentos",
        r"diplomas[_\s]*aprovados": "Diplomas Aprovados",
        r"o_e|orcamento[_\s]*estado": "Orçamento Estado",
        r"reunioes[_\s]*visitas": "Reuniões Visitas",
        r"grupos[_\s]*amizade": "Grupos Amizade",
        r"dar|diario[_\s]*assembleia": "Diário Assembleia",
    }
    
    @classmethod
    def extract_metadata(cls, file_url: str, file_name: str) -> Dict[str, str]:
        """Extract all metadata from URL and filename"""
        metadata = {
            'file_url': file_url,
            'file_name': file_name,
            'legislatura': None,
            'category': None,
            'file_type': None,
            'sub_series': None,
            'session': None,
            'number': None,
        }
        
        # Extract file type from extension
        if file_name.endswith('.xml'):
            metadata['file_type'] = 'XML'
        elif file_name.endswith('.json') or file_name.endswith('_json.txt'):
            metadata['file_type'] = 'JSON'
        elif file_name.endswith('.pdf'):
            metadata['file_type'] = 'PDF'
        elif file_name.endswith('.zip'):
            metadata['file_type'] = 'Archive'
        else:
            metadata['file_type'] = 'Unknown'
        
        # Extract legislatura from URL path
        metadata['legislatura'] = cls._extract_legislatura(file_url)
        
        # Extract category from URL path
        metadata['category'] = cls._extract_category(file_url)
        
        # Extract DAR-specific fields
        if 'dar' in file_url.lower() or 'diario' in file_url.lower():
            metadata.update(cls._extract_dar_metadata(file_url))
        
        return metadata
    
    @classmethod
    def _extract_legislatura(cls, file_url: str) -> Optional[str]:
        """Extract legislatura from URL path"""
        # Try different patterns for legislature identification
        patterns = [
            r"([XVII]+)[_\s]*Legislatura",
            r"Legislatura[_\s]*([XVII]+)",
            r"/([XVII]+)_Legislatura/",
            r"/([XVII]+)/",
            r"(Constituinte)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, file_url, re.IGNORECASE)
            if match:
                leg = match.group(1).upper()
                # Convert roman numerals to standardized format
                if leg == "CONSTITUINTE":
                    return "Constituinte"
                return leg
        
        return None
    
    @classmethod
    def _extract_category(cls, file_url: str) -> Optional[str]:
        """Extract category from URL path"""
        url_lower = file_url.lower()
        
        for pattern, category in cls.CATEGORY_PATTERNS.items():
            if re.search(pattern, url_lower):
                return category
        
        return "Unknown"
    
    @classmethod
    def _extract_dar_metadata(cls, file_url: str) -> Dict[str, Optional[str]]:
        """Extract DAR-specific metadata (sub_series, session, number)"""
        metadata = {
            'sub_series': None,
            'session': None, 
            'number': None,
        }
        
        # Extract sub-series (e.g., "Serie_I", "Serie_II-A")
        series_match = re.search(r"Serie[_\s]*(I+(?:-[A-Z])?)", file_url, re.IGNORECASE)
        if series_match:
            metadata['sub_series'] = f"Serie_{series_match.group(1).upper()}"
        
        # Extract session (e.g., "Sessao_04")
        session_match = re.search(r"Sessao[_\s]*(\d+)", file_url, re.IGNORECASE)
        if session_match:
            metadata['session'] = f"Sessao_{session_match.group(1).zfill(2)}"
        
        # Extract number (e.g., "Numero_036")
        number_match = re.search(r"Numero[_\s]*(\d+)", file_url, re.IGNORECASE)
        if number_match:
            metadata['number'] = f"Numero_{number_match.group(1).zfill(3)}"
        
        return metadata


class DiscoveryService:
    """Main discovery service for parliament data files"""
    
    def __init__(self, rate_limit_delay: float = 0.5):
        self.rate_limit_delay = rate_limit_delay
        self.base_url = "https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def discover_all_files(self, legislature_filter: str = None, category_filter: str = None) -> int:
        """Discover all parliament files and store metadata in database"""
        print(f"Starting discovery from {self.base_url}")
        if legislature_filter:
            print(f"Filtering for legislature: {legislature_filter}")
        if category_filter:
            print(f"Filtering for category: {category_filter}")
        
        discovered_count = 0
        
        # Get recursos links from main page
        recursos_links = self._extract_recursos_links()
        if not recursos_links:
            print("ERROR: No recursos links found")
            return 0
            
        print(f"Found {len(recursos_links)} main sections")
        
        # Process each section
        with DatabaseSession() as db_session:
            for i, link_info in enumerate(recursos_links, 1):
                section_name = link_info['section_name']
                section_url = link_info['url']
                
                print(f"\n[{i}/{len(recursos_links)}] Processing section: {section_name}")
                
                # Check category filter
                if category_filter and category_filter.lower() not in section_name.lower():
                    print(f"SKIP: Skipping section (category filter)")
                    continue
                
                section_count = self._discover_section_files(
                    db_session, section_url, section_name, legislature_filter
                )
                discovered_count += section_count
                
                print(f"DONE: Section complete: {section_count} files discovered")
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
            
            # Commit all discoveries
            db_session.commit()
            
        print(f"\nDiscovery complete: {discovered_count} total files cataloged")
        return discovered_count
    
    def _extract_recursos_links(self) -> List[Dict[str, str]]:
        """Extract main recursos section links"""
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            recursos_links = []
            
            for link in soup.find_all('a', href=True):
                link_text = link.get_text(strip=True)
                if 'Recursos' in link_text:
                    href = link['href']
                    full_url = urljoin(self.base_url, href)
                    
                    # Extract section name from URL
                    url_parts = href.split('/')
                    if url_parts:
                        filename = url_parts[-1]
                        if filename.startswith('DA'):
                            name_part = filename[2:].replace('.aspx', '')
                            section_name = re.sub(r'([A-Z])', r' \1', name_part).strip()
                        else:
                            section_name = filename.replace('.aspx', '')
                    else:
                        section_name = "Unknown Section"
                    
                    recursos_links.append({
                        'section_name': section_name,
                        'text': link_text,
                        'url': full_url
                    })
            
            return recursos_links
            
        except Exception as e:
            print(f"ERROR: Error extracting recursos links: {e}")
            return []
    
    def _discover_section_files(self, db_session, section_url: str, section_name: str, 
                               legislature_filter: str = None) -> int:
        """Discover files within a section"""
        discovered_count = 0
        
        try:
            response = self.session.get(section_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            archive_items = soup.find_all('div', class_='archive-item')
            
            if not archive_items:
                print(f"  FOLDER: No archive items found in section")
                return 0
                
            print(f"  FOLDER: Found {len(archive_items)} level-2 items")
            
            for item in archive_items:
                link = item.find('a', href=True)
                if not link:
                    continue
                    
                item_url = urljoin(section_url, link['href'])
                item_name = link.get_text(strip=True)
                
                # Apply legislature filter at level-2
                if legislature_filter and not self._matches_legislature(item_name, legislature_filter):
                    continue
                    
                print(f"    SEARCH: Exploring: {item_name}")
                
                count = self._discover_recursive(
                    db_session, item_url, item_name, max_depth=6
                )
                discovered_count += count
                
                # Rate limiting
                time.sleep(self.rate_limit_delay * 0.5)
                
        except Exception as e:
            print(f"  ERROR: Error processing section {section_name}: {e}")
            
        return discovered_count
    
    def _discover_recursive(self, db_session, url: str, name: str, current_depth: int = 1, 
                           max_depth: int = 6) -> int:
        """Recursively discover files at various archive levels"""
        if current_depth > max_depth:
            return 0
            
        discovered_count = 0
        
        # Check if this is a direct file
        if self._is_file_url(url, name):
            return self._catalog_file(db_session, url, name)
            
        # Otherwise, explore deeper
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            archive_items = soup.find_all('div', class_='archive-item')
            
            if archive_items:
                print(f"      {'  ' * current_depth}DIR: Level {current_depth + 1}: {len(archive_items)} items")
                
                for item in archive_items:
                    link = item.find('a', href=True)
                    if not link:
                        continue
                        
                    next_url = urljoin(url, link['href'])
                    next_name = link.get_text(strip=True)
                    
                    count = self._discover_recursive(
                        db_session, next_url, next_name, current_depth + 1, max_depth
                    )
                    discovered_count += count
                    
                    # Rate limiting
                    time.sleep(self.rate_limit_delay * 0.2)
            else:
                print(f"      {'  ' * current_depth}FILE: No more archive items at level {current_depth + 1}")
                
        except Exception as e:
            print(f"      {'  ' * current_depth}ERROR: Error at depth {current_depth}: {e}")
            
        return discovered_count
    
    def _is_file_url(self, url: str, name: str) -> bool:
        """Check if URL/name represents a downloadable file"""
        file_extensions = ['.xml', '.json', '.pdf', '.xsd', '.zip', '_json.txt']
        
        # Check name for file extension
        if any(name.lower().endswith(ext) for ext in file_extensions):
            return True
            
        # Check URL path for file extension
        url_path = urlparse(url).path.lower()
        if any(url_path.endswith(ext) for ext in file_extensions):
            return True
            
        return False
    
    def _catalog_file(self, db_session, file_url: str, file_name: str) -> int:
        """Catalog a single file in the database"""
        try:
            # Extract metadata from URL and name
            metadata = ParliamentURLExtractor.extract_metadata(file_url, file_name)
            
            # Get HTTP metadata with HEAD request
            http_metadata = self._get_http_metadata(file_url)
            
            # Check if file already exists in database
            existing = db_session.query(ImportStatus).filter_by(file_url=file_url).first()
            
            if existing:
                # Update existing record if HTTP metadata changed
                updated = False
                if http_metadata.get('last_modified') != existing.last_modified:
                    existing.last_modified = http_metadata.get('last_modified')
                    updated = True
                if http_metadata.get('content_length') != existing.content_length:
                    existing.content_length = http_metadata.get('content_length')
                    updated = True
                if http_metadata.get('etag') != existing.etag:
                    existing.etag = http_metadata.get('etag')
                    updated = True
                    
                if updated:
                    existing.updated_at = datetime.now()
                    existing.status = 'download_pending'  # Mark for re-download
                    print(f"        UPDATE: Updated: {file_name}")
                else:
                    print(f"        SKIP:  Unchanged: {file_name}")
                    
            else:
                # Create new record
                import_status = ImportStatus(
                    file_url=file_url,
                    file_name=file_name,
                    file_type=metadata['file_type'],
                    category=metadata['category'],
                    legislatura=metadata['legislatura'],
                    sub_series=metadata['sub_series'],
                    session=metadata['session'],
                    number=metadata['number'],
                    last_modified=http_metadata.get('last_modified'),
                    content_length=http_metadata.get('content_length'),
                    etag=http_metadata.get('etag'),
                    discovered_at=datetime.now(),
                    status='discovered',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db_session.add(import_status)
                print(f"        SUCCESS: Cataloged: {file_name}")
                
            return 1
            
        except Exception as e:
            print(f"        ERROR: Error cataloging {file_name}: {e}")
            return 0
    
    def _get_http_metadata(self, url: str) -> Dict:
        """Get HTTP metadata using HEAD request"""
        try:
            response = self.session.head(url, timeout=10)
            
            metadata = {}
            
            # Parse Last-Modified header
            if 'Last-Modified' in response.headers:
                from email.utils import parsedate_to_datetime
                try:
                    metadata['last_modified'] = parsedate_to_datetime(
                        response.headers['Last-Modified']
                    )
                except:
                    pass
            
            # Parse Content-Length header
            if 'Content-Length' in response.headers:
                try:
                    metadata['content_length'] = int(response.headers['Content-Length'])
                except:
                    pass
            
            # Parse ETag header
            if 'ETag' in response.headers:
                metadata['etag'] = response.headers['ETag']
                
            return metadata
            
        except Exception as e:
            print(f"          WARN:  HTTP metadata error: {e}")
            return {}
    
    def _matches_legislature(self, name: str, target_legislature: str) -> bool:
        """Check if item name matches target legislature"""
        if not target_legislature or target_legislature.lower() == 'all':
            return True
            
        # Handle "latest" by converting to actual latest legislature  
        if target_legislature.lower() == 'latest':
            target_legislature = 'XVII'
            
        name_upper = name.upper()
        target_upper = target_legislature.upper()
        
        # Roman numeral mapping
        roman_map = {
            '1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V',
            '6': 'VI', '7': 'VII', '8': 'VIII', '9': 'IX', '10': 'X',
            '11': 'XI', '12': 'XII', '13': 'XIII', '14': 'XIV', '15': 'XV',
            '16': 'XVI', '17': 'XVII', '18': 'XVIII', '19': 'XIX', '20': 'XX'
        }
        
        # Build target variants
        target_variants = {target_upper}
        
        if target_upper.isdigit():
            # Target is number - add roman equivalent
            roman = roman_map.get(target_upper)
            if roman:
                target_variants.add(roman)
        else:
            # Target is roman - add numeric equivalent
            for num, roman in roman_map.items():
                if target_upper == roman:
                    target_variants.add(num)
                    break
                    
        # Special case for Constituinte
        if target_upper == 'CONSTITUINTE':
            target_variants.add('CONS')
            
        # Check if any variant matches
        for variant in target_variants:
            if re.search(r'\b' + re.escape(variant) + r'\b', name_upper):
                return True
                
        return False


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Parliament Data Discovery Service")
    parser.add_argument('--discover-all', action='store_true',
                       help='Discover all available files')
    parser.add_argument('--legislature', type=str,
                       help='Filter by legislature (e.g., XVII, 17, Constituinte)')
    parser.add_argument('--category', type=str,
                       help='Filter by category (e.g., "Atividade Deputado")')
    parser.add_argument('--rate-limit', type=float, default=0.5,
                       help='Rate limit delay between requests (default: 0.5s)')
    
    args = parser.parse_args()
    
    if not args.discover_all:
        print("Use --discover-all to start discovery")
        return
        
    # Create discovery service
    service = DiscoveryService(rate_limit_delay=args.rate_limit)
    
    # Run discovery
    discovered_count = service.discover_all_files(
        legislature_filter=args.legislature,
        category_filter=args.category
    )
    
    print(f"\nFINISH: Discovery completed: {discovered_count} files cataloged")


if __name__ == "__main__":
    main()