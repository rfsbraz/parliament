#!/usr/bin/env python3
"""
Parliament Data Source Extractor
Robust extractor for Portuguese Parliament open data resources
Source: https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx
"""

import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List, Tuple
import re

class ParliamentDataSourceExtractor:
    """Extract and analyze Portuguese Parliament open data sources"""
    
    def __init__(self):
        self.base_url = "https://www.parlamento.pt"
        self.open_data_url = "https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_page_content(self, url: str) -> BeautifulSoup:
        """Fetch and parse webpage content"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"SUCCESS: Successfully fetched {len(response.text)} characters")
            return soup
            
        except requests.RequestException as e:
            print(f"ERROR: Error fetching {url}: {e}")
            return None
    
    def extract_resource_categories(self) -> List[Dict]:
        """Extract all resource categories and their URLs from the open data page"""
        print("EXTRACTING PARLIAMENT OPEN DATA RESOURCES")
        print("=" * 60)
        
        soup = self.get_page_content(self.open_data_url)
        if not soup:
            return []
        
        resources = []
        
        # Look for different patterns that might contain resource links
        resource_patterns = [
            # Pattern 1: Links with "Recursos" or data-related text
            {'selector': 'a[href*="xml"]', 'description': 'XML file links'},
            {'selector': 'a[href*="dados"]', 'description': 'Data links'},
            {'selector': 'a[href*="deputados"]', 'description': 'Deputy links'},
            {'selector': 'a[href*="iniciativas"]', 'description': 'Initiative links'},
            {'selector': 'a[href*="votacoes"]', 'description': 'Voting links'},
            {'selector': 'a[href*="intervencoes"]', 'description': 'Intervention links'},
            {'selector': 'a[href*="agenda"]', 'description': 'Agenda links'},
            # Pattern 2: Links in specific sections
            {'selector': 'div.ms-rtestate-field a', 'description': 'Content area links'},
            {'selector': '.ms-webpartzone-cell a', 'description': 'Web part links'},
            # Pattern 3: All external and internal links that might be resources
            {'selector': 'a[href*="parlamento.pt"]', 'description': 'Parliament domain links'},
        ]
        
        all_links = set()  # Use set to avoid duplicates
        
        for pattern in resource_patterns:
            print(f"\nScanning for: {pattern['description']}")
            links = soup.select(pattern['selector'])
            print(f"Found {len(links)} links matching pattern")
            
            for link in links:
                href = link.get('href')
                if not href:
                    continue
                    
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = urljoin(self.base_url, href)
                elif not href.startswith('http'):
                    href = urljoin(self.open_data_url, href)
                
                # Extract link text
                link_text = link.get_text(strip=True)
                
                # Skip empty or very short links
                if not link_text or len(link_text) < 3:
                    continue
                
                # Skip internal navigation links
                if any(skip in href.lower() for skip in ['#', 'javascript:', 'mailto:']):
                    continue
                
                all_links.add((href, link_text, pattern['description']))
        
        # Convert set back to list and sort
        unique_links = sorted(list(all_links))
        
        # Categorize the links
        categories = {
            'Deputados': [],
            'Iniciativas': [],
            'Votações': [],
            'Intervenções': [],
            'Agenda': [],
            'XML/Data Files': [],
            'Other Parliament Data': []
        }
        
        for href, text, source in unique_links:
            resource = {
                'url': href,
                'title': text,
                'source_pattern': source
            }
            
            # Categorize based on URL and text content
            href_lower = href.lower()
            text_lower = text.lower()
            
            if any(keyword in href_lower or keyword in text_lower 
                   for keyword in ['deputado', 'deputy']):
                categories['Deputados'].append(resource)
            elif any(keyword in href_lower or keyword in text_lower 
                     for keyword in ['iniciativa', 'initiative', 'proposta']):
                categories['Iniciativas'].append(resource)
            elif any(keyword in href_lower or keyword in text_lower 
                     for keyword in ['votac', 'voto', 'voting']):
                categories['Votações'].append(resource)
            elif any(keyword in href_lower or keyword in text_lower 
                     for keyword in ['intervenc', 'intervention']):
                categories['Intervenções'].append(resource)
            elif any(keyword in href_lower or keyword in text_lower 
                     for keyword in ['agenda', 'calendario', 'sessao']):
                categories['Agenda'].append(resource)
            elif '.xml' in href_lower or 'dados' in href_lower:
                categories['XML/Data Files'].append(resource)
            else:
                categories['Other Parliament Data'].append(resource)
        
        return categories
    
    def analyze_resource_structure(self, categories: Dict) -> None:
        """Analyze and display the structure of found resources"""
        print("\nRESOURCE ANALYSIS")
        print("=" * 60)
        
        total_resources = sum(len(resources) for resources in categories.values())
        print(f"Total resources found: {total_resources}")
        
        for category, resources in categories.items():
            if not resources:
                continue
                
            print(f"\n[{category.upper()}] ({len(resources)} resources)")
            print("-" * 40)
            
            for i, resource in enumerate(resources[:10], 1):  # Show first 10
                print(f"{i:2d}. {resource['title'][:60]}...")
                print(f"    URL: {resource['url']}")
                print()
                
            if len(resources) > 10:
                print(f"    ... and {len(resources) - 10} more resources")
                print()
    
    def save_resources_to_file(self, categories: Dict, filename: str = "parliament_resources.json") -> None:
        """Save extracted resources to JSON file"""
        output_file = f"D:\\GoPro\\Building Modern App for Portuguese Government Data Analysis\\{filename}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        
        print(f"SUCCESS: Resources saved to: {output_file}")
    
    def extract_and_analyze_all(self) -> Dict:
        """Main method to extract and analyze all resources"""
        print("PORTUGUESE PARLIAMENT DATA SOURCE EXTRACTOR")
        print("=" * 60)
        print(f"Source: {self.open_data_url}")
        print()
        
        # Extract resources
        categories = self.extract_resource_categories()
        
        if not categories:
            print("ERROR: No resources extracted")
            return {}
        
        # Analyze structure
        self.analyze_resource_structure(categories)
        
        # Save to file
        self.save_resources_to_file(categories)
        
        return categories

def main():
    """Main execution function"""
    extractor = ParliamentDataSourceExtractor()
    resources = extractor.extract_and_analyze_all()
    
    if resources:
        print("\n" + "=" * 60)
        print("EXTRACTION COMPLETED SUCCESSFULLY!")
        print("Review the generated parliament_resources.json file")
        print("Next step: Analyze specific resource endpoints")
    else:
        print("\n" + "=" * 60)
        print("EXTRACTION FAILED - Check network connectivity and URL accessibility")

if __name__ == "__main__":
    main()