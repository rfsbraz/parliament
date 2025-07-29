#!/usr/bin/env python3
"""
Parliament API Discovery
Discover Portuguese Parliament API endpoints and data sources
Based on existing data patterns and official documentation
"""

import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List, Tuple
import re

class ParliamentAPIDiscovery:
    """Discover Parliament API endpoints and data structures"""
    
    def __init__(self):
        self.base_url = "https://www.parlamento.pt"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Known patterns from existing data analysis
        self.known_endpoints = {
            'activities': '/Cidadania/Paginas/dadosabertos.aspx',
            'deputies': '/Deputados/',
            'initiatives': '/Iniciativas/', 
            'interventions': '/Intervencoes/',
            'votes': '/Votacoes/',
            'agenda': '/Agenda/'
        }
        
        # Common legislatura patterns (based on your existing data)
        self.legislaturas = [
            'XVII', 'XVI', 'XV', 'XIV', 'XIII', 'XII', 'XI', 'X', 'IX', 'VIII', 'VII', 'VI', 'V', 'IV', 'III', 'II', 'I', 'CONSTITUINTE'
        ]
    
    def test_endpoint(self, url: str) -> Dict:
        """Test if an endpoint exists and returns data"""
        try:
            print(f"Testing: {url}")
            response = self.session.get(url, timeout=15)
            
            result = {
                'url': url,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'content_length': len(response.content),
                'accessible': response.status_code == 200,
                'is_xml': 'xml' in response.headers.get('content-type', '').lower(),
                'is_json': 'json' in response.headers.get('content-type', '').lower()
            }
            
            if response.status_code == 200:
                # Check if it looks like XML data
                content_preview = response.text[:500]
                if content_preview.strip().startswith('<?xml') or content_preview.strip().startswith('<'):
                    result['appears_to_be_xml'] = True
                    result['preview'] = content_preview[:200] + '...'
                else:
                    result['appears_to_be_xml'] = False
                    
                print(f"  SUCCESS: {response.status_code} - {len(response.content)} bytes")
            else:
                print(f"  FAILED: {response.status_code}")
                
            return result
            
        except requests.RequestException as e:
            print(f"  ERROR: {str(e)}")
            return {
                'url': url,
                'error': str(e),
                'accessible': False
            }
    
    def discover_api_patterns(self) -> Dict:
        """Discover API patterns based on known Parliament data structures"""
        print("PARLIAMENT API DISCOVERY")
        print("=" * 60)
        
        discoveries = {
            'direct_xml_endpoints': [],
            'web_services': [],
            'data_pages': [],
            'archive_endpoints': []
        }
        
        # Test direct XML patterns (based on existing data structure)
        xml_patterns = [
            # Based on existing file patterns in parliament_data_final
            f"{self.base_url}/WebServices/Deputados.asmx/ObterDeputados",
            f"{self.base_url}/WebServices/Iniciativas.asmx/ObterIniciativas", 
            f"{self.base_url}/WebServices/Intervencoes.asmx/ObterIntervencoes",
            f"{self.base_url}/WebServices/Votacoes.asmx/ObterVotacoes",
            f"{self.base_url}/WebServices/Agenda.asmx/ObterAgenda",
            
            # Try common web service patterns
            f"{self.base_url}/webservices/deputados",
            f"{self.base_url}/webservices/iniciativas",
            f"{self.base_url}/webservices/intervencoes", 
            f"{self.base_url}/webservices/votacoes",
            f"{self.base_url}/webservices/agenda",
            
            # Try API patterns
            f"{self.base_url}/api/deputados",
            f"{self.base_url}/api/iniciativas",
            f"{self.base_url}/api/intervencoes",
            f"{self.base_url}/api/votacoes",
            f"{self.base_url}/api/agenda",
            
            # Try direct data patterns
            f"{self.base_url}/dados/deputados.xml",
            f"{self.base_url}/dados/iniciativas.xml",
            f"{self.base_url}/dados/intervencoes.xml",
            f"{self.base_url}/dados/votacoes.xml",
        ]
        
        print("TESTING DIRECT XML ENDPOINTS:")
        print("-" * 40)
        for url in xml_patterns:
            result = self.test_endpoint(url)
            if result.get('accessible'):
                discoveries['direct_xml_endpoints'].append(result)
            time.sleep(0.5)  # Be nice to server
        
        # Test web service endpoints with legislatura parameters
        print("\nTESTING WEB SERVICES WITH PARAMETERS:")
        print("-" * 40)
        
        webservice_patterns = [
            f"{self.base_url}/WebServices/Deputados.asmx",
            f"{self.base_url}/WebServices/Iniciativas.asmx",
            f"{self.base_url}/WebServices/Intervencoes.asmx",
            f"{self.base_url}/WebServices/Votacoes.asmx"
        ]
        
        for url in webservice_patterns:
            result = self.test_endpoint(url)
            if result.get('accessible'):
                discoveries['web_services'].append(result)
            time.sleep(0.5)
        
        return discoveries
    
    def analyze_open_data_page_deeply(self) -> List[Dict]:
        """Deep analysis of the main open data page for hidden links"""
        print("\nDEEP ANALYSIS OF OPEN DATA PAGE:")
        print("-" * 40)
        
        url = "https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx"
        
        try:
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for any links that might be data endpoints
            all_links = soup.find_all('a', href=True)
            
            data_links = []
            for link in all_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                # Skip empty links
                if not href or not text:
                    continue
                
                # Convert to absolute URL
                if href.startswith('/'):
                    href = urljoin(self.base_url, href)
                
                # Look for data-related keywords
                if any(keyword in href.lower() or keyword in text.lower() 
                       for keyword in ['xml', 'dados', 'data', 'download', 'ficheiro', 'webservice', 'api']):
                    data_links.append({
                        'url': href,
                        'text': text,
                        'context': 'Open Data Page'
                    })
            
            print(f"Found {len(data_links)} potential data links")
            for link in data_links:
                print(f"- {link['text']}: {link['url']}")
            
            return data_links
            
        except Exception as e:
            print(f"Error analyzing open data page: {e}")
            return []
    
    def check_existing_data_patterns(self) -> Dict:
        """Check patterns based on existing parliament_data_final structure"""
        print("\nCHECKING EXISTING DATA PATTERNS:")
        print("-" * 40)
        
        # Based on the files we see in parliament_data_final
        known_patterns = {
            'Deputados': [
                '/WebServices/Deputados.asmx/ObterDeputados',
                '/dados/deputados/DeputadosPortugal.xml'
            ],
            'Iniciativas': [
                '/WebServices/Iniciativas.asmx/ObterIniciativas', 
                '/dados/iniciativas/IniciativasXVII.xml'
            ],
            'Intervencoes': [
                '/WebServices/Intervencoes.asmx/ObterIntervencoes',
                '/dados/intervencoes/IntervencoesXVII.xml'
            ],
            'Votacoes': [
                '/WebServices/Votacoes.asmx/ObterVotacoes',
                '/dados/votacoes/VotacoesXVII.xml'
            ],
            'Agenda': [
                '/WebServices/Agenda.asmx/ObterAgenda',
                '/dados/agenda/AgendaParlamentar.xml'
            ]
        }
        
        working_endpoints = {}
        
        for category, patterns in known_patterns.items():
            print(f"\nTesting {category} patterns:")
            working_endpoints[category] = []
            
            for pattern in patterns:
                url = self.base_url + pattern
                result = self.test_endpoint(url)
                if result.get('accessible'):
                    working_endpoints[category].append(result)
        
        return working_endpoints
    
    def save_discoveries(self, discoveries: Dict, filename: str = "parliament_api_discoveries.json") -> None:
        """Save API discoveries to JSON file"""
        output_file = f"D:\\GoPro\\Building Modern App for Portuguese Government Data Analysis\\{filename}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(discoveries, f, ensure_ascii=False, indent=2)
        
        print(f"SUCCESS: API discoveries saved to: {output_file}")

def main():
    """Main execution function"""
    discovery = ParliamentAPIDiscovery()
    
    # Discover API patterns
    api_discoveries = discovery.discover_api_patterns()
    
    # Analyze open data page
    data_page_links = discovery.analyze_open_data_page_deeply()
    
    # Check existing patterns
    existing_patterns = discovery.check_existing_data_patterns()
    
    # Combine all discoveries
    all_discoveries = {
        'api_endpoints': api_discoveries,
        'data_page_links': data_page_links,
        'existing_patterns': existing_patterns,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save discoveries
    discovery.save_discoveries(all_discoveries)
    
    # Generate summary
    print("\n" + "=" * 60)
    print("API DISCOVERY SUMMARY")
    print("=" * 60)
    
    total_working = len(api_discoveries.get('direct_xml_endpoints', [])) + len(api_discoveries.get('web_services', []))
    print(f"Working endpoints found: {total_working}")
    print(f"Data page links found: {len(data_page_links)}")
    
    if total_working > 0:
        print("\nWORKING ENDPOINTS:")
        for endpoint in api_discoveries.get('direct_xml_endpoints', []):
            print(f"- {endpoint['url']} ({endpoint['content_length']} bytes)")
    
    print("\nNext steps:")
    print("1. Test working endpoints with different parameters")
    print("2. Analyze XML structure of working endpoints")
    print("3. Build robust data importer based on findings")

if __name__ == "__main__":
    main()