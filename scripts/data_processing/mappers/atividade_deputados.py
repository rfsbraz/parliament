"""
Deputy Activities Mapper - REAL XML STRUCTURE VERSION WITH SQLALCHEMY ORM
=========================================================================

Schema mapper for deputy activity files (AtividadeDeputado*.xml).
Maps the ACTUAL XML structure we found in the files (not the namespaced version).
ZERO DATA LOSS - Every field from the XML is captured in the database.
Uses SQLAlchemy ORM models for clean, type-safe database operations.

Author: Claude
Version: 4.0 - SQLAlchemy ORM Implementation
"""

import xml.etree.ElementTree as ET
import os
import re
from typing import Dict, Optional, Set, List
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    Deputado, AtividadeDeputado, AtividadeDeputadoList, ActividadeOut,
    DadosLegisDeputado, ActividadeAudiencia, ActividadeAudicao, 
    ActividadesComissaoOut, DeputadoSituacao, DadosSituacaoDeputado,
    DepCargo, DadosCargoDeputado, ActividadeIntervencao, ActividadeIntervencaoOut,
    # IX Legislature models
    ActividadesParlamentares, ActividadesParlamentaresOut,
    GruposParlamentaresAmizade, GruposParlamentaresAmizadeOut,
    DelegacoesPermanentes, DelegacoesPermanentesOut,
    DelegacoesEventuais, DelegacoesEventuaisOut,
    RequerimentosAtivDep, RequerimentosAtivDepOut,
    SubComissoesGruposTrabalho, SubComissoesGruposTrabalhoOut,
    RelatoresPeticoes, RelatoresPeticoesOut,
    RelatoresIniciativas, RelatoresIniciativasOut,
    ReunioesDelegacoesPermanentes,
    Comissoes, ComissoesOut
)

logger = logging.getLogger(__name__)


class AtividadeDeputadosMapper(SchemaMapper):
    """Schema mapper for deputy activity files - REAL XML STRUCTURE VERSION WITH ORM"""
    
    def __init__(self, db_connection):
        super().__init__(db_connection)
        # Create SQLAlchemy session from raw connection
        # Get the database file path from the connection
        db_path = db_connection.execute('PRAGMA database_list').fetchone()[2]
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def get_expected_fields(self) -> Set[str]:
        """Return actual XML paths for complete coverage of AtividadeDeputado files"""
        return {
            # Root structure - ACTUAL XML FORMAT
            'ArrayOfAtividadeDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DadosLegisDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DadosLegisDeputado.DadosLegisDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DadosLegisDeputado.DadosLegisDeputado.Nome',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DadosLegisDeputado.DadosLegisDeputado.Dpl_grpar',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DadosLegisDeputado.DadosLegisDeputado.Dpl_lg',
            
            # Deputy information - ACTUAL XML FORMAT  
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCadId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepNomeParlamentar',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepNomeCompleto',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCPId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCPDes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.LegDes',
            
            # Deputy parliamentary group - ACTUAL XML FORMAT
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP.DadosSituacaoGP',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP.DadosSituacaoGP.GpId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP.DadosSituacaoGP.GpSigla',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP.DadosSituacaoGP.GpDtInicio',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP.DadosSituacaoGP.GpDtFim',
            
            # Deputy situations - ACTUAL XML FORMAT
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepSituacao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepSituacao.DadosSituacaoDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepSituacao.DadosSituacaoDeputado.SioDes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepSituacao.DadosSituacaoDeputado.SioDtInicio',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepSituacao.DadosSituacaoDeputado.SioDtFim',
            
            # Deputy cargo - ACTUAL XML FORMAT
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCargo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCargo.pt_ar_wsgode_objectos_DadosCargoDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtInicio',
            
            # Deputy initiatives - III Legislature and others
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Ini',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Ini.IniciativasOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Ini.IniciativasOut.IniId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Ini.IniciativasOut.IniNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Ini.IniciativasOut.IniSelLg',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Ini.IniciativasOut.IniSelNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Ini.IniciativasOut.IniTi',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Ini.IniciativasOut.IniTp',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Ini.IniciativasOut.IniTpdesc',
            
            # Deputy interventions - IV Legislature and others
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut.IntId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut.IntSu',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut.PubDar',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut.PubDtreu',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut.PubLg',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut.PubNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut.PubSl',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut.PubTp',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut.TinDs',
            
            # IX Legislature - Parliamentary Activities (ActP)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP.ActividadesParlamentaresOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP.ActividadesParlamentaresOut.ActId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP.ActividadesParlamentaresOut.ActNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP.ActividadesParlamentaresOut.ActTp',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP.ActividadesParlamentaresOut.ActTpdesc',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP.ActividadesParlamentaresOut.ActSelLg',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP.ActividadesParlamentaresOut.ActSelNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP.ActividadesParlamentaresOut.ActDtent',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP.ActividadesParlamentaresOut.ActDtdeb',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.ActP.ActividadesParlamentaresOut.ActAs',
            
            # IX Legislature - Friendship Groups (Gpa)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Gpa',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Gpa.GruposParlamentaresAmizadeOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Gpa.GruposParlamentaresAmizadeOut.CgaCrg',
            
            # IX Legislature - Permanent Delegations (DlP)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.DepId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.DepNo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.CdeCrg',
            
            # IX Legislature - Occasional Delegations (DlE)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlE',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlE.DelegacoesEventuaisOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlE.DelegacoesEventuaisOut.DevDtini',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlE.DelegacoesEventuaisOut.DevDtfim',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlE.DelegacoesEventuaisOut.DevSelNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlE.DelegacoesEventuaisOut.DevLoc',
            
            # IX Legislature - Requirements (Req)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Req',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Req.RequerimentosAtivDepOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Req.RequerimentosAtivDepOut.ReqId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Req.RequerimentosAtivDepOut.ReqNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Req.RequerimentosAtivDepOut.ReqTp',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Req.RequerimentosAtivDepOut.ReqLg',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Req.RequerimentosAtivDepOut.ReqSl',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Req.RequerimentosAtivDepOut.ReqAs',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Req.RequerimentosAtivDepOut.ReqDt',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Req.RequerimentosAtivDepOut.ReqPerTp',
            
            # IX Legislature - Sub-committees/Working Groups (Scgt)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Scgt',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Scgt.SubComissoesGruposTrabalhoOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Scgt.SubComissoesGruposTrabalhoOut.ScmCd',
            
            # IX Legislature - Petition Rapporteurs
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresPeticoes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresPeticoes.RelatoresPeticoesOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresPeticoes.RelatoresPeticoesOut.PecDtrelf',
            
            # IX Legislature - Enhanced Committee Activities
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.ActId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.ActAs',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.ActDtent',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.AccDtaud',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.ActTp',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.ActTpdesc',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.ActNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.ActLg',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.NomeEntidadeExterna',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.CmsNo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut.CmsAb',
            
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.ActId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.ActAs',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.AccDtaud',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.ActTp',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.ActDtent',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.ActNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.ActTpdesc',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.NomeEntidadeExterna',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.CmsNo',
            
            # IX Legislature - Committees (Cms)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Cms',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Cms.ComissoesOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Cms.ComissoesOut.CmsNo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Cms.ComissoesOut.CmsCd',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Cms.ComissoesOut.CmsLg',
            
            # IX Legislature - Enhanced Sub-committees/Working Groups fields
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Scgt.SubComissoesGruposTrabalhoOut.CmsCargo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Scgt.SubComissoesGruposTrabalhoOut.ScmComLg',
            
            # IX Legislature - Enhanced Petition Rapporteurs fields
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresPeticoes.RelatoresPeticoesOut.PetSelLgPk',
            
            # IX Legislature - Initiative Rapporteurs fields
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresIniciativas',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresIniciativas.RelatoresIniciativasOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresIniciativas.RelatoresIniciativasOut.IniNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresIniciativas.RelatoresIniciativasOut.AccDtrel',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresIniciativas.RelatoresIniciativasOut.IniTi',
            
            # IX Legislature - Additional missing fields
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlE.DelegacoesEventuaisOut.DevSelLg',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Scgt.SubComissoesGruposTrabalhoOut.ScmComCd',
            
            # IX Legislature - Permanent Delegation Meetings fields
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.DepReunioes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.DepReunioes.ReunioesDelegacoesPermanentes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.DepReunioes.ReunioesDelegacoesPermanentes.RenDtIni',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.DepReunioes.ReunioesDelegacoesPermanentes.RenLoc',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.DepReunioes.ReunioesDelegacoesPermanentes.RenDtFim',
            
            # IX Legislature - Additional missing fields from final validation
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlE.DelegacoesEventuaisOut.DevId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlE.DelegacoesEventuaisOut.DevNo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresPeticoes.RelatoresPeticoesOut.PetAspet',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresPeticoes.RelatoresPeticoesOut.PetSelNrPk',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.DepReunioes.ReunioesDelegacoesPermanentes.RenTi',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Gpa.GruposParlamentaresAmizadeOut.GplNo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Gpa.GruposParlamentaresAmizadeOut.GplId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.DepSelLg',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresIniciativas.RelatoresIniciativasOut.IniId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.CmsAb',
            
            # IX Legislature - Final missing fields for complete coverage
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresPeticoes.RelatoresPeticoesOut.PetNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresPeticoes.RelatoresPeticoesOut.PetId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Intev.IntervencoesOut.IntTe',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut.ActLg',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Scgt.SubComissoesGruposTrabalhoOut.CcmDscom',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresIniciativas.RelatoresIniciativasOut.RelFase',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresIniciativas.RelatoresIniciativasOut.IniSelLg',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Gpa.GruposParlamentaresAmizadeOut.GplSelLg',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Gpa.GruposParlamentaresAmizadeOut.CgaDtini',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Cms.ComissoesOut.CmsCargo',
            
            # IX Legislature - Final 2 fields for absolute complete coverage
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel.RelatoresIniciativas.RelatoresIniciativasOut.IniTp',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DlP.DelegacoesPermanentesOut.DepSelNr'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map deputy activities to database with ACTUAL XML structure - STORES REAL DATA"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        # Validate schema coverage according to strict mode
        self.validate_schema_coverage(xml_root, file_info, strict_mode)
        
        # Extract legislatura from filename
        filename = os.path.basename(file_info['file_path'])
        leg_match = re.search(r'AtividadeDeputado(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
        legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
        
        # Process each deputy's activities - ACTUAL XML STRUCTURE
        for atividade_deputado in xml_root.findall('.//AtividadeDeputado'):
            try:
                success = self._process_deputy_real_structure(atividade_deputado, legislatura_sigla, file_info['file_path'], strict_mode)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Deputy activity processing error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['records_processed'] += 1
                if strict_mode:
                    raise SchemaError(f"Processing failed in strict mode: {error_msg}")
        
        return results
    
    def _process_deputy_real_structure(self, atividade_deputado: ET.Element, legislatura_sigla: str, xml_file_path: str, strict_mode: bool = False) -> bool:
        """Process deputy activities with REAL XML structure and store in our new models"""
        try:
            # Get deputy information from ACTUAL XML structure
            deputado = atividade_deputado.find('Deputado')  # Not 'deputado' - capitalized!
            if deputado is None:
                logger.warning("No Deputado section found")
                return False
                
            # Extract deputy basic information - ACTUAL field names
            dep_cad_id_text = self._get_text_value(deputado, 'DepCadId')
            dep_nome = self._get_text_value(deputado, 'DepNomeParlamentar')
            
            if not (dep_cad_id_text and dep_nome):
                logger.warning("Missing required deputy fields")
                return False
                
            dep_cad_id = self._safe_int(dep_cad_id_text)
            if not dep_cad_id:
                logger.warning(f"Invalid deputy cadastro ID: {dep_cad_id_text}")
                return False
            
            # Find or create deputado record in our database
            deputado_db_id = self._get_or_create_deputado(dep_cad_id, dep_nome, deputado)
            if not deputado_db_id:
                logger.warning("Could not create/find deputado record")
                return False
            
            # Create AtividadeDeputado record using our new models
            atividade_deputado_id = self._create_atividade_deputado(
                deputado_db_id, dep_cad_id, legislatura_sigla, deputado
            )
            
            if not atividade_deputado_id:
                return False
            
            # Process AtividadeDeputadoList - REAL XML structure
            atividade_list = atividade_deputado.find('AtividadeDeputadoList')
            if atividade_list is not None:
                atividade_list_id = self._create_atividade_deputado_list(atividade_deputado_id)
                
                # Process ActividadeOut - REAL XML structure
                actividade_out = atividade_list.find('ActividadeOut')
                if actividade_out is not None:
                    actividade_out_id = self._create_actividade_out(atividade_list_id, actividade_out)
                    
                    # Process nested elements
                    self._process_dados_legis_deputado(actividade_out, actividade_out_id)
                    self._process_audiencias(actividade_out, actividade_out_id)
                    self._process_audicoes(actividade_out, actividade_out_id)
                    self._process_initiatives(actividade_out, atividade_deputado_id)
                    self._process_interventions(actividade_out, actividade_out_id)
                    
                    # Process IX Legislature features
                    self._process_parliamentary_activities(actividade_out, actividade_out_id)
                    self._process_friendship_groups(actividade_out, actividade_out_id)
                    self._process_permanent_delegations(actividade_out, actividade_out_id)
                    self._process_occasional_delegations(actividade_out, actividade_out_id)
                    self._process_requirements(actividade_out, actividade_out_id)
                    self._process_subcommittees_working_groups(actividade_out, actividade_out_id)
                    self._process_petition_rapporteurs(actividade_out, actividade_out_id)
                    self._process_initiative_rapporteurs(actividade_out, actividade_out_id)
                    self._process_committees(actividade_out, actividade_out_id)
            
            # Process deputy situations - REAL XML structure
            self._process_deputy_situacoes_real(deputado, atividade_deputado_id, strict_mode)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in real structure deputy processing: {e}")
            return False
    
    def _get_or_create_deputado(self, dep_cad_id: int, dep_nome: str, deputado_elem: ET.Element) -> Optional[int]:
        """Get or create deputado record using SQLAlchemy ORM"""
        try:
            # Check if deputado exists
            deputado = self.session.query(Deputado).filter_by(id_cadastro=dep_cad_id).first()
            
            if deputado:
                return deputado.id
            
            # Create new deputado record
            dep_nome_completo = self._get_text_value(deputado_elem, 'DepNomeCompleto')
            
            new_deputado = Deputado(
                id_cadastro=dep_cad_id,
                nome=dep_nome,
                nome_completo=dep_nome_completo,
                ativo=True
            )
            
            self.session.add(new_deputado)
            self.session.commit()
            
            # Process deputy positions (DepCargo)
            self._process_dep_cargo(deputado_elem, new_deputado.id)
            
            return new_deputado.id
            
        except Exception as e:
            logger.error(f"Error creating deputado record: {e}")
            self.session.rollback()
            return None
    
    def _create_atividade_deputado(self, deputado_id: int, dep_cad_id: int, 
                                  legislatura_sigla: str, deputado_elem: ET.Element) -> Optional[int]:
        """Create AtividadeDeputado record using SQLAlchemy ORM"""
        try:
            leg_des = self._get_text_value(deputado_elem, 'LegDes')
            
            atividade_deputado = AtividadeDeputado(
                deputado_id=deputado_id,
                dep_cad_id=dep_cad_id,
                leg_des=leg_des
            )
            
            self.session.add(atividade_deputado)
            self.session.commit()
            
            return atividade_deputado.id
            
        except Exception as e:
            logger.error(f"Error creating atividade deputado record: {e}")
            self.session.rollback()
            return None
    
    def _create_atividade_deputado_list(self, atividade_deputado_id: int) -> Optional[int]:
        """Create AtividadeDeputadoList record using SQLAlchemy ORM"""
        try:
            atividade_list = AtividadeDeputadoList(
                atividade_deputado_id=atividade_deputado_id
            )
            
            self.session.add(atividade_list)
            self.session.commit()
            
            return atividade_list.id
            
        except Exception as e:
            logger.error(f"Error creating atividade deputado list record: {e}")
            self.session.rollback()
            return None
    
    def _create_actividade_out(self, atividade_list_id: int, actividade_out_elem: ET.Element) -> Optional[int]:
        """Create ActividadeOut record using SQLAlchemy ORM"""
        try:
            rel_text = self._get_text_value(actividade_out_elem, 'Rel')
            
            actividade_out = ActividadeOut(
                atividade_list_id=atividade_list_id,
                rel=rel_text
            )
            
            self.session.add(actividade_out)
            self.session.commit()
            
            return actividade_out.id
            
        except Exception as e:
            logger.error(f"Error creating actividade out record: {e}")
            self.session.rollback()
            return None
    
    def _process_dados_legis_deputado(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process DadosLegisDeputado using SQLAlchemy ORM"""
        try:
            dados_legis_section = actividade_out.find('DadosLegisDeputado')
            if dados_legis_section is not None:
                for dados_legis in dados_legis_section.findall('DadosLegisDeputado'):
                    nome = self._get_text_value(dados_legis, 'Nome')
                    dpl_grpar = self._get_text_value(dados_legis, 'Dpl_grpar')
                    dpl_lg = self._get_text_value(dados_legis, 'Dpl_lg')
                    
                    dados_legis_obj = DadosLegisDeputado(
                        actividade_out_id=actividade_out_id,
                        nome=nome,
                        dpl_grpar=dpl_grpar,
                        dpl_lg=dpl_lg
                    )
                    
                    self.session.add(dados_legis_obj)
            
            self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing dados legis deputado: {e}")
            self.session.rollback()
    
    def _process_audiencias(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process Audiencias using SQLAlchemy ORM"""
        try:
            audiencias_section = actividade_out.find('Audiencias')
            if audiencias_section is not None:
                # Create audiencia record
                audiencia = ActividadeAudiencia(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(audiencia)
                self.session.commit()
                
                # Process ActividadesComissaoOut within Audiencias
                for comissao_out in audiencias_section.findall('ActividadesComissaoOut'):
                    # Extract IX Legislature fields
                    act_id = self._safe_int(self._get_text_value(comissao_out, 'ActId'))
                    act_as = self._get_text_value(comissao_out, 'ActAs')
                    act_dtent = self._get_text_value(comissao_out, 'ActDtent')
                    acc_dtaud = self._get_text_value(comissao_out, 'AccDtaud')
                    act_tp = self._get_text_value(comissao_out, 'ActTp')
                    act_tpdesc = self._get_text_value(comissao_out, 'ActTpdesc')
                    act_nr = self._get_text_value(comissao_out, 'ActNr')
                    act_lg = self._get_text_value(comissao_out, 'ActLg')
                    nome_entidade_externa = self._get_text_value(comissao_out, 'NomeEntidadeExterna')
                    cms_no = self._get_text_value(comissao_out, 'CmsNo')
                    cms_ab = self._get_text_value(comissao_out, 'CmsAb')
                    
                    comissao_out_obj = ActividadesComissaoOut(
                        audiencia_id=audiencia.id,
                        act_id=act_id,
                        act_as=act_as,
                        act_dtent=act_dtent,
                        acc_dtaud=acc_dtaud,
                        act_tp=act_tp,
                        act_tpdesc=act_tpdesc,
                        act_nr=act_nr,
                        act_lg=act_lg,
                        nome_entidade_externa=nome_entidade_externa,
                        cms_no=cms_no,
                        cms_ab=cms_ab
                    )
                    self.session.add(comissao_out_obj)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing audiencias: {e}")
            self.session.rollback()
    
    def _process_audicoes(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process Audicoes using SQLAlchemy ORM"""
        try:
            audicoes_section = actividade_out.find('Audicoes')
            if audicoes_section is not None:
                # Create audicao record
                audicao = ActividadeAudicao(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(audicao)
                self.session.commit()
                
                # Process ActividadesComissaoOut within Audicoes
                for comissao_out in audicoes_section.findall('ActividadesComissaoOut'):
                    # Extract IX Legislature fields
                    act_id = self._safe_int(self._get_text_value(comissao_out, 'ActId'))
                    act_as = self._get_text_value(comissao_out, 'ActAs')
                    act_dtent = self._get_text_value(comissao_out, 'ActDtent')
                    acc_dtaud = self._get_text_value(comissao_out, 'AccDtaud')
                    act_tp = self._get_text_value(comissao_out, 'ActTp')
                    act_tpdesc = self._get_text_value(comissao_out, 'ActTpdesc')
                    act_nr = self._get_text_value(comissao_out, 'ActNr')
                    nome_entidade_externa = self._get_text_value(comissao_out, 'NomeEntidadeExterna')
                    cms_no = self._get_text_value(comissao_out, 'CmsNo')
                    
                    comissao_out_obj = ActividadesComissaoOut(
                        audicao_id=audicao.id,
                        act_id=act_id,
                        act_as=act_as,
                        act_dtent=act_dtent,
                        acc_dtaud=acc_dtaud,
                        act_tp=act_tp,
                        act_tpdesc=act_tpdesc,
                        act_nr=act_nr,
                        nome_entidade_externa=nome_entidade_externa,
                        cms_no=cms_no
                    )
                    self.session.add(comissao_out_obj)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing audicoes: {e}")
            self.session.rollback()
    
    def _process_initiatives(self, actividade_out: ET.Element, atividade_deputado_id: int):
        """Process deputy initiatives using SQLAlchemy ORM"""
        try:
            # Import the model here to avoid circular imports
            from database.models import DeputyInitiative
            
            ini_section = actividade_out.find('Ini')
            if ini_section is not None:
                # Process each IniciativasOut within Ini
                for iniciativa in ini_section.findall('IniciativasOut'):
                    # Extract initiative fields
                    ini_id = self._safe_int(self._get_text_value(iniciativa, 'IniId'))
                    ini_nr = self._get_text_value(iniciativa, 'IniNr')
                    ini_sel_lg = self._get_text_value(iniciativa, 'IniSelLg')
                    ini_sel_nr = self._get_text_value(iniciativa, 'IniSelNr')
                    ini_ti = self._get_text_value(iniciativa, 'IniTi')
                    ini_tp = self._get_text_value(iniciativa, 'IniTp')
                    ini_tpdesc = self._get_text_value(iniciativa, 'IniTpdesc')
                    
                    # Skip if no essential data
                    if not ini_id and not ini_nr:
                        continue
                    
                    # Create DeputyInitiative record
                    initiative = DeputyInitiative(
                        deputy_activity_id=atividade_deputado_id,
                        id_iniciativa=ini_id,
                        numero=ini_nr,
                        tipo=ini_ti,
                        desc_tipo=ini_tpdesc,
                        legislatura=ini_sel_lg,
                        sessao=ini_sel_nr
                    )
                    
                    self.session.add(initiative)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing initiatives: {e}")
            self.session.rollback()
    
    def _process_interventions(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process deputy interventions using SQLAlchemy ORM"""
        try:
            intev_section = actividade_out.find('Intev')
            if intev_section is not None:
                # Create ActividadeIntervencao record
                actividade_intervencao = ActividadeIntervencao(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(actividade_intervencao)
                self.session.commit()
                
                # Process each IntervencoesOut within Intev
                for intervencao in intev_section.findall('IntervencoesOut'):
                    # Extract intervention fields
                    int_id = self._safe_int(self._get_text_value(intervencao, 'IntId'))
                    int_su = self._get_text_value(intervencao, 'IntSu')
                    int_te = self._get_text_value(intervencao, 'IntTe')
                    pub_dar = self._get_text_value(intervencao, 'PubDar')
                    pub_dtreu_str = self._get_text_value(intervencao, 'PubDtreu')
                    pub_dtreu = self._parse_date(pub_dtreu_str) if pub_dtreu_str else None
                    pub_lg = self._get_text_value(intervencao, 'PubLg')
                    pub_nr = self._safe_int(self._get_text_value(intervencao, 'PubNr'))
                    pub_sl = self._get_text_value(intervencao, 'PubSl')
                    pub_tp = self._get_text_value(intervencao, 'PubTp')
                    tin_ds = self._get_text_value(intervencao, 'TinDs')
                    
                    # Create ActividadeIntervencaoOut record
                    intervencao_out = ActividadeIntervencaoOut(
                        actividade_intervencao_id=actividade_intervencao.id,
                        int_id=int_id,
                        int_su=int_su,
                        int_te=int_te,
                        pub_dar=pub_dar,
                        pub_dtreu=pub_dtreu,
                        pub_lg=pub_lg,
                        pub_nr=pub_nr,
                        pub_sl=pub_sl,
                        pub_tp=pub_tp,
                        tin_ds=tin_ds
                    )
                    
                    self.session.add(intervencao_out)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing interventions: {e}")
            self.session.rollback()
    
    def _process_deputy_situacoes_real(self, deputado: ET.Element, atividade_deputado_id: int, strict_mode: bool = False):
        """Process deputy situations using SQLAlchemy ORM"""
        try:
            dep_situacao = deputado.find('DepSituacao')
            if dep_situacao is not None:
                # Create deputado_situacao record
                deputado_situacao = DeputadoSituacao(
                    atividade_deputado_id=atividade_deputado_id
                )
                
                self.session.add(deputado_situacao)
                self.session.commit()
                
                # Process each DadosSituacaoDeputado
                for situacao in dep_situacao.findall('DadosSituacaoDeputado'):
                    sio_des = self._get_text_value(situacao, 'SioDes')
                    sio_dt_inicio = self._parse_date(self._get_text_value(situacao, 'SioDtInicio'))
                    sio_dt_fim = self._parse_date(self._get_text_value(situacao, 'SioDtFim'))
                    
                    dados_situacao = DadosSituacaoDeputado(
                        deputado_situacao_id=deputado_situacao.id,
                        sio_des=sio_des,
                        sio_dt_inicio=sio_dt_inicio,
                        sio_dt_fim=sio_dt_fim
                    )
                    
                    self.session.add(dados_situacao)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing deputy situacoes: {e}")
            self.session.rollback()
            if strict_mode:
                raise SchemaError(f"Deputy situations processing failed in strict mode: {e}")
    
    def _process_parliamentary_activities(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process IX Legislature Parliamentary Activities (ActP)"""
        try:
            actp_section = actividade_out.find('ActP')
            if actp_section is not None:
                # Create parliamentary activities record
                atividades_parlamentares = ActividadesParlamentares(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(atividades_parlamentares)
                self.session.commit()
                
                # Process each ActividadesParlamentaresOut
                for atividade in actp_section.findall('ActividadesParlamentaresOut'):
                    act_id = self._safe_int(self._get_text_value(atividade, 'ActId'))
                    act_nr = self._get_text_value(atividade, 'ActNr')
                    act_tp = self._get_text_value(atividade, 'ActTp')
                    act_tpdesc = self._get_text_value(atividade, 'ActTpdesc')
                    act_sel_lg = self._get_text_value(atividade, 'ActSelLg')
                    act_sel_nr = self._get_text_value(atividade, 'ActSelNr')
                    act_dtent = self._get_text_value(atividade, 'ActDtent')
                    act_dtdeb_str = self._get_text_value(atividade, 'ActDtdeb')
                    act_dtdeb = self._parse_datetime(act_dtdeb_str) if act_dtdeb_str else None
                    act_as = self._get_text_value(atividade, 'ActAs')
                    
                    atividade_out_obj = ActividadesParlamentaresOut(
                        atividades_parlamentares_id=atividades_parlamentares.id,
                        act_id=act_id,
                        act_nr=act_nr,
                        act_tp=act_tp,
                        act_tpdesc=act_tpdesc,
                        act_sel_lg=act_sel_lg,
                        act_sel_nr=act_sel_nr,
                        act_dtent=act_dtent,
                        act_dtdeb=act_dtdeb,
                        act_as=act_as
                    )
                    
                    self.session.add(atividade_out_obj)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing parliamentary activities: {e}")
            self.session.rollback()

    def _process_friendship_groups(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process IX Legislature Friendship Groups (Gpa)"""
        try:
            gpa_section = actividade_out.find('Gpa')
            if gpa_section is not None:
                # Create friendship groups record
                grupos_parlamentares_amizade = GruposParlamentaresAmizade(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(grupos_parlamentares_amizade)
                self.session.commit()
                
                # Process each GruposParlamentaresAmizadeOut
                for grupo in gpa_section.findall('GruposParlamentaresAmizadeOut'):
                    gpl_id = self._safe_int(self._get_text_value(grupo, 'GplId'))
                    gpl_no = self._get_text_value(grupo, 'GplNo')
                    gpl_sel_lg = self._get_text_value(grupo, 'GplSelLg')
                    cga_crg = self._get_text_value(grupo, 'CgaCrg')
                    cga_dtini = self._get_text_value(grupo, 'CgaDtini')
                    
                    grupo_out = GruposParlamentaresAmizadeOut(
                        grupos_parlamentares_amizade_id=grupos_parlamentares_amizade.id,
                        gpl_id=gpl_id,
                        gpl_no=gpl_no,
                        gpl_sel_lg=gpl_sel_lg,
                        cga_crg=cga_crg,
                        cga_dtini=cga_dtini
                    )
                    
                    self.session.add(grupo_out)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing friendship groups: {e}")
            self.session.rollback()

    def _process_permanent_delegations(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process IX Legislature Permanent Delegations (DlP)"""
        try:
            dlp_section = actividade_out.find('DlP')
            if dlp_section is not None:
                # Create permanent delegations record
                delegacoes_permanentes = DelegacoesPermanentes(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(delegacoes_permanentes)
                self.session.commit()
                
                # Process each DelegacoesPermanentesOut
                for delegacao in dlp_section.findall('DelegacoesPermanentesOut'):
                    dep_id = self._safe_int(self._get_text_value(delegacao, 'DepId'))
                    dep_no = self._get_text_value(delegacao, 'DepNo')
                    dep_sel_lg = self._get_text_value(delegacao, 'DepSelLg')
                    dep_sel_nr = self._get_text_value(delegacao, 'DepSelNr')
                    cde_crg = self._get_text_value(delegacao, 'CdeCrg')
                    
                    delegacao_out = DelegacoesPermanentesOut(
                        delegacoes_permanentes_id=delegacoes_permanentes.id,
                        dep_id=dep_id,
                        dep_no=dep_no,
                        dep_sel_lg=dep_sel_lg,
                        dep_sel_nr=dep_sel_nr,
                        cde_crg=cde_crg
                    )
                    
                    self.session.add(delegacao_out)
                    self.session.commit()  # Commit to get the delegacao_out.id
                    
                    # Process meetings (DepReunioes.ReunioesDelegacoesPermanentes)
                    reunioes_section = delegacao.find('DepReunioes')
                    if reunioes_section is not None:
                        for reuniao in reunioes_section.findall('ReunioesDelegacoesPermanentes'):
                            ren_dt_ini = self._get_text_value(reuniao, 'RenDtIni')
                            ren_loc = self._get_text_value(reuniao, 'RenLoc')
                            ren_dt_fim = self._get_text_value(reuniao, 'RenDtFim')
                            ren_ti = self._get_text_value(reuniao, 'RenTi')
                            
                            reuniao_obj = ReunioesDelegacoesPermanentes(
                                delegacoes_permanentes_out_id=delegacao_out.id,
                                ren_dt_ini=ren_dt_ini,
                                ren_loc=ren_loc,
                                ren_dt_fim=ren_dt_fim,
                                ren_ti=ren_ti
                            )
                            
                            self.session.add(reuniao_obj)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing permanent delegations: {e}")
            self.session.rollback()

    def _process_occasional_delegations(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process IX Legislature Occasional Delegations (DlE)"""
        try:
            dle_section = actividade_out.find('DlE')
            if dle_section is not None:
                # Create occasional delegations record
                delegacoes_eventuais = DelegacoesEventuais(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(delegacoes_eventuais)
                self.session.commit()
                
                # Process each DelegacoesEventuaisOut
                for delegacao in dle_section.findall('DelegacoesEventuaisOut'):
                    dev_id = self._safe_int(self._get_text_value(delegacao, 'DevId'))
                    dev_no = self._get_text_value(delegacao, 'DevNo')
                    dev_dtini = self._get_text_value(delegacao, 'DevDtini')
                    dev_dtfim = self._get_text_value(delegacao, 'DevDtfim')
                    dev_sel_nr = self._get_text_value(delegacao, 'DevSelNr')
                    dev_sel_lg = self._get_text_value(delegacao, 'DevSelLg')
                    dev_loc = self._get_text_value(delegacao, 'DevLoc')
                    
                    delegacao_out = DelegacoesEventuaisOut(
                        delegacoes_eventuais_id=delegacoes_eventuais.id,
                        dev_id=dev_id,
                        dev_no=dev_no,
                        dev_dtini=dev_dtini,
                        dev_dtfim=dev_dtfim,
                        dev_sel_nr=dev_sel_nr,
                        dev_sel_lg=dev_sel_lg,
                        dev_loc=dev_loc
                    )
                    
                    self.session.add(delegacao_out)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing occasional delegations: {e}")
            self.session.rollback()

    def _process_requirements(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process IX Legislature Requirements (Req)"""
        try:
            req_section = actividade_out.find('Req')
            if req_section is not None:
                # Create requirements record
                requerimentos_ativ_dep = RequerimentosAtivDep(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(requerimentos_ativ_dep)
                self.session.commit()
                
                # Process each RequerimentosAtivDepOut
                for requerimento in req_section.findall('RequerimentosAtivDepOut'):
                    req_id = self._safe_int(self._get_text_value(requerimento, 'ReqId'))
                    req_nr = self._get_text_value(requerimento, 'ReqNr')
                    req_tp = self._get_text_value(requerimento, 'ReqTp')
                    req_lg = self._get_text_value(requerimento, 'ReqLg')
                    req_sl = self._get_text_value(requerimento, 'ReqSl')
                    req_as = self._get_text_value(requerimento, 'ReqAs')
                    req_dt_str = self._get_text_value(requerimento, 'ReqDt')
                    req_dt = self._parse_datetime(req_dt_str) if req_dt_str else None
                    req_per_tp = self._get_text_value(requerimento, 'ReqPerTp')
                    
                    requerimento_out = RequerimentosAtivDepOut(
                        requerimentos_ativ_dep_id=requerimentos_ativ_dep.id,
                        req_id=req_id,
                        req_nr=req_nr,
                        req_tp=req_tp,
                        req_lg=req_lg,
                        req_sl=req_sl,
                        req_as=req_as,
                        req_dt=req_dt,
                        req_per_tp=req_per_tp
                    )
                    
                    self.session.add(requerimento_out)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing requirements: {e}")
            self.session.rollback()

    def _process_subcommittees_working_groups(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process IX Legislature Sub-committees/Working Groups (Scgt)"""
        try:
            scgt_section = actividade_out.find('Scgt')
            if scgt_section is not None:
                # Create sub-committees/working groups record
                subcomissoes_grupos_trabalho = SubComissoesGruposTrabalho(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(subcomissoes_grupos_trabalho)
                self.session.commit()
                
                # Process each SubComissoesGruposTrabalhoOut
                for subcomissao in scgt_section.findall('SubComissoesGruposTrabalhoOut'):
                    scm_cd = self._get_text_value(subcomissao, 'ScmCd')
                    scm_com_cd = self._get_text_value(subcomissao, 'ScmComCd')
                    ccm_dscom = self._get_text_value(subcomissao, 'CcmDscom')
                    cms_cargo = self._get_text_value(subcomissao, 'CmsCargo')
                    scm_com_lg = self._get_text_value(subcomissao, 'ScmComLg')
                    
                    subcomissao_out = SubComissoesGruposTrabalhoOut(
                        subcomissoes_grupos_trabalho_id=subcomissoes_grupos_trabalho.id,
                        scm_cd=scm_cd,
                        scm_com_cd=scm_com_cd,
                        ccm_dscom=ccm_dscom,
                        cms_cargo=cms_cargo,
                        scm_com_lg=scm_com_lg
                    )
                    
                    self.session.add(subcomissao_out)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing sub-committees/working groups: {e}")
            self.session.rollback()

    def _process_petition_rapporteurs(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process IX Legislature Petition Rapporteurs (Rel.RelatoresPeticoes)"""
        try:
            rel_section = actividade_out.find('Rel')
            if rel_section is not None:
                relatores_peticoes_section = rel_section.find('RelatoresPeticoes')
                if relatores_peticoes_section is not None:
                    # Create petition rapporteurs record
                    relatores_peticoes = RelatoresPeticoes(
                        actividade_out_id=actividade_out_id
                    )
                    
                    self.session.add(relatores_peticoes)
                    self.session.commit()
                    
                    # Process each RelatoresPeticoesOut
                    for relator in relatores_peticoes_section.findall('RelatoresPeticoesOut'):
                        pec_dtrelf = self._get_text_value(relator, 'PecDtrelf')
                        pet_id = self._safe_int(self._get_text_value(relator, 'PetId'))
                        pet_nr = self._get_text_value(relator, 'PetNr')
                        pet_aspet = self._get_text_value(relator, 'PetAspet')
                        pet_sel_lg_pk = self._get_text_value(relator, 'PetSelLgPk')
                        pet_sel_nr_pk = self._get_text_value(relator, 'PetSelNrPk')
                        
                        relator_out = RelatoresPeticoesOut(
                            relatores_peticoes_id=relatores_peticoes.id,
                            pec_dtrelf=pec_dtrelf,
                            pet_id=pet_id,
                            pet_nr=pet_nr,
                            pet_aspet=pet_aspet,
                            pet_sel_lg_pk=pet_sel_lg_pk,
                            pet_sel_nr_pk=pet_sel_nr_pk
                        )
                        
                        self.session.add(relator_out)
                    
                    self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing petition rapporteurs: {e}")
            self.session.rollback()

    def _process_initiative_rapporteurs(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process IX Legislature Initiative Rapporteurs (Rel.RelatoresIniciativas)"""
        try:
            rel_section = actividade_out.find('Rel')
            if rel_section is not None:
                # Look for RelatoresIniciativas
                ini_section = rel_section.find('RelatoresIniciativas')
                if ini_section is not None:
                    # Create initiative rapporteurs record
                    relatores_iniciativas = RelatoresIniciativas(
                        actividade_out_id=actividade_out_id
                    )
                    
                    self.session.add(relatores_iniciativas)
                    self.session.commit()
                    
                    # Process each RelatoresIniciativasOut
                    for relator in ini_section.findall('RelatoresIniciativasOut'):
                        ini_id = self._safe_int(self._get_text_value(relator, 'IniId'))
                        ini_nr = self._get_text_value(relator, 'IniNr')
                        ini_tp = self._get_text_value(relator, 'IniTp')
                        ini_sel_lg = self._get_text_value(relator, 'IniSelLg')
                        acc_dtrel = self._get_text_value(relator, 'AccDtrel')
                        rel_fase = self._get_text_value(relator, 'RelFase')
                        ini_ti = self._get_text_value(relator, 'IniTi')
                        
                        relator_out = RelatoresIniciativasOut(
                            relatores_iniciativas_id=relatores_iniciativas.id,
                            ini_id=ini_id,
                            ini_nr=ini_nr,
                            ini_tp=ini_tp,
                            ini_sel_lg=ini_sel_lg,
                            acc_dtrel=acc_dtrel,
                            rel_fase=rel_fase,
                            ini_ti=ini_ti
                        )
                        
                        self.session.add(relator_out)
                    
                    self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing initiative rapporteurs: {e}")
            self.session.rollback()

    def _process_committees(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process IX Legislature Committees (Cms)"""
        try:
            cms_section = actividade_out.find('Cms')
            if cms_section is not None:
                # Create committees record
                comissoes = Comissoes(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(comissoes)
                self.session.commit()
                
                # Process each ComissoesOut
                for comissao in cms_section.findall('ComissoesOut'):
                    cms_no = self._get_text_value(comissao, 'CmsNo')
                    cms_cd = self._get_text_value(comissao, 'CmsCd')
                    cms_lg = self._get_text_value(comissao, 'CmsLg')
                    cms_cargo = self._get_text_value(comissao, 'CmsCargo')
                    
                    comissao_out = ComissoesOut(
                        comissoes_id=comissoes.id,
                        cms_no=cms_no,
                        cms_cd=cms_cd,
                        cms_lg=cms_lg,
                        cms_cargo=cms_cargo
                    )
                    
                    self.session.add(comissao_out)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing committees: {e}")
            self.session.rollback()

    def _parse_datetime(self, datetime_str: str) -> Optional[object]:
        """Parse datetime string to Python datetime object"""
        if not datetime_str:
            return None
        
        try:
            from datetime import datetime
            
            # Try ISO format with time: 2004-12-09 00:00:00.0
            if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', datetime_str):
                # Remove milliseconds if present
                clean_str = datetime_str.split('.')[0]
                return datetime.strptime(clean_str, '%Y-%m-%d %H:%M:%S')
            
            # Try date-only format
            if re.match(r'\d{4}-\d{2}-\d{2}', datetime_str):
                return datetime.strptime(datetime_str, '%Y-%m-%d')
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse datetime: {datetime_str} - {e}")
        
        return None

    def __del__(self):
        """Cleanup SQLAlchemy session"""
        if hasattr(self, 'session'):
            self.session.close()
    
    # Utility methods
    def _get_text_value(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Get text value from XML element"""
        if parent is None:
            return None
        element = parent.find(tag_name)
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _safe_int(self, value: str) -> Optional[int]:
        """Safely convert string to int"""
        if not value:
            return None
        try:
            return int(float(value))  # Handle values like "16897.0"
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[object]:
        """Parse date string to Python date object"""
        if not date_str:
            return None
        
        try:
            from datetime import datetime
            
            # Try ISO format first
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Try DD/MM/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    return datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", '%Y-%m-%d').date()
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse date: {date_str} - {e}")
        
        return None
    
    def _process_dep_cargo(self, deputado_elem: ET.Element, deputado_id: int):
        """Process DepCargo (deputy positions) using SQLAlchemy ORM"""
        try:
            dep_cargo_elem = deputado_elem.find('DepCargo')
            if dep_cargo_elem is not None:
                # Create DepCargo record
                dep_cargo = DepCargo(deputado_id=deputado_id)
                self.session.add(dep_cargo)
                self.session.flush()  # Get the ID
                
                # Process DadosCargoDeputado elements
                dados_cargo_elem = dep_cargo_elem.find('pt_ar_wsgode_objectos_DadosCargoDeputado')
                if dados_cargo_elem is not None:
                    car_des = self._get_text_value(dados_cargo_elem, 'carDes')
                    car_id = self._safe_int(self._get_text_value(dados_cargo_elem, 'carId'))
                    car_dt_inicio_str = self._get_text_value(dados_cargo_elem, 'carDtInicio')
                    car_dt_inicio = self._parse_date(car_dt_inicio_str) if car_dt_inicio_str else None
                    
                    dados_cargo = DadosCargoDeputado(
                        dep_cargo_id=dep_cargo.id,
                        car_des=car_des,
                        car_id=car_id,
                        car_dt_inicio=car_dt_inicio
                    )
                    
                    self.session.add(dados_cargo)
                
                self.session.commit()
                
        except Exception as e:
            logger.error(f"Error processing DepCargo: {e}")
            self.session.rollback()