#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import time
import os
import re
import sys
import signal

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print(f"\n\nShutdown requested (Ctrl+C). Will exit after current file download completes...")
    shutdown_requested = True

def check_shutdown():
    """Check if shutdown was requested and exit gracefully"""
    if shutdown_requested:
        print("Exiting gracefully...")
        sys.exit(0)

def safe_filename(name):
    """Convert a string to a safe filename"""
    # Remove or replace accented characters
    name = re.sub(r'[àáâãäå]', 'a', name)
    name = re.sub(r'[èéêë]', 'e', name)
    name = re.sub(r'[ìíîï]', 'i', name)
    name = re.sub(r'[òóôõö]', 'o', name)
    name = re.sub(r'[ùúûü]', 'u', name)
    name = re.sub(r'[ýÿ]', 'y', name)
    name = re.sub(r'[ñ]', 'n', name)
    name = re.sub(r'[ç]', 'c', name)
    name = re.sub(r'[ÀÁÂÃÄÅ]', 'A', name)
    name = re.sub(r'[ÈÉÊË]', 'E', name)
    name = re.sub(r'[ÌÍÎÏ]', 'I', name)
    name = re.sub(r'[ÒÓÔÕÖ]', 'O', name)
    name = re.sub(r'[ÙÚÛÜ]', 'U', name)
    name = re.sub(r'[ÝŸ]', 'Y', name)
    name = re.sub(r'[Ñ]', 'N', name)
    name = re.sub(r'[Ç]', 'C', name)
    
    # Replace problematic characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'[^\w\s\-_.]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'_{2,}', '_', name)
    name = name.strip('_')
    
    return name

def extract_recursos_links():
    """Extract 'Recursos' links from Parliament's open data page"""
    base_url = "https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx"
    
    print(f"Visiting: {base_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        recursos_links = []
        
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            if 'Recursos' in link_text:
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # Extract section name from URL
                url_parts = href.split('/')
                if url_parts:
                    filename = url_parts[-1]
                    if filename.startswith('DA'):
                        name_part = filename[2:].replace('.aspx', '')
                        section_name = re.sub(r'([A-Z])', r' \1', name_part).strip()
                        if not section_name:
                            section_name = filename
                    else:
                        section_name = filename
                else:
                    section_name = "Unknown Section"
                
                recursos_links.append({
                    'section_name': section_name,
                    'text': link_text,
                    'url': full_url,
                    'original_href': href
                })
        
        print(f"\nFound {len(recursos_links)} 'Recursos' links:")
        for i, link in enumerate(recursos_links, 1):
            print(f"{i}. {link['section_name']} - {link['text']}")
            print(f"   URL: {link['url']}")
            print()
        
        return recursos_links
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def download_file(url, filename, folder_path, overwrite, headers, indent_level=14):
    """Download a file based on its extension"""
    indent = ' ' * indent_level
    
    # Determine file type
    if filename.endswith('.xml'):
        safe_filename_str = safe_filename(filename)
        if not safe_filename_str.endswith('.xml'):
            safe_filename_str += '.xml'
        file_type = 'XML'
        mode = 'w'
        content_attr = 'text'
    elif filename.endswith('_json.txt') or filename.endswith('.json.txt'):
        if filename.endswith('_json.txt'):
            safe_filename_str = safe_filename(filename.replace('_json.txt', '.json'))
        else:
            safe_filename_str = safe_filename(filename.replace('.json.txt', '.json'))
        if not safe_filename_str.endswith('.json'):
            safe_filename_str += '.json'
        file_type = 'JSON'
        mode = 'w'
        content_attr = 'text'
    elif filename.endswith('.pdf'):
        safe_filename_str = safe_filename(filename)
        if not safe_filename_str.endswith('.pdf'):
            safe_filename_str += '.pdf'
        file_type = 'PDF'
        mode = 'wb'
        content_attr = 'content'
    elif filename.endswith('.xsd'):
        safe_filename_str = safe_filename(filename)
        if not safe_filename_str.endswith('.xsd'):
            safe_filename_str += '.xsd'
        file_type = 'XSD'
        mode = 'w'
        content_attr = 'text'
    elif filename.endswith('.zip'):
        safe_filename_str = safe_filename(filename)
        if not safe_filename_str.endswith('.zip'):
            safe_filename_str += '.zip'
        file_type = 'ZIP'
        mode = 'wb'
        content_attr = 'content'
    else:
        return False
    
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, safe_filename_str)
    
    if os.path.exists(file_path) and not overwrite:
        print(f"{indent}SKIP {file_type} (exists): {safe_filename_str}")
        return True
    
    try:
        file_response = requests.get(url, headers=headers, timeout=30)
        file_response.raise_for_status()
        
        with open(file_path, mode, encoding='utf-8' if mode == 'w' else None) as f:
            if content_attr == 'text':
                f.write(file_response.text)
            else:
                f.write(file_response.content)
        
        action = "Overwritten" if os.path.exists(file_path) and overwrite else "Downloaded"
        print(f"{indent}{action} {file_type}: {file_path}")
        
        check_shutdown()
        return True
        
    except Exception as e:
        print(f"{indent}ERROR downloading {file_type}: {e}")
        return False

def process_archive_level(url, level_name, folder_path, overwrite, headers, current_level, max_level=8):
    """Recursively process archive items up to max_level"""
    if current_level > max_level:
        return True
    
    indent = ' ' * (10 + (current_level - 3) * 4)
    progress_indent = ' ' * (8 + (current_level - 3) * 4)
    
    # Check if it's a downloadable file first
    if ('.' in level_name and 
        (level_name.endswith('.xml') or level_name.endswith('_json.txt') or level_name.endswith('.json.txt') or
         level_name.endswith('.pdf') or level_name.endswith('.xsd') or level_name.endswith('.zip'))):
        return download_file(url, level_name, folder_path, overwrite, headers, len(indent))
    
    # Check if URL points to a file (even if name doesn't have extension)
    if '.' not in level_name:
        clean_url = url.split('?')[0].split('#')[0]
        url_filename = clean_url.split('/')[-1] if '/' in clean_url else ''
        
        if (url_filename.endswith('.xml') or url_filename.endswith('_json.txt') or url_filename.endswith('.json.txt') or
            url_filename.endswith('.pdf') or url_filename.endswith('.xsd') or url_filename.endswith('.zip')):
            print(f"{indent}URL points to file: {url_filename}")
            return download_file(url, url_filename, folder_path, overwrite, headers, len(indent))
    
    # If not a file, try to go deeper
    if '.' not in level_name:
        print(f"{indent}LEVEL {current_level + 1} entry found: {level_name}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            print(f"{indent}Status: {response.status_code} | Size: {len(response.text):,} chars")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            archive_items = soup.find_all('div', class_='archive-item')
            
            if archive_items:
                print(f"{indent}Found {len(archive_items)} LEVEL {current_level + 1} archive items")
                
                safe_level_name = safe_filename(level_name)
                next_folder_path = os.path.join(folder_path, safe_level_name)
                
                for i, item in enumerate(archive_items, 1):
                    link = item.find('a', href=True)
                    if link:
                        next_url = urljoin(url, link['href'])
                        next_name = link.get_text(strip=True)
                        
                        progress = f"[{i:2d}/{len(archive_items):2d}]"
                        print(f"{progress_indent}{progress} LEVEL {current_level + 1}: {next_name}")
                        
                        success = process_archive_level(
                            next_url, next_name, next_folder_path, 
                            overwrite, headers, current_level + 1, max_level
                        )
                        
                        if not success:
                            print(f"{indent}ERROR: Failed to process LEVEL {current_level + 1} item: {next_name}")
                            print(f"{indent}Processing failed at URL: {next_url}")
                            sys.exit(1)
                        
                        time.sleep(0.2)
            else:
                print(f"{indent}No LEVEL {current_level + 1} archive items found")
            
            return True
            
        except Exception as e:
            print(f"{indent}ERROR: Failed to process LEVEL {current_level + 1} page - {e}")
            print(f"{indent}Processing failed at URL: {url}")
            sys.exit(1)
    else:
        print(f"{indent}ERROR: Unknown file type '{level_name}' (expected .xml, _json.txt, .pdf, .xsd, or .zip)")
        print(f"{indent}Processing failed at URL: {url}")
        sys.exit(1)

def process_recursos_pages(recursos_links, overwrite=False):
    """Process each recursos page"""
    print(f"\n{'='*60}")
    print(f"Processing {len(recursos_links)} recursos pages")
    print(f"Overwrite mode: {'ON' if overwrite else 'OFF'}")
    print(f"{'='*60}")
    
    for i, link_info in enumerate(recursos_links, 1):
        section_name = link_info['section_name']
        url = link_info['url']
        
        progress = f"[{i:2d}/{len(recursos_links):2d}]"
        print(f"\n{progress} Processing: {section_name}")
        print(f"{'':6} URL: {url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            print(f"{'':6} Status: {response.status_code} | Size: {len(response.text):,} chars")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            archive_items = soup.find_all('div', class_='archive-item')
            
            if archive_items:
                print(f"{'':6} Found {len(archive_items)} archive items")
                
                # Process each archive item (LEVEL 2)
                for j, item in enumerate(archive_items, 1):
                    link = item.find('a', href=True)
                    if link:
                        item_url = urljoin(url, link['href'])
                        item_name = link.get_text(strip=True)
                        
                        level2_progress = f"    [{j:2d}/{len(archive_items):2d}]"
                        print(f"{level2_progress} LEVEL 2: {item_name}")
                        
                        try:
                            item_response = requests.get(item_url, headers=headers, timeout=30)
                            item_response.raise_for_status()
                            print(f"{'':10} Status: {item_response.status_code} | Size: {len(item_response.text):,} chars")
                            
                            item_soup = BeautifulSoup(item_response.text, 'html.parser')
                            level3_archive_items = item_soup.find_all('div', class_='archive-item')
                            
                            if level3_archive_items:
                                print(f"{'':10} Found {len(level3_archive_items)} LEVEL 3 archive items")
                                
                                safe_level1 = safe_filename(section_name)
                                safe_level2 = safe_filename(item_name)
                                folder_path = os.path.join("data", "downloads", safe_level1, safe_level2)
                                
                                # Process each LEVEL 3+ archive item using recursive function
                                for k, level3_item in enumerate(level3_archive_items, 1):
                                    level3_link = level3_item.find('a', href=True)
                                    if level3_link:
                                        level3_url = urljoin(item_url, level3_link['href'])
                                        level3_name = level3_link.get_text(strip=True)
                                        
                                        level3_progress = f"        [{k:2d}/{len(level3_archive_items):2d}]"
                                        print(f"{level3_progress} LEVEL 3: {level3_name}")
                                        
                                        success = process_archive_level(
                                            level3_url, level3_name, folder_path,
                                            overwrite, headers, 3, max_level=8
                                        )
                                        
                                        if not success:
                                            print(f"{'':14} ERROR: Failed to process LEVEL 3+ item: {level3_name}")
                                            print(f"{'':14} Processing failed at URL: {level3_url}")
                                            sys.exit(1)
                                        
                                        time.sleep(0.2)
                            else:
                                print(f"{'':10} No LEVEL 3 archive items found")
                            
                            time.sleep(0.3)
                            
                        except Exception as e:
                            print(f"{'':10} ERROR: Failed to process LEVEL 2 page - {e}")
            else:
                print(f"{'':6} No archive items found")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"{'':6} ERROR: Failed to fetch page - {e}")

if __name__ == "__main__":
    import argparse
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download Parliament data files')
    parser.add_argument('--overwrite', action='store_true', 
                        help='Overwrite existing files (default: skip existing files)')
    args = parser.parse_args()
    
    # Extract recursos links
    recursos_links = extract_recursos_links()
    
    if recursos_links:
        # Process each recursos page
        process_recursos_pages(recursos_links, overwrite=args.overwrite)
    else:
        print("No recursos links found to process.")