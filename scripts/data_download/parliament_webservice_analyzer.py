#!/usr/bin/env python3
"""
Parliament Web Service Analyzer
Analyze Portuguese Parliament web services to understand their structure and parameters
"""

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import json
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List, Tuple
import re

class ParliamentWebServiceAnalyzer:
    """Analyze Parliament web services structure and capabilities"""
    
    def __init__(self):
        self.base_url = "https://www.parlamento.pt"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Discovered working web services
        self.web_services = {
            'Deputados': 'https://www.parlamento.pt/WebServices/Deputados.asmx',
            'Iniciativas': 'https://www.parlamento.pt/WebServices/Iniciativas.asmx',
            'Intervencoes': 'https://www.parlamento.pt/WebServices/Intervencoes.asmx',
            'Votacoes': 'https://www.parlamento.pt/WebServices/Votacoes.asmx',
            'Agenda': 'https://www.parlamento.pt/WebServices/Agenda.asmx'
        }
    
    def analyze_webservice_wsdl(self, service_name: str, url: str) -> Dict:
        """Analyze a web service's WSDL to understand available methods and parameters"""
        print(f"\nANALYZING WEB SERVICE: {service_name}")
        print("-" * 50)
        
        try:
            # Fetch the web service description page
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for available operations/methods
            operations = []
            
            # Pattern 1: Look for operation links
            operation_links = soup.find_all('a', href=True)
            for link in operation_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                # Skip non-operation links
                if not href or href.startswith('#') or href.startswith('http'):
                    continue
                
                # Web service operations typically don't have file extensions
                if '.' not in href or href.endswith('.asmx'):
                    operations.append({
                        'name': text,
                        'endpoint': href,
                        'full_url': urljoin(url, href)
                    })
            
            # Pattern 2: Look for method descriptions in the HTML
            method_pattern = re.compile(r'\\b(Obter\\w+|Get\\w+|List\\w+)\\b')
            method_matches = method_pattern.findall(response.text)
            for match in method_matches:
                if not any(op['name'] == match for op in operations):
                    operations.append({
                        'name': match,
                        'endpoint': match,
                        'full_url': f"{url}/{match}"
                    })
            
            print(f"Found {len(operations)} operations:")
            for op in operations:
                print(f"  - {op['name']}: {op['full_url']}")
            
            return {
                'service_name': service_name,
                'base_url': url,
                'operations': operations,
                'total_operations': len(operations),
                'raw_content_length': len(response.text)
            }
            
        except Exception as e:
            print(f"Error analyzing {service_name}: {e}")
            return {
                'service_name': service_name, 
                'base_url': url,
                'error': str(e),
                'operations': []
            }
    
    def test_webservice_operation(self, operation_url: str) -> Dict:
        """Test a specific web service operation"""
        print(f"Testing operation: {operation_url}")
        
        try:
            response = self.session.get(operation_url, timeout=30)
            
            result = {
                'url': operation_url,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'content_length': len(response.content),
                'success': response.status_code == 200
            }
            
            if response.status_code == 200:
                # Try to parse as XML
                try:
                    content_text = response.text
                    
                    # Check if it's XML
                    if content_text.strip().startswith('<?xml') or '<' in content_text:
                        root = ET.fromstring(content_text)
                        result['is_xml'] = True
                        result['xml_root'] = root.tag
                        result['xml_children'] = len(list(root))
                        result['preview'] = content_text[:300] + '...'
                        
                        # Extract some sample data structure
                        sample_elements = []
                        for child in list(root)[:3]:  # First 3 children
                            sample_elements.append({
                                'tag': child.tag,
                                'attributes': child.attrib,
                                'has_children': len(list(child)) > 0,
                                'text_content': child.text[:100] if child.text else None
                            })
                        result['sample_elements'] = sample_elements
                    else:
                        result['is_xml'] = False
                        result['preview'] = content_text[:300] + '...'
                        
                except ET.ParseError as e:
                    result['xml_parse_error'] = str(e)
                    result['preview'] = response.text[:300] + '...'
                
                print(f"  SUCCESS: {result['content_length']} bytes")
            else:
                print(f"  FAILED: Status {response.status_code}")
            
            return result
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            return {
                'url': operation_url,
                'error': str(e),
                'success': False
            }
    
    def discover_operation_parameters(self, service_name: str, base_url: str, operations: List[Dict]) -> Dict:
        """Try to discover what parameters each operation accepts"""
        print(f"\nDISCOVERING PARAMETERS FOR {service_name}")
        print("-" * 40)
        
        operation_results = {}
        
        for operation in operations[:3]:  # Test first 3 operations
            op_name = operation['name']
            op_url = operation['full_url']
            
            print(f"\nTesting operation: {op_name}")
            
            # Test the operation without parameters
            base_result = self.test_webservice_operation(op_url)
            
            # Test with common parameters
            parameter_tests = [
                {'leg': 'XVII'},
                {'legislatura': 'XVII'}, 
                {'id': '1'},
                {'numero': '17'}
            ]
            
            param_results = []
            for params in parameter_tests:
                param_url = op_url + '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
                print(f"  Testing with params: {params}")
                param_result = self.test_webservice_operation(param_url)
                param_result['parameters'] = params
                param_results.append(param_result)
                time.sleep(0.5)  # Be nice to server
            
            operation_results[op_name] = {
                'base_result': base_result,
                'parameter_tests': param_results
            }
            
            time.sleep(1)  # Be nice to server
        
        return operation_results
    
    def analyze_all_webservices(self) -> Dict:
        """Analyze all discovered web services"""
        print("PARLIAMENT WEB SERVICES ANALYSIS")
        print("=" * 60)
        
        all_analysis = {}
        
        for service_name, url in self.web_services.items():
            # Analyze the web service structure
            service_analysis = self.analyze_webservice_wsdl(service_name, url)
            
            # Test operations with parameters
            if service_analysis.get('operations'):
                operation_results = self.discover_operation_parameters(
                    service_name, url, service_analysis['operations']
                )
                service_analysis['operation_results'] = operation_results
            
            all_analysis[service_name] = service_analysis
            
            time.sleep(2)  # Be nice to server
        
        return all_analysis
    
    def generate_api_documentation(self, analysis: Dict) -> str:
        """Generate documentation for the discovered APIs"""
        doc = "# Portuguese Parliament Web Services API Documentation\\n\\n"
        doc += "Discovered from official Parliament web services.\\n\\n"
        
        for service_name, service_data in analysis.items():
            if service_data.get('error'):
                continue
                
            doc += f"## {service_name} Service\\n\\n"
            doc += f"**Base URL:** {service_data['base_url']}\\n\\n"
            
            if service_data.get('operations'):
                doc += "### Available Operations:\\n\\n"
                for op in service_data['operations']:
                    doc += f"- **{op['name']}**\\n"
                    doc += f"  - Endpoint: `{op['full_url']}`\\n\\n"
            
            if service_data.get('operation_results'):
                doc += "### Operation Test Results:\\n\\n"
                for op_name, op_data in service_data['operation_results'].items():
                    doc += f"#### {op_name}\\n\\n"
                    
                    base_result = op_data.get('base_result', {})
                    if base_result.get('success'):
                        doc += f"- **Status:** Working ({base_result.get('content_length', 0)} bytes)\\n"
                        if base_result.get('is_xml'):
                            doc += f"- **Format:** XML\\n"
                            doc += f"- **Root Element:** {base_result.get('xml_root', 'Unknown')}\\n"
                            doc += f"- **Child Elements:** {base_result.get('xml_children', 0)}\\n"
                    
                    # Document parameter tests
                    param_tests = op_data.get('parameter_tests', [])
                    working_params = [test for test in param_tests if test.get('success')]
                    if working_params:
                        doc += f"- **Working Parameters:**\\n"
                        for test in working_params:
                            params_str = ', '.join([f"{k}={v}" for k, v in test.get('parameters', {}).items()])
                            doc += f"  - `{params_str}` ({test.get('content_length', 0)} bytes)\\n"
                    
                    doc += "\\n"
            
            doc += "---\\n\\n"
        
        return doc
    
    def save_analysis(self, analysis: Dict, filename: str = "parliament_webservice_analysis.json") -> None:
        """Save analysis results to JSON file"""
        output_file = f"D:\\GoPro\\Building Modern App for Portuguese Government Data Analysis\\{filename}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"SUCCESS: Analysis saved to: {output_file}")
    
    def save_documentation(self, doc: str, filename: str = "parliament_api_documentation.md") -> None:
        """Save API documentation to markdown file"""
        output_file = f"D:\\GoPro\\Building Modern App for Portuguese Government Data Analysis\\{filename}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(doc)
        
        print(f"SUCCESS: Documentation saved to: {output_file}")

def main():
    """Main execution function"""
    analyzer = ParliamentWebServiceAnalyzer()
    
    # Analyze all web services
    analysis = analyzer.analyze_all_webservices()
    
    # Generate documentation
    documentation = analyzer.generate_api_documentation(analysis)
    
    # Save results
    analyzer.save_analysis(analysis)
    analyzer.save_documentation(documentation)
    
    # Print summary
    print("\\n" + "=" * 60)
    print("WEB SERVICE ANALYSIS COMPLETE")
    print("=" * 60)
    
    working_services = sum(1 for service in analysis.values() if not service.get('error'))
    total_operations = sum(service.get('total_operations', 0) for service in analysis.values())
    
    print(f"Working services: {working_services}/{len(analyzer.web_services)}")
    print(f"Total operations discovered: {total_operations}")
    
    print("\\nFiles generated:")
    print("- parliament_webservice_analysis.json (detailed analysis)")
    print("- parliament_api_documentation.md (human-readable docs)")
    
    print("\\nNext steps:")
    print("1. Review the generated documentation")
    print("2. Test specific operations with real parameters") 
    print("3. Build robust data importer using working endpoints")

if __name__ == "__main__":
    main()