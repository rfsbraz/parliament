#!/usr/bin/env python3
"""
Parliament Data Import System
Integrates data discovery with file-by-file processing and import tracking
"""

import sys
import argparse
import data_importer
from file_processor import ParliamentFileProcessor

def group_files_by_name(files):
    """Group files by base name to choose optimal format (JSON over XML)"""
    grouped = {}
    
    for file_data in files:
        # Extract base name without extension
        file_name = file_data.get('text', '')
        base_name = file_name
        
        # Remove common extensions to group related files
        for ext in ['.json.txt', '.xml', '.json', '.pdf', '.zip']:
            if base_name.endswith(ext):
                base_name = base_name[:-len(ext)]
                break
        
        if base_name not in grouped:
            grouped[base_name] = []
        grouped[base_name].append(file_data)
    
    return grouped

def choose_optimal_file(file_group):
    """Choose the best file from a group (prefer JSON over XML)"""
    json_files = [f for f in file_group if f.get('type') in ['JSON']]
    xml_files = [f for f in file_group if f.get('type') in ['XML']]
    other_files = [f for f in file_group if f.get('type') not in ['JSON', 'XML']]
    
    # Priority: JSON > XML > Others
    if json_files:
        return json_files[0]
    elif xml_files:
        return xml_files[0]
    elif other_files:
        return other_files[0]
    else:
        return file_group[0] if file_group else None

def main():
    parser = argparse.ArgumentParser(description='Import Parliament data with tracking')
    parser.add_argument('--discover', action='store_true', help='Discover and queue all files for processing')
    parser.add_argument('--process', action='store_true', help='Process queued files one by one')
    parser.add_argument('--category', help='Process only files from specific category')
    parser.add_argument('--legislatura', help='Process only files from specific legislatura')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--skip-existing', action='store_true', help='Skip files already processed')
    
    args = parser.parse_args()
    
    # Initialize processors
    file_processor = ParliamentFileProcessor()
    
    if args.discover:
        print("DISCOVERING PARLIAMENT DATA FILES...")
        print("="*80)
        
        # Get all resource URLs
        print("Step 1: Getting resource URLs...")
        resources = data_importer.get_parliament_open_data_resources()
        print(f"Found {len(resources)} resource categories")
        
        # Get all data files
        print("\nStep 2: Extracting all data files...")
        all_data = data_importer.get_legislative_periods_and_data_links(resources)
        
        # Flatten and queue files for processing
        total_files = 0
        total_groups = 0
        
        for category, legislaturas in all_data.items():
            print(f"\nProcessing category: {category}")
            
            for legislatura, files in legislaturas.items():
                print(f"  Legislatura {legislatura}: {len(files)} files")
                
                # Group files by base name to choose optimal format
                grouped_files = group_files_by_name(files)
                
                for base_name, file_group in grouped_files.items():
                    total_groups += 1
                    
                    # Choose optimal file from group
                    chosen_file = choose_optimal_file(file_group)
                    if chosen_file:
                        # Add metadata
                        chosen_file['category'] = category
                        
                        # Queue file for processing
                        file_info = file_processor.get_file_info(chosen_file)
                        file_processor.insert_import_record(file_info)
                        total_files += 1
                        
                        # Show what was skipped
                        skipped = [f for f in file_group if f != chosen_file]
                        if skipped:
                            skipped_types = [f.get('type', 'Unknown') for f in skipped]
                            print(f"    Queued: {chosen_file.get('type')} {chosen_file.get('text')}")
                            print(f"    Skipped: {', '.join(skipped_types)} (same base name)")
        
        print(f"\n" + "="*80)
        print(f"DISCOVERY COMPLETE")
        print(f"Total file groups processed: {total_groups}")
        print(f"Total files queued for import: {total_files}")
        print(f"Use --process to start processing files")
    
    elif args.process:
        print("PROCESSING QUEUED FILES...")
        print("="*80)
        
        # Get files to process from database
        import sqlite3
        with sqlite3.connect(file_processor.db_path) as conn:
            cursor = conn.cursor()
            
            # Build query with filters
            query = "SELECT * FROM import_status WHERE status = 'pending'"
            params = []
            
            if args.category:
                query += " AND category LIKE ?"
                params.append(f"%{args.category}%")
            
            if args.legislatura:
                query += " AND legislatura = ?"
                params.append(args.legislatura)
            
            if args.limit:
                query += " LIMIT ?"
                params.append(args.limit)
            
            cursor.execute(query, params)
            pending_files = cursor.fetchall()
        
        if not pending_files:
            print("No pending files found for processing")
            return
        
        print(f"Found {len(pending_files)} files to process")
        
        # Process each file
        for i, file_record in enumerate(pending_files, 1):
            file_data = {
                'url': file_record[1],  # file_url
                'text': file_record[3],  # file_name
                'type': file_record[4],  # file_type
                'category': file_record[5],  # category
                'legislatura': file_record[6],  # legislatura
                'sub_series': file_record[7],  # sub_series
                'session': file_record[8],  # session
                'number': file_record[9]  # number
            }
            
            print(f"\n[{i}/{len(pending_files)}]")
            
            # Process the file
            success = file_processor.process_single_file(file_data)
            
            if not success:
                print(f"\nProcessing stopped due to schema mismatch or error.")
                print(f"Please review the file structure and update the schema mapping.")
                print(f"Use --status to see current import status.")
                break
        
        print(f"\n" + "="*80)
        print("PROCESSING COMPLETE")
        
        # Show final status
        summary = file_processor.get_import_status_summary()
        print("Final Import Status:")
        for status, count in summary.items():
            print(f"  {status}: {count}")
    
    else:
        print("Parliament Data Import System")
        print("Use --help for available options")
        print("\nBasic workflow:")
        print("1. python import_parliament_data.py --discover    # Discover and queue files")
        print("2. python import_parliament_data.py --process     # Process files one by one")
        print("3. python file_processor.py --status             # Check import status")

if __name__ == "__main__":
    main()