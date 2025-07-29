#!/usr/bin/env python3
"""
Parliamentary Data File Processor with Import Tracking
Processes files one-by-one with complete schema validation and relational data extraction
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
import hashlib
import sqlite3
import requests
import argparse
from datetime import datetime
from pathlib import Path
import PyPDF2
import xmltodict
import traceback
from typing import Dict, List, Any, Optional, Tuple

class ParliamentFileProcessor:
    def __init__(self, db_path: str = "parliament_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with import_status table"""
        with sqlite3.connect(self.db_path) as conn:
            # Read and execute the migration
            migration_path = Path("migrations/create_import_status.sql")
            if migration_path.exists():
                with open(migration_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
                print("+ Import status table initialized")
            else:
                print("- Migration file not found")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA1 hash of file content"""
        sha1_hash = hashlib.sha1()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha1_hash.update(chunk)
            return sha1_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def get_file_info(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive file information"""
        return {
            'file_url': file_data.get('url', ''),
            'file_name': file_data.get('text', ''),
            'file_type': file_data.get('type', 'Unknown'),
            'category': file_data.get('category', ''),
            'legislatura': file_data.get('legislatura', ''),
            'sub_series': file_data.get('sub_series', ''),
            'session': file_data.get('session', ''),
            'number': file_data.get('number', '')
        }
    
    def is_file_processed(self, file_url: str, file_hash: str) -> bool:
        """Check if file is already processed with same hash"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status FROM import_status 
                WHERE file_url = ? AND file_hash = ? AND status = 'completed'
            """, (file_url, file_hash))
            return cursor.fetchone() is not None
    
    def update_import_status(self, file_url: str, **kwargs):
        """Update import status record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            if set_clauses:
                query = f"UPDATE import_status SET {', '.join(set_clauses)} WHERE file_url = ?"
                values.append(file_url)
                cursor.execute(query, values)
                conn.commit()
    
    def insert_import_record(self, file_info: Dict[str, Any]):
        """Insert new import status record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO import_status (
                    file_url, file_name, file_type, category, legislatura,
                    sub_series, session, number, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                file_info['file_url'], file_info['file_name'], file_info['file_type'],
                file_info['category'], file_info['legislatura'], file_info['sub_series'],
                file_info['session'], file_info['number']
            ))
            conn.commit()
    
    def download_file(self, url: str, local_path: str) -> bool:
        """Download file from URL to local path"""
        try:
            print(f"    Downloading: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"    Download failed: {e}")
            return False
    
    def read_pdf_content(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"    Error reading PDF: {e}")
            return ""
    
    def analyze_data_structure(self, file_path: str, file_type: str) -> Tuple[Dict[str, Any], List[str]]:
        """Analyze file structure and identify schema issues"""
        schema_issues = []
        structure = {}
        
        try:
            if file_type == 'JSON':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                structure = self.analyze_json_structure(data)
            
            elif file_type == 'XML':
                tree = ET.parse(file_path)
                root = tree.getroot()
                structure = self.analyze_xml_structure(root)
            
            elif file_type == 'XSD':
                # XSD files are for learning schema structure, not for data import
                structure = self.analyze_xsd_schema(file_path)
                schema_issues.append("XSD is schema documentation only - skipping import")
            
            elif file_type == 'PDF':
                # PDFs are for documentation/learning only, not for data import
                text_content = self.read_pdf_content(file_path)
                structure = {
                    'type': 'documentation',
                    'pdf_content_preview': text_content[:1000] + "..." if len(text_content) > 1000 else text_content,
                    'note': 'PDF is for documentation purposes only - not imported'
                }
                schema_issues.append("PDF is documentation only - skipping import")
            
            else:
                schema_issues.append(f"Unsupported file type: {file_type}")
        
        except Exception as e:
            schema_issues.append(f"Error analyzing structure: {str(e)}")
        
        return structure, schema_issues
    
    def analyze_json_structure(self, data: Any, path: str = "root") -> Dict[str, Any]:
        """Recursively analyze JSON structure"""
        if isinstance(data, dict):
            structure = {"type": "object", "keys": {}}
            for key, value in data.items():
                structure["keys"][key] = self.analyze_json_structure(value, f"{path}.{key}")
            return structure
        
        elif isinstance(data, list):
            if data:
                return {"type": "array", "length": len(data), "item_structure": self.analyze_json_structure(data[0], f"{path}[0]")}
            else:
                return {"type": "array", "length": 0}
        
        else:
            return {"type": type(data).__name__, "sample_value": str(data)[:100]}
    
    def analyze_xml_structure(self, element: ET.Element, path: str = "root") -> Dict[str, Any]:
        """Recursively analyze XML structure"""
        structure = {
            "tag": element.tag,
            "attributes": dict(element.attrib) if element.attrib else {},
            "text": element.text.strip() if element.text and element.text.strip() else None,
            "children": {}
        }
        
        # Analyze child elements
        child_tags = {}
        for child in element:
            tag = child.tag
            if tag not in child_tags:
                child_tags[tag] = {"count": 0, "structure": None}
            child_tags[tag]["count"] += 1
            if child_tags[tag]["structure"] is None:
                child_tags[tag]["structure"] = self.analyze_xml_structure(child, f"{path}.{tag}")
        
        structure["children"] = child_tags
        return structure
    
    def analyze_xsd_schema(self, xsd_path: str) -> Dict[str, Any]:
        """Analyze XSD schema file to extract database structure information"""
        try:
            tree = ET.parse(xsd_path)
            root = tree.getroot()
            
            # Extract namespace
            ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}
            
            schema_info = {
                'type': 'schema_documentation',
                'target_namespace': root.get('targetNamespace'),
                'complex_types': {},
                'elements': {},
                'database_fields': []
            }
            
            # Extract complex types (these define our data structures)
            for complex_type in root.findall('.//xs:complexType', ns):
                type_name = complex_type.get('name')
                if type_name:
                    fields = []
                    
                    # Extract sequence elements (fields)
                    for element in complex_type.findall('.//xs:element', ns):
                        field_name = element.get('name')
                        field_type = element.get('type', '').replace('xs:', '')
                        min_occurs = element.get('minOccurs', '1')
                        max_occurs = element.get('maxOccurs', '1')
                        nillable = element.get('nillable', 'false')
                        
                        if field_name:
                            field_info = {
                                'name': field_name,
                                'type': field_type,
                                'required': min_occurs != '0',
                                'nullable': nillable == 'true',
                                'min_occurs': min_occurs,
                                'max_occurs': max_occurs
                            }
                            fields.append(field_info)
                            
                            # Also add to database fields for easy reference
                            schema_info['database_fields'].append({
                                'table': type_name,
                                'column': field_name,
                                'data_type': self.map_xsd_type_to_sql(field_type),
                                'nullable': nillable == 'true',
                                'description': f'Field from {type_name} complex type'
                            })
                    
                    schema_info['complex_types'][type_name] = {
                        'fields': fields,
                        'field_count': len(fields)
                    }
            
            # Extract global elements
            for element in root.findall('./xs:element', ns):
                elem_name = element.get('name')
                elem_type = element.get('type')
                if elem_name:
                    schema_info['elements'][elem_name] = {
                        'type': elem_type,
                        'nillable': element.get('nillable', 'false')
                    }
            
            return schema_info
            
        except Exception as e:
            return {
                'type': 'schema_documentation',
                'error': f'Failed to parse XSD: {str(e)}',
                'note': 'XSD file could not be analyzed'
            }
    
    def map_xsd_type_to_sql(self, xsd_type: str) -> str:
        """Map XSD data types to SQL data types"""
        type_mapping = {
            'string': 'TEXT',
            'int': 'INTEGER',
            'boolean': 'BOOLEAN',
            'dateTime': 'DATETIME',
            'date': 'DATE',
            'time': 'TIME',
            'decimal': 'DECIMAL',
            'float': 'REAL',
            'double': 'REAL'
        }
        return type_mapping.get(xsd_type, 'TEXT')
    
    def validate_against_schema(self, structure: Dict[str, Any], file_type: str, category: str) -> List[str]:
        """Validate data structure against expected database schema"""
        issues = []
        
        # This is where we'll implement schema validation rules
        # For now, return basic validation
        if not structure:
            issues.append("Empty or invalid data structure")
        
        # Add category-specific validation rules here
        if category.lower() in ['iniciativas', 'initiatives']:
            issues.extend(self.validate_initiatives_schema(structure, file_type))
        elif category.lower() in ['deputados', 'deputies']:
            issues.extend(self.validate_deputies_schema(structure, file_type))
        elif category.lower() in ['intervencoes', 'interventions']:
            issues.extend(self.validate_interventions_schema(structure, file_type))
        
        return issues
    
    def validate_initiatives_schema(self, structure: Dict[str, Any], file_type: str) -> List[str]:
        """Validate initiatives data structure"""
        issues = []
        # Add specific validation rules for initiatives
        return issues
    
    def validate_deputies_schema(self, structure: Dict[str, Any], file_type: str) -> List[str]:
        """Validate deputies data structure"""
        issues = []
        # Add specific validation rules for deputies
        return issues
    
    def validate_interventions_schema(self, structure: Dict[str, Any], file_type: str) -> List[str]:
        """Validate interventions data structure"""
        issues = []
        # Add specific validation rules for interventions
        return issues
    
    def choose_optimal_format(self, files_group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Choose the optimal file format from a group (prefer JSON over XML)"""
        json_files = [f for f in files_group if f.get('type') == 'JSON']
        xml_files = [f for f in files_group if f.get('type') == 'XML']
        
        # Prefer JSON for easier processing
        if json_files:
            return json_files[0]
        elif xml_files:
            return xml_files[0]
        else:
            return files_group[0] if files_group else None
    
    def extract_relational_data(self, data: Any, file_type: str, category: str = '') -> Dict[str, List[Dict]]:
        """Extract entities that should be stored relationally (deputies, parties, etc.)"""
        entities = {
            'agenda_parlamentar': [],
            'parliament_groups': [],
            'agenda_anexos': [],
            'deputies': [],
            'parties': [],
            'initiatives': [],
            'interventions': [],
            'activities': [],
            'commissions': [],
            'deputy_activities': [],
            'biographical_records': [],
            'qualifications': [],
            'positions': [],
            'decorations': []
        }
        
        try:
            if category == 'Agenda Parlamentar':
                entities.update(self.extract_agenda_parlamentar_data(data))
            elif category == 'Atividade dos Deputados':
                entities.update(self.extract_atividade_deputados_data(data))
            elif category == 'Composição de Órgãos':
                entities.update(self.extract_composicao_orgaos_data(data))
            elif category == 'Registo Biográfico':
                entities.update(self.extract_registo_biografico_data(data))
            elif category == 'Registo de Interesses' or 'Registo Interesses' in category:
                entities.update(self.extract_registo_interesses_data(data))
            elif category == 'Atividades':
                entities.update(self.extract_atividades_data(data))
            else:
                print(f"    Warning: No specific extractor for category '{category}' - using basic extraction")
            
        except Exception as e:
            print(f"    Error extracting relational data: {e}")
        
        return entities
    
    def extract_agenda_parlamentar_data(self, data: Any) -> Dict[str, List[Dict]]:
        """Extract AgendaParlamentar data into relational entities"""
        entities = {
            'agenda_parlamentar': [],
            'parliament_groups': [],
            'agenda_anexos': []
        }
        
        # Handle both XML dict structure and direct parsing
        if isinstance(data, dict):
            # Check if it's the root element from xmltodict
            if 'ArrayOfAgendaParlamentar' in data:
                agenda_items = data['ArrayOfAgendaParlamentar'].get('AgendaParlamentar', [])
            elif 'AgendaParlamentar' in data:
                agenda_items = data['AgendaParlamentar']
            else:
                agenda_items = [data] if 'Id' in data else []
        else:
            # If data is not a dict, try to parse it as XML directly
            try:
                if hasattr(data, 'tag'):  # It's an XML element
                    # Convert XML element to dict structure
                    agenda_items = self.xml_element_to_dict_list(data)
                else:
                    agenda_items = []
            except:
                agenda_items = []
        
        # Ensure it's a list
        if not isinstance(agenda_items, list):
            agenda_items = [agenda_items]
        
        parliament_groups_seen = set()
        
        for item in agenda_items:
            if not isinstance(item, dict):
                continue
            
            # Extract parliament group if present
            if 'ParlamentGroup' in item and item['ParlamentGroup']:
                group_id = str(item['ParlamentGroup'])
                if group_id != '0' and group_id not in parliament_groups_seen:
                    parliament_groups_seen.add(group_id)
                    
                    # Extract group name from title
                    group_name = self.extract_group_name_from_title(item.get('Title', ''))
                    
                    entities['parliament_groups'].append({
                        'source_id': group_id,
                        'name': group_name,
                        'short_name': self.extract_short_group_name(group_name),
                        'legislatura': item.get('LegDes', ''),
                        'first_seen_date': item.get('EventStartDate', ''),
                        'import_source': 'agenda_parlamentar'
                    })
            
            # Extract main agenda item with safe value extraction
            agenda_item = {
                'source_id': self.safe_get_value(item.get('Id')),
                'parliament_group_id': self.safe_get_value(item.get('ParlamentGroup')),
                'section_id': self.safe_get_value(item.get('SectionId')),
                'theme_id': self.safe_get_value(item.get('ThemeId')),
                'title': self.safe_get_value(item.get('Title')),
                'subtitle': self.safe_get_value(item.get('Subtitle')),
                'section': self.safe_get_value(item.get('Section')),
                'theme': self.safe_get_value(item.get('Theme')),
                'event_start_date': self.safe_get_value(item.get('EventStartDate')),
                'event_start_time': self.safe_get_value(item.get('EventStartTime')),
                'event_end_date': self.safe_get_value(item.get('EventEndDate')),
                'event_end_time': self.safe_get_value(item.get('EventEndTime')),
                'all_day_event': self.safe_get_value(item.get('AllDayEvent'), False),
                'internet_text': self.safe_get_value(item.get('InternetText')),
                'local': self.safe_get_value(item.get('Local')),
                'link': self.safe_get_value(item.get('Link')),
                'leg_des': self.safe_get_value(item.get('LegDes')),
                'org_des': self.safe_get_value(item.get('OrgDes')),
                'reu_numero': self.safe_get_value(item.get('ReuNumero')),
                'sel_numero': self.safe_get_value(item.get('SelNumero')),
                'order_value': self.safe_get_value(item.get('OrderValue')),
                'post_plenary': self.safe_get_value(item.get('PostPlenary'), False),
                'import_source': 'agenda_parlamentar_xml'
            }
            entities['agenda_parlamentar'].append(agenda_item)
            
            # Extract anexos if present
            for anexo_type in ['AnexosComissaoPermanente', 'AnexosPlenario']:
                anexos = item.get(anexo_type)
                if anexos and isinstance(anexos, dict):
                    anexo_items = anexos.get('AnexoEventos', [])
                    if not isinstance(anexo_items, list):
                        anexo_items = [anexo_items]
                    
                    for anexo in anexo_items:
                        entities['agenda_anexos'].append({
                            'agenda_source_id': item.get('Id'),
                            'anexo_type': 'comissao_permanente' if 'Comissao' in anexo_type else 'plenario',
                            'source_id': anexo.get('idField'),
                            'tipo_documento': anexo.get('tipoDocumentoField'),
                            'titulo': anexo.get('tituloField'),
                            'url': anexo.get('uRLField')
                        })
        
        return entities
    
    def extract_group_name_from_title(self, title: str) -> str:
        """Extract parliamentary group name from event title"""
        if not title:
            return ''
        
        # Common patterns: "Audiências do Grupo Parlamentar do PS"
        if 'Grupo Parlamentar do ' in title:
            return title.split('Grupo Parlamentar do ')[-1].split(' ')[0]
        elif 'Grupo Parlamentar da ' in title:
            return title.split('Grupo Parlamentar da ')[-1].split(' ')[0]
        
        return ''
    
    def extract_short_group_name(self, full_name: str) -> str:
        """Extract short name from full parliamentary group name"""
        # Common abbreviations
        abbreviations = {
            'Partido Socialista': 'PS',
            'Partido Social Democrata': 'PSD', 
            'Chega': 'CH',
            'Iniciativa Liberal': 'IL',
            'Partido Comunista Português': 'PCP',
            'Centro Democrático Social': 'CDS-PP',
            'Bloco de Esquerda': 'BE',
            'Pessoas-Animais-Natureza': 'PAN',
            'Livre': 'L'
        }
        
        for full, short in abbreviations.items():
            if full_name and full.lower() in full_name.lower():
                return short
        
        return full_name[:10] if full_name else ''
    
    def extract_atividade_deputados_data(self, data: Any) -> Dict[str, List[Dict]]:
        """Extract AtividadeDeputado data into relational entities"""
        entities = {
            'deputies': [],
            'initiatives': [],
            'interventions': [],
            'deputy_activities': [],
            'commissions': [],
            'deputy_commissions': []
        }
        
        # Handle XML structure: ArrayOfAtividadeDeputado -> AtividadeDeputado (list)
        if isinstance(data, dict):
            if 'ArrayOfAtividadeDeputado' in data:
                atividade_items = data['ArrayOfAtividadeDeputado'].get('AtividadeDeputado', [])
            elif 'AtividadeDeputado' in data:
                atividade_items = data['AtividadeDeputado'] 
            else:
                atividade_items = [data] if 'Deputado' in data else []
        else:
            atividade_items = []
        
        if not isinstance(atividade_items, list):
            atividade_items = [atividade_items]
        
        for item in atividade_items:
            if not isinstance(item, dict):
                continue
            
            # Extract deputy information
            deputado = item.get('Deputado', {})
            if isinstance(deputado, dict):
                deputy_id = self.safe_get_value(deputado.get('DepId'))
                if deputy_id:
                    entities['deputies'].append({
                        'source_id': deputy_id,
                        'cadastro_id': self.safe_get_value(deputado.get('DepCadId')),
                        'nome_parlamentar': self.safe_get_value(deputado.get('DepNomeParlamentar')),
                        'nome_completo': self.safe_get_value(deputado.get('DepNomeCompleto')),
                        'legislatura': self.safe_get_value(deputado.get('LegDes')),
                        'circulo_id': self.safe_get_value(deputado.get('DepCPId')),
                        'circulo_descricao': self.safe_get_value(deputado.get('DepCPDes')),
                        'import_source': 'atividade_deputados'
                    })
            
            # Extract activities list
            atividade_list = item.get('AtividadeDeputadoList', {}).get('ActividadeOut', {})
            if isinstance(atividade_list, dict):
                
                # Extract initiatives
                iniciativas = atividade_list.get('Ini', {}).get('IniciativasOut', [])
                if not isinstance(iniciativas, list):
                    iniciativas = [iniciativas] if iniciativas else []
                
                for ini in iniciativas:
                    if isinstance(ini, dict):
                        entities['initiatives'].append({
                            'source_id': self.safe_get_value(ini.get('IniId')),
                            'numero': self.safe_get_value(ini.get('IniNr')),
                            'tipo': self.safe_get_value(ini.get('IniTp')),
                            'tipo_descricao': self.safe_get_value(ini.get('IniTpdesc')),
                            'legislatura': self.safe_get_value(ini.get('IniSelLg')),
                            'sessao': self.safe_get_value(ini.get('IniSelNr')),
                            'titulo': self.safe_get_value(ini.get('IniTi')),
                            'deputy_id': deputy_id,
                            'import_source': 'atividade_deputados'
                        })
                
                # Extract interventions
                intervencoes = atividade_list.get('Intev', {}).get('IntervencoesOut', [])
                if not isinstance(intervencoes, list):
                    intervencoes = [intervencoes] if intervencoes else []
                
                for intv in intervencoes:
                    if isinstance(intv, dict):
                        entities['interventions'].append({
                            'source_id': self.safe_get_value(intv.get('IntId')),
                            'titulo': self.safe_get_value(intv.get('IntTe')),
                            'assunto': self.safe_get_value(intv.get('IntSu')),
                            'data_publicacao': self.safe_get_value(intv.get('PubDtreu')),
                            'tipo_publicacao': self.safe_get_value(intv.get('PubTp')),
                            'legislatura': self.safe_get_value(intv.get('PubLg')),
                            'sessao': self.safe_get_value(intv.get('PubSl')),
                            'numero': self.safe_get_value(intv.get('PubNr')),
                            'tipo_intervencao': self.safe_get_value(intv.get('TinDs')),
                            'paginas_dar': self.safe_get_value(intv.get('PubDar')),
                            'deputy_id': deputy_id,
                            'import_source': 'atividade_deputados'
                        })
                
                # Extract commissions
                comissoes = atividade_list.get('Cms', {}).get('ComissoesOut', [])
                if not isinstance(comissoes, list):
                    comissoes = [comissoes] if comissoes else []
                
                for cms in comissoes:
                    if isinstance(cms, dict):
                        commission_id = self.safe_get_value(cms.get('CmsCd'))
                        entities['commissions'].append({
                            'source_id': commission_id,
                            'nome': self.safe_get_value(cms.get('CmsNo')),
                            'legislatura': self.safe_get_value(cms.get('CmsLg')),
                            'import_source': 'atividade_deputados'
                        })
                        
                        # Link deputy to commission
                        entities['deputy_commissions'].append({
                            'deputy_id': deputy_id,
                            'commission_id': commission_id,
                            'situacao': self.safe_get_value(cms.get('CmsSituacao')),
                            'legislatura': self.safe_get_value(cms.get('CmsLg')),
                            'import_source': 'atividade_deputados'
                        })
        
        return entities
    
    def extract_composicao_orgaos_data(self, data: Any) -> Dict[str, List[Dict]]:
        """Extract Composição de Órgãos data"""
        # Placeholder for organ composition data
        return {'organs': [], 'organ_members': []}
    
    def extract_registo_biografico_data(self, data: Any) -> Dict[str, List[Dict]]:
        """Extract Registo Biográfico data into relational entities"""
        entities = {
            'biographical_records': [],
            'qualifications': [],
            'positions': [],
            'decorations': []
        }
        
        # Handle XML structure: ArrayOfDadosRegistoBiografico -> DadosRegistoBiografico (list)
        if isinstance(data, dict):
            if 'ArrayOfDadosRegistoBiografico' in data:
                bio_items = data['ArrayOfDadosRegistoBiografico'].get('DadosRegistoBiografico', [])
            elif 'DadosRegistoBiografico' in data:
                bio_items = data['DadosRegistoBiografico']
            else:
                bio_items = [data] if 'CadId' in data else []
        else:
            bio_items = []
        
        if not isinstance(bio_items, list):
            bio_items = [bio_items]
        
        for item in bio_items:
            if not isinstance(item, dict):
                continue
            
            cadastro_id_raw = self.safe_get_value(item.get('CadId'))
            if not cadastro_id_raw:
                continue
            
            # Convert cadastro_id to integer (remove decimal .0 if present)
            try:
                cadastro_id = int(float(cadastro_id_raw))
            except (ValueError, TypeError):
                print(f"    Warning: Invalid cadastro_id format: {cadastro_id_raw}")
                continue
                
            # Extract main biographical record
            entities['biographical_records'].append({
                'cadastro_id': cadastro_id,
                'nome_completo': self.safe_get_value(item.get('CadNomeCompleto')),
                'data_nascimento': self.safe_get_value(item.get('CadDtNascimento')),
                'sexo': self.safe_get_value(item.get('CadSexo')),
                'profissao': self.safe_get_value(item.get('CadProfissao')),
                'import_source': 'registo_biografico'
            })
            
            # Extract qualifications
            habilitacoes = item.get('CadHabilitacoes', {}).get('DadosHabilitacoes', [])
            if not isinstance(habilitacoes, list):
                habilitacoes = [habilitacoes] if habilitacoes else []
            
            for hab in habilitacoes:
                if isinstance(hab, dict):
                    entities['qualifications'].append({
                        'source_id': self.safe_get_value(hab.get('HabId')),
                        'cadastro_id': cadastro_id,
                        'descricao': self.safe_get_value(hab.get('HabDes')),
                        'tipo_id': self.safe_get_value(hab.get('HabTipoId')),
                        'estado': self.safe_get_value(hab.get('HabEstado')),
                        'import_source': 'registo_biografico'
                    })
            
            # Extract positions/functions
            cargos = item.get('CadCargosFuncoes', {}).get('DadosCargosFuncoes', [])
            if not isinstance(cargos, list):
                cargos = [cargos] if cargos else []
            
            for cargo in cargos:
                if isinstance(cargo, dict):
                    entities['positions'].append({
                        'source_id': self.safe_get_value(cargo.get('FunId')),
                        'cadastro_id': cadastro_id,
                        'descricao': self.safe_get_value(cargo.get('FunDes')),
                        'ordem': self.safe_get_value(cargo.get('FunOrdem')),
                        'antiga': self.safe_get_value(cargo.get('FunAntiga')),
                        'import_source': 'registo_biografico'
                    })
            
            # Extract decorations/honors
            condecoracoes = item.get('CadCondecoracoes', {}).get('DadosCondecoracoes', [])
            if not isinstance(condecoracoes, list):
                condecoracoes = [condecoracoes] if condecoracoes else []
            
            for cond in condecoracoes:
                if isinstance(cond, dict):
                    entities['decorations'].append({
                        'source_id': self.safe_get_value(cond.get('CodId')),
                        'cadastro_id': cadastro_id,
                        'descricao': self.safe_get_value(cond.get('CodDes')),
                        'ordem': self.safe_get_value(cond.get('CodOrdem')),
                        'import_source': 'registo_biografico'
                    })
        
        return entities
    
    def extract_registo_interesses_data(self, data: Any) -> Dict[str, List[Dict]]:
        """Extract Registo Interesses (conflicts of interest) data into relational entities"""
        entities = {
            'conflicts_of_interest': []
        }
        
        # Handle XML structure: ArrayOfRegistoInteresses -> RegistoInteresses (list)
        if isinstance(data, dict):
            if 'ArrayOfRegistoInteresses' in data:
                interest_items = data['ArrayOfRegistoInteresses'].get('RegistoInteresses', [])
            elif 'RegistoInteresses' in data:
                interest_items = data['RegistoInteresses']
            else:
                interest_items = [data] if 'RecordId' in data else []
        else:
            interest_items = []
        
        if not isinstance(interest_items, list):
            interest_items = [interest_items]
        
        for item in interest_items:
            if not isinstance(item, dict):
                continue
            
            # Extract the RegistoInteressesV3 data if it exists
            interest_data = item.get('RegistoInteressesV3', item)
            if not isinstance(interest_data, dict):
                continue
            
            record_id = self.safe_get_value(interest_data.get('RecordId'))
            if not record_id:
                continue
                
            # Extract conflicts of interest record
            entities['conflicts_of_interest'].append({
                'record_id': record_id,
                'full_name': self.safe_get_value(interest_data.get('FullName')),
                'marital_status': self.safe_get_value(interest_data.get('MaritalStatus')),
                'spouse_name': self.safe_get_value(interest_data.get('SpouseName')),
                'matrimonial_regime': self.safe_get_value(interest_data.get('MatrimonialRegime')),
                'exclusivity': self.safe_get_value(interest_data.get('Exclusivity')),
                'dgf_number': self.safe_get_value(interest_data.get('DGFNumber')),
                'import_source': 'registo_interesses'
            })
        
        return entities
    
    def extract_atividades_data(self, data: Any) -> Dict[str, List[Dict]]:
        """Extract Atividades (parliamentary activities) data into relational entities"""
        entities = {
            'activities': [],
            'activity_votes': [],
            'activity_participants': [],
            'activity_publications': []
        }
        
        # Handle XML structure: Atividades -> AtividadesGerais -> Atividades -> Atividade (list)
        if isinstance(data, dict):
            if 'Atividades' in data:
                activities_container = data['Atividades']
                if 'AtividadesGerais' in activities_container:
                    gerais = activities_container['AtividadesGerais']
                    if 'Atividades' in gerais and isinstance(gerais['Atividades'], dict):
                        activities_list = gerais['Atividades'].get('Atividade', [])
                    else:
                        activities_list = []
                elif 'Atividade' in activities_container:
                    activities_list = activities_container['Atividade']
                else:
                    activities_list = []
            else:
                activities_list = [data] if 'Tipo' in data else []
        else:
            activities_list = []

        if not isinstance(activities_list, list):
            activities_list = [activities_list]

        for activity in activities_list:
            if not isinstance(activity, dict):
                continue

            activity_id = f"{activity.get('Legislatura', '')}_{activity.get('Sessao', '')}_{activity.get('Tipo', '')}_{activity.get('Numero', '')}"
            
            # Extract main activity record
            entities['activities'].append({
                'activity_id': activity_id,
                'tipo': self.safe_get_value(activity.get('Tipo')),
                'desc_tipo': self.safe_get_value(activity.get('DescTipo')),
                'assunto': self.safe_get_value(activity.get('Assunto')),
                'legislatura': self.safe_get_value(activity.get('Legislatura')),
                'sessao': self.safe_get_value(activity.get('Sessao')),
                'numero': self.safe_get_value(activity.get('Numero')),
                'data_entrada': self.safe_get_value(activity.get('DataEntrada')),
                'data_agendamento_debate': self.safe_get_value(activity.get('DataAgendamentoDebate')),
                'orgao_exterior': self.safe_get_value(activity.get('OrgaoExterior')),
                'observacoes': self.safe_get_value(activity.get('Observacoes')),
                'tipo_autor': self.safe_get_value(activity.get('TipoAutor')),
                'import_source': 'atividades'
            })

            # Extract voting data if present
            votacao_debate = activity.get('VotacaoDebate')
            if votacao_debate and isinstance(votacao_debate, dict):
                vote_data = votacao_debate.get('pt_gov_ar_objectos_VotacaoOut', votacao_debate)
                if isinstance(vote_data, dict):
                    entities['activity_votes'].append({
                        'activity_id': activity_id,
                        'vote_id': self.safe_get_value(vote_data.get('id')),
                        'resultado': self.safe_get_value(vote_data.get('resultado')),
                        'reuniao': self.safe_get_value(vote_data.get('reuniao')),
                        'unanime': self.safe_get_value(vote_data.get('unanime')),
                        'data_votacao': self.safe_get_value(vote_data.get('data')),
                        'descricao': self.safe_get_value(vote_data.get('descricao')),
                        'import_source': 'atividades'
                    })

            # Extract participants (authors, elected officials, guests)
            # Authors from parliamentary groups
            autores_gp = activity.get('AutoresGP')
            if autores_gp:
                # AutoresGP can be a list of strings or a dict with 'string' key
                if isinstance(autores_gp, list):
                    authors_list = autores_gp
                elif isinstance(autores_gp, dict) and 'string' in autores_gp:
                    authors_list = autores_gp['string']
                    if not isinstance(authors_list, list):
                        authors_list = [authors_list]
                else:
                    authors_list = []
                
                for autor in authors_list:
                    if isinstance(autor, str):
                        entities['activity_participants'].append({
                            'activity_id': activity_id,
                            'nome': autor,
                            'tipo_participacao': 'autor_gp',
                            'import_source': 'atividades'
                        })

            # Elected officials
            eleitos = activity.get('Eleitos')
            if eleitos:
                # Handle the nested structure
                if isinstance(eleitos, dict) and 'pt_gov_ar_objectos_EleitosOut' in eleitos:
                    eleitos_list = eleitos['pt_gov_ar_objectos_EleitosOut']
                    if not isinstance(eleitos_list, list):
                        eleitos_list = [eleitos_list]
                elif isinstance(eleitos, list):
                    eleitos_list = eleitos
                else:
                    eleitos_list = []
                
                for eleito_data in eleitos_list:
                    if isinstance(eleito_data, dict):
                        entities['activity_participants'].append({
                            'activity_id': activity_id,
                            'nome': self.safe_get_value(eleito_data.get('nome')),
                            'cargo': self.safe_get_value(eleito_data.get('cargo')),
                            'tipo_participacao': 'eleito',
                            'import_source': 'atividades'
                        })

            # Guests/invitees
            convidados = activity.get('Convidados')
            if convidados:
                # Handle the nested structure
                if isinstance(convidados, dict) and 'pt_gov_ar_objectos_ConvidadosOut' in convidados:
                    convidados_list = convidados['pt_gov_ar_objectos_ConvidadosOut']
                    if not isinstance(convidados_list, list):
                        convidados_list = [convidados_list]
                elif isinstance(convidados, list):
                    convidados_list = convidados
                else:
                    convidados_list = []
                
                for convidado_data in convidados_list:
                    if isinstance(convidado_data, dict):
                        entities['activity_participants'].append({
                            'activity_id': activity_id,
                            'nome': self.safe_get_value(convidado_data.get('nome')),
                            'cargo': self.safe_get_value(convidado_data.get('cargo')),
                            'pais': self.safe_get_value(convidado_data.get('pais')),
                            'honra': self.safe_get_value(convidado_data.get('honra')),
                            'tipo_participacao': 'convidado',
                            'import_source': 'atividades'
                        })

            # Extract publications
            publicacoes = []
            if 'Publicacao' in activity:
                pub_data = activity['Publicacao']
                if isinstance(pub_data, list):
                    publicacoes.extend(pub_data)
                elif isinstance(pub_data, dict):
                    publicacoes.append(pub_data)

            if 'PublicacaoDebate' in activity:
                pub_data = activity['PublicacaoDebate']
                if isinstance(pub_data, list):
                    publicacoes.extend(pub_data)
                elif isinstance(pub_data, dict):
                    publicacoes.append(pub_data)

            # Process publications
            for pub in publicacoes:
                if isinstance(pub, dict):
                    pub_detail = pub.get('pt_gov_ar_objectos_PublicacoesOut', pub)
                    if isinstance(pub_detail, dict):
                        entities['activity_publications'].append({
                            'activity_id': activity_id,
                            'pub_nr': self.safe_get_value(pub_detail.get('pubNr')),
                            'pub_tipo': self.safe_get_value(pub_detail.get('pubTipo')),
                            'pub_data': self.safe_get_value(pub_detail.get('pubdt')),
                            'url_diario': self.safe_get_value(pub_detail.get('URLDiario')),
                            'legislatura': self.safe_get_value(pub_detail.get('pubLeg')),
                            'import_source': 'atividades'
                        })

        return entities
    
    def safe_get_value(self, data: Any, default: Any = None) -> Any:
        """Safely extract value from data, handling various types"""
        if data is None:
            return default
        if isinstance(data, dict) and len(data) == 0:
            return default
        if isinstance(data, str):
            return data.strip() if data.strip() else default
        if isinstance(data, (int, bool)):
            return data
        return str(data) if data else default
    
    def import_entities_to_database(self, entities: Dict[str, List[Dict]], file_info: Dict[str, Any]) -> int:
        """Import extracted entities into database tables"""
        total_records = 0
        
        try:
            # Create tables if they don't exist
            self.create_agenda_tables()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Import parliament groups first (referenced by agenda items)
                for group in entities.get('parliament_groups', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO parliament_groups 
                        (source_id, name, short_name, legislatura, first_seen_date, import_source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        group['source_id'], group['name'], group['short_name'],
                        group['legislatura'], group['first_seen_date'], group['import_source']
                    ))
                    total_records += 1
                
                # Import agenda items
                for agenda in entities.get('agenda_parlamentar', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO agenda_parlamentar 
                        (source_id, parliament_group_id, section_id, theme_id, title, subtitle, 
                         section, theme, event_start_date, event_start_time, event_end_date, 
                         event_end_time, all_day_event, internet_text, local, link, leg_des, 
                         org_des, reu_numero, sel_numero, order_value, post_plenary, import_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        agenda['source_id'], agenda['parliament_group_id'], agenda['section_id'],
                        agenda['theme_id'], agenda['title'], agenda['subtitle'], agenda['section'],
                        agenda['theme'], agenda['event_start_date'], agenda['event_start_time'],
                        agenda['event_end_date'], agenda['event_end_time'], agenda['all_day_event'],
                        agenda['internet_text'], agenda['local'], agenda['link'], agenda['leg_des'],
                        agenda['org_des'], agenda['reu_numero'], agenda['sel_numero'],
                        agenda['order_value'], agenda['post_plenary'], agenda['import_source']
                    ))
                    agenda_id = cursor.lastrowid
                    total_records += 1
                    
                    # Import anexos for this agenda item
                    for anexo in entities.get('agenda_anexos', []):
                        if anexo['agenda_source_id'] == agenda['source_id']:
                            cursor.execute("""
                                INSERT INTO agenda_anexos 
                                (agenda_id, anexo_type, source_id, tipo_documento, titulo, url)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                agenda_id, anexo['anexo_type'], anexo['source_id'],
                                anexo['tipo_documento'], anexo['titulo'], anexo['url']
                            ))
                            total_records += 1
                
                # Import deputies
                for deputy in entities.get('deputies', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO deputies_extended 
                        (source_id, cadastro_id, nome_parlamentar, nome_completo, legislatura, 
                         circulo_id, circulo_descricao, import_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        deputy['source_id'], deputy['cadastro_id'], deputy['nome_parlamentar'],
                        deputy['nome_completo'], deputy['legislatura'], deputy['circulo_id'],
                        deputy['circulo_descricao'], deputy['import_source']
                    ))
                    total_records += 1
                
                # Import initiatives
                for initiative in entities.get('initiatives', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO initiatives_extended 
                        (source_id, numero, tipo, tipo_descricao, legislatura, sessao, titulo, deputy_id, import_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        initiative['source_id'], initiative['numero'], initiative['tipo'],
                        initiative['tipo_descricao'], initiative['legislatura'], initiative['sessao'],
                        initiative['titulo'], initiative['deputy_id'], initiative['import_source']
                    ))
                    total_records += 1
                
                # Import interventions
                for intervention in entities.get('interventions', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO interventions_extended 
                        (source_id, titulo, assunto, data_publicacao, tipo_publicacao, legislatura, 
                         sessao, numero, tipo_intervencao, paginas_dar, deputy_id, import_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        intervention['source_id'], intervention['titulo'], intervention['assunto'],
                        intervention['data_publicacao'], intervention['tipo_publicacao'], 
                        intervention['legislatura'], intervention['sessao'], intervention['numero'],
                        intervention['tipo_intervencao'], intervention['paginas_dar'],
                        intervention['deputy_id'], intervention['import_source']
                    ))
                    total_records += 1
                
                # Import commissions
                for commission in entities.get('commissions', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO commissions_extended 
                        (source_id, nome, legislatura, import_source)
                        VALUES (?, ?, ?, ?)
                    """, (
                        commission['source_id'], commission['nome'], commission['legislatura'], commission['import_source']
                    ))
                    total_records += 1
                
                # Import deputy-commission relationships
                for deputy_commission in entities.get('deputy_commissions', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO deputy_commissions_extended 
                        (deputy_id, commission_id, situacao, legislatura, import_source)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        deputy_commission['deputy_id'], deputy_commission['commission_id'],
                        deputy_commission['situacao'], deputy_commission['legislatura'], deputy_commission['import_source']
                    ))
                    total_records += 1
                
                # Import biographical records
                for bio in entities.get('biographical_records', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO biographical_records 
                        (cadastro_id, nome_completo, data_nascimento, sexo, profissao, import_source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        bio['cadastro_id'], bio['nome_completo'], bio['data_nascimento'],
                        bio['sexo'], bio['profissao'], bio['import_source']
                    ))
                    total_records += 1
                
                # Import qualifications
                for qual in entities.get('qualifications', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO qualifications 
                        (source_id, cadastro_id, descricao, tipo_id, estado, import_source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        qual['source_id'], qual['cadastro_id'], qual['descricao'],
                        qual['tipo_id'], qual['estado'], qual['import_source']
                    ))
                    total_records += 1
                
                # Import positions
                for pos in entities.get('positions', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO positions 
                        (source_id, cadastro_id, descricao, ordem, antiga, import_source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        pos['source_id'], pos['cadastro_id'], pos['descricao'],
                        pos['ordem'], pos['antiga'], pos['import_source']
                    ))
                    total_records += 1
                
                # Import decorations
                for dec in entities.get('decorations', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO decorations 
                        (source_id, cadastro_id, descricao, ordem, import_source)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        dec['source_id'], dec['cadastro_id'], dec['descricao'],
                        dec['ordem'], dec['import_source']
                    ))
                    total_records += 1
                
                # Import conflicts of interest
                for conflict in entities.get('conflicts_of_interest', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO conflicts_of_interest 
                        (record_id, full_name, marital_status, spouse_name, matrimonial_regime, exclusivity, dgf_number, import_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        conflict['record_id'], conflict['full_name'], conflict['marital_status'],
                        conflict['spouse_name'], conflict['matrimonial_regime'], conflict['exclusivity'], 
                        conflict['dgf_number'], conflict['import_source']
                    ))
                    total_records += 1
                
                # Import activities
                for activity in entities.get('activities', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO activities 
                        (activity_id, tipo, desc_tipo, assunto, legislatura, sessao, numero, data_entrada, 
                         data_agendamento_debate, orgao_exterior, observacoes, tipo_autor, import_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        activity['activity_id'], activity['tipo'], activity['desc_tipo'],
                        activity['assunto'], activity['legislatura'], activity['sessao'], activity['numero'],
                        activity['data_entrada'], activity['data_agendamento_debate'], activity['orgao_exterior'],
                        activity['observacoes'], activity['tipo_autor'], activity['import_source']
                    ))
                    total_records += 1
                
                # Import activity votes
                for vote in entities.get('activity_votes', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO activity_votes 
                        (activity_id, vote_id, resultado, reuniao, unanime, data_votacao, descricao, import_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        vote['activity_id'], vote['vote_id'], vote['resultado'], vote['reuniao'],
                        vote['unanime'], vote['data_votacao'], vote['descricao'], vote['import_source']
                    ))
                    total_records += 1
                
                # Import activity participants
                for participant in entities.get('activity_participants', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO activity_participants 
                        (activity_id, nome, cargo, pais, honra, tipo_participacao, import_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        participant['activity_id'], participant['nome'], participant.get('cargo'),
                        participant.get('pais'), participant.get('honra'), participant['tipo_participacao'], 
                        participant['import_source']
                    ))
                    total_records += 1
                
                # Import activity publications
                for pub in entities.get('activity_publications', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO activity_publications 
                        (activity_id, pub_nr, pub_tipo, pub_data, url_diario, legislatura, import_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pub['activity_id'], pub['pub_nr'], pub['pub_tipo'], pub['pub_data'],
                        pub['url_diario'], pub['legislatura'], pub['import_source']
                    ))
                    total_records += 1
                
                conn.commit()
                print(f"    Imported {total_records} records into database")
                
        except Exception as e:
            print(f"    Error importing to database: {e}")
            return 0
        
        return total_records
    
    def create_agenda_tables(self):
        """Create agenda parlamentar and extended tables if they don't exist"""
        # Create agenda tables
        migration_path = Path("migrations/create_agenda_parlamentar_tables.sql")
        if migration_path.exists():
            with sqlite3.connect(self.db_path) as conn:
                with open(migration_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
        
        # Create extended tables for new entity types
        extended_path = Path("migrations/create_extended_tables.sql")
        if extended_path.exists():
            with sqlite3.connect(self.db_path) as conn:
                with open(extended_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
        
        # Create conflicts of interest table
        conflicts_path = Path("migrations/create_conflicts_of_interest.sql")
        if conflicts_path.exists():
            with sqlite3.connect(self.db_path) as conn:
                with open(conflicts_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
        
        # Create activities tables
        activities_path = Path("migrations/create_activities_tables.sql")
        if activities_path.exists():
            with sqlite3.connect(self.db_path) as conn:
                with open(activities_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
    
    def process_single_file(self, file_data: Dict[str, Any], download_dir: str = "downloads") -> bool:
        """Process a single file with complete validation and tracking"""
        file_info = self.get_file_info(file_data)
        file_url = file_info['file_url']
        
        print(f"\n{'='*80}")
        print(f"PROCESSING FILE: {file_info['file_name']}")
        print(f"Category: {file_info['category']}")
        print(f"Legislatura: {file_info['legislatura']}")
        print(f"Type: {file_info['file_type']}")
        print(f"URL: {file_url}")
        
        # Insert/update import record
        self.insert_import_record(file_info)
        self.update_import_status(file_url, 
            status='processing', 
            processing_started_at=datetime.now().isoformat()
        )
        
        try:
            # Determine local file path
            safe_filename = "".join(c for c in file_info['file_name'] if c.isalnum() or c in '._-')
            category_dir = "".join(c for c in file_info['category'] if c.isalnum() or c in '._-')
            local_path = os.path.join(download_dir, category_dir, file_info['legislatura'], safe_filename)
            
            # Download file if not exists
            if not os.path.exists(local_path):
                if not self.download_file(file_url, local_path):
                    self.update_import_status(file_url, 
                        status='failed', 
                        error_message='Download failed',
                        processing_completed_at=datetime.now().isoformat()
                    )
                    return False
            
            # Calculate file hash
            file_hash = self.calculate_file_hash(local_path)
            file_size = os.path.getsize(local_path)
            
            # Check if already processed
            if self.is_file_processed(file_url, file_hash):
                print("    File already processed with same hash, skipping")
                return True
            
            # Update with hash and size
            self.update_import_status(file_url, 
                file_path=local_path,
                file_hash=file_hash,
                file_size=file_size
            )
            
            # Check for PDF documentation in same folder (for learning data structures)
            if file_info['file_type'] == 'PDF':
                print("    PDF detected - this is documentation for learning data structures")
                pdf_content = self.read_pdf_content(local_path)
                if pdf_content:
                    print(f"    PDF Content Preview (for learning): {pdf_content[:300]}...")
                    self.update_import_status(file_url,
                        status='completed',
                        records_imported=0,
                        processing_completed_at=datetime.now().isoformat(),
                        error_message='PDF processed for documentation - no data imported'
                    )
                    print("    PDF processed for documentation purposes")
                    return True
            else:
                # Check for accompanying PDF documentation
                pdf_files = [f for f in os.listdir(os.path.dirname(local_path)) if f.lower().endswith('.pdf')]
                if pdf_files:
                    print(f"    Found accompanying PDF documentation: {pdf_files}")
                    for pdf_file in pdf_files:
                        pdf_path = os.path.join(os.path.dirname(local_path), pdf_file)
                        pdf_content = self.read_pdf_content(pdf_path)
                        if pdf_content:
                            print(f"    PDF Documentation Preview: {pdf_content[:200]}...")
            
            # Analyze data structure
            print("    Analyzing data structure...")
            structure, initial_issues = self.analyze_data_structure(local_path, file_info['file_type'])
            
            # Validate against database schema
            print("    Validating against database schema...")
            schema_issues = self.validate_against_schema(structure, file_info['file_type'], file_info['category'])
            all_issues = initial_issues + schema_issues
            
            if all_issues:
                print(f"    SCHEMA MISMATCH DETECTED:")
                for issue in all_issues:
                    print(f"      - {issue}")
                
                print(f"\n    DATA STRUCTURE:")
                print(json.dumps(structure, indent=2, ensure_ascii=False))
                
                self.update_import_status(file_url,
                    status='schema_mismatch',
                    schema_issues=json.dumps(all_issues),
                    processing_completed_at=datetime.now().isoformat()
                )
                
                print(f"\n    STOPPING: Please review the data structure and update schema mapping.")
                print(f"    File: {local_path}")
                return False
            
            # If no schema issues, proceed with import
            print("    Schema validation passed")
            
            # Extract relational entities
            print("    Extracting relational data...")
            if file_info['file_type'] == 'JSON':
                with open(local_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif file_info['file_type'] == 'XML':
                with open(local_path, 'r', encoding='utf-8') as f:
                    data = xmltodict.parse(f.read())
            else:
                data = None
            
            entities = self.extract_relational_data(data, file_info['file_type'], file_info['category'])
            
            # Import data into database tables
            records_imported = self.import_entities_to_database(entities, file_info)
            
            self.update_import_status(file_url,
                status='completed',
                records_imported=records_imported,
                processing_completed_at=datetime.now().isoformat()
            )
            
            print(f"    File processed successfully: {records_imported} records imported")
            return True
            
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            print(f"    {error_msg}")
            traceback.print_exc()
            
            self.update_import_status(file_url,
                status='failed',
                error_message=error_msg,
                processing_completed_at=datetime.now().isoformat()
            )
            return False
    
    def get_import_status_summary(self):
        """Get summary of import status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM import_status 
                GROUP BY status
            """)
            return dict(cursor.fetchall())

def main():
    parser = argparse.ArgumentParser(description='Process Parliament data files with import tracking')
    parser.add_argument('--test-file', help='Test processing a single file by URL')
    parser.add_argument('--process-category', help='Process all files from a specific category')
    parser.add_argument('--status', action='store_true', help='Show import status summary')
    parser.add_argument('--reset-failed', action='store_true', help='Reset failed imports to pending')
    
    args = parser.parse_args()
    
    processor = ParliamentFileProcessor()
    
    if args.status:
        summary = processor.get_import_status_summary()
        print("Import Status Summary:")
        for status, count in summary.items():
            print(f"  {status}: {count}")
    
    elif args.test_file:
        # Test with a single file
        test_file = {
            'url': args.test_file,
            'text': args.test_file.split('/')[-1],
            'type': 'JSON' if 'json' in args.test_file.lower() else 'XML',
            'category': 'test',
            'legislatura': 'TEST'
        }
        processor.process_single_file(test_file)
    
    else:
        print("Parliamentary Data File Processor")
        print("Use --help for available options")

if __name__ == "__main__":
    main()