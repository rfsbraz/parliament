#!/usr/bin/env python3
"""
Direct Portuguese Parliament Data Downloader
Downloads data using known direct API endpoints
"""

import os
import json
import requests
import logging
from datetime import datetime
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parliament_direct_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DirectParliamentDownloader:
    def __init__(self, output_dir="parliament_data"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Direct download URLs for Portuguese Parliament data
        # These are the actual data endpoints discovered through analysis
        self.direct_urls = {
            "XVII_Legislature": {
                "InformacaoBase": {
                    "deputados_xml": "https://app.parlamento.pt/webutils/docs/doc.xml?path=6148523063446f764c324679626d56304c334e706447567a4c31684a566b786c5a793944543030764e6a497653586c6653475679595735765a476c6e636d46745953396b5a58423164474677623278685a323970593238756558687462413d3d&fich=deputadolegislativo.xml&Inline=true",
                    "deputados_json": "https://app.parlamento.pt/webutils/docs/doc.json?path=6148523063446f764c324679626d56304c334e706447567a4c31684a566b786c5a793944543030764e6a497653586c6653475679595735765a476c6e636d46745953396b5a58423164474677623278685a323970593238756158687462413d3d&fich=deputadolegislativo.json&Inline=true",
                    "grupos_parlamentares_xml": "https://app.parlamento.pt/webutils/docs/doc.xml?path=6148523063446f764c324679626d56304c334e706447567a4c31684a566b786c5a793944543030764e6a497653586c6653475679595735765a476c6e636d46745953396e636e56776231397759584a7359573167626e52686369357862577c3d&fich=grupoparlamentar.xml&Inline=true",
                    "orgaos_xml": "https://app.parlamento.pt/webutils/docs/doc.xml?path=6148523063446f764c324679626d56304c334e706447567a4c31684a566b786c5a793944543030764e6a497653586c6653475679595735765a476c6e636d46745953397663bdbhbm8756567674c777c3d&fich=orgao.xml&Inline=true",
                },
                "Atividades": {
                    "iniciativas_xml": "https://app.parlamento.pt/webutils/docs/doc.xml?path=6148523063446f764c324679626d56304c334e706447567a4c31684a566b786c5a793944543030764e6a497653586c6653475679595735765a476c6e636d46745953397062326c6a6157463061585a68637935346257773d&fich=iniciativas.xml&Inline=true",
                    "votacoes_xml": "https://app.parlamento.pt/webutils/docs/doc.xml?path=6148523063446f764c324679626d56304c334e706447567a4c31684a566b786c5a793944543030764e6a497653586c6653475679595735765a476c6e636d46745953393262335268593246765a584d756547317a&fich=votacoes.xml&Inline=true",
                },
                "Agenda": {
                    "agenda_trabalhos": "https://www.parlamento.pt/ActividadeParlamentar/Paginas/AgendaTrabalhos.aspx",
                }
            }
        }
        
        # Additional endpoints to try
        self.additional_endpoints = [
            # Direct API base paths
            ("deputados_info", "https://app.parlamento.pt/webutils/docs/doc.xml?path=6148523063446f764c324679595842686f6131636b566c4a53556b5a5a576b744e6a497653586c66576e4a7662324a6859574a6b5a5639775a58567a5a6e6c7a62326c7a4c6e687462413d3d&fich=deputado_pessoais.xml"),
            ("partidos_actuais", "https://www.parlamento.pt/DeputadoGP/Paginas/PartidosPoliticosAtuais.aspx"),
            ("biografia_deputados", "https://www.parlamento.pt/DeputadoGP/Paginas/Biografia.aspx?BID="),
            
            # Try different legislature paths
            ("leg_xv", "https://www.parlamento.pt/ActividadeParlamentar/Paginas/DetalheLegislatura.aspx?BID=112590"),
            ("leg_xvi", "https://www.parlamento.pt/ActividadeParlamentar/Paginas/DetalheLegislatura.aspx?BID=112591"),
            ("leg_xvii", "https://www.parlamento.pt/ActividadeParlamentar/Paginas/DetalheLegislatura.aspx?BID=112592"),
        ]
    
    def create_directory_structure(self):
        """Create directory structure for downloads"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create subdirectories
        subdirs = ["XVII_Legislature", "XVI_Legislature", "XV_Legislature", "API_Direct", "Other"]
        for subdir in subdirs:
            os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)
        
        logger.info(f"Created directory structure in: {self.output_dir}")
    
    def download_file(self, url, filename, category="Other"):
        """Download a file from URL"""
        try:
            logger.info(f"Downloading: {filename}")
            logger.info(f"From URL: {url}")
            
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Determine if it's actual data or HTML
            content_type = response.headers.get('Content-Type', '')
            is_data = False
            
            if 'xml' in content_type or 'json' in content_type:
                is_data = True
            elif response.content[:100].strip().startswith((b'<', b'{')):
                is_data = True
            
            if is_data:
                # Save the data file
                filepath = os.path.join(self.output_dir, category, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content) / 1024  # KB
                logger.info(f"[OK] Saved: {filename} ({file_size:.2f} KB)")
                
                return True, filepath, file_size
            else:
                logger.warning(f"URL returned HTML instead of data: {filename}")
                return False, None, 0
                
        except Exception as e:
            logger.error(f"[FAILED] Failed to download {filename}: {e}")
            return False, None, 0
    
    def download_all_direct_urls(self):
        """Download all known direct URLs"""
        logger.info("Starting direct downloads from known endpoints...")
        
        successful_downloads = []
        failed_downloads = []
        
        # Download main XVII legislature data
        for category, urls in self.direct_urls["XVII_Legislature"].items():
            logger.info(f"\n--- Downloading {category} ---")
            
            for name, url in urls.items():
                if isinstance(url, str):
                    filename = f"{name}_{datetime.now().strftime('%Y%m%d')}.{name.split('_')[-1]}"
                    success, filepath, size = self.download_file(url, filename, "XVII_Legislature")
                    
                    if success:
                        successful_downloads.append({
                            'name': name,
                            'filepath': filepath,
                            'size_kb': size,
                            'category': category,
                            'url': url
                        })
                    else:
                        failed_downloads.append({
                            'name': name,
                            'url': url,
                            'category': category
                        })
                    
                    time.sleep(1)  # Be polite
        
        # Try additional endpoints
        logger.info("\n--- Trying additional endpoints ---")
        for name, url in self.additional_endpoints:
            filename = f"{name}_{datetime.now().strftime('%Y%m%d')}.xml"
            success, filepath, size = self.download_file(url, filename, "API_Direct")
            
            if success:
                successful_downloads.append({
                    'name': name,
                    'filepath': filepath,
                    'size_kb': size,
                    'category': 'API_Direct',
                    'url': url
                })
            else:
                failed_downloads.append({
                    'name': name,
                    'url': url,
                    'category': 'API_Direct'
                })
            
            time.sleep(1)
        
        return successful_downloads, failed_downloads
    
    def generate_summary_report(self, successful_downloads, failed_downloads):
        """Generate and save summary report"""
        total_size = sum(d['size_kb'] for d in successful_downloads)
        
        summary = {
            'download_date': datetime.now().isoformat(),
            'statistics': {
                'total_attempted': len(successful_downloads) + len(failed_downloads),
                'successful': len(successful_downloads),
                'failed': len(failed_downloads),
                'total_size_kb': total_size,
                'total_size_mb': total_size / 1024
            },
            'successful_downloads': successful_downloads,
            'failed_downloads': failed_downloads,
            'categories_downloaded': list(set(d['category'] for d in successful_downloads))
        }
        
        # Save summary
        summary_path = os.path.join(self.output_dir, 'download_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("="*80)
        logger.info(f"Total files attempted: {summary['statistics']['total_attempted']}")
        logger.info(f"Successful downloads: {summary['statistics']['successful']}")
        logger.info(f"Failed downloads: {summary['statistics']['failed']}")
        logger.info(f"Total size downloaded: {summary['statistics']['total_size_mb']:.2f} MB")
        logger.info(f"Categories: {', '.join(summary['categories_downloaded'])}")
        logger.info(f"\nSummary saved to: {summary_path}")
        
        if successful_downloads:
            logger.info("\nSuccessfully downloaded files:")
            for dl in successful_downloads:
                logger.info(f"  [OK] {dl['name']} ({dl['size_kb']:.2f} KB)")
        
        if failed_downloads:
            logger.info("\nFailed downloads:")
            for dl in failed_downloads:
                logger.info(f"  [FAILED] {dl['name']} - {dl['url']}")
        
        logger.info("="*80)
        
        return summary

def main():
    """Main entry point"""
    downloader = DirectParliamentDownloader()
    
    try:
        # Create directory structure
        downloader.create_directory_structure()
        
        # Download all files
        logger.info("Starting Portuguese Parliament Direct Data Download")
        logger.info("="*80)
        
        successful, failed = downloader.download_all_direct_urls()
        
        # Generate summary
        summary = downloader.generate_summary_report(successful, failed)
        
        # If we got some data, provide import instructions
        if successful:
            logger.info("\n" + "="*80)
            logger.info("NEXT STEPS:")
            logger.info("="*80)
            logger.info("1. Check the downloaded files in: parliament_data/XVII_Legislature/")
            logger.info("2. The main files for import are:")
            logger.info("   - deputados_xml_*.xml - Deputies information")
            logger.info("   - grupos_parlamentares_xml_*.xml - Parliamentary groups")
            logger.info("   - iniciativas_xml_*.xml - Legislative initiatives")
            logger.info("3. Run the importer with these files to populate your database")
            logger.info("="*80)
        
    except KeyboardInterrupt:
        logger.info("\nDownload interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()