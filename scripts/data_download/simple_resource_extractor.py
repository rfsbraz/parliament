#!/usr/bin/env python3
"""
Simple Parliament Resource URL Extractor
Extract top-level resource categories and URLs from Portuguese Parliament open data page
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_parliament_resource_urls():
    """Extract all top-level resource URLs from Parliament open data page"""
    
    url = "https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return {}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all links on the page
    links = soup.find_all('a', href=True)
    
    resources = {}
    
    for link in links:
        href = link.get('href')
        text = link.get_text(strip=True)
        
        if not href or not text or len(text) < 3:
            continue
        
        # Convert relative URLs to absolute
        if href.startswith('/'):
            href = urljoin("https://www.parlamento.pt", href)
        
        # Skip javascript and anchor links
        if href.startswith('javascript:') or href.startswith('#') or href.startswith('mailto:'):
            continue
        
        # Only include Parliament domain links
        if 'parlamento.pt' in href:
            resources[text] = href
    
    return resources

def main():
    print("PORTUGUESE PARLIAMENT OPEN DATA RESOURCES")
    print("=" * 60)
    print("Source: https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx")
    print()
    
    resources = get_parliament_resource_urls()
    
    print("CATEGORIES AND LINKS:")
    print("-" * 40)
    
    for i, (category, url) in enumerate(resources.items(), 1):
        print(f"{i:2d}. {category}")
        print(f"    {url}")
        print()
    
    print(f"Total resources found: {len(resources)}")

if __name__ == "__main__":
    main()