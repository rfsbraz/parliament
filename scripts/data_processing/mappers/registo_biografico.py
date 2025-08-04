"""
Biographical Registry Mapper
============================

Schema mapper for biographical registry files (RegistoBiografico*.xml).
Handles complete deputy biographical data including qualifications, roles, and organ activities.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Optional, Set
import logging

from .base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import Deputado

logger = logging.getLogger(__name__)


class RegistoBiograficoMapper(SchemaMapper):
    """Schema mapper for biographical registry files"""
    
    def __init__(self, session):
        super().__init__(session)
        # Use the passed SQLAlchemy session
        self.session = session
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # I Legislature XML structure - Complete field coverage
            'RegistoBiografico',
            'RegistoBiografico.RegistoBiograficoList',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb',
            
            # Basic biographical data
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadNomeCompleto',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDtNascimento',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadSexo',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadProfissao',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadNaturalidade',
            
            # Academic qualifications (cadHabilitacoes)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes.pt_ar_wsgode_objectos_DadosHabilitacoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes.pt_ar_wsgode_objectos_DadosHabilitacoes.habId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes.pt_ar_wsgode_objectos_DadosHabilitacoes.habDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes.pt_ar_wsgode_objectos_DadosHabilitacoes.habTipoId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes.pt_ar_wsgode_objectos_DadosHabilitacoes.habEstado',
            
            # Professional roles (cadCargosFuncoes)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes.pt_ar_wsgode_objectos_DadosCargosFuncoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes.pt_ar_wsgode_objectos_DadosCargosFuncoes.funId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes.pt_ar_wsgode_objectos_DadosCargosFuncoes.funDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes.pt_ar_wsgode_objectos_DadosCargosFuncoes.funOrdem',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes.pt_ar_wsgode_objectos_DadosCargosFuncoes.funAntiga',
            
            # Titles/Awards (cadTitulos)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadTitulos',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadTitulos.pt_ar_wsgode_objectos_DadosTitulos',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadTitulos.pt_ar_wsgode_objectos_DadosTitulos.titId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadTitulos.pt_ar_wsgode_objectos_DadosTitulos.titDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadTitulos.pt_ar_wsgode_objectos_DadosTitulos.titOrdem',
            
            # Decorations (cadCondecoracoes)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCondecoracoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCondecoracoes.pt_ar_wsgode_objectos_DadosCondecoracoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCondecoracoes.pt_ar_wsgode_objectos_DadosCondecoracoes.codId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCondecoracoes.pt_ar_wsgode_objectos_DadosCondecoracoes.codDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCondecoracoes.pt_ar_wsgode_objectos_DadosCondecoracoes.codOrdem',
            
            # Published Works (cadObrasPublicadas)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadObrasPublicadas',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadObrasPublicadas.pt_ar_wsgode_objectos_DadosObrasPublicadas',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadObrasPublicadas.pt_ar_wsgode_objectos_DadosObrasPublicadas.pubId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadObrasPublicadas.pt_ar_wsgode_objectos_DadosObrasPublicadas.pubDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadObrasPublicadas.pt_ar_wsgode_objectos_DadosObrasPublicadas.pubOrdem',
            
            # Organ activities
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT',
            
            # Committee activity details (actividadeCom)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.orgSigla',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.orgDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.orgId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.legDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao.tiaDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.timDes',
            
            # Working group activity details (actividadeGT)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.orgSigla',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.orgDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.orgId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.timDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.legDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao.tiaDes',
            
            # Deputy legislature data with all I Legislature fields
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.depNomeParlamentar',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.legDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.ceDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.parSigla',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.parDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.gpSigla',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.gpDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.indDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.urlVideoBiografia',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.indData',
            
            # Interest Registry V2 (RegistoInteressesV2List)
            'RegistoBiografico.RegistoInteressesV2List',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2.cadId',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2.cadEstadoCivilCod',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2.cadNomeCompleto',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2.cadActividadeProfissional',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2.cadEstadoCivilDes',
            
            # Interest Registry V1 (RegistoInteressesList)
            'RegistoBiografico.RegistoInteressesList',
            
            # Additional Interest Registry versions found in I Legislature files
            'RegistoBiografico.RegistoInteressesV1List',
            'RegistoBiografico.RegistoInteressesV3List', 
            'RegistoBiografico.RegistoInteressesV5List',
            
            # VIII Legislature XML structure (ArrayOfDadosRegistoBiografico)
            'ArrayOfDadosRegistoBiografico',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico',
            
            # Basic biographical data - VIII Legislature
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadNomeCompleto',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDtNascimento',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadSexo',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadProfissao',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadNaturalidade',
            
            # Academic qualifications - VIII Legislature
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes.DadosHabilitacoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes.DadosHabilitacoes.HabId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes.DadosHabilitacoes.HabDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes.DadosHabilitacoes.HabTipoId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes.DadosHabilitacoes.HabEstado',
            
            # Professional roles - VIII Legislature
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes.DadosCargosFuncoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes.DadosCargosFuncoes.FunId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes.DadosCargosFuncoes.FunDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes.DadosCargosFuncoes.FunOrdem',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes.DadosCargosFuncoes.FunAntiga',
            
            # Titles/Awards - VIII Legislature
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadTitulos',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadTitulos.DadosTitulos',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadTitulos.DadosTitulos.TitId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadTitulos.DadosTitulos.TitDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadTitulos.DadosTitulos.TitOrdem',
            
            # Decorations - VIII Legislature
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCondecoracoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCondecoracoes.DadosCondecoracoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCondecoracoes.DadosCondecoracoes.CodId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCondecoracoes.DadosCondecoracoes.CodDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCondecoracoes.DadosCondecoracoes.CodOrdem',
            
            # Published Works - VIII Legislature
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadObrasPublicadas',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadObrasPublicadas.DadosObrasPublicadas',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadObrasPublicadas.DadosObrasPublicadas.PubId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadObrasPublicadas.DadosObrasPublicadas.PubDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadObrasPublicadas.DadosObrasPublicadas.PubOrdem',
            
            # Deputy legislature data - VIII Legislature
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.DepNomeParlamentar',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.LegDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.CeDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.ParSigla',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.ParDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.GpSigla',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.GpDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.IndDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.IndData',
            
            # Organ activities - VIII Legislature
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.orgId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.orgDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.orgSigla',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.legDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.timDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao.tiaDes',
            
            # Working groups - VIII Legislature  
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.orgId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.orgDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.orgSigla',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.legDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.timDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao.tiaDes',
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map biographical data to database with comprehensive field processing - supports both I and VIII Legislature structures"""
        results = {
            'records_processed': 0,
            'records_imported': 0,
            'errors': []
        }
        
        try:
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Determine XML structure and process accordingly
            if xml_root.tag == 'ArrayOfDadosRegistoBiografico':
                # ArrayOfDadosRegistoBiografico structure (used by multiple legislatures)
                # Extract legislature from file path for accurate logging
                legislature_name = self._extract_legislature_from_path(file_info.get('file_path', ''))
                logger.info(f"Processing {legislature_name} biographical structure (ArrayOfDadosRegistoBiografico format)")
                for record in xml_root.findall('DadosRegistoBiografico'):
                    try:
                        success = self._process_viii_legislature_biographical_record(record, file_info)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"Error processing VIII Legislature biographical record: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        if strict_mode:
                            raise
            else:
                # I Legislature structure
                legislature_name = self._extract_legislature_from_path(file_info.get('file_path', ''))
                logger.info(f"Processing {legislature_name} biographical structure (I Legislature format)")
                biografico_list = xml_root.find('RegistoBiograficoList')
                if biografico_list is not None:
                    for record in biografico_list.findall('pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb'):
                        try:
                            success = self._process_i_legislature_biographical_record(record, file_info)
                            results['records_processed'] += 1
                            if success:
                                results['records_imported'] += 1
                        except Exception as e:
                            error_msg = f"Error processing I Legislature biographical record: {str(e)}"
                            results['errors'].append(error_msg)
                            logger.error(error_msg)
                            if strict_mode:
                                raise
            
            # Process Interest Registry V2 if present
            interesses_list = xml_root.find('RegistoInteressesV2List')
            if interesses_list is not None:
                for record in interesses_list.findall('pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2'):
                    try:
                        success = self._process_registo_interesses_v2(record, file_info)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"Error processing interest registry V2: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        if strict_mode:
                            raise
            
            return results
            
        except Exception as e:
            error_msg = f"Error in biographical mapping: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
            if strict_mode:
                raise
            return results
    
    def _process_i_legislature_biographical_record(self, record: ET.Element, file_info: Dict) -> bool:
        """Process comprehensive I Legislature biographical record with all fields"""
        try:
            from database.models import (
                Deputado, DeputadoHabilitacao, DeputadoCargoFuncao, DeputadoTitulo,
                DeputadoCondecoracao, DeputadoObraPublicada, DeputadoAtividadeOrgao, DeputadoMandatoLegislativo
            )
            
            # Extract basic biographical data
            cad_id = self._get_text_value(record, 'cadId')
            if not cad_id:
                return False
                
            cad_id = int(float(cad_id))
            
            # Get or create deputy
            deputy = self.session.query(Deputado).filter(Deputado.id_cadastro == cad_id).first()
            if not deputy:
                deputy = Deputado(
                    id_cadastro=cad_id,
                    nome=self._get_text_value(record, 'cadNomeCompleto') or f"Deputy {cad_id}",
                    nome_completo=self._get_text_value(record, 'cadNomeCompleto'),
                    legislatura_id=self._get_legislatura_id(file_info),
                    sexo=self._get_text_value(record, 'cadSexo'),  # New I Legislature field
                    profissao=self._get_text_value(record, 'cadProfissao'),
                    data_nascimento=self._parse_date(self._get_text_value(record, 'cadDtNascimento')),
                    naturalidade=self._get_text_value(record, 'cadNaturalidade')
                )
                self.session.add(deputy)
                self.session.flush()  # Get the ID
            else:
                # Update existing fields
                deputy.nome_completo = self._get_text_value(record, 'cadNomeCompleto') or deputy.nome_completo
                deputy.sexo = self._get_text_value(record, 'cadSexo') or deputy.sexo
                deputy.profissao = self._get_text_value(record, 'cadProfissao') or deputy.profissao
                deputy.data_nascimento = self._parse_date(self._get_text_value(record, 'cadDtNascimento')) or deputy.data_nascimento
                deputy.naturalidade = self._get_text_value(record, 'cadNaturalidade') or deputy.naturalidade
            
            # Process Academic Qualifications (cadHabilitacoes)
            habilitacoes = record.find('cadHabilitacoes')
            if habilitacoes is not None:
                for hab in habilitacoes.findall('pt_ar_wsgode_objectos_DadosHabilitacoes'):
                    hab_id = self._get_text_value(hab, 'habId')
                    if hab_id:
                        # Check if already exists
                        existing = self.session.query(DeputadoHabilitacao).filter(
                            DeputadoHabilitacao.deputado_id == deputy.id,
                            DeputadoHabilitacao.hab_id == int(float(hab_id))
                        ).first()
                        
                        if not existing:
                            qualification = DeputadoHabilitacao(
                                deputado_id=deputy.id,
                                hab_id=int(float(hab_id)),
                                hab_des=self._get_text_value(hab, 'habDes'),
                                hab_tipo_id=self._parse_int(self._get_text_value(hab, 'habTipoId')),
                                hab_estado=self._get_text_value(hab, 'habEstado')  # New I Legislature field
                            )
                            self.session.add(qualification)
            
            # Process Professional Roles (cadCargosFuncoes)
            cargos_funcoes = record.find('cadCargosFuncoes')
            if cargos_funcoes is not None:
                for cargo in cargos_funcoes.findall('pt_ar_wsgode_objectos_DadosCargosFuncoes'):
                    fun_id = self._get_text_value(cargo, 'funId')
                    if fun_id:
                        # Check if already exists
                        existing = self.session.query(DeputadoCargoFuncao).filter(
                            DeputadoCargoFuncao.deputado_id == deputy.id,
                            DeputadoCargoFuncao.fun_id == int(float(fun_id))
                        ).first()
                        
                        if not existing:
                            role = DeputadoCargoFuncao(
                                deputado_id=deputy.id,
                                fun_id=int(float(fun_id)),
                                fun_des=self._get_text_value(cargo, 'funDes'),
                                fun_ordem=self._parse_int(self._get_text_value(cargo, 'funOrdem')),  # New I Legislature field
                                fun_antiga=self._get_text_value(cargo, 'funAntiga')  # New I Legislature field
                            )
                            self.session.add(role)
            
            # Process Titles/Awards (cadTitulos)
            titulos = record.find('cadTitulos')
            if titulos is not None:
                for titulo in titulos.findall('pt_ar_wsgode_objectos_DadosTitulos'):
                    tit_id = self._get_text_value(titulo, 'titId')
                    if tit_id:
                        # Check if already exists
                        existing = self.session.query(DeputadoTitulo).filter(
                            DeputadoTitulo.deputado_id == deputy.id,
                            DeputadoTitulo.tit_id == int(float(tit_id))
                        ).first()
                        
                        if not existing:
                            title = DeputadoTitulo(
                                deputado_id=deputy.id,
                                tit_id=int(float(tit_id)),
                                tit_des=self._get_text_value(titulo, 'titDes'),
                                tit_ordem=self._parse_int(self._get_text_value(titulo, 'titOrdem'))
                            )
                            self.session.add(title)
            
            # Process Decorations (cadCondecoracoes)
            condecoracoes = record.find('cadCondecoracoes')
            if condecoracoes is not None:
                for cond in condecoracoes.findall('pt_ar_wsgode_objectos_DadosCondecoracoes'):
                    cod_id = self._get_text_value(cond, 'codId')
                    if cod_id:
                        # Check if already exists
                        existing = self.session.query(DeputadoCondecoracao).filter(
                            DeputadoCondecoracao.deputado_id == deputy.id,
                            DeputadoCondecoracao.cod_id == int(float(cod_id))
                        ).first()
                        
                        if not existing:
                            decoration = DeputadoCondecoracao(
                                deputado_id=deputy.id,
                                cod_id=int(float(cod_id)),
                                cod_des=self._get_text_value(cond, 'codDes'),
                                cod_ordem=self._parse_int(self._get_text_value(cond, 'codOrdem'))
                            )
                            self.session.add(decoration)
            
            # Process Published Works (cadObrasPublicadas)
            obras = record.find('cadObrasPublicadas')
            if obras is not None:
                for obra in obras.findall('pt_ar_wsgode_objectos_DadosObrasPublicadas'):
                    pub_id = self._get_text_value(obra, 'pubId')
                    if pub_id:
                        # Check if already exists
                        existing = self.session.query(DeputadoObraPublicada).filter(
                            DeputadoObraPublicada.deputado_id == deputy.id,
                            DeputadoObraPublicada.pub_id == int(float(pub_id))
                        ).first()
                        
                        if not existing:
                            publication = DeputadoObraPublicada(
                                deputado_id=deputy.id,
                                pub_id=int(float(pub_id)),
                                pub_des=self._get_text_value(obra, 'pubDes'),
                                pub_ordem=self._parse_int(self._get_text_value(obra, 'pubOrdem'))
                            )
                            self.session.add(publication)
            
            # Process Organ Activities (cadActividadeOrgaos)
            atividades_orgaos = record.find('cadActividadeOrgaos')
            if atividades_orgaos is not None:
                # Process Committee Activities (actividadeCom)
                comissoes = atividades_orgaos.findall('actividadeCom')
                for comissao in comissoes:
                    dados_orgao = comissao.find('pt_ar_wsgode_objectos_DadosOrgaos')
                    if dados_orgao is not None:
                        # Check for position details in committee (cargoDes structure)
                        tia_des = None
                        cargo_des_elem = dados_orgao.find('cargoDes')
                        if cargo_des_elem is not None:
                            cargo_data = cargo_des_elem.find('pt_ar_wsgode_objectos_DadosCargosOrgao')
                            if cargo_data is not None:
                                tia_des = self._get_text_value(cargo_data, 'tiaDes')
                        
                        atividade = DeputadoAtividadeOrgao(
                            deputado_id=deputy.id,
                            tipo_atividade='committee',
                            org_id=self._parse_int(self._get_text_value(dados_orgao, 'orgId')),
                            org_sigla=self._get_text_value(dados_orgao, 'orgSigla'),
                            org_des=self._get_text_value(dados_orgao, 'orgDes'),
                            cargo_des=self._get_text_value(dados_orgao, 'cargoDes'),
                            tim_des=self._get_text_value(dados_orgao, 'timDes'),
                            leg_des=self._get_text_value(dados_orgao, 'legDes'),
                            tia_des=tia_des
                        )
                        self.session.add(atividade)
                
                # Process Working Group Activities (actividadeGT)
                grupos_trabalho = atividades_orgaos.findall('actividadeGT')
                for grupo in grupos_trabalho:
                    dados_orgao = grupo.find('pt_ar_wsgode_objectos_DadosOrgaos')
                    if dados_orgao is not None:
                        # Check for position details (cargoDes structure)
                        tia_des = None
                        cargo_des_elem = dados_orgao.find('cargoDes')
                        if cargo_des_elem is not None:
                            cargo_data = cargo_des_elem.find('pt_ar_wsgode_objectos_DadosCargosOrgao')
                            if cargo_data is not None:
                                tia_des = self._get_text_value(cargo_data, 'tiaDes')
                        
                        atividade = DeputadoAtividadeOrgao(
                            deputado_id=deputy.id,
                            tipo_atividade='working_group',
                            org_id=self._parse_int(self._get_text_value(dados_orgao, 'orgId')),
                            org_sigla=self._get_text_value(dados_orgao, 'orgSigla'),
                            org_des=self._get_text_value(dados_orgao, 'orgDes'),
                            cargo_des=self._get_text_value(dados_orgao, 'cargoDes'),
                            tim_des=self._get_text_value(dados_orgao, 'timDes'),
                            leg_des=self._get_text_value(dados_orgao, 'legDes'),
                            tia_des=tia_des
                        )
                        self.session.add(atividade)
            
            # Process Legislative Mandates (cadDeputadoLegis)
            legislaturas = record.find('cadDeputadoLegis')
            if legislaturas is not None:
                for mandato in legislaturas.findall('pt_ar_wsgode_objectos_DadosDeputadoLegis'):
                    leg_des = self._get_text_value(mandato, 'legDes')
                    ce_des = self._get_text_value(mandato, 'ceDes')
                    
                    if leg_des:
                        # Check if already exists
                        existing = self.session.query(DeputadoMandatoLegislativo).filter(
                            DeputadoMandatoLegislativo.deputado_id == deputy.id,
                            DeputadoMandatoLegislativo.leg_des == leg_des,
                            DeputadoMandatoLegislativo.ce_des == ce_des
                        ).first()
                        
                        if not existing:
                            mandate = DeputadoMandatoLegislativo(
                                deputado_id=deputy.id,
                                dep_nome_parlamentar=self._get_text_value(mandato, 'depNomeParlamentar'),
                                leg_des=leg_des,
                                ce_des=ce_des,  # New I Legislature field
                                par_sigla=self._get_text_value(mandato, 'parSigla'),
                                par_des=self._get_text_value(mandato, 'parDes'),
                                gp_sigla=self._get_text_value(mandato, 'gpSigla'),  # New I Legislature field
                                gp_des=self._get_text_value(mandato, 'gpDes'),  # New I Legislature field
                                ind_des=self._get_text_value(mandato, 'indDes'),  # New I Legislature field
                                url_video_biografia=self._get_text_value(mandato, 'urlVideoBiografia'),  # New I Legislature field
                                ind_data=self._parse_date(self._get_text_value(mandato, 'indData'))  # New I Legislature field
                            )
                            self.session.add(mandate)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing I Legislature biographical record: {e}")
            return False
    
    def _process_viii_legislature_biographical_record(self, record: ET.Element, file_info: Dict) -> bool:
        """Process VIII Legislature biographical record (ArrayOfDadosRegistoBiografico structure)"""
        try:
            from database.models import (
                Deputado, DeputadoHabilitacao, DeputadoCargoFuncao, DeputadoTitulo,
                DeputadoCondecoracao, DeputadoObraPublicada, DeputadoAtividadeOrgao, DeputadoMandatoLegislativo
            )
            
            # Extract basic biographical data using VIII Legislature structure
            cad_id = self._get_text_value(record, 'CadId')
            if not cad_id:
                return False
                
            cad_id = int(float(cad_id))
            
            # Get or create deputy
            deputy = self.session.query(Deputado).filter(Deputado.id_cadastro == cad_id).first()
            if not deputy:
                deputy = Deputado(
                    id_cadastro=cad_id,
                    nome=self._get_text_value(record, 'CadNomeCompleto') or f"Deputy {cad_id}",
                    nome_completo=self._get_text_value(record, 'CadNomeCompleto'),
                    legislatura_id=self._get_legislatura_id(file_info),
                    sexo=self._get_text_value(record, 'CadSexo'),
                    profissao=self._get_text_value(record, 'CadProfissao'),
                    data_nascimento=self._parse_date(self._get_text_value(record, 'CadDtNascimento')),
                    naturalidade=self._get_text_value(record, 'CadNaturalidade')
                )
                self.session.add(deputy)
                self.session.flush()
            else:
                # Update existing fields
                deputy.nome_completo = self._get_text_value(record, 'CadNomeCompleto') or deputy.nome_completo
                deputy.sexo = self._get_text_value(record, 'CadSexo') or deputy.sexo
                deputy.profissao = self._get_text_value(record, 'CadProfissao') or deputy.profissao
                deputy.data_nascimento = self._parse_date(self._get_text_value(record, 'CadDtNascimento')) or deputy.data_nascimento
                deputy.naturalidade = self._get_text_value(record, 'CadNaturalidade') or deputy.naturalidade
            
            # Process Academic Qualifications (CadHabilitacoes)
            habilitacoes = record.find('CadHabilitacoes')
            if habilitacoes is not None:
                for hab in habilitacoes.findall('DadosHabilitacoes'):
                    hab_id = self._get_text_value(hab, 'HabId')
                    if hab_id:
                        existing = self.session.query(DeputadoHabilitacao).filter(
                            DeputadoHabilitacao.deputado_id == deputy.id,
                            DeputadoHabilitacao.hab_id == int(float(hab_id))
                        ).first()
                        
                        if not existing:
                            qualification = DeputadoHabilitacao(
                                deputado_id=deputy.id,
                                hab_id=int(float(hab_id)),
                                hab_des=self._get_text_value(hab, 'HabDes'),
                                hab_tipo_id=self._parse_int(self._get_text_value(hab, 'HabTipoId')),
                                hab_estado=self._get_text_value(hab, 'HabEstado')
                            )
                            self.session.add(qualification)
            
            # Process Professional Roles (CadCargosFuncoes)
            cargos_funcoes = record.find('CadCargosFuncoes')
            if cargos_funcoes is not None:
                for cargo in cargos_funcoes.findall('DadosCargosFuncoes'):
                    fun_id = self._get_text_value(cargo, 'FunId')
                    if fun_id:
                        existing = self.session.query(DeputadoCargoFuncao).filter(
                            DeputadoCargoFuncao.deputado_id == deputy.id,
                            DeputadoCargoFuncao.fun_id == int(float(fun_id))
                        ).first()
                        
                        if not existing:
                            role = DeputadoCargoFuncao(
                                deputado_id=deputy.id,
                                fun_id=int(float(fun_id)),
                                fun_des=self._get_text_value(cargo, 'FunDes'),
                                fun_ordem=self._parse_int(self._get_text_value(cargo, 'FunOrdem')),
                                fun_antiga=self._get_text_value(cargo, 'FunAntiga')
                            )
                            self.session.add(role)
            
            # Process Titles/Awards (CadTitulos)
            titulos = record.find('CadTitulos')
            if titulos is not None:
                for titulo in titulos.findall('DadosTitulos'):
                    tit_id = self._get_text_value(titulo, 'TitId')
                    if tit_id:
                        existing = self.session.query(DeputadoTitulo).filter(
                            DeputadoTitulo.deputado_id == deputy.id,
                            DeputadoTitulo.tit_id == int(float(tit_id))
                        ).first()
                        
                        if not existing:
                            title = DeputadoTitulo(
                                deputado_id=deputy.id,
                                tit_id=int(float(tit_id)),
                                tit_des=self._get_text_value(titulo, 'TitDes'),
                                tit_ordem=self._parse_int(self._get_text_value(titulo, 'TitOrdem'))
                            )
                            self.session.add(title)
            
            # Process Decorations (CadCondecoracoes)
            condecoracoes = record.find('CadCondecoracoes')
            if condecoracoes is not None:
                for cond in condecoracoes.findall('DadosCondecoracoes'):
                    cod_id = self._get_text_value(cond, 'CodId')
                    if cod_id:
                        existing = self.session.query(DeputadoCondecoracao).filter(
                            DeputadoCondecoracao.deputado_id == deputy.id,
                            DeputadoCondecoracao.cod_id == int(float(cod_id))
                        ).first()
                        
                        if not existing:
                            decoration = DeputadoCondecoracao(
                                deputado_id=deputy.id,
                                cod_id=int(float(cod_id)),
                                cod_des=self._get_text_value(cond, 'CodDes'),
                                cod_ordem=self._parse_int(self._get_text_value(cond, 'CodOrdem'))
                            )
                            self.session.add(decoration)
            
            # Process Published Works (CadObrasPublicadas)
            obras = record.find('CadObrasPublicadas')
            if obras is not None:
                for obra in obras.findall('DadosObrasPublicadas'):
                    pub_id = self._get_text_value(obra, 'PubId')
                    if pub_id:
                        existing = self.session.query(DeputadoObraPublicada).filter(
                            DeputadoObraPublicada.deputado_id == deputy.id,
                            DeputadoObraPublicada.pub_id == int(float(pub_id))
                        ).first()
                        
                        if not existing:
                            publication = DeputadoObraPublicada(
                                deputado_id=deputy.id,
                                pub_id=int(float(pub_id)),
                                pub_des=self._get_text_value(obra, 'PubDes'),
                                pub_ordem=self._parse_int(self._get_text_value(obra, 'PubOrdem'))
                            )
                            self.session.add(publication)
            
            # Process Legislative Mandates (CadDeputadoLegis)
            legislaturas = record.find('CadDeputadoLegis')
            if legislaturas is not None:
                for mandato in legislaturas.findall('DadosDeputadoLegis'):
                    leg_des = self._get_text_value(mandato, 'LegDes')
                    ce_des = self._get_text_value(mandato, 'CeDes')
                    
                    if leg_des:
                        existing = self.session.query(DeputadoMandatoLegislativo).filter(
                            DeputadoMandatoLegislativo.deputado_id == deputy.id,
                            DeputadoMandatoLegislativo.leg_des == leg_des,
                            DeputadoMandatoLegislativo.ce_des == ce_des
                        ).first()
                        
                        if not existing:
                            mandate = DeputadoMandatoLegislativo(
                                deputado_id=deputy.id,
                                dep_nome_parlamentar=self._get_text_value(mandato, 'DepNomeParlamentar'),
                                leg_des=leg_des,
                                ce_des=ce_des,
                                par_sigla=self._get_text_value(mandato, 'ParSigla'),
                                par_des=self._get_text_value(mandato, 'ParDes'),
                                gp_sigla=self._get_text_value(mandato, 'GpSigla'),
                                gp_des=self._get_text_value(mandato, 'GpDes'),
                                ind_des=self._get_text_value(mandato, 'IndDes'),  # VIII Legislature field
                                ind_data=self._parse_date(self._get_text_value(mandato, 'IndData'))  # VIII Legislature field
                            )
                            self.session.add(mandate)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing VIII Legislature biographical record: {e}")
            return False
    
    def _process_registo_interesses_v2(self, record: ET.Element, file_info: Dict) -> bool:
        """Process Interest Registry V2 record"""
        try:
            from database.models import RegistoInteressesV2, Deputado
            
            cad_id = self._get_text_value(record, 'cadId')
            if not cad_id:
                return False
                
            cad_id = int(float(cad_id))
            
            # Find the deputy
            deputy = self.session.query(Deputado).filter(Deputado.id_cadastro == cad_id).first()
            if not deputy:
                logger.warning(f"Deputy with id_cadastro {cad_id} not found for Interest Registry V2")
                return False
            
            # Check if already exists
            existing = self.session.query(RegistoInteressesV2).filter(
                RegistoInteressesV2.deputado_id == deputy.id,
                RegistoInteressesV2.cad_id == cad_id
            ).first()
            
            if not existing:
                interest_registry = RegistoInteressesV2(
                    deputado_id=deputy.id,
                    cad_id=cad_id,
                    cad_estado_civil_cod=self._get_text_value(record, 'cadEstadoCivilCod'),
                    cad_nome_completo=self._get_text_value(record, 'cadNomeCompleto'),  # New I Legislature field
                    cad_actividade_profissional=self._get_text_value(record, 'cadActividadeProfissional'),  # New I Legislature field
                    cad_estado_civil_des=self._get_text_value(record, 'cadEstadoCivilDes')  # New I Legislature field
                )
                self.session.add(interest_registry)
                
                # Also update deputy's marital status
                deputy.estado_civil_cod = self._get_text_value(record, 'cadEstadoCivilCod') or deputy.estado_civil_cod
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Interest Registry V2: {e}")
            return False
    
    def _get_text_value(self, element: ET.Element, tag: str) -> Optional[str]:
        """Get text value from XML element"""
        if element is None:
            return None
        child = element.find(tag)
        return child.text.strip() if child is not None and child.text else None
    
    def _parse_int(self, value: str) -> Optional[int]:
        """Parse integer from string"""
        if not value:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date from string"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    
    def _extract_legislature_from_path(self, file_path: str) -> str:
        """Extract legislature name from file path for accurate logging"""
        if not file_path:
            return "Unknown Legislature"
        
        import re
        # Try to match patterns like "V_Legislatura", "XIII_Legislatura", "RegistoBiograficoXIII.xml", etc.
        legislature_match = re.search(r'([IVX]+)_Legislatura|RegistoBiografico([IVX]+)\.xml|Legislatura_([IVX]+)', file_path, re.IGNORECASE)
        
        if legislature_match:
            # Get the first non-None group
            legislature_roman = legislature_match.group(1) or legislature_match.group(2) or legislature_match.group(3)
            return f"{legislature_roman} Legislature"
        
        # Try to match patterns like "Constituinte"
        if re.search(r'Constituinte', file_path, re.IGNORECASE):
            return "Constituinte"
            
        return "Unknown Legislature"
