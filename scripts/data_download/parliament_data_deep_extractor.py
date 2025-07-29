#!/usr/bin/env python3
"""
Parliament Data Deep Extractor
Deep analysis of Portuguese Parliament data resource pages to find actual download URLs
"""

import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List, Tuple
import re

class ParliamentDataDeepExtractor:
    """Deep extractor for actual Parliament data download URLs"""
    
    def __init__(self):
        self.base_url = "https://www.parlamento.pt"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Key resource pages that should contain data download links
        self.resource_pages = {
            'Deputados': 'https://www.parlamento.pt/Cidadania/Paginas/DAatividadeDeputado.aspx',
            'Iniciativas': 'https://www.parlamento.pt/Cidadania/Paginas/DAIniciativas.aspx', 
            'Intervenções': 'https://www.parlamento.pt/Cidadania/Paginas/DAIntervencoes.aspx',
            'Votações': 'https://www.parlamento.pt/ArquivoDocumentacao/Paginas/Arquivodevotacoes.aspx'
        }
        
    def get_page_content(self, url: str) -> BeautifulSoup:
        """Fetch and parse webpage content"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"SUCCESS: Fetched {len(response.text)} characters")
            return soup
            
        except requests.RequestException as e:
            print(f"ERROR: Error fetching {url}: {e}")
            return None
    
    def extract_download_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract actual download links from a resource page"""
        if not soup:
            return []
        
        download_links = []
        
        # Pattern 1: Direct XML links
        xml_links = soup.find_all('a', href=re.compile(r'\.xml$', re.I))
        for link in xml_links:
            href = link.get('href')
            if href:
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                download_links.append({
                    'url': href,
                    'title': link.get_text(strip=True),
                    'type': 'XML Direct',
                    'file_extension': '.xml'
                })
        
        # Pattern 2: Links with download indicators
        download_indicators = ['download', 'descarregar', 'ficheiro', 'file', 'dados', 'xml']
        for indicator in download_indicators:
            links = soup.find_all('a', string=re.compile(indicator, re.I))
            for link in links:
                href = link.get('href')
                if href and href not in [dl['url'] for dl in download_links]:
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    download_links.append({
                        'url': href,
                        'title': link.get_text(strip=True),
                        'type': f'Download Link ({indicator})',
                        'file_extension': self.guess_file_extension(href)
                    })
        
        # Pattern 3: Links in tables (common for data listings)
        tables = soup.find_all('table')
        for table in tables:
            table_links = table.find_all('a')
            for link in table_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                if href and text and len(text) > 5:  # Avoid empty/short links
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    if href not in [dl['url'] for dl in download_links]:
                        download_links.append({
                            'url': href,
                            'title': text,
                            'type': 'Table Link',
                            'file_extension': self.guess_file_extension(href)
                        })
        
        # Pattern 4: JavaScript/AJAX calls (look for data endpoints)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for URL patterns in JavaScript
                url_matches = re.findall(r'["\']([^"\']*(?:\.xml|dados|data)[^"\']*)["\']', script.string, re.I)
                for match in url_matches:
                    if match.startswith('/') or match.startswith('http'):
                        if not match.startswith('http'):
                            match = urljoin(base_url, match)
                        if match not in [dl['url'] for dl in download_links]:
                            download_links.append({
                                'url': match,
                                'title': f'JS Reference: {match.split("/")[-1]}',
                                'type': 'JavaScript Reference',
                                'file_extension': self.guess_file_extension(match)
                            })
        
        return download_links
    
    def guess_file_extension(self, url: str) -> str:
        """Guess file extension from URL"""
        if '.xml' in url.lower():
            return '.xml'
        elif '.json' in url.lower():
            return '.json'
        elif '.csv' in url.lower():
            return '.csv'
        elif any(ext in url.lower() for ext in ['.zip', '.rar', '.7z']):
            return '.archive'
        else:
            return '.unknown'
    
    def analyze_resource_page(self, category: str, url: str) -> Dict:
        """Analyze a specific resource page for download links"""
        print(f"\nANALYZING: {category}")
        print("-" * 50)
        
        soup = self.get_page_content(url)
        if not soup:
            return {'category': category, 'url': url, 'downloads': [], 'error': 'Failed to fetch'}
        
        # Extract download links
        download_links = self.extract_download_links(soup, url)
        
        print(f"Found {len(download_links)} potential download links")
        
        # Display findings
        for i, link in enumerate(download_links[:5], 1):  # Show first 5
            print(f"{i:2d}. {link['title'][:50]}...")
            print(f"    URL: {link['url']}")
            print(f"    Type: {link['type']} ({link['file_extension']})")
            print()
        
        if len(download_links) > 5:
            print(f"    ... and {len(download_links) - 5} more links")
        
        return {
            'category': category,
            'url': url,
            'downloads': download_links,
            'total_found': len(download_links)
        }
    
    def extract_all_data_sources(self) -> Dict:
        """Extract data sources from all resource pages"""
        print("PARLIAMENT DATA DEEP EXTRACTION")
        print("=" * 60)
        
        all_sources = {}
        
        for category, url in self.resource_pages.items():
            result = self.analyze_resource_page(category, url)
            all_sources[category] = result
            time.sleep(1)  # Be nice to the server
        
        return all_sources
    
    def save_data_sources(self, sources: Dict, filename: str = "parliament_data_sources.json") -> None:
        """Save extracted data sources to JSON file"""
        output_file = f"D:\\GoPro\\Building Modern App for Portuguese Government Data Analysis\\{filename}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)
        
        print(f"SUCCESS: Data sources saved to: {output_file}")
    
    def generate_summary_report(self, sources: Dict) -> None:
        """Generate a summary report of all found data sources"""
        print("\nDATA SOURCES SUMMARY REPORT")
        print("=" * 60)
        
        total_sources = sum(src['total_found'] for src in sources.values())
        print(f"Total data sources found: {total_sources}")
        
        print("\nBREAKDOWN BY CATEGORY:")
        for category, data in sources.items():
            print(f"- {category}: {data['total_found']} sources")
            
            # Show top sources by type
            if data['downloads']:
                types = {}
                for dl in data['downloads']:
                    file_type = dl['file_extension']
                    types[file_type] = types.get(file_type, 0) + 1
                
                if types:
                    type_summary = ', '.join([f"{count} {ext}" for ext, count in types.items()])
                    print(f"  Types: {type_summary}")
        
        print("\nPOTENTIAL XML DATA FILES:")
        xml_files = []
        for category, data in sources.items():
            for dl in data['downloads']:
                if dl['file_extension'] == '.xml':
                    xml_files.append(f"{category}: {dl['title']} -> {dl['url']}")
        
        for xml_file in xml_files[:10]:  # Show first 10 XML files
            print(f"- {xml_file}")
        
        if len(xml_files) > 10:
            print(f"... and {len(xml_files) - 10} more XML files")

def main():
    """Main execution function"""
    extractor = ParliamentDataDeepExtractor()
    
    # Extract all data sources
    sources = extractor.extract_all_data_sources()
    
    # Generate summary report
    extractor.generate_summary_report(sources)
    
    # Save results
    extractor.save_data_sources(sources)
    
    print("\n" + "=" * 60)
    print("DEEP EXTRACTION COMPLETED!")
    print("Check parliament_data_sources.json for full results")

if __name__ == "__main__":
    main()