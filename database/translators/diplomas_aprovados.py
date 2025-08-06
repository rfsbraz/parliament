"""
Diplomas Aprovados Translation Module
=====================================

Field translations and enum mappings for approved diplomas (Diplomas*.xml).

Based on official Portuguese Parliament documentation from December 2017:
"Significado das Tags do Ficheiro Diplomas<Legislatura>.xml"

This module provides translations for all diploma-related fields and structures
including related entities like publications, initiatives, and budget data.
"""

from enum import Enum
from typing import Dict, Optional
from .common_enums import TipoParticipante


# Note: The PDF documentation lists the following diploma types in the introductory text:
# "Decretos Constitucionais, Decretos da Assembleia, Deliberações, Leis, Leis Constitucionais, 
# Leis Orgânicas, Retificações, Regimentos, Regimentos da AR, Resoluções e Resoluções da AR"
# However, no specific enum values are provided in the field specifications, 
# so we don't create enum classes for these types.


# Field Translations Dictionary
DIPLOMA_FIELDS = {
    # Core Diploma Fields (Diplomas_DetalhePesquisaDiplomasOut)
    "id": {
        "pt": "Identificador do Diploma",
        "en": "Diploma Identifier",
        "description": "Unique identifier for the diploma",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Id"
    },
    "numero": {
        "pt": "Número de Diploma",
        "en": "Diploma Number", 
        "description": "Sequential number of the diploma",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Numero"
    },
    "numero2": {
        "pt": "Complemento do Número",
        "en": "Number Complement",
        "description": "Additional numbering complement",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Numero2"
    },
    "titulo": {
        "pt": "Título do Diploma",
        "en": "Diploma Title",
        "description": "Full title of the diploma",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Titulo"
    },
    "tipo": {
        "pt": "Tipo de Diploma",
        "en": "Diploma Type",
        "description": "Type classification of the diploma",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Tipo"
    },
    "tp": {
        "pt": "Tipo de Diploma (abreviado)",
        "en": "Diploma Type (abbreviated)",
        "description": "Abbreviated form of diploma type",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Tp"
    },
    "legislatura": {
        "pt": "Legislatura",
        "en": "Legislature",
        "description": "Legislature period",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Legislatura"
    },
    "sessao": {
        "pt": "Sessão legislativa",
        "en": "Legislative Session",
        "description": "Legislative session number",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Sessao"
    },
    "ano_civil": {
        "pt": "Ano a que corresponde o Diploma",
        "en": "Civil Year",
        "description": "Year to which the diploma corresponds",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.AnoCivil"
    },
    "link_texto": {
        "pt": "Link para o texto do diploma",
        "en": "Link to Diploma Text",
        "description": "URL link to the diploma text",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.LinkTexto"
    },
    "observacoes": {
        "pt": "Observações",
        "en": "Observations",
        "description": "Additional notes or observations",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Observacoes"
    },
    "versao": {
        "pt": "Versão do Diploma",
        "en": "Diploma Version",
        "description": "Version of the diploma",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Versao"
    },
    "anexos": {
        "pt": "Anexos associados ao Diploma",
        "en": "Associated Attachments",
        "description": "Attachments associated with the diploma",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Anexos"
    },
    "actividades": {
        "pt": "Dados das Atividades associadas",
        "en": "Associated Activities Data",
        "description": "Data of activities associated with the diploma",
        "xml_path": "ArrayOfDiplomaOut.DiplomaOut.Actividades"
    }
}

# Publication Fields (PublicacoesOut)
PUBLICACAO_FIELDS = {
    "pub_nr": {
        "pt": "Número da Publicação",
        "en": "Publication Number",
        "description": "Sequential number of the publication",
        "xml_path": "pubNr"
    },
    "pub_tipo": {
        "pt": "Descrição do Tipo de Publicação",
        "en": "Publication Type Description",
        "description": "Full description of publication type",
        "xml_path": "pubTipo"
    },
    "pub_tp": {
        "pt": "Abreviatura do Tipo de Publicação",
        "en": "Publication Type Abbreviation",
        "description": "Abbreviated form of publication type",
        "xml_path": "pubTp"
    },
    "pub_leg": {
        "pt": "Legislatura em que ocorreu a Publicação",
        "en": "Legislature of Publication",
        "description": "Legislature period when publication occurred",
        "xml_path": "pubLeg"
    },
    "pub_sl": {
        "pt": "Sessão legislativa em que ocorreu a Publicação",
        "en": "Legislative Session of Publication", 
        "description": "Legislative session when publication occurred",
        "xml_path": "pubSL"
    },
    "pub_dt": {
        "pt": "Data da Publicação",
        "en": "Publication Date",
        "description": "Date of publication",
        "xml_path": "pubdt"
    },
    "pag": {
        "pt": "Páginas",
        "en": "Pages",
        "description": "Page numbers in the publication",
        "xml_path": "pag"
    },
    "id_pag": {
        "pt": "Identificador da Paginação",
        "en": "Pagination Identifier",
        "description": "Unique identifier for pagination",
        "xml_path": "idPag"
    },
    "url_diario": {
        "pt": "Link para o DAR da Publicação",
        "en": "Link to Assembly Diary",
        "description": "URL link to Assembly Diary publication",
        "xml_path": "URLDiario"
    },
    "supl": {
        "pt": "Suplemento da Publicação",
        "en": "Publication Supplement",
        "description": "Supplement information",
        "xml_path": "supl"
    },
    "obs": {
        "pt": "Observações",
        "en": "Observations",
        "description": "Additional notes or observations",
        "xml_path": "obs"
    },
    "pag_final_diario_supl": {
        "pt": "Página final do suplemento",
        "en": "Supplement Final Page",
        "description": "Final page of the supplement",
        "xml_path": "pagFinalDiarioSupl"
    },
    "debate_dt_reu": {
        "pt": "Data do debate na reunião plenária",
        "en": "Plenary Meeting Debate Date",
        "description": "Date of debate in plenary meeting",
        "xml_path": "debateDtReu"
    },
    "id_act": {
        "pt": "Identificador da Atividade associada à Publicação",
        "en": "Publication Activity Identifier",
        "description": "Identifier of activity associated with publication",
        "xml_path": "idAct"
    },
    "id_deb": {
        "pt": "Identificador do Debate associado à Publicação",
        "en": "Publication Debate Identifier",
        "description": "Identifier of debate associated with publication",
        "xml_path": "idDeb"
    },
    "id_int": {
        "pt": "Identificador da Intervenção associada à Publicação",
        "en": "Publication Intervention Identifier",
        "description": "Identifier of intervention associated with publication",
        "xml_path": "idInt"
    }
}

# Initiative Fields (Iniciativas_DetalhePesquisaIniciativasOut)
INICIATIVA_FIELDS = {
    "ini_nr": {
        "pt": "Número da Iniciativa",
        "en": "Initiative Number",
        "description": "Sequential number of the initiative",
        "xml_path": "IniNr"
    },
    "ini_tipo": {
        "pt": "Tipo de Iniciativa",
        "en": "Initiative Type",
        "description": "Type classification of the initiative",
        "xml_path": "IniTipo"
    },
    "ini_link_texto": {
        "pt": "Link para o texto da iniciativa",
        "en": "Link to Initiative Text",
        "description": "URL link to the initiative text",
        "xml_path": "IniLinkTexto"
    },
    "ini_id": {
        "pt": "Identificador da Iniciativa",
        "en": "Initiative Identifier",
        "description": "Unique identifier for the initiative",
        "xml_path": "IniId"
    },
    "ini_leg": {
        "pt": "Legislatura da iniciativa",
        "en": "Initiative Legislature",
        "description": "Legislature period of the initiative",
        "xml_path": "iniLeg"
    },
    "ini_sel": {
        "pt": "Sessão legislativa da iniciativa", 
        "en": "Initiative Legislative Session",
        "description": "Legislative session of the initiative",
        "xml_path": "iniSel"
    },
    "ini_titulo": {
        "pt": "Título da Iniciativa",
        "en": "Initiative Title",
        "description": "Full title of the initiative",
        "xml_path": "iniTitulo"
    },
    "ini_obs": {
        "pt": "Observações associadas",
        "en": "Associated Observations",
        "description": "Notes or observations about the initiative",
        "xml_path": "iniObs"
    },
    "ini_desc_tipo": {
        "pt": "Descrição do Tipo de Iniciativa",
        "en": "Initiative Type Description",
        "description": "Full description of initiative type",
        "xml_path": "iniDescTipo"
    },
    "ini_epigrafe": {
        "pt": "Indica se tem texto em epígrafe",
        "en": "Has Epigraph Text",
        "description": "Indicates if initiative has epigraph text",
        "xml_path": "iniEpigrafe"
    },
    "ini_testa_ficheiro": {
        "pt": "Indica se existe ficheiro",
        "en": "Has File",
        "description": "Indicates if file exists",
        "xml_path": "iniTestaFicheiro"
    },
    "ini_texto_subst": {
        "pt": "Indica se tem texto de substituição",
        "en": "Has Substitution Text",
        "description": "Indicates if has substitution text",
        "xml_path": "iniTextoSubst"
    },
    "ini_texto_subst_campo": {
        "pt": "Texto de substituição",
        "en": "Substitution Text",
        "description": "Actual substitution text content",
        "xml_path": "iniTextoSubstCampo"
    }
}

# Budget/Management Account Fields (OrcamentoContasGerencia_OrcamentoContasGerenciaOut)
ORCAMENTO_FIELDS = {
    "orcam_id": {
        "pt": "Identificador da conta de gerência",
        "en": "Management Account Identifier",
        "description": "Unique identifier for management account",
        "xml_path": "id"
    },
    "tipo": {
        "pt": "Tipo de Conta de Gerência",
        "en": "Management Account Type",
        "description": "Type of management account",
        "xml_path": "tipo"
    },
    "tp": {
        "pt": "Descrição do Orçamento",
        "en": "Budget Description",
        "description": "Description of the budget",
        "xml_path": "tp"
    },
    "titulo": {
        "pt": "Título da Conta de Gerência",
        "en": "Management Account Title",
        "description": "Title of the management account",
        "xml_path": "titulo"
    },
    "ano": {
        "pt": "Ano a que se refere o Orçamento",
        "en": "Budget Reference Year",
        "description": "Year to which the budget refers",
        "xml_path": "ano"
    },
    "leg": {
        "pt": "Legislatura",
        "en": "Legislature",
        "description": "Legislature period",
        "xml_path": "leg"
    },
    "sl": {
        "pt": "Sessão Legislativa",
        "en": "Legislative Session",
        "description": "Legislative session",
        "xml_path": "SL"
    },
    "anexos": {
        "pt": "Anexos associados a este Orçamento",
        "en": "Budget Associated Attachments",
        "description": "Attachments associated with this budget",
        "xml_path": "anexos"
    },
    "textos_aprovados": {
        "pt": "Textos Aprovados associados a este Orçamento",
        "en": "Associated Approved Texts",
        "description": "Approved texts associated with this budget",
        "xml_path": "textosAprovados"
    },
    "votacao": {
        "pt": "Resultado da votação ao Orçamento",
        "en": "Budget Voting Result",
        "description": "Result of the budget voting",
        "xml_path": "votacao"
    },
    "dt_aprovacao_ca": {
        "pt": "Data de aprovação do Orçamento pelo Conselho de Administração",
        "en": "Administrative Council Approval Date",
        "description": "Date of budget approval by Administrative Council",
        "xml_path": "dtAprovacaoCA"
    },
    "dt_agendamento": {
        "pt": "Data de Agendamento do Orçamento",
        "en": "Budget Scheduling Date",
        "description": "Date of budget scheduling",
        "xml_path": "dtAgendamento"
    },
    "obs": {
        "pt": "Campo das observações",
        "en": "Observations Field",
        "description": "Additional observations or notes",
        "xml_path": "obs"
    }
}

# Document Fields (DocsOut)
DOCUMENT_FIELDS = {
    "titulo_documento": {
        "pt": "Título do documento",
        "en": "Document Title",
        "description": "Title of the document",
        "xml_path": "tituloDocumento"
    },
    "data_documento": {
        "pt": "Data de criação do documento", 
        "en": "Document Creation Date",
        "description": "Date when document was created",
        "xml_path": "dataDocumento"
    },
    "publicar_internet": {
        "pt": "Publicar documento na internet",
        "en": "Publish Document on Internet",
        "description": "Flag to publish document on internet",
        "xml_path": "publicarInternet"
    },
    "tipo_documento": {
        "pt": "Tipo de documento",
        "en": "Document Type",
        "description": "Type classification of document",
        "xml_path": "tipoDocumento"
    },
    "url": {
        "pt": "Hiperligação para o documento",
        "en": "Document Hyperlink",
        "description": "URL hyperlink to the document",
        "xml_path": "URL"
    }
}

# Combined translation dictionaries
ALL_FIELDS = {
    **DIPLOMA_FIELDS,
    **PUBLICACAO_FIELDS, 
    **INICIATIVA_FIELDS,
    **ORCAMENTO_FIELDS,
    **DOCUMENT_FIELDS
}

def get_field_translation(field_name: str, language: str = "pt") -> str:
    """
    Get translation for a field name
    
    Args:
        field_name: Name of the field
        language: Language code ('pt' or 'en')
        
    Returns:
        Translated field name or original if not found
    """
    field_info = ALL_FIELDS.get(field_name, {})
    return field_info.get(language, field_name)

def get_field_description(field_name: str) -> str:
    """
    Get description for a field
    
    Args:
        field_name: Name of the field
        
    Returns:
        Field description or empty string if not found
    """
    field_info = ALL_FIELDS.get(field_name, {})
    return field_info.get("description", "")

def get_field_xml_path(field_name: str) -> str:
    """
    Get XML path for a field
    
    Args:
        field_name: Name of the field
        
    Returns:
        XML path or empty string if not found
    """
    field_info = ALL_FIELDS.get(field_name, {})
    return field_info.get("xml_path", "")

def get_field_enum(field_name: str) -> Optional[Enum]:
    """
    Get enum class for a field if it exists
    
    Args:
        field_name: Name of the field
        
    Returns:
        Enum class or None if field has no enum
    """
    field_info = ALL_FIELDS.get(field_name, {})
    return field_info.get("enum", None)