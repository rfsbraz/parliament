#!/usr/bin/env python3
"""
Correção dos Importadores de XML - Parlamento Português
Script para corrigir as funções de importação baseado na estrutura XML real
"""

import sqlite3
import xml.etree.ElementTree as ET
import os
import glob
from datetime import datetime, date, time
import re
import html
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

def get_parliament_open_data_resources():
    """
    Get all top-level resource categories and URLs from Parliament open data page
    Returns dict with category names and their resource URLs
    """
    print("FETCHING PARLIAMENT OPEN DATA RESOURCES...")
    
    url = "https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching open data page: {e}")
        return {}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all "Recursos" links - these are the actual data resource pages
    recursos_links = soup.find_all('a', title='Recursos')
    
    resources = {}
    
    for link in recursos_links:
        href = link.get('href')
        if not href:
            continue
        
        # Convert relative URLs to absolute
        if href.startswith('/'):
            href = urljoin("https://www.parlamento.pt", href)
        
        # Get the parent section to determine category
        parent_section = link.find_parent()
        while parent_section:
            # Look for section titles
            title_elem = parent_section.find_previous('span', class_='ms-rteStyle-details_page_title18')
            if title_elem:
                category = title_elem.get_text(strip=True)
                resources[category] = href
                break
            parent_section = parent_section.find_parent()
    
    print(f"Found {len(resources)} resource categories")
    return resources

def get_legislative_periods_and_data_links(resources):
    """
    Iterate through resource pages and extract all legislative periods and their actual data files
    Returns nested dict: {category: {legislatura: [data_files]}}
    """
    print("EXTRACTING LEGISLATIVE PERIODS AND DATA FILES...")
    
    all_data = {}
    
    for category, resource_url in resources.items():
        # Clean category name for safe printing
        safe_category = ''.join(c for c in category if ord(c) < 128).strip()
        if not safe_category:
            safe_category = "Category"
        print(f"\nProcessing: {safe_category}")
        print(f"URL: {resource_url}")
        
        try:
            response = requests.get(resource_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  Error fetching {category}: {e}")
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        category_data = {}
        
        print(f"    Checking for archive-items on this page...")
        
        # Special handling for DAR (Diário da República) which has 5-level hierarchy
        if is_dar_category(resource_url, safe_category):
            print(f"    Detected DAR category - using 5-level extraction...")
            category_data = extract_dar_data(resource_url)
        else:
            # The resource_url itself IS the data page - check it directly for legislatura sub-pages
            legislatura_pages = extract_legislatura_pages_from_main_page(resource_url)
            
            if legislatura_pages:
                # This page has legislatura-specific sub-pages or archive files
                for item in legislatura_pages:
                    if len(item) == 3:
                        leg_page_url, legislatura, item_type = item
                    else:
                        # Handle old format for backward compatibility
                        leg_page_url, legislatura = item
                        item_type = 'page'
                    
                    if item_type == 'archive':
                        # Handle archive files directly
                        print(f"      Processing {legislatura} archive file...")
                        file_type = get_file_type(leg_page_url)
                        filename = leg_page_url.split('/')[-1] if '/' in leg_page_url else leg_page_url
                        
                        if legislatura not in category_data:
                            category_data[legislatura] = []
                        
                        category_data[legislatura].append({
                            'text': filename,
                            'url': leg_page_url,
                            'type': file_type,
                            'legislatura': legislatura
                        })
                        print(f"        Found: {file_type} - {filename}")
                    else:
                        # Handle regular pages
                        print(f"      Processing {legislatura} legislatura page...")
                        data_files = extract_archive_items_from_page(leg_page_url, legislatura)
                        
                        if data_files:
                            if legislatura not in category_data:
                                category_data[legislatura] = []
                            category_data[legislatura].extend(data_files)
            else:
                # This page might have data files directly, check for archive-items
                print(f"    No legislatura sub-pages found, checking for direct data files...")
                data_files = extract_archive_items_from_page(resource_url, None)
                
                if data_files:
                    # Group files by their legislatura (extracted from filename)
                    for file_data in data_files:
                        legislatura = file_data.get('legislatura')
                        if legislatura:
                            if legislatura not in category_data:
                                category_data[legislatura] = []
                            category_data[legislatura].append(file_data)
        
        if category_data:
            all_data[category] = category_data
            total_files = sum(len(files) for files in category_data.values())
            print(f"  Found {len(category_data)} legislative periods with {total_files} data files")
        else:
            print(f"  No data found")
    
    return all_data

def extract_legislatura_pages_from_main_page(main_page_url):
    """
    Extract legislatura-specific page URLs from the main data page's archive-items
    Returns list of tuples: [(legislatura_page_url, legislatura_name), ...]
    """
    try:
        print(f"        Extracting legislatura pages from main page...")
        response = requests.get(main_page_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all archive-item elements (these contain links to legislatura pages)
        archive_items = soup.find_all(class_='archive-item')
        
        legislatura_pages = []
        
        for item in archive_items:
            # Look for links within each archive item
            links = item.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if not href or not text:
                    continue
                
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = urljoin("https://www.parlamento.pt", href)
                
                # Extract legislatura from the link text
                legislatura = extract_legislatura_from_text(text)
                
                if legislatura:
                    # Check if this is an archive file
                    if any(ext in href.lower() for ext in ['.zip', '.rar']):
                        legislatura_pages.append((href, legislatura, 'archive'))
                        print(f"          Found {legislatura} archive file: {text}")
                    else:
                        legislatura_pages.append((href, legislatura, 'page'))
                        print(f"          Found {legislatura} legislatura page")
        
        print(f"        Found {len(legislatura_pages)} legislatura pages/archives")
        return legislatura_pages
        
    except Exception as e:
        print(f"        Error extracting legislatura pages: {e}")
        return []

def extract_archive_items_from_page(page_url, legislatura):
    """
    Extract actual data files from archive-item elements on a legislatura page
    """
    try:
        print(f"      Extracting archive items from page...")
        response = requests.get(page_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all archive-item elements
        archive_items = soup.find_all(class_='archive-item')
        
        data_files = []
        
        for item in archive_items:
            # Look for download links within each archive item
            links = item.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if not href or not text:
                    continue
                
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = urljoin("https://www.parlamento.pt", href)
                
                # Remove &Inline=true parameter to make file downloadable
                if '&Inline=true' in href:
                    href = href.replace('&Inline=true', '')
                elif '?Inline=true' in href:
                    href = href.replace('?Inline=true', '')
                
                # Check if this is a data file (look for parliament URLs with file extensions or ZIP files)
                is_data_file = ('app.parlamento.pt/webutils/docs/' in href and 
                               any(ext in href.lower() for ext in ['.xml', '.txt', '.pdf', '.json', '.xsd']))
                is_zip_file = any(ext in href.lower() for ext in ['.zip', '.rar'])
                
                if is_data_file or is_zip_file:
                    # Determine file type from filename, not just URL
                    file_type = get_file_type(text)  # Use filename instead of URL
                    
                    # Extract legislatura from filename if not provided
                    file_legislatura = legislatura or extract_legislatura_from_text(text)
                    
                    data_files.append({
                        'text': text,
                        'url': href,
                        'type': file_type,
                        'legislatura': file_legislatura
                    })
                    print(f"        Found: {file_type} - {text}")
        
        print(f"      Found {len(data_files)} data files")
        return data_files
        
    except Exception as e:
        print(f"      Error extracting from {page_url}: {e}")
        return []

def extract_legislatura_from_text(text):
    """Extract legislatura number from link text"""
    if not text:
        return None
    
    # Look for roman numerals (XVII, XVI, etc.)
    roman_match = re.search(r'\b(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|I|X|V|CONSTITUINTE)\b', text.upper())
    if roman_match:
        return roman_match.group(1)
    
    # Look for "Leg" followed by number
    leg_match = re.search(r'leg\s*(\d+)', text.lower())
    if leg_match:
        return leg_match.group(1)
    
    return None

def extract_legislatura_from_url(url):
    """Extract legislatura number from URL"""
    if not url:
        return None
    
    # Look for roman numerals in URL
    roman_match = re.search(r'(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|I|X|V|CONSTITUINTE)', url.upper())
    if roman_match:
        return roman_match.group(1)
    
    # Look for leg followed by number
    leg_match = re.search(r'leg(\d+)', url.lower())
    if leg_match:
        return leg_match.group(1)
    
    return None

def get_file_type(filename):
    """Determine file type from filename"""
    filename_lower = filename.lower()
    if '.pdf' in filename_lower:
        return 'PDF'
    elif '.xml' in filename_lower:
        return 'XML'
    elif '.xsd' in filename_lower:
        return 'XSD'
    elif '.json' in filename_lower or '_json.txt' in filename_lower:
        return 'JSON'
    elif '.txt' in filename_lower:
        return 'TXT'
    elif any(ext in filename_lower for ext in ['.zip', '.rar']):
        return 'Archive'
    else:
        return 'Page'

def is_dar_category(resource_url, category_name):
    """Check if this is a DAR (Diário da República) category"""
    return ('DAdar.aspx' in resource_url or 
            'dar' in category_name.lower() or 
            'diário' in category_name.lower() or
            'republica' in category_name.lower())

def extract_dar_data(main_dar_url):
    """
    Extract data from DAR's 5-level hierarchy:
    Level 1: Sub-series (Série I, II-A, etc.)
    Level 2: Legislaturas (XVII, XVI, etc.)  
    Level 3: Sessions (Sessão 01, etc.)
    Level 4: Numbers (Número 001, etc.)
    Level 5: Actual Files (JSON, XML)
    
    Returns: {legislatura: [data_files]}
    """
    print("        Using DAR 5-level extraction...")
    dar_data = {}
    
    try:
        # Level 1: Get sub-series from main DAR page
        response = requests.get(main_dar_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        sub_series = []
        archive_items = soup.find_all(class_='archive-item')
        
        for item in archive_items:
            title_elem = item.find('h3') or item.find('h2') or item.find('a')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            link_elem = item.find('a')
            if not link_elem:
                continue
                
            link = link_elem.get('href')
            if not link:
                continue
                
            if not link.startswith('http'):
                link = urljoin("https://www.parlamento.pt", link)
            
            # Only process sub-series pages (not ZIP files)
            if 'série' in title.lower() or 'serie' in title.lower():
                sub_series.append((title, link))
                print(f"          Found sub-series: {title}")
        
        # Level 2: Process each sub-series to get legislaturas
        for serie_title, serie_url in sub_series[:2]:  # Limit to first 2 for testing
            print(f"          Processing sub-series: {serie_title}")
            
            try:
                response = requests.get(serie_url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                legislaturas = []
                archive_items = soup.find_all(class_='archive-item')
                
                for item in archive_items:
                    title_elem = item.find('h3') or item.find('h2') or item.find('a')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    link_elem = item.find('a')
                    if not link_elem:
                        continue
                        
                    link = link_elem.get('href')
                    if not link:
                        continue
                        
                    if not link.startswith('http'):
                        link = urljoin("https://www.parlamento.pt", link)
                    
                    # Process both legislatura pages and ZIP files
                    if 'legislatura' in title.lower():
                        legislatura = extract_legislatura_from_text(title)
                        if legislatura:
                            if '.zip' in title.lower():
                                # Handle ZIP files directly
                                file_type = get_file_type(title)
                                
                                # Initialize legislatura data if needed
                                if legislatura not in dar_data:
                                    dar_data[legislatura] = []
                                
                                dar_data[legislatura].append({
                                    'text': title,
                                    'url': link,
                                    'type': file_type,
                                    'legislatura': legislatura,
                                    'sub_series': serie_title,
                                    'session': None,
                                    'number': None
                                })
                                print(f"            Found ZIP file: {legislatura} - {title}")
                            else:
                                # Handle regular legislatura pages
                                legislaturas.append((legislatura, title, link))
                                print(f"            Found legislatura: {legislatura}")
                
                # Level 3: Process each legislatura to get sessions
                for legislatura, leg_title, leg_url in legislaturas[:1]:  # Limit to first 1 for testing
                    print(f"            Processing legislatura: {legislatura}")
                    
                    try:
                        response = requests.get(leg_url, timeout=30)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        sessions = []
                        archive_items = soup.find_all(class_='archive-item')
                        
                        for item in archive_items:
                            title_elem = item.find('h3') or item.find('h2') or item.find('a')
                            if not title_elem:
                                continue
                                
                            title = title_elem.text.strip()
                            link_elem = item.find('a')
                            if not link_elem:
                                continue
                                
                            link = link_elem.get('href')
                            if not link:
                                continue
                                
                            if not link.startswith('http'):
                                link = urljoin("https://www.parlamento.pt", link)
                            
                            # Look for sessions
                            if 'sessão' in title.lower() or 'sessao' in title.lower():
                                sessions.append((title, link))
                                print(f"              Found session: {title}")
                        
                        # Level 4: Process each session to get numbers
                        for session_title, session_url in sessions[:1]:  # Limit to first 1 for testing
                            print(f"              Processing session: {session_title}")
                            
                            try:
                                response = requests.get(session_url, timeout=30)
                                response.raise_for_status()
                                soup = BeautifulSoup(response.content, 'html.parser')
                                
                                numbers = []
                                archive_items = soup.find_all(class_='archive-item')
                                
                                for item in archive_items:
                                    title_elem = item.find('h3') or item.find('h2') or item.find('a')
                                    if not title_elem:
                                        continue
                                        
                                    title = title_elem.text.strip()
                                    link_elem = item.find('a')
                                    if not link_elem:
                                        continue
                                        
                                    link = link_elem.get('href')
                                    if not link:
                                        continue
                                        
                                    if not link.startswith('http'):
                                        link = urljoin("https://www.parlamento.pt", link)
                                    
                                    # Look for numbers
                                    if 'número' in title.lower() or 'numero' in title.lower():
                                        numbers.append((title, link))
                                        print(f"                Found number: {title}")
                                
                                # Level 5: Process each number to get actual files
                                for number_title, number_url in numbers[:2]:  # Limit to first 2 for testing
                                    print(f"                Processing number: {number_title}")
                                    
                                    try:
                                        response = requests.get(number_url, timeout=30)
                                        response.raise_for_status()
                                        soup = BeautifulSoup(response.content, 'html.parser')
                                        
                                        archive_items = soup.find_all(class_='archive-item')
                                        
                                        for item in archive_items:
                                            links = item.find_all('a', href=True)
                                            
                                            for link in links:
                                                href = link.get('href')
                                                text = link.get_text(strip=True)
                                                
                                                if not href or not text:
                                                    continue
                                                
                                                # Convert relative URLs to absolute
                                                if href.startswith('/'):
                                                    href = urljoin("https://www.parlamento.pt", href)
                                                
                                                # Remove &Inline=true parameter
                                                if '&Inline=true' in href:
                                                    href = href.replace('&Inline=true', '')
                                                elif '?Inline=true' in href:
                                                    href = href.replace('?Inline=true', '')
                                                
                                                # Check if this is a data file
                                                if ('app.parlamento.pt/webutils/docs/' in href and 
                                                    any(ext in href.lower() for ext in ['.xml', '.txt', '.pdf', '.json', '.xsd'])):
                                                    
                                                    file_type = get_file_type(text)
                                                    
                                                    # Initialize legislatura data if needed
                                                    if legislatura not in dar_data:
                                                        dar_data[legislatura] = []
                                                    
                                                    dar_data[legislatura].append({
                                                        'text': text,
                                                        'url': href,
                                                        'type': file_type,
                                                        'legislatura': legislatura,
                                                        'sub_series': serie_title,
                                                        'session': session_title,
                                                        'number': number_title
                                                    })
                                                    print(f"                  Found: {file_type} - {text}")
                                    
                                    except Exception as e:
                                        print(f"                  Error processing number {number_title}: {e}")
                            
                            except Exception as e:
                                print(f"                Error processing session {session_title}: {e}")
                    
                    except Exception as e:
                        print(f"              Error processing legislatura {legislatura}: {e}")
            
            except Exception as e:
                print(f"            Error processing sub-series {serie_title}: {e}")
    
    except Exception as e:
        print(f"        Error processing DAR main page: {e}")
    
    return dar_data

def print_data_tree(data):
    """Print the data structure in a neat tree format"""
    print("\n" + "="*80)
    print("PARLIAMENT DATA TREE")
    print("="*80)
    
    for category, legislaturas in data.items():
        print(f"\n[{category}]")
        
        # Sort legislaturas (put CONSTITUINTE first, then reverse order)
        sorted_legs = sorted(legislaturas.keys(), key=lambda x: (
            0 if x == 'CONSTITUINTE' else 
            1000 - roman_to_int(x) if x in ['XVII', 'XVI', 'XV', 'XIV', 'XIII', 'XII', 'XI', 'X', 'IX', 'VIII', 'VII', 'VI', 'V', 'IV', 'III', 'II', 'I'] else 
            int(x) if x.isdigit() else 999
        ))
        
        for i, legislatura in enumerate(sorted_legs):
            links = legislaturas[legislatura]
            is_last_leg = i == len(sorted_legs) - 1
            leg_prefix = "+--" if is_last_leg else "+--"
            
            print(f"    {leg_prefix} Legislatura {legislatura} ({len(links)} files)")
            
            for j, link in enumerate(links):
                is_last_link = j == len(links) - 1
                link_prefix = "        +--"
                
                file_icon = "[PDF]" if link['type'] == 'PDF' else "[XML]" if link['type'] == 'XML' else "[XSD]" if link['type'] == 'XSD' else "[JSON]" if link['type'] == 'JSON' else "[TXT]" if link['type'] == 'TXT' else "[ZIP]" if link['type'] == 'Archive' else "[PAGE]"
                # Clean text for safe printing - keep only ASCII
                clean_text = ''.join(c for c in link['text'] if ord(c) < 128).strip()
                if not clean_text:
                    clean_text = "Data File"
                clean_text = clean_text[:60] + ('...' if len(clean_text) > 60 else '')
                print(f"{link_prefix} {file_icon} {clean_text}")
                print(f"{' ' * (len(link_prefix) + 2)} -> {link['url']}")
    
    total_categories = len(data)
    total_legislaturas = sum(len(legs) for legs in data.values())
    total_files = sum(len(links) for legs in data.values() for links in legs.values())
    
    print(f"\nSUMMARY:")
    print(f"    Categories: {total_categories}")
    print(f"    Legislative Periods: {total_legislaturas}")
    print(f"    Total Data Files: {total_files}")

def filter_recent_legislaturas(data, recent_only=False):
    """
    Filter data to include only recent legislative periods if requested
    """
    if not recent_only:
        return data
    
    print("Filtering for recent legislative periods only...")
    
    # Define recent legislaturas (current and previous few)
    recent_legislaturas = {'XVII', 'XVI', 'XV', 'XIV'}
    
    filtered_data = {}
    total_removed = 0
    
    for category, legislaturas in data.items():
        filtered_legislaturas = {}
        
        for legislatura, files in legislaturas.items():
            if legislatura in recent_legislaturas:
                filtered_legislaturas[legislatura] = files
            else:
                total_removed += len(files)
        
        if filtered_legislaturas:
            filtered_data[category] = filtered_legislaturas
    
    print(f"Filtered to recent periods only - removed {total_removed} older files")
    return filtered_data

def download_parliament_data_files(data, base_folder="parliament_data", skip_existing=False):
    """
    Download all discovered data files into a folder structure matching the tree
    """
    print("DOWNLOADING PARLIAMENT DATA FILES...")
    print("=" * 50)
    
    base_path = Path(base_folder)
    base_path.mkdir(exist_ok=True)
    
    total_downloaded = 0
    total_skipped = 0
    total_errors = 0
    
    for category, legislaturas in data.items():
        # Clean category name for safe printing and folder creation
        clean_category = ''.join(c for c in category if ord(c) < 128).strip()
        if not clean_category:
            clean_category = "Category"
        print(f"\nProcessing category: {clean_category}")
        
        # Create safe folder name by removing invalid characters for Windows paths
        safe_folder_name = re.sub(r'[<>:"/\\|?*]', '_', clean_category)
        safe_folder_name = safe_folder_name.replace(' / ', '_')  # Replace " / " with "_"
        safe_folder_name = safe_folder_name.strip()
        
        # Create category folder with safe name
        category_path = base_path / safe_folder_name
        category_path.mkdir(exist_ok=True)
        
        for legislatura, links in legislaturas.items():
            print(f"  Processing Legislatura {legislatura} ({len(links)} files)")
            
            # Create legislatura folder
            leg_path = category_path / f"Legislatura_{legislatura}"
            leg_path.mkdir(exist_ok=True)
            
            for i, link in enumerate(links):
                try:
                    url = link['url']
                    text = link['text']
                    file_type = link['type']
                    
                    # Determine file extension based on type and content
                    filename = text.lower()
                    if file_type == 'PDF' or '.pdf' in url.lower():
                        ext = '.pdf'
                    elif file_type == 'XML' or '.xml' in url.lower():
                        ext = '.xml'
                    elif file_type == 'XSD' or '.xsd' in url.lower():
                        ext = '.xsd'
                    elif file_type == 'JSON' or '.json' in url.lower():
                        ext = '.json'
                    elif file_type == 'TXT' or '.txt' in url.lower():
                        # Check if this is actually JSON data in a TXT file
                        if '_json.txt' in filename or 'json' in filename:
                            ext = '.json'  # Save JSON data with proper extension
                        else:
                            ext = '.txt'
                    elif file_type == 'Archive':
                        if '.zip' in url.lower():
                            ext = '.zip'
                        elif '.rar' in url.lower():
                            ext = '.rar'
                        else:
                            ext = '.zip'  # default
                    else:
                        ext = '.html'  # for pages
                    
                    # Create safe filename from text - remove all non-ASCII characters
                    safe_text = ''.join(c for c in text if ord(c) < 128).strip()
                    if not safe_text:
                        safe_text = "DataFile"
                    safe_filename = re.sub(r'[<>:"/\\\\|?*]', '_', safe_text)
                    safe_filename = safe_filename[:100]  # limit length
                    filename = f"{i+1:03d}_{safe_filename}{ext}"
                    
                    file_path = leg_path / filename
                    
                    # Check if file exists and handle skip/overwrite logic
                    if file_path.exists():
                        if skip_existing:
                            print(f"    [SKIP] File {i+1:03d} (already exists)")
                            total_skipped += 1
                            continue
                        else:
                            print(f"    [OVER] File {i+1:03d} (overwriting)")
                    else:
                        print(f"    [DOWN] File {i+1:03d}")
                    
                    response = requests.get(url, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    # Write file in chunks to handle large files
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    total_downloaded += 1
                    
                    # Small delay to be respectful to the server
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"    [ERR ] File {i+1:03d} failed: {str(e)[:50]}")
                    total_errors += 1
                    continue
    
    print("\n" + "=" * 50)
    print("DOWNLOAD SUMMARY:")
    print(f"  Files downloaded: {total_downloaded}")
    print(f"  Files skipped: {total_skipped}")
    print(f"  Errors: {total_errors}")
    print(f"  Download folder: {base_path.absolute()}")

def run_parliament_data_discovery(recent_only=False, skip_existing=False):
    """
    Run the complete Parliament data discovery and download process
    """
    scope = "RECENT" if recent_only else "FULL"
    print(f"PORTUGUESE PARLIAMENT DATA DISCOVERY & DOWNLOAD ({scope})")
    print("=" * 60)
    
    # Step 1: Get resource URLs
    print("\nSTEP 1: Getting resource categories...")
    resources = get_parliament_open_data_resources()
    
    if not resources:
        print("No resources found. Exiting.")
        return
    
    print(f"Found {len(resources)} resource categories")
    
    # Step 2: Extract legislative periods and data links
    print("\nSTEP 2: Extracting legislative periods and data links...")
    data = get_legislative_periods_and_data_links(resources)
    
    if not data:
        print("No data links found. Exiting.")
        return
    
    # Step 3: Filter for recent periods if requested
    if recent_only:
        print("\nSTEP 3: Filtering for recent legislative periods...")
        data = filter_recent_legislaturas(data, recent_only=True)
    
    # Step 4: Display summary
    total_categories = len(data)
    total_legislaturas = sum(len(legs) for legs in data.values())
    total_files = sum(len(links) for legs in data.values() for links in legs.values())
    
    step_num = 4 if recent_only else 3
    print(f"\nSTEP {step_num}: Data discovery summary:")
    print(f"  Categories: {total_categories}")
    print(f"  Legislative Periods: {total_legislaturas}")
    print(f"  Total Data Files: {total_files}")
    
    # Step 5/4: Download all files
    step_num += 1
    mode = " (skipping existing files)" if skip_existing else " (overwriting existing files)"
    print(f"\nSTEP {step_num}: Downloading data files{mode}...")
    download_parliament_data_files(data, skip_existing=skip_existing)
    
    print(f"\nPARLIAMENT DATA DISCOVERY COMPLETE ({scope})!")

def clean_xml_content(content: bytes) -> bytes:
    """Limpar conteúdo XML removendo BOM Unicode"""
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]
    elif content.startswith(b'\xff\xfe'):
        content = content[2:]
    elif content.startswith(b'\xfe\xff'):
        content = content[2:]
    return content

def parse_date(date_str: str) -> date:
    """Converter string de data para objeto date"""
    if not date_str or date_str.strip() == '':
        return None
    
    date_str = date_str.strip()
    
    try:
        # Formato padrão: 2025-06-03
        if '-' in date_str and len(date_str) >= 10:
            return datetime.strptime(date_str[:10], '%Y-%m-%d').date()
    except ValueError:
        pass
        
    try:
        # Formato alternativo: 2025-06-03T00:00:00
        if 'T' in date_str:
            return datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').date()
    except ValueError:
        pass
    
    return None

def safe_int(value) -> int:
    """Converter para int de forma segura"""
    if value is None or value == '':
        return None
    try:
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                return None
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None

def roman_to_int(roman: str) -> int:
    """Converter numeração romana para inteiro"""
    if not roman or roman.strip() == '':
        return 17
    
    roman_map = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
        'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18,
        'CONSTITUINTE': 0
    }
    
    roman = roman.strip().upper()
    return roman_map.get(roman, 17)

def get_or_create_legislatura(cursor: sqlite3.Cursor, sigla: str) -> int:
    """Buscar ou criar legislatura"""
    numero = roman_to_int(sigla)
    
    cursor.execute("SELECT id FROM legislaturas WHERE numero = ?", (numero,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # Criar nova legislatura
    cursor.execute("""
    INSERT INTO legislaturas (numero, designacao, ativa)
    VALUES (?, ?, ?)
    """, (numero, f"{sigla} Legislatura", sigla == 'XVII'))
    
    return cursor.lastrowid

def extract_time_from_text(text):
    """Extract the first time pattern from text like '14h30' or '09h45'"""
    if not text:
        return None
    
    # Decode HTML entities first
    decoded_text = html.unescape(text)
    
    # Pattern to match Portuguese time format: 14h30, 09h45, 11h00, etc.
    time_pattern = r'(\d{1,2})h(\d{2})'
    
    match = re.search(time_pattern, decoded_text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        
        # Validate time
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    
    return None

def extract_all_times_from_text(text):
    """Extract all time patterns from text and return as list"""
    if not text:
        return []
    
    # Decode HTML entities first
    decoded_text = html.unescape(text)
    
    # Pattern to match Portuguese time format: 14h30, 09h45, 11h00, etc.
    time_pattern = r'(\d{1,2})h(\d{2})'
    
    times = []
    for match in re.finditer(time_pattern, decoded_text):
        hour = int(match.group(1))
        minute = int(match.group(2))
        
        # Validate time
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            times.append(time(hour, minute))
    
    return times

def extract_time_range_info(text):
    """Extract comprehensive time information from agenda text"""
    if not text:
        return None, None, []
    
    times = extract_all_times_from_text(text)
    
    if not times:
        return None, None, []
    
    # First time as start, last time as potential end
    hora_inicio = times[0]
    hora_fim = times[-1] if len(times) > 1 else None
    
    # If start and end are the same, set end to None
    if hora_fim and hora_inicio == hora_fim:
        hora_fim = None
    
    return hora_inicio, hora_fim, times

def corrigir_importacao_iniciativas():
    """Corrigir importação de iniciativas com estrutura XML real"""
    
    print("CORRIGINDO IMPORTACAO DE INICIATIVAS...")
    
    db_path = 'parlamento.db'
    base_path = "parliament_data_final"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Limpar dados existentes de iniciativas
    cursor.execute("DELETE FROM iniciativas_legislativas")
    cursor.execute("DELETE FROM autores_iniciativas")
    
    total_iniciativas = 0
    total_autores = 0
    
    # Buscar todos os arquivos de iniciativas
    pattern = f"{base_path}/Iniciativas/**/*.xml"
    arquivos = glob.glob(pattern, recursive=True)
    
    print(f"Encontrados {len(arquivos)} arquivos de iniciativas")
    
    for i, arquivo in enumerate(arquivos):
        print(f"[{i+1}/{len(arquivos)}] Processando: {os.path.basename(arquivo)}")
        
        try:
            with open(arquivo, 'rb') as f:
                content = clean_xml_content(f.read())
            
            root = ET.fromstring(content.decode('utf-8'))
            
            # Extrair legislatura do nome do arquivo
            filename = os.path.basename(arquivo)
            leg_match = re.search(r'Iniciativas(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
            legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
            legislatura_id = get_or_create_legislatura(cursor, legislatura_sigla)
            
            # Buscar iniciativas com a estrutura XML real
            for iniciativa in root.findall('.//Pt_gov_ar_objectos_iniciativas_DetalhePesquisaIniciativasOut'):
                try:
                    # Extrair campos conforme estrutura XML real
                    ini_nr = iniciativa.find('IniNr')
                    ini_tipo = iniciativa.find('IniTipo')
                    ini_desc_tipo = iniciativa.find('IniDescTipo')
                    ini_titulo = iniciativa.find('IniTitulo')
                    ini_id = iniciativa.find('IniId')
                    data_inicio_leg = iniciativa.find('DataInicioleg')
                    ini_leg = iniciativa.find('IniLeg')
                    ini_sel = iniciativa.find('IniSel')
                    
                    numero = ini_nr.text if ini_nr is not None else None
                    tipo = ini_tipo.text if ini_tipo is not None else None
                    tipo_descricao = ini_desc_tipo.text if ini_desc_tipo is not None else None
                    titulo = ini_titulo.text if ini_titulo is not None else None
                    id_externo = ini_id.text if ini_id is not None else None
                    data_apresentacao = data_inicio_leg.text if data_inicio_leg is not None else None
                    sessao = ini_sel.text if ini_sel is not None else None
                    
                    if numero and tipo and titulo:
                        # Inserir iniciativa
                        cursor.execute("""
                        INSERT OR REPLACE INTO iniciativas_legislativas 
                        (id_externo, numero, tipo, tipo_descricao, titulo, data_apresentacao, sessao, legislatura_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            safe_int(id_externo),
                            safe_int(numero),
                            tipo,
                            tipo_descricao,
                            titulo,
                            parse_date(data_apresentacao),
                            safe_int(sessao),
                            legislatura_id
                        ))
                        
                        iniciativa_db_id = cursor.lastrowid
                        if cursor.rowcount == 0:  # Se foi substituição, buscar ID
                            cursor.execute("SELECT id FROM iniciativas_legislativas WHERE id_externo = ?", (safe_int(id_externo),))
                            result = cursor.fetchone()
                            if result:
                                iniciativa_db_id = result[0]
                        
                        total_iniciativas += 1
                        
                        # Processar autores deputados
                        autores_deputados = iniciativa.find('IniAutorDeputados')
                        if autores_deputados is not None:
                            for autor in autores_deputados.findall('pt_gov_ar_objectos_iniciativas_AutoresDeputadosOut'):
                                id_cadastro_elem = autor.find('idCadastro')
                                nome_elem = autor.find('nome')
                                gp_elem = autor.find('GP')
                                
                                id_cadastro = id_cadastro_elem.text if id_cadastro_elem is not None else None
                                
                                if id_cadastro:
                                    # Buscar deputado
                                    cursor.execute("SELECT id FROM deputados WHERE id_cadastro = ?", (safe_int(id_cadastro),))
                                    dep_result = cursor.fetchone()
                                    
                                    if dep_result:
                                        cursor.execute("""
                                        INSERT OR REPLACE INTO autores_iniciativas 
                                        (iniciativa_id, deputado_id, tipo_autor, ordem)
                                        VALUES (?, ?, ?, ?)
                                        """, (iniciativa_db_id, dep_result[0], 'principal', 1))
                                        total_autores += 1
                        
                        # Processar autores grupos parlamentares
                        autores_gps = iniciativa.find('IniAutorGruposParlamentares')
                        if autores_gps is not None:
                            for autor_gp in autores_gps.findall('pt_gov_ar_objectos_AutoresGruposParlamentaresOut'):
                                gp_elem = autor_gp.find('GP')
                                gp = gp_elem.text if gp_elem is not None else None
                                
                                if gp:
                                    # Buscar partido
                                    cursor.execute("SELECT id FROM partidos WHERE sigla = ?", (gp,))
                                    partido_result = cursor.fetchone()
                                    
                                    if partido_result:
                                        cursor.execute("""
                                        INSERT OR REPLACE INTO autores_iniciativas 
                                        (iniciativa_id, partido_id, tipo_autor, ordem)
                                        VALUES (?, ?, ?, ?)
                                        """, (iniciativa_db_id, partido_result[0], 'apresentante', 1))
                                        total_autores += 1
                
                except Exception as e:
                    print(f"  Erro ao processar iniciativa individual: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"  Erro ao processar arquivo {arquivo}: {str(e)}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"CORRECAO INICIATIVAS CONCLUIDA:")
    print(f"  Iniciativas importadas: {total_iniciativas}")
    print(f"  Autores importados: {total_autores}")

def extract_thumbnail_url_from_video_url(video_url):
    """Extract thumbnail URL from video URL pattern"""
    if not video_url:
        return None
    
    # Pattern: https://av.parlamento.pt/videos/Plenary/17/1/9/30
    # Thumbnail: /api/v1/videos/Plenary/17/1/9/thumbnail/30
    try:
        # Extract the path after /videos/
        if '/videos/' in video_url:
            path_parts = video_url.split('/videos/')[1]
            thumbnail_url = f"/api/v1/videos/{path_parts.replace('/', '/')}/thumbnail/{path_parts.split('/')[-1]}"
            # Fix the thumbnail URL format
            parts = path_parts.split('/')
            if len(parts) >= 4:
                # Plenary/17/1/9/30 -> /api/v1/videos/Plenary/17/1/9/thumbnail/30
                thumbnail_url = f"/api/v1/videos/{'/'.join(parts[:-1])}/thumbnail/{parts[-1]}"
                return thumbnail_url
    except:
        pass
    
    return None

def corrigir_importacao_intervencoes():
    """Corrigir importação de intervenções com dados audiovisuais"""
    
    print("CORRIGINDO IMPORTACAO DE INTERVENCOES...")
    
    db_path = 'parlamento.db'
    base_path = "parliament_data_final"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Limpar dados existentes
    cursor.execute("DELETE FROM intervencoes")
    
    total_intervencoes = 0
    total_com_video = 0
    
    # Buscar todos os arquivos de intervenções
    pattern = f"{base_path}/Intervencoes/**/*.xml"
    arquivos = glob.glob(pattern, recursive=True)
    
    print(f"Encontrados {len(arquivos)} arquivos de intervencoes")
    
    for i, arquivo in enumerate(arquivos):
        print(f"[{i+1}/{len(arquivos)}] Processando: {os.path.basename(arquivo)}")
        
        try:
            with open(arquivo, 'rb') as f:
                content = clean_xml_content(f.read())
            
            root = ET.fromstring(content.decode('utf-8'))
            
            # Extrair legislatura do nome do arquivo
            filename = os.path.basename(arquivo)
            leg_match = re.search(r'Intervencoes(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
            legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
            legislatura_id = get_or_create_legislatura(cursor, legislatura_sigla)
            
            # Buscar intervenções usando estrutura real: DadosPesquisaIntervencoesOut
            for intervencao in root.findall('.//DadosPesquisaIntervencoesOut'):
                try:
                    # Extrair campos conforme estrutura XML real
                    id_elem = intervencao.find('Id')
                    data_elem = intervencao.find('DataReuniaoPlenaria')
                    tipo_elem = intervencao.find('TipoIntervencao')
                    resumo_elem = intervencao.find('Resumo')
                    
                    # Extract deputy ID from nested Deputados element
                    deputados_elem = intervencao.find('Deputados')
                    deputado_cad_id = None
                    if deputados_elem is not None:
                        id_cadastro_elem = deputados_elem.find('idCadastro')
                        if id_cadastro_elem is not None:
                            deputado_cad_id = id_cadastro_elem.text
                    
                    # Extract audiovisual data
                    dados_audiovisual = intervencao.find('DadosAudiovisual')
                    url_video = None
                    thumbnail_url = None
                    assunto = None
                    duracao_video = None
                    
                    if dados_audiovisual is not None:
                        av_out = dados_audiovisual.find('pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut')
                        if av_out is not None:
                            assunto_elem = av_out.find('assunto')
                            url_elem = av_out.find('url')
                            duracao_elem = av_out.find('duracao')
                            
                            if assunto_elem is not None:
                                assunto = assunto_elem.text
                            if url_elem is not None:
                                url_video = url_elem.text
                                thumbnail_url = extract_thumbnail_url_from_video_url(url_video)
                            if duracao_elem is not None:
                                duracao_video = duracao_elem.text
                    
                    if deputado_cad_id and data_elem is not None and data_elem.text:
                        id_externo = id_elem.text if id_elem is not None else None
                        data_intervencao = data_elem.text
                        tipo_intervencao = tipo_elem.text if tipo_elem is not None else 'Intervenção'
                        resumo = resumo_elem.text if resumo_elem is not None else None
                        
                        # Buscar deputado
                        cursor.execute("SELECT id FROM deputados WHERE id_cadastro = ?", (safe_int(deputado_cad_id),))
                        dep_result = cursor.fetchone()
                        
                        if dep_result:
                            cursor.execute("""
                            INSERT OR REPLACE INTO intervencoes 
                            (id_externo, deputado_id, data_intervencao, tipo_intervencao, sumario, resumo, 
                             legislatura_id, url_video, thumbnail_url, assunto, duracao_video)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                safe_int(id_externo),
                                dep_result[0],
                                parse_date(data_intervencao),
                                tipo_intervencao,
                                resumo,
                                resumo,  # using resumo for both sumario and resumo
                                legislatura_id,
                                url_video,
                                thumbnail_url,
                                assunto,
                                duracao_video
                            ))
                            total_intervencoes += 1
                            
                            if url_video:
                                total_com_video += 1
                
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"  Erro ao processar arquivo {arquivo}: {str(e)}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"CORRECAO INTERVENCOES CONCLUIDA:")
    print(f"  Intervencoes importadas: {total_intervencoes}")
    print(f"  Intervencoes com video: {total_com_video}")

def corrigir_horarios_agenda():
    """Extract and update agenda times from subtitles and descriptions with multiple time support"""
    
    print("CORRIGINDO HORARIOS DA AGENDA...")
    
    db_path = 'parlamento.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find all records to update time information (reset and re-extract)
    cursor.execute('''
        SELECT id, titulo, subtitulo, descricao
        FROM agenda_parlamentar 
        WHERE (subtitulo LIKE '%h%' OR descricao LIKE '%h%')
    ''')
    
    records = cursor.fetchall()
    updated_count = 0
    multiple_times_count = 0
    
    print(f"Encontrados {len(records)} registros de agenda para processar...")
    
    for record in records:
        id_record, titulo, subtitulo, descricao = record
        
        # Try to extract time range info from subtitle first, then description
        text_to_process = subtitulo or descricao
        
        if text_to_process:
            hora_inicio, hora_fim, all_times = extract_time_range_info(text_to_process)
            
            if hora_inicio:
                # Update the record with extracted time information
                cursor.execute('''
                    UPDATE agenda_parlamentar 
                    SET hora_inicio = ?, hora_fim = ?
                    WHERE id = ?
                ''', (
                    hora_inicio.strftime('%H:%M:%S'), 
                    hora_fim.strftime('%H:%M:%S') if hora_fim else None,
                    id_record
                ))
                
                updated_count += 1
                
                if len(all_times) > 1:
                    multiple_times_count += 1
                    times_str = ', '.join([t.strftime('%H:%M') for t in all_times])
                    print(f"  Múltiplos horários: '{titulo[:40]}...' -> {times_str}")
                else:
                    print(f"  Atualizado '{titulo[:50]}...' com horario {hora_inicio}")
    
    conn.commit()
    conn.close()
    
    print(f"CORRECAO HORARIOS CONCLUIDA:")
    print(f"  Registros atualizados: {updated_count}")
    print(f"  Registros com multiplos horarios: {multiple_times_count}")

def calcular_assiduidade_deputados():
    """Calculate attendance rates for all deputies and populate metricas_deputados table"""
    
    print("CALCULANDO ASSIDUIDADE DOS DEPUTADOS...")
    
    db_path = 'parlamento.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing metrics
    cursor.execute("DELETE FROM metricas_deputados")
    
    # Get all deputies with their mandate periods and voting data
    query = """
    SELECT 
        d.id as deputado_id,
        d.nome,
        m.legislatura_id,
        l.numero as leg_numero,
        m.data_inicio as mandate_start,
        m.data_fim as mandate_end,
        COUNT(DISTINCT vi.votacao_id) as votes_cast,
        COUNT(DISTINCT i.id) as total_interventions
    FROM deputados d
    INNER JOIN mandatos m ON d.id = m.deputado_id
    INNER JOIN legislaturas l ON m.legislatura_id = l.id
    LEFT JOIN votos_individuais vi ON d.id = vi.deputado_id
    LEFT JOIN votacoes v ON vi.votacao_id = v.id AND v.legislatura_id = m.legislatura_id
    LEFT JOIN intervencoes i ON d.id = i.deputado_id AND i.legislatura_id = m.legislatura_id
    -- Include all mandates regardless of ativo status
    GROUP BY d.id, m.legislatura_id, d.nome, l.numero, m.data_inicio, m.data_fim
    ORDER BY l.numero DESC, d.nome
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    metrics_inserted = 0
    
    for row in results:
        deputado_id, nome, leg_id, leg_num, mandate_start, mandate_end, votes_cast, interventions = row
        
        # Calculate total possible votes for this deputy in this legislature
        cursor.execute("SELECT COUNT(DISTINCT id) FROM votacoes WHERE legislatura_id = ?", (leg_id,))
        total_possible_votes = cursor.fetchone()[0]
        
        # Calculate attendance rate
        if total_possible_votes > 0:
            attendance_rate = (votes_cast / total_possible_votes) * 100
        else:
            attendance_rate = 0.0
        
        # Get initiative count
        cursor.execute("""
            SELECT COUNT(DISTINCT ai.iniciativa_id)
            FROM autores_iniciativas ai
            INNER JOIN iniciativas_legislativas il ON ai.iniciativa_id = il.id
            WHERE ai.deputado_id = ? AND il.legislatura_id = ?
        """, (deputado_id, leg_id))
        
        total_initiatives = cursor.fetchone()[0]
        
        # Insert metrics
        cursor.execute("""
            INSERT INTO metricas_deputados (
                deputado_id, legislatura_id, periodo_inicio, periodo_fim,
                total_intervencoes, total_iniciativas, total_votacoes_participadas,
                taxa_assiduidade, ultima_atualizacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            deputado_id, leg_id, mandate_start, mandate_end,
            interventions, total_initiatives, votes_cast,
            round(attendance_rate, 2), datetime.now()
        ))
        
        metrics_inserted += 1
    
    conn.commit()
    conn.close()
    
    print(f"CALCULO DE ASSIDUIDADE CONCLUIDO:")
    print(f"  Metricas calculadas: {metrics_inserted}")

def verificar_dados_corrigidos():
    """Verificar dados após correção"""
    
    print("VERIFICANDO DADOS CORRIGIDOS...")
    
    db_path = 'parlamento.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar totais
    cursor.execute("SELECT COUNT(*) FROM iniciativas_legislativas")
    total_iniciativas = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM autores_iniciativas")
    total_autores = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM intervencoes")
    total_intervencoes = cursor.fetchone()[0]
    
    # Verificar agenda com horários
    cursor.execute("SELECT COUNT(*) FROM agenda_parlamentar WHERE hora_inicio IS NOT NULL")
    agenda_com_hora = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM agenda_parlamentar")
    total_agenda = cursor.fetchone()[0]
    
    # Verificar métricas de assiduidade
    cursor.execute("SELECT COUNT(*) FROM metricas_deputados")
    total_metricas = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(taxa_assiduidade) FROM metricas_deputados WHERE taxa_assiduidade > 0")
    avg_attendance = cursor.fetchone()[0]
    
    # Verificar dados biográficos
    cursor.execute("SELECT COUNT(*) FROM deputados WHERE profissao IS NOT NULL AND profissao != ''")
    with_profession = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM deputados WHERE habilitacoes_academicas IS NOT NULL AND habilitacoes_academicas != ''")
    with_education = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM deputados")
    total_deputies = cursor.fetchone()[0]
    
    print(f"DADOS FINAIS:")
    print(f"  Iniciativas legislativas: {total_iniciativas}")
    print(f"  Autores de iniciativas: {total_autores}")
    print(f"  Intervencoes: {total_intervencoes}")
    print(f"  Agenda total: {total_agenda}")
    print(f"  Agenda com horario: {agenda_com_hora}")
    print(f"  Metricas de assiduidade: {total_metricas}")
    if avg_attendance:
        print(f"  Taxa media de assiduidade: {avg_attendance:.1f}%")
    print(f"  Deputados total: {total_deputies}")
    print(f"  Deputados com profissao: {with_profession}")
    print(f"  Deputados com habilitacoes: {with_education}")
    
    # Mostrar algumas iniciativas por legislatura
    print(f"\nINICIATIVAS POR LEGISLATURA:")
    cursor.execute("""
    SELECT l.designacao, COUNT(i.id)
    FROM legislaturas l
    LEFT JOIN iniciativas_legislativas i ON l.id = i.legislatura_id
    GROUP BY l.id, l.designacao
    ORDER BY l.numero DESC
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} iniciativas")
    
    conn.close()

def corrigir_importacao_dados_biograficos():
    """Importar dados biográficos dos deputados"""
    
    print("CORRIGINDO IMPORTACAO DE DADOS BIOGRAFICOS...")
    
    db_path = 'parlamento.db'
    base_path = "parliament_data_final"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_updated = 0
    
    # Buscar todos os arquivos de dados biográficos
    pattern = f"{base_path}/RegistoBiografico/**/*.xml"
    arquivos = glob.glob(pattern, recursive=True)
    
    print(f"Encontrados {len(arquivos)} arquivos de dados biograficos")
    
    for i, arquivo in enumerate(arquivos):
        print(f"[{i+1}/{len(arquivos)}] Processando: {os.path.basename(arquivo)}")
        
        try:
            with open(arquivo, 'rb') as f:
                content = clean_xml_content(f.read())
            
            root = ET.fromstring(content.decode('utf-8'))
            
            # Processar registros biográficos usando a estrutura XML real  
            for record in root.findall('.//DadosRegistoBiografico'):
                try:
                    # Extrair campos do registro biográfico
                    cad_id_elem = record.find('CadId')
                    nome_completo_elem = record.find('CadNomeCompleto')
                    data_nascimento_elem = record.find('CadDtNascimento')
                    sexo_elem = record.find('CadSexo')
                    profissao_elem = record.find('CadProfissao')
                    
                    id_cadastro = safe_int(cad_id_elem.text) if cad_id_elem is not None else None
                    nome_completo = nome_completo_elem.text if nome_completo_elem is not None else None
                    data_nascimento = data_nascimento_elem.text if data_nascimento_elem is not None else None
                    sexo = sexo_elem.text if sexo_elem is not None else None
                    profissao = profissao_elem.text if profissao_elem is not None else None
                    
                    # Processar habilitações acadêmicas
                    habilitacoes_list = []
                    habilitacoes_elem = record.find('CadHabilitacoes')
                    if habilitacoes_elem is not None:
                        for hab in habilitacoes_elem.findall('DadosHabilitacoes'):
                            hab_des = hab.find('HabDes')
                            if hab_des is not None and hab_des.text:
                                habilitacoes_list.append(hab_des.text)
                    
                    habilitacoes_academicas = '; '.join(habilitacoes_list) if habilitacoes_list else None
                    
                    if id_cadastro:
                        # Verificar se o deputado existe
                        cursor.execute("SELECT id FROM deputados WHERE id_cadastro = ?", (id_cadastro,))
                        deputado_result = cursor.fetchone()
                        
                        if deputado_result:
                            # Atualizar informações biográficas
                            cursor.execute("""
                            UPDATE deputados 
                            SET nome_completo = COALESCE(?, nome_completo),
                                profissao = COALESCE(?, profissao),
                                habilitacoes_academicas = COALESCE(?, habilitacoes_academicas),
                                updated_at = ?
                            WHERE id_cadastro = ?
                            """, (
                                nome_completo,
                                profissao,
                                habilitacoes_academicas,
                                datetime.now(),
                                id_cadastro
                            ))
                            
                            if cursor.rowcount > 0:
                                total_updated += 1
                
                except Exception as e:
                    print(f"  Erro ao processar registro biografico individual: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"  Erro ao processar arquivo {arquivo}: {str(e)}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"CORRECAO DADOS BIOGRAFICOS CONCLUIDA:")
    print(f"  Deputados atualizados: {total_updated}")

def main():
    """Função principal"""
    print("CORRIGINDO IMPORTADORES DE XML")
    print("=" * 50)
    
    # Corrigir iniciativas
    corrigir_importacao_iniciativas()
    print()
    
    # Corrigir intervenções
    corrigir_importacao_intervencoes()
    print()
    
    # Corrigir horários da agenda
    corrigir_horarios_agenda()
    print()
    
    # Calcular assiduidade dos deputados
    calcular_assiduidade_deputados()
    print()
    
    # Importar dados biográficos
    corrigir_importacao_dados_biograficos()
    print()
    
    # Verificar dados
    verificar_dados_corrigidos()
    
    print("\nCORRECAO CONCLUIDA!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--discover":
        # Parse flags
        recent_only = "--recent" in sys.argv
        skip_existing = "--skip-existing" in sys.argv
        
        # Run the new data discovery and download process
        run_parliament_data_discovery(recent_only=recent_only, skip_existing=skip_existing)
    else:
        # Run the original XML correction process
        main()