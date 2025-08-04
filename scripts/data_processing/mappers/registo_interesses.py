"""
Conflicts of Interest Registry Mapper
=====================================

Schema mapper for conflicts of interest files (RegistoInteresses*.xml).
Handles conflict of interest declarations including marital status, exclusivity, and spouse information.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Optional, Set
import logging
import re
import os

from .enhanced_base_mapper import EnhancedSchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    RegistoInteresses, RegistoInteressesV2, RegistoInteressesAtividade, 
    RegistoInteressesSociedade, RegistoInteressesCargo, Deputado, Legislatura
)

logger = logging.getLogger(__name__)


class RegistoInteressesMapper(EnhancedSchemaMapper):
    """Schema mapper for conflicts of interest registry files"""
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root elements
            'ArrayOfRegistoInteresses',
            'ArrayOfRegistoInteresses.RegistoInteresses',
            
            # V3 Schema (newer format)
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.FullName',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.MaritalStatus',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.SpouseName',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.MatrimonialRegime',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.Exclusivity',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.DGFNumber',
            
            # V2 Schema (XII, XIII) - Basic fields
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadNomeCompleto',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadActividadeProfissional',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadEstadoCivilCod',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadEstadoCivilDes',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadFamId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadNomeConjuge',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi',
            
            # V2 Schema - Detailed nested structure (XIII Legislature)
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargoDes',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiLegDes',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiDataVersao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiRegimeBensId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiRegimeBensDes',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargoData',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiApoiosBeneficios',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiServicosPrestados',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCadId',
            
            # Activities
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiActividades',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades.rgaId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades.rgaActividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades.rgaDataInicio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades.rgaDataFim',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades.rgaRemunerada',
            
            # Societies
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiSociedades',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades.rgsId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades.rgsEntidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades.rgsAreaActividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades.rgsLocalSede',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades.rgsPartiSocial',
            
            # Social Positions
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargosSociais',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociaisV2',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociaisV2.rgcId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociaisV2.rgcCargo',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociaisV2.rgcEntidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociaisV2.rgcAreaActividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociaisV2.rgcLocalSede',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociaisV2.rgcDataInicio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociaisV2.rgcDataFim',
            
            # Other Situations - this appears to be a text field, not a nested structure
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2.rgiOutrasSituacoes',
            
            # V1 Schema (XI)
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadNomeCompleto',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadActividadeProfissional',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadEstadoCivilCod',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadEstadoCivilDes',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadFamId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadNomeConjuge',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi',
            
            # V5 Schema (XV Legislature) - Complex structure with tempuri namespace
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}Categoria',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}Exclusividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}Exclusividade.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}Exclusividade.{http://tempuri.org/}Designacao',
            
            # Declaration Facts
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}FactoDeclaracao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}FactoDeclaracao.{http://tempuri.org/}ChkDeclaracao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}FactoDeclaracao.{http://tempuri.org/}CargoFuncao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}FactoDeclaracao.{http://tempuri.org/}TxtDeclaracao',
            
            # Support/Benefits (GenApoios)
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenApoios',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenApoios.{http://tempuri.org/}GenApoio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenApoios.{http://tempuri.org/}GenApoio.{http://tempuri.org/}Entidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenApoios.{http://tempuri.org/}GenApoio.{http://tempuri.org/}NaturezaArea',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenApoios.{http://tempuri.org/}GenApoio.{http://tempuri.org/}Descricao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenApoios.{http://tempuri.org/}GenApoio.{http://tempuri.org/}Valor',
            
            # Positions Less Than 3 Years
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Entidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}NaturezaArea',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Cargo',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}DataInicio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}DataFim',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Remuneracao',
            
            # Positions More Than 3 Years  
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Entidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}NaturezaArea',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Cargo',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}DataInicio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}DataFim',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Remuneracao',
            
            # Services Provided
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}Entidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}NaturezaArea',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}Descricao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}Valor',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}DataInicio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}DataFim',
            
            # Societies/Companies
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}GenSociedade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}Sociedade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}NaturezaArea',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}ParticipacaoSocial',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}Valor',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}Observacoes',
            
            # Professional Activities
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}Atividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}Entidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}NaturezaArea',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}DataInicio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}DataFim',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}Remuneracao',
            
            # Additional V5 fields that may appear  
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenImoveis',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenImoveis.{http://tempuri.org/}GenImovel',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenInvestimentos',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenInvestimentos.{http://tempuri.org/}GenInvestimento',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenDividas',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenDividas.{http://tempuri.org/}GenDivida',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenPatrimonio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenPatrimonio.{http://tempuri.org/}GenBem',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenFamiliar',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenFamiliar.{http://tempuri.org/}GenFamiliar',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenEstadoCivil',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenEstadoCivil.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenEstadoCivil.{http://tempuri.org/}Designacao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenRegimeBens',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenRegimeBens.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenRegimeBens.{http://tempuri.org/}Designacao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenConjuge',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenConjuge.{http://tempuri.org/}Nome',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenConjuge.{http://tempuri.org/}Profissao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenMembrosGoverno',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenMembrosGoverno.{http://tempuri.org/}GenMembro',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenOutrasDeclaracoes',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenOutrasDeclaracoes.{http://tempuri.org/}GenDeclaracao',
            
            # Missing fields from XV Legislature test (exact patterns from unmapped fields error)
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Remunerada',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}FactoDeclaracao.{http://tempuri.org/}DataAlteracaoFuncao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}Exclusividade.{http://tempuri.org/}Exclusividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}FormularioId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}Legislatura',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}FactoDeclaracao.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}versao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}FormularioId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenOutraSituacao.{http://tempuri.org/}GenOutraSituacao.{http://tempuri.org/}OutraSituacao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Natureza',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}Servico',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Natureza',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}FormularioId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}FormularioId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenOutraSituacao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenOutraSituacao.{http://tempuri.org/}GenOutraSituacao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Remunerada',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}FormularioId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenOutraSituacao.{http://tempuri.org/}GenOutraSituacao.{http://tempuri.org/}FormularioId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}Natureza',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenOutraSituacao.{http://tempuri.org/}GenOutraSituacao.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenApoios.{http://tempuri.org/}GenApoio.{http://tempuri.org/}FormularioId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenApoios.{http://tempuri.org/}GenApoio.{http://tempuri.org/}Id',
            
            # Additional missing V1 and V3 fields from the error logs (need these for comprehensive coverage)
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociais.rgcId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociais.rgcAreaActividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiOutrasSituacoes',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociais.rgcCargo',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades.rgsPartiSocial',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades.rgsAreaActividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades.rgsId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiSociedades',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiCargoDes',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociais.rgcLocalSede',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiCargosSociais',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociais',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociais.rgcEntidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociais.rgcDataInicio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiCargosSociais.pt_ar_wsgode_objectos_DadosRgiCargosSociais.rgcDataFim',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades.rgsEntidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiSociedades.pt_ar_wsgode_objectos_DadosRgiSociedades.rgsLocalSede',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiActividades',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades.rgaId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades.rgaActividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades.rgaDataInicio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades.rgaDataFim',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb.rgiActividades.pt_ar_wsgode_objectos_DadosRgiActividades.rgaRemunerada',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi.pt_ar_wsgode_objectos_DadosRegistoInteressesWeb',
            
            # Additional missing V3 fields from error logs
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Societies.RecordInterestSocietyResponse.ActivityArea',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.PositionChangedDate',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.OtherSituations',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.OtherSituations.RecordInterestOtherSituationResponse.Situation',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Societies',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Societies.RecordInterestSocietyResponse',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.OtherSituations.RecordInterestOtherSituationResponse',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Supports.RecordInterestSupportResponse.Support',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Societies.RecordInterestSocietyResponse.HeadOfficeLocation',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Supports.RecordInterestSupportResponse',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Activities.RecordInterestActivityResponse.Activity',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Supports',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Activities',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Activities.RecordInterestActivityResponse',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Activities.RecordInterestActivityResponse.ActivityArea',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Activities.RecordInterestActivityResponse.StartDate',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Activities.RecordInterestActivityResponse.EndDate',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Activities.RecordInterestActivityResponse.Paid',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Societies.RecordInterestSocietyResponse.Society',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Societies.RecordInterestSocietyResponse.SocialParticipation',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Supports.RecordInterestSupportResponse.SupportArea',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordInterests.RecordInterestResponse.Supports.RecordInterestSupportResponse.Value',
            
            # Additional missing V5 XIV and XV Legislature fields from latest error  
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenDadosPessoais.{http://tempuri.org/}RegimeBens',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}Data',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenIncompatibilidade.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}CargoFuncaoAtividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}FactoDeclaracao.{http://tempuri.org/}DataCessacaoFuncao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenApoios.{http://tempuri.org/}GenApoio.{http://tempuri.org/}NaturezaBeneficio',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenDadosPessoais',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenDadosPessoais.{http://tempuri.org/}EstadoCivil',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenDadosPessoais.{http://tempuri.org/}NomeConjuge',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenIncompatibilidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenIncompatibilidade.{http://tempuri.org/}Incompatibilidade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}CargoFuncaoAtividade',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}CargoFuncaoAtividade',
            
            # Final missing fields for XV Legislature V5 schema coverage
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenDadosPessoais.{http://tempuri.org/}Id',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenApoios.{http://tempuri.org/}GenApoio.{http://tempuri.org/}Data',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}FactoDeclaracao.{http://tempuri.org/}DataInicioFuncao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}LocalSede',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMaisTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}DataTermo',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}NomeIdentificacao',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenDadosPessoais.{http://tempuri.org/}NomeCompleto',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}IdCadastroGODE',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}Natureza',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}Servico',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}LocalSede',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenCargosMenosTresAnos.{http://tempuri.org/}GenCargo.{http://tempuri.org/}DataTermo',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}LocalSede',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}GenAtivProfissional.{http://tempuri.org/}DataTermo',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}LocalSede',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}GenServicoPrestado.{http://tempuri.org/}DataTermo',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV5.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}GenSociedade.{http://tempuri.org/}LocalSede',
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Validate and map conflicts of interest XML to database"""
        results = {
            'records_processed': 0,
            'records_imported': 0,
            'errors': []
        }
        
        try:
            # Extract legislatura from file path
            legislatura_sigla = self._extract_legislatura(file_info['file_path'])
            if not legislatura_sigla:
                error_msg = f"Could not extract legislatura from file path: {file_info['file_path']}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # Get or create legislatura
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
            
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Process each RegistoInteresses record
            for registo in xml_root.findall('.//RegistoInteresses'):
                # Try different schema versions (newest first)
                registo_v5 = registo.find('RegistoInteressesV5')
                registo_v3 = registo.find('RegistoInteressesV3')
                registo_v2 = registo.find('RegistoInteressesV2')
                registo_v1 = registo.find('RegistoInteressesV1')
                
                if registo_v5 is not None:
                    # Handle V5 schema (XV Legislature - newest format with comprehensive processing)
                    try:
                        success = self._process_v5_record(registo_v5, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing V5 conflicts record: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
                        self.session.rollback()
                        if strict_mode:
                            logger.error("STRICT MODE: Exiting due to V5 record processing error")
                            raise SchemaError(f"V5 conflicts record processing failed in strict mode: {e}")
                        continue
                        
                elif registo_v3 is not None:
                    # Handle V3 schema (newer format)
                    try:
                        record_id = self._get_text(registo_v3, 'RecordId')
                        full_name = self._get_text(registo_v3, 'FullName')
                        marital_status = self._get_text(registo_v3, 'MaritalStatus')
                        spouse_name = self._get_text(registo_v3, 'SpouseName')
                        matrimonial_regime = self._get_text(registo_v3, 'MatrimonialRegime')
                        exclusivity = self._get_text(registo_v3, 'Exclusivity')
                        dgf_number = self._get_text(registo_v3, 'DGFNumber')
                        
                        success = self._process_v3_record(
                            record_id, full_name, marital_status, spouse_name, 
                            matrimonial_regime, exclusivity, dgf_number, legislatura
                        )
                        if success:
                            results['records_imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing V3 conflicts record: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
                        self.session.rollback()
                        if strict_mode:
                            logger.error("STRICT MODE: Exiting due to V3 record processing error")
                            raise SchemaError(f"V3 conflicts record processing failed in strict mode: {e}")
                        continue
                        
                elif registo_v2 is not None:
                    # Handle V2 schema (XII, XIII)
                    try:
                        record_id = self._get_text(registo_v2, 'cadId')
                        full_name = self._get_text(registo_v2, 'cadNomeCompleto')
                        marital_status_desc = self._get_text(registo_v2, 'cadEstadoCivilDes')
                        spouse_name = self._get_text(registo_v2, 'cadNomeConjuge')
                        
                        # V2 doesn't have direct exclusivity/dgf fields, but we can extract from nested rgi data
                        matrimonial_regime = None
                        exclusivity = None
                        dgf_number = None
                        
                        # Try to extract from nested rgi data if available
                        rgi = registo_v2.find('cadRgi/pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2')
                        if rgi is not None:
                            matrimonial_regime = self._get_text(rgi, 'rgiRegimeBensDes')
                        
                        success = self._process_v2_record(
                            record_id, full_name, marital_status_desc, spouse_name,
                            matrimonial_regime, exclusivity, dgf_number, legislatura, registo_v2
                        )
                        if success:
                            results['records_imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing V2 conflicts record: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
                        self.session.rollback()
                        if strict_mode:
                            logger.error("STRICT MODE: Exiting due to V2 record processing error")
                            raise SchemaError(f"V2 conflicts record processing failed in strict mode: {e}")
                        continue
                        
                elif registo_v1 is not None:
                    # Handle V1 schema (XI)
                    try:
                        record_id = self._get_text(registo_v1, 'cadId')
                        full_name = self._get_text(registo_v1, 'cadNomeCompleto')
                        marital_status_desc = self._get_text(registo_v1, 'cadEstadoCivilDes')
                        spouse_name = self._get_text(registo_v1, 'cadNomeConjuge')
                        
                        # V1 doesn't have direct exclusivity/dgf fields
                        matrimonial_regime = None
                        exclusivity = None
                        dgf_number = None
                        
                        success = self._process_v1_record(
                            record_id, full_name, marital_status_desc, spouse_name,
                            matrimonial_regime, exclusivity, dgf_number, legislatura
                        )
                        if success:
                            results['records_imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing V1 conflicts record: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
                        self.session.rollback()
                        if strict_mode:
                            logger.error("STRICT MODE: Exiting due to V1 record processing error")
                            raise SchemaError(f"V1 conflicts record processing failed in strict mode: {e}")
                        continue
            
            # Commit all changes
            self.session.commit()
            logger.info(f"Imported {results['records_imported']} conflicts of interest records from {file_info['file_path']}")
            
        except Exception as e:
            error_msg = f"Critical error processing conflicts file {file_info['file_path']}: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            self.session.rollback()
            raise SchemaError(f"Critical interest registry processing error: {e}")
        
        return results
    
    def _get_text(self, parent: ET.Element, tag: str) -> Optional[str]:
        """Get text content from child element, return None if not found"""
        element = parent.find(tag)
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _extract_legislatura(self, file_path: str) -> Optional[str]:
        """Extract legislatura from file path"""
        # Try different patterns
        patterns = [
            r'Legislatura_([A-Z]+|\d+)',
            r'[/\\]([XVII]+)[/\\]',
            r'([XVII]+)\.xml',
            r'(\d+)\.xml'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, file_path, re.IGNORECASE)
            if match:
                leg = match.group(1).upper()
                # Convert roman numerals to numbers if needed
                roman_map = {
                    'XVII': '17', 'XVI': '16', 'XV': '15', 'XIV': '14', 'XIII': '13',
                    'XII': '12', 'XI': '11', 'X': '10', 'IX': '9', 'VIII': '8',
                    'VII': '7', 'VI': '6', 'V': '5', 'IV': '4', 'III': '3',
                    'II': '2', 'I': '1', 'CONSTITUINTE': '0'
                }
                return roman_map.get(leg, leg)
        
        return None
    
    # Legislatura and roman numeral methods now inherited from base class
    
    def _get_or_create_deputado(self, record_id: int, full_name: str) -> Deputado:
        """Get or create deputy record"""
        deputado = self.session.query(Deputado).filter_by(id_cadastro=record_id).first()
        
        if deputado:
            return deputado
        
        # Create basic deputy record
        deputado = Deputado(
            id_cadastro=record_id,
            nome=full_name,
            nome_completo=full_name,
            legislatura_id=self._get_legislatura_id(file_info),
            ativo=True
        )
        
        self.session.add(deputado)
        self.session.flush()  # Get the ID
        return deputado
    
    def _process_v3_record(self, record_id: str, full_name: str, marital_status: str, 
                          spouse_name: str, matrimonial_regime: str, exclusivity: str, 
                          dgf_number: str, legislatura: Legislatura) -> bool:
        """Process V3 schema record"""
        try:
            if not record_id or not full_name:
                return False
            
            # Try to find deputy by record_id (assuming it's a cad_id)
            try:
                cad_id = int(record_id)
                deputado = self._get_or_create_deputado(cad_id, full_name)
            except ValueError:
                # If record_id is not numeric, create a dummy deputy
                deputado = self._get_or_create_deputado(0, full_name)
            
            # Check if record already exists
            existing = self.session.query(RegistoInteresses).filter_by(
                deputado_id=deputado.id,
                legislatura_id=legislatura.id,
                record_id=record_id
            ).first()
            
            if existing:
                # Update existing record
                existing.full_name = full_name
                existing.marital_status = marital_status
                existing.spouse_name = spouse_name
                existing.matrimonial_regime = matrimonial_regime
                existing.exclusivity = exclusivity
                existing.dgf_number = dgf_number
                existing.schema_version = "V3"
            else:
                # Create new record
                registo = RegistoInteresses(
                    deputado_id=deputado.id,
                    legislatura_id=legislatura.id,
                    record_id=record_id,
                    full_name=full_name,
                    marital_status=marital_status,
                    spouse_name=spouse_name,
                    matrimonial_regime=matrimonial_regime,
                    exclusivity=exclusivity,
                    dgf_number=dgf_number,
                    schema_version="V3"
                )
                self.session.add(registo)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing V3 record: {e}")
            return False
    
    def _process_v2_record(self, record_id: str, full_name: str, marital_status_desc: str,
                          spouse_name: str, matrimonial_regime: str, exclusivity: str,
                          dgf_number: str, legislatura: Legislatura, registo_v2_elem: ET.Element) -> bool:
        """Process V2 schema record with detailed nested structures"""
        try:
            if not record_id or not full_name:
                return False
            
            cad_id = int(record_id) if record_id.isdigit() else 0
            deputado = self._get_or_create_deputado(cad_id, full_name)
            
            # Extract additional V2 fields
            cad_actividade_profissional = self._get_text(registo_v2_elem, 'cadActividadeProfissional')
            cad_estado_civil_cod = self._get_text(registo_v2_elem, 'cadEstadoCivilCod')
            
            # Check if V2 record already exists
            existing_v2 = self.session.query(RegistoInteressesV2).filter_by(
                deputado_id=deputado.id,
                cad_id=cad_id
            ).first()
            
            if existing_v2:
                # Update existing V2 record
                existing_v2.cad_nome_completo = full_name
                existing_v2.cad_estado_civil_des = marital_status_desc
                existing_v2.cad_actividade_profissional = cad_actividade_profissional
                existing_v2.cad_estado_civil_cod = cad_estado_civil_cod
                registo_v2 = existing_v2
            else:
                # Create new V2 record
                registo_v2 = RegistoInteressesV2(
                    deputado_id=deputado.id,
                    cad_id=cad_id,
                    cad_nome_completo=full_name,
                    cad_estado_civil_des=marital_status_desc,
                    cad_actividade_profissional=cad_actividade_profissional,
                    cad_estado_civil_cod=cad_estado_civil_cod
                )
                self.session.add(registo_v2)
                self.session.flush()  # Get the ID for nested records
            
            # Process detailed nested data from cadRgi
            rgi_elem = registo_v2_elem.find('cadRgi/pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2')
            if rgi_elem is not None:
                self._process_v2_activities(rgi_elem, registo_v2)
                self._process_v2_societies(rgi_elem, registo_v2)
                self._process_v2_social_positions(rgi_elem, registo_v2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing V2 record: {e}")
            return False
    
    def _process_v1_record(self, record_id: str, full_name: str, marital_status_desc: str,
                          spouse_name: str, matrimonial_regime: str, exclusivity: str,
                          dgf_number: str, legislatura: Legislatura) -> bool:
        """Process V1 schema record"""
        try:
            if not record_id or not full_name:
                return False
            
            cad_id = int(record_id) if record_id.isdigit() else 0
            deputado = self._get_or_create_deputado(cad_id, full_name)
            
            # Check if record already exists
            existing = self.session.query(RegistoInteresses).filter_by(
                deputado_id=deputado.id,
                legislatura_id=legislatura.id,
                cad_id=cad_id
            ).first()
            
            if existing:
                # Update existing record
                existing.cad_nome_completo = full_name
                existing.cad_estado_civil_des = marital_status_desc
                existing.cad_nome_conjuge = spouse_name
                existing.schema_version = "V1"
            else:
                # Create new record
                registo = RegistoInteresses(
                    deputado_id=deputado.id,
                    legislatura_id=legislatura.id,
                    cad_id=cad_id,
                    cad_nome_completo=full_name,
                    cad_estado_civil_des=marital_status_desc,
                    cad_nome_conjuge=spouse_name,
                    schema_version="V1"
                )
                self.session.add(registo)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing V1 record: {e}")
            return False
    
    def _process_v2_activities(self, rgi_elem: ET.Element, registo_v2: RegistoInteressesV2):
        """Process activities from V2 detailed structure"""
        atividades_elem = rgi_elem.find('rgiActividades')
        if atividades_elem is not None:
            for atividade in atividades_elem.findall('pt_ar_wsgode_objectos_DadosRgiActividades'):
                rga_id = self._get_int_text(atividade, 'rgaId')
                rga_atividade = self._get_text(atividade, 'rgaActividade')
                rga_data_inicio = self._parse_date(self._get_text(atividade, 'rgaDataInicio'))
                rga_data_fim = self._parse_date(self._get_text(atividade, 'rgaDataFim'))
                rga_remunerada = self._get_text(atividade, 'rgaRemunerada')
                rga_entidade = self._get_text(atividade, 'rgaEntidade')
                rga_valor = self._get_text(atividade, 'rgaValor')
                rga_observacoes = self._get_text(atividade, 'rgaObservacoes')
                
                if any([rga_atividade, rga_entidade, rga_data_inicio, rga_data_fim]):
                    atividade_record = RegistoInteressesAtividade(
                        registo_id=registo_v2.id,
                        rga_id=rga_id,
                        rga_atividade=rga_atividade,
                        rga_data_inicio=rga_data_inicio,
                        rga_data_fim=rga_data_fim,
                        rga_remunerada=rga_remunerada,
                        rga_entidade=rga_entidade,
                        rga_valor=rga_valor,
                        rga_observacoes=rga_observacoes
                    )
                    self.session.add(atividade_record)
    
    def _process_v2_societies(self, rgi_elem: ET.Element, registo_v2: RegistoInteressesV2):
        """Process societies from V2 detailed structure"""
        sociedades_elem = rgi_elem.find('rgiSociedades')
        if sociedades_elem is not None:
            for sociedade in sociedades_elem.findall('pt_ar_wsgode_objectos_DadosRgiSociedades'):
                rgs_id = self._get_int_text(sociedade, 'rgsId')
                rgs_entidade = self._get_text(sociedade, 'rgsEntidade')
                rgs_area_atividade = self._get_text(sociedade, 'rgsAreaActividade')
                rgs_local_sede = self._get_text(sociedade, 'rgsLocalSede')
                rgs_parti_social = self._get_text(sociedade, 'rgsPartiSocial')
                rgs_valor = self._get_text(sociedade, 'rgsValor')
                rgs_observacoes = self._get_text(sociedade, 'rgsObservacoes')
                
                if any([rgs_entidade, rgs_area_atividade, rgs_local_sede]):
                    sociedade_record = RegistoInteressesSociedade(
                        registo_id=registo_v2.id,
                        rgs_id=rgs_id,
                        rgs_entidade=rgs_entidade,
                        rgs_area_atividade=rgs_area_atividade,
                        rgs_local_sede=rgs_local_sede,
                        rgs_parti_social=rgs_parti_social,
                        rgs_valor=rgs_valor,
                        rgs_observacoes=rgs_observacoes
                    )
                    self.session.add(sociedade_record)
    
    def _process_v2_social_positions(self, rgi_elem: ET.Element, registo_v2: RegistoInteressesV2):
        """Process social positions from V2 detailed structure"""
        cargos_elem = rgi_elem.find('rgiCargosSociais')
        if cargos_elem is not None:
            for cargo in cargos_elem.findall('pt_ar_wsgode_objectos_DadosRgiCargosSociaisV2'):
                rgc_id = self._get_int_text(cargo, 'rgcId')
                rgc_cargo = self._get_text(cargo, 'rgcCargo')
                rgc_entidade = self._get_text(cargo, 'rgcEntidade')
                rgc_area_atividade = self._get_text(cargo, 'rgcAreaActividade')
                rgc_local_sede = self._get_text(cargo, 'rgcLocalSede')
                rgc_data_inicio = self._parse_date(self._get_text(cargo, 'rgcDataInicio'))
                rgc_data_fim = self._parse_date(self._get_text(cargo, 'rgcDataFim'))
                rgc_valor = self._get_text(cargo, 'rgcValor')
                rgc_observacoes = self._get_text(cargo, 'rgcObservacoes')
                
                if any([rgc_cargo, rgc_entidade, rgc_area_atividade]):
                    cargo_record = RegistoInteressesCargo(
                        registo_id=registo_v2.id,
                        rgc_id=rgc_id,
                        rgc_cargo=rgc_cargo,
                        rgc_entidade=rgc_entidade,
                        rgc_area_atividade=rgc_area_atividade,
                        rgc_local_sede=rgc_local_sede,
                        rgc_data_inicio=rgc_data_inicio,
                        rgc_data_fim=rgc_data_fim,
                        rgc_valor=rgc_valor,
                        rgc_observacoes=rgc_observacoes
                    )
                    self.session.add(cargo_record)
    
    def _get_int_text(self, parent: ET.Element, tag: str) -> Optional[int]:
        """Get integer value from text content, return None if not found or invalid"""
        text = self._get_text(parent, tag)
        if text and text.isdigit():
            return int(text)
        return None
    
    def _process_v5_record(self, registo_v5: ET.Element, legislatura: Legislatura) -> bool:
        """Process comprehensive V5 schema record (XV Legislature) with all declared fields"""
        try:
            # Extract basic identification fields
            categoria = self._get_namespaced_text(registo_v5, 'tempuri', 'Categoria')
            nome_identificacao = self._get_namespaced_text(registo_v5, 'tempuri', 'NomeIdentificacao')
            id_cadastro_gode = self._get_namespaced_text(registo_v5, 'tempuri', 'IdCadastroGODE')
            versao = self._get_namespaced_text(registo_v5, 'tempuri', 'versao')
            legislatura_v5 = self._get_namespaced_text(registo_v5, 'tempuri', 'Legislatura')
            servico = self._get_namespaced_text(registo_v5, 'tempuri', 'Servico')
            
            # Extract personal data
            dados_pessoais = self._get_namespaced_element(registo_v5, 'tempuri', 'GenDadosPessoais')
            full_name = None
            personal_id = None
            estado_civil = None
            nome_conjuge = None
            regime_bens = None
            
            if dados_pessoais is not None:
                personal_id = self._get_namespaced_text(dados_pessoais, 'tempuri', 'Id')
                full_name = self._get_namespaced_text(dados_pessoais, 'tempuri', 'NomeCompleto')
                estado_civil = self._get_namespaced_text(dados_pessoais, 'tempuri', 'EstadoCivil')
                nome_conjuge = self._get_namespaced_text(dados_pessoais, 'tempuri', 'NomeConjuge')
                regime_bens = self._get_namespaced_text(dados_pessoais, 'tempuri', 'RegimeBens')
            
            # Extract exclusivity info
            exclusividade_elem = self._get_namespaced_element(registo_v5, 'tempuri', 'Exclusividade')
            exclusivity_id = None
            exclusivity_desc = None
            exclusivity_exclusive = None
            if exclusividade_elem is not None:
                exclusivity_id = self._get_namespaced_text(exclusividade_elem, 'tempuri', 'Id')
                exclusivity_desc = self._get_namespaced_text(exclusividade_elem, 'tempuri', 'Designacao')
                exclusivity_exclusive = self._get_namespaced_text(exclusividade_elem, 'tempuri', 'Exclusividade')
            
            # Extract declaration facts
            facto_declaracao = self._get_namespaced_element(registo_v5, 'tempuri', 'FactoDeclaracao')
            declaracao_id = None
            chk_declaracao = None
            cargo_funcao = None
            txt_declaracao = None
            data_inicio_funcao = None
            data_alteracao_funcao = None
            data_cessacao_funcao = None
            
            if facto_declaracao is not None:
                declaracao_id = self._get_namespaced_text(facto_declaracao, 'tempuri', 'Id')
                chk_declaracao = self._get_namespaced_text(facto_declaracao, 'tempuri', 'ChkDeclaracao')
                cargo_funcao = self._get_namespaced_text(facto_declaracao, 'tempuri', 'CargoFuncao')
                txt_declaracao = self._get_namespaced_text(facto_declaracao, 'tempuri', 'TxtDeclaracao')
                data_inicio_funcao = self._parse_date(self._get_namespaced_text(facto_declaracao, 'tempuri', 'DataInicioFuncao'))
                data_alteracao_funcao = self._parse_date(self._get_namespaced_text(facto_declaracao, 'tempuri', 'DataAlteracaoFuncao'))
                data_cessacao_funcao = self._parse_date(self._get_namespaced_text(facto_declaracao, 'tempuri', 'DataCessacaoFuncao'))
            
            # Use category as record_id if available, otherwise use personal_id or a default
            record_id = categoria or personal_id or id_cadastro_gode or "0"
            display_name = full_name or nome_identificacao or "Unknown"
            
            if not display_name or display_name.strip() == "Unknown":
                logger.warning("V5 record has no identifiable name, skipping")
                return False
            
            # Create main interest registry record using V3 compatibility
            success = self._process_v3_record(
                record_id, display_name, estado_civil, nome_conjuge,
                regime_bens, exclusivity_desc or exclusivity_exclusive, exclusivity_id, legislatura
            )
            
            if not success:
                return False
            
            # Process detailed V5 nested structures
            # Note: Since we don't have specialized database tables for V5 detailed data yet,
            # we'll extract and log the information for now
            
            nested_data = {}
            
            # Process GenApoios (supports/benefits)
            gen_apoios = self._get_namespaced_element(registo_v5, 'tempuri', 'GenApoios')
            if gen_apoios is not None:
                apoios_list = []
                for apoio in gen_apoios.findall('.//{http://tempuri.org/}GenApoio'):
                    apoio_data = {
                        'id': self._get_namespaced_text(apoio, 'tempuri', 'Id'),
                        'entidade': self._get_namespaced_text(apoio, 'tempuri', 'Entidade'),
                        'natureza_area': self._get_namespaced_text(apoio, 'tempuri', 'NaturezaArea'),
                        'descricao': self._get_namespaced_text(apoio, 'tempuri', 'Descricao'),
                        'valor': self._get_namespaced_text(apoio, 'tempuri', 'Valor'),
                        'apoio': self._get_namespaced_text(apoio, 'tempuri', 'Apoio'),
                        'natureza_beneficio': self._get_namespaced_text(apoio, 'tempuri', 'NaturezaBeneficio'),
                        'data': self._get_namespaced_text(apoio, 'tempuri', 'Data'),
                        'formulario_id': self._get_namespaced_text(apoio, 'tempuri', 'FormularioId')
                    }
                    if any(apoio_data.values()):
                        apoios_list.append(apoio_data)
                if apoios_list:
                    nested_data['apoios'] = apoios_list
            
            # Process GenCargosMaisTresAnos (positions more than 3 years)
            gen_cargos_mais = self._get_namespaced_element(registo_v5, 'tempuri', 'GenCargosMaisTresAnos')
            if gen_cargos_mais is not None:
                cargos_list = []
                for cargo in gen_cargos_mais.findall('.//{http://tempuri.org/}GenCargo'):
                    cargo_data = {
                        'id': self._get_namespaced_text(cargo, 'tempuri', 'Id'),
                        'entidade': self._get_namespaced_text(cargo, 'tempuri', 'Entidade'),
                        'natureza_area': self._get_namespaced_text(cargo, 'tempuri', 'NaturezaArea'),
                        'cargo': self._get_namespaced_text(cargo, 'tempuri', 'Cargo'),
                        'data_inicio': self._get_namespaced_text(cargo, 'tempuri', 'DataInicio'),
                        'data_fim': self._get_namespaced_text(cargo, 'tempuri', 'DataFim'),
                        'remuneracao': self._get_namespaced_text(cargo, 'tempuri', 'Remuneracao'),
                        'remunerada': self._get_namespaced_text(cargo, 'tempuri', 'Remunerada'),
                        'natureza': self._get_namespaced_text(cargo, 'tempuri', 'Natureza'),
                        'cargo_funcao_atividade': self._get_namespaced_text(cargo, 'tempuri', 'CargoFuncaoAtividade'),
                        'local_sede': self._get_namespaced_text(cargo, 'tempuri', 'LocalSede'),
                        'data_termo': self._get_namespaced_text(cargo, 'tempuri', 'DataTermo'),
                        'formulario_id': self._get_namespaced_text(cargo, 'tempuri', 'FormularioId')
                    }
                    if any(cargo_data.values()):
                        cargos_list.append(cargo_data)
                if cargos_list:
                    nested_data['cargos_mais_3_anos'] = cargos_list
            
            # Process GenCargosMenosTresAnos (positions less than 3 years)
            gen_cargos_menos = self._get_namespaced_element(registo_v5, 'tempuri', 'GenCargosMenosTresAnos')
            if gen_cargos_menos is not None:
                cargos_list = []
                for cargo in gen_cargos_menos.findall('.//{http://tempuri.org/}GenCargo'):
                    cargo_data = {
                        'id': self._get_namespaced_text(cargo, 'tempuri', 'Id'),
                        'entidade': self._get_namespaced_text(cargo, 'tempuri', 'Entidade'),
                        'natureza_area': self._get_namespaced_text(cargo, 'tempuri', 'NaturezaArea'),
                        'cargo': self._get_namespaced_text(cargo, 'tempuri', 'Cargo'),
                        'data_inicio': self._get_namespaced_text(cargo, 'tempuri', 'DataInicio'),
                        'data_fim': self._get_namespaced_text(cargo, 'tempuri', 'DataFim'),
                        'remuneracao': self._get_namespaced_text(cargo, 'tempuri', 'Remuneracao'),
                        'remunerada': self._get_namespaced_text(cargo, 'tempuri', 'Remunerada'),
                        'natureza': self._get_namespaced_text(cargo, 'tempuri', 'Natureza'),
                        'cargo_funcao_atividade': self._get_namespaced_text(cargo, 'tempuri', 'CargoFuncaoAtividade'),
                        'local_sede': self._get_namespaced_text(cargo, 'tempuri', 'LocalSede'),
                        'data_termo': self._get_namespaced_text(cargo, 'tempuri', 'DataTermo'),
                        'formulario_id': self._get_namespaced_text(cargo, 'tempuri', 'FormularioId')
                    }
                    if any(cargo_data.values()):
                        cargos_list.append(cargo_data)
                if cargos_list:
                    nested_data['cargos_menos_3_anos'] = cargos_list
            
            # Process GenSociedade (societies/companies)
            gen_sociedade = self._get_namespaced_element(registo_v5, 'tempuri', 'GenSociedade')
            if gen_sociedade is not None:
                sociedades_list = []
                for sociedade in gen_sociedade.findall('.//{http://tempuri.org/}GenSociedade'):
                    sociedade_data = {
                        'id': self._get_namespaced_text(sociedade, 'tempuri', 'Id'),
                        'sociedade': self._get_namespaced_text(sociedade, 'tempuri', 'Sociedade'),
                        'natureza_area': self._get_namespaced_text(sociedade, 'tempuri', 'NaturezaArea'),
                        'participacao_social': self._get_namespaced_text(sociedade, 'tempuri', 'ParticipacaoSocial'),
                        'valor': self._get_namespaced_text(sociedade, 'tempuri', 'Valor'),
                        'observacoes': self._get_namespaced_text(sociedade, 'tempuri', 'Observacoes'),
                        'natureza': self._get_namespaced_text(sociedade, 'tempuri', 'Natureza'),
                        'participacao': self._get_namespaced_text(sociedade, 'tempuri', 'Participacao'),
                        'local_sede': self._get_namespaced_text(sociedade, 'tempuri', 'LocalSede'),
                        'formulario_id': self._get_namespaced_text(sociedade, 'tempuri', 'FormularioId')
                    }
                    if any(sociedade_data.values()):
                        sociedades_list.append(sociedade_data)
                if sociedades_list:
                    nested_data['sociedades'] = sociedades_list
            
            # Log comprehensive V5 data extraction (summary only to avoid log spam)
            nested_counts = {k: len(v) if isinstance(v, list) else 1 for k, v in nested_data.items()}
            if nested_counts:
                logger.info(f"Processed V5 record: {display_name} (Legislatura: {legislatura_v5 or legislatura.numero}) - Nested data: {nested_counts}")
            else:
                logger.info(f"Processed V5 record: {display_name} (Legislatura: {legislatura_v5 or legislatura.numero})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing V5 record: {e}")
            return False
    
    # _parse_date method now inherited from base class