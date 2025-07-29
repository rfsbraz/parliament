#!/usr/bin/env python3
"""
Debug downloader to examine what we're actually getting
"""

import requests
from urllib.parse import urljoin
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_download():
    """Download and examine a specific file"""
    
    # The URL from your log (without &Inline=true)
    test_url = "https://app.parlamento.pt/webutils/docs/doc.xml?path=alhFkw5P1irlZhcFkGkTevn0t5vLANz1kcYn5YE673hK8hPuRBvzOXCgjRtWzal0keYrRvZ1ZVcAmqA5R96QFHmvS06kfle3EGHIUBK7neSrYO8UVOVNGzUMKTFxGovN%2fejA6Ca%2bbVil4OO62HRpNBQzEIUAJ1CBCiiFa7m2YeEKcw3rFlLNoMPHVUXZeN3oRvwbJrBz4FLThu%2bHVtD1ubSDKk67CtpjYHdBuy1jFr0GqpECiq0A1TC4wp1SI1xFcYQFN5q3oVRK2veU7f%2fZWqQIx1PC3lAIxNdlnoeICawk65Um0nPT7kvm7Km6IvPCTnVt3iORkAspaTKXjCX7kVLL6pEddkVIHJ2Ctl36VIglq7zNJ4hMLKvAvmKQarwbDgOkJmXTrN7N5%2bPrc%2fb9sA%3d%3d&fich=AgendaParlamentar.xml"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    try:
        logger.info(f"Testing URL: {test_url}")
        
        response = session.get(test_url, timeout=30)
        response.raise_for_status()
        
        content = response.content
        content_type = response.headers.get('Content-Type', '')
        
        logger.info(f"Response size: {len(content)} bytes")
        logger.info(f"Content-Type: {content_type}")
        
        # Show first 500 characters
        logger.info("First 500 characters:")
        logger.info("-" * 50)
        try:
            decoded_content = content[:500].decode('utf-8', errors='ignore')
            logger.info(decoded_content)
        except Exception as e:
            logger.info(f"Decode error: {e}")
            logger.info(content[:500])
        logger.info("-" * 50)
        
        # Show last 200 characters
        logger.info("Last 200 characters:")
        logger.info("-" * 50)
        try:
            decoded_content = content[-200:].decode('utf-8', errors='ignore')
            logger.info(decoded_content)
        except Exception as e:
            logger.info(f"Decode error: {e}")
            logger.info(content[-200:])
        logger.info("-" * 50)
        
        # Check what it starts with
        starts_with_xml = content.strip().startswith(b'<?xml')
        starts_with_bracket = content.strip().startswith(b'<')
        has_html_doctype = b'<!DOCTYPE html' in content[:500]
        has_html_tag = b'<html' in content[:500]
        
        logger.info(f"Starts with <?xml: {starts_with_xml}")
        logger.info(f"Starts with <: {starts_with_bracket}")
        logger.info(f"Has HTML doctype: {has_html_doctype}")
        logger.info(f"Has HTML tag: {has_html_tag}")
        
        # Look for XML content patterns
        has_xml_content = b'<?xml' in content or (b'<' in content and b'>' in content)
        logger.info(f"Has XML-like content: {has_xml_content}")
        
        # Save for manual inspection
        with open('debug_download_sample.xml', 'wb') as f:
            f.write(content)
        logger.info("Content saved to debug_download_sample.xml for manual inspection")
        
        # If it looks like it might be XML wrapped in HTML, try to extract it
        if not starts_with_xml and has_xml_content:
            logger.info("Attempting to extract XML from HTML wrapper...")
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for XML in various places
            pre_tags = soup.find_all('pre')
            logger.info(f"Found {len(pre_tags)} <pre> tags")
            
            for i, pre in enumerate(pre_tags):
                pre_content = pre.get_text()
                if pre_content.strip().startswith('<?xml') or pre_content.strip().startswith('<'):
                    logger.info(f"Pre tag {i+1} contains XML-like content ({len(pre_content)} chars)")
                    logger.info("First 200 chars of pre content:")
                    logger.info(pre_content[:200])
                    
                    # Save extracted content
                    with open(f'debug_extracted_xml_{i+1}.xml', 'w', encoding='utf-8') as f:
                        f.write(pre_content)
                    logger.info(f"Extracted XML saved to debug_extracted_xml_{i+1}.xml")
            
            # Also check other common tags
            for tag_name in ['div', 'span', 'code', 'textarea']:
                tags = soup.find_all(tag_name)
                for i, tag in enumerate(tags):
                    tag_content = tag.get_text()
                    if len(tag_content) > 1000 and (tag_content.strip().startswith('<?xml') or tag_content.strip().startswith('<')):
                        logger.info(f"{tag_name} tag {i+1} contains XML-like content ({len(tag_content)} chars)")
                        with open(f'debug_extracted_from_{tag_name}_{i+1}.xml', 'w', encoding='utf-8') as f:
                            f.write(tag_content)
                        logger.info(f"Extracted XML saved to debug_extracted_from_{tag_name}_{i+1}.xml")
                        break
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    debug_download()