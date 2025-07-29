#!/usr/bin/env python3
"""
Get Parliament Resource URLs
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_parliament_resources():
    url = "https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error: {e}")
        return {}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    
    # Key resource categories we're looking for
    key_resources = {}
    
    for link in links:
        href = link.get('href')
        text = link.get_text(strip=True)
        
        if not href or not text:
            continue
        
        # Convert relative URLs to absolute
        if href.startswith('/'):
            href = urljoin("https://www.parlamento.pt", href)
        
        # Skip non-parliament links
        if 'parlamento.pt' not in href:
            continue
        
        # Look for data-related resources
        text_lower = text.lower()
        href_lower = href.lower()
        
        if any(keyword in text_lower for keyword in ['deputado', 'deputy']):
            if 'atividade' in href_lower or 'dados' in href_lower:
                key_resources['Deputados'] = href
        elif any(keyword in text_lower for keyword in ['iniciativa', 'initiative']):
            if 'dados' in href_lower or 'atividade' in href_lower:
                key_resources['Iniciativas'] = href
        elif any(keyword in text_lower for keyword in ['intervenc', 'intervention']):
            if 'atividade' in href_lower or 'dados' in href_lower:
                key_resources['Intervencoes'] = href
        elif any(keyword in text_lower for keyword in ['votac', 'voting']):
            if 'arquivo' in href_lower:
                key_resources['Votacoes'] = href
        elif 'agenda' in text_lower:
            if 'agenda.parlamento.pt' in href:
                key_resources['Agenda'] = href
    
    return key_resources

def main():
    print("PARLIAMENT DATA RESOURCES")
    print("=" * 50)
    
    resources = get_parliament_resources()
    
    if resources:
        for category, url in resources.items():
            print(f"{category}: {url}")
    else:
        print("No resources found")

if __name__ == "__main__":
    main()