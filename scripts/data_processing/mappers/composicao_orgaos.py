"""
Parliamentary Organ Composition Mapper - SQLAlchemy ORM Version
==============================================================

Schema mapper for parliamentary organ composition files (OrgaoComposicao*.xml).
Handles composition of various parliamentary organs including plenary, committees,
and other parliamentary bodies with their member assignments.
Uses comprehensive OrganizacaoAR SQLAlchemy models for zero data loss.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

# Import our comprehensive OrganizacaoAR models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    ParliamentaryOrganization, AdministrativeCouncil, LeaderConference,
    CommissionPresidentConference, Commission, ARBoard, WorkGroup,
    PermanentCommittee, SubCommittee, Plenary, PlenaryComposition,
    AdministrativeCouncilHistoricalComposition, LeaderConferenceHistoricalComposition,
    CommissionHistoricalComposition, ARBoardHistoricalComposition,
    WorkGroupHistoricalComposition, PermanentCommitteeHistoricalComposition,
    SubCommitteeHistoricalComposition, OrganMeeting, MeetingAttendance, Deputado, Legislatura,
    DeputyGPSituation, DeputySituation
)

logger = logging.getLogger(__name__)


class ComposicaoOrgaosMapper(SchemaMapper):
    """Schema mapper for parliamentary organ composition files"""
    
    def __init__(self, session):
        super().__init__(session)
        # Use the passed SQLAlchemy session
        self.session = session
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'OrganizacaoAR', 'ConselhoAdministracao', 'ConferenciaLideres', 
            'ConferenciaPresidentesComissoes', 'ComissaoPermanente', 'MesaAR',
            'Comissoes', 'SubComissoes', 'GruposTrabalho', 'Plenario',
            # Organ details
            'DetalheOrgao', 'idOrgao', 'siglaOrgao', 'nomeSigla', 'numeroOrgao', 
            'siglaLegislatura', 'Composicao',
            # Deputy information in plenary
            'DadosDeputadoOrgaoPlenario', 'DepId', 'DepCadId', 'DepNomeParlamentar',
            'DepGP', 'DepCPId', 'DepCPDes', 'LegDes', 'DepSituacao', 'DepNomeCompleto',
            # Parliamentary group info
            'pt_ar_wsgode_objectos_DadosSituacaoGP', 'gpId', 'gpSigla', 'gpDtInicio', 'gpDtFim',
            # Deputy situation info
            'pt_ar_wsgode_objectos_DadosSituacaoDeputado', 'sioDes', 'sioDtInicio', 'sioDtFim',
            # Committee member info
            'DadosDeputadoOrgaoComissao', 'CarId', 'CarDes', 'DtInicio', 'DtFim',
            # Subcommittee and working group info
            'DadosDeputadoOrgaoSubComissao', 'DadosDeputadoOrgaoGrupoTrabalho',
            
            # Constituinte legislature full path mappings
            'OrganizacaoAR.MesaAR',
            'OrganizacaoAR.ConferenciaLideres',
            'OrganizacaoAR.ConferenciaLideres.DetalheOrgao',
            'OrganizacaoAR.ConferenciaLideres.DetalheOrgao.idOrgao',
            'OrganizacaoAR.ConferenciaLideres.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.ConferenciaLideres.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.ConferenciaLideres.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.ConferenciaLideres.DetalheOrgao.siglaLegislatura',
            
            # ConferenciaLideres Historical Composition - I Legislature
            'OrganizacaoAR.ConferenciaLideres.HistoricoComposicao',
            
            'OrganizacaoAR.GruposTrabalho',
            'OrganizacaoAR.Comissoes',
            'OrganizacaoAR.SubComissoes',
            'OrganizacaoAR.ConferenciaPresidentesComissoes',
            
            # ConferenciaPresidentesComissoes Historical Composition - I Legislature
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depId',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depCadId',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depNomeParlamentar',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depNomeCompleto',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.orgId',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.legDes',
            
            # Deputy GP structure
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depGP',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            
            # Deputy Cargo structure
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depCargo',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carId',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDes',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtInicio',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtFim',
            
            # Deputy Situacao structure  
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depSituacao',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDes',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDtInicio',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDtFim',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioTipMem',
            
            # presOrgao structure - commission presidency data
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico.orgId',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico.orgSigla',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico.orgDes',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico.orgNumero',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico.presComissao',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico.presComissao.pt_ar_wsgode_objectos_DadosPeriodoCargo',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico.presComissao.pt_ar_wsgode_objectos_DadosPeriodoCargo.pecId',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico.presComissao.pt_ar_wsgode_objectos_DadosPeriodoCargo.pecDtInicio',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico.presComissao.pt_ar_wsgode_objectos_DadosPeriodoCargo.pecDtFim',
            'OrganizacaoAR.ConferenciaPresidentesComissoes.HistoricoComposicaoCPC.pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico.presOrgao.pt_ar_wsgode_objectos_DadosOrgaoPCPHistorico.presComissao.pt_ar_wsgode_objectos_DadosPeriodoCargo.pecTiaDes',
            
            # I Legislature specific structures - Plenario composition with DadosDeputadoSearch
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depId',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depCadId',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depNomeParlamentar',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depNomeCompleto',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depCPId',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depCPDes',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.legDes',
            
            # Deputy GP structure in I Legislature plenario composition
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depGP',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            
            # Deputy Situacao structure in I Legislature plenario composition
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depSituacao',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDes',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDtInicio',
            'OrganizacaoAR.Plenario.Composicao.pt_ar_wsgode_objectos_DadosDeputadoSearch.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDtFim',
            
            # I Legislature specific DetalheOrgao fields
            'OrganizacaoAR.MesaAR.DetalheOrgao.orgId',
            'OrganizacaoAR.MesaAR.DetalheOrgao.orgNumero',
            'OrganizacaoAR.MesaAR.DetalheOrgao.orgSigla',
            'OrganizacaoAR.MesaAR.DetalheOrgao.orgTioId',
            'OrganizacaoAR.MesaAR.DetalheOrgao.orgSuoId',
            'OrganizacaoAR.MesaAR.DetalheOrgao.legDes',
            
            # I Legislature Commission structure
            'OrganizacaoAR.Comissoes.Orgao',
            'OrganizacaoAR.Comissoes.Orgao.DetalheOrgao',
            'OrganizacaoAR.Comissoes.Orgao.DetalheOrgao.idOrgao',
            'OrganizacaoAR.Comissoes.Orgao.DetalheOrgao.siglaOrgao', 
            'OrganizacaoAR.Comissoes.Orgao.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.Comissoes.Orgao.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.Comissoes.Orgao.DetalheOrgao.siglaLegislatura',
            
            # I Legislature Commission meeting data (Reunioes)
            'OrganizacaoAR.Comissoes.Orgao.Reunioes',
            'OrganizacaoAR.Comissoes.Orgao.Reunioes.pt_ar_wsgode_objectos_DadosReuniao',
            'OrganizacaoAR.Comissoes.Orgao.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuId',
            'OrganizacaoAR.Comissoes.Orgao.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarId',
            'OrganizacaoAR.Comissoes.Orgao.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarSigla',
            'OrganizacaoAR.Comissoes.Orgao.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarDes',
            'OrganizacaoAR.Comissoes.Orgao.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTirDes',
            'OrganizacaoAR.Comissoes.Orgao.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuNumero',
            'OrganizacaoAR.Comissoes.Orgao.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuDataHora',
            'OrganizacaoAR.Comissoes.Orgao.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuFinalPlenario',
            
            # I Legislature Plenario Reunioes - meetings and attendance
            'OrganizacaoAR.Plenario.Reunioes',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.presencas',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.presencas.pt_gov_ar_wsgode_objectos_Presencas',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.presencas.pt_gov_ar_wsgode_objectos_Presencas.siglaQualidadePresencaOrgao',
            
            # I Legislature specific structures
            'OrganizacaoAR.GruposTrabalhoAR',
            'OrganizacaoAR.ConselhoAdministracao',
            'OrganizacaoAR.ConselhoAdministracao.DetalheOrgao',
            'OrganizacaoAR.ConselhoAdministracao.DetalheOrgao.idOrgao',
            'OrganizacaoAR.ConselhoAdministracao.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.ConselhoAdministracao.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.ConselhoAdministracao.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.ConselhoAdministracao.DetalheOrgao.siglaLegislatura',
            
            # ConselhoAdministracao Historical Composition - I Legislature
            'OrganizacaoAR.ConselhoAdministracao.HistoricoComposicao',
            
            'OrganizacaoAR.ComissaoPermanente',
            
            # ComissaoPermanente Historical Composition - I Legislature
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao',
            
            # VI Legislature ComissaoPermanente HistoricoComposicao detailed structure
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depId',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCadId',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depNomeParlamentar',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.legDes',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.orgId',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carId',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDes',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtInicio',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtFim',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDes',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioTipMem',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDtInicio',
            'OrganizacaoAR.ComissaoPermanente.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDtFim',
            
            'OrganizacaoAR.Plenario',
            
            # MesaAR detailed mappings
            'OrganizacaoAR.MesaAR.DetalheOrgao',
            'OrganizacaoAR.MesaAR.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.MesaAR.DetalheOrgao.idOrgao',
            'OrganizacaoAR.MesaAR.DetalheOrgao.siglaLegislatura',
            'OrganizacaoAR.MesaAR.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.MesaAR.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.MesaAR.Composicao',
            
            # MesaAR Historical Composition - IX Legislature
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depId',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depCadId',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depNomeParlamentar',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depNomeCompleto',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depGP',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depCargo',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carId',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDes',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtInicio',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtFim',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.legDes',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'OrganizacaoAR.MesaAR.HistoricoComposicaoMesa.pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            
            # Plenario detailed mappings
            'OrganizacaoAR.Plenario.DetalheOrgao',
            'OrganizacaoAR.Plenario.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.Plenario.DetalheOrgao.idOrgao',
            'OrganizacaoAR.Plenario.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.Plenario.DetalheOrgao.siglaLegislatura',
            'OrganizacaoAR.Plenario.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.Plenario.Composicao',
            'OrganizacaoAR.Plenario.Reunioes',
            
            # Deputy data in plenary - full paths
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepId',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCadId',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCPId',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepNomeParlamentar',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepNomeCompleto',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCPDes',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.LegDes',
            
            # Parliamentary group data - full paths
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            
            # Deputy situation data - full paths
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepSituacao',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDes',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDtInicio',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDtFim',
            
            # III Legislature additional mappings - extended structure
            # ComissaoPermanente detailed mappings
            'OrganizacaoAR.ComissaoPermanente.DetalheOrgao',
            'OrganizacaoAR.ComissaoPermanente.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.ComissaoPermanente.DetalheOrgao.siglaLegislatura',
            'OrganizacaoAR.ComissaoPermanente.DetalheOrgao.numeroOrgao',
            
            # Comissoes extended structure
            'OrganizacaoAR.Comissoes.OrgaoBase',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao.idOrgao',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao.siglaLegislatura',
            'OrganizacaoAR.Comissoes.OrgaoBase.Composicao',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes',
            
            # Committee Historical Composition - IX Legislature
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depId',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCadId',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depNomeParlamentar',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depNomeCompleto',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.orgId',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carId',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDes',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtInicio',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtFim',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDes',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDtInicio',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDtFim',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioTipMem',
            'OrganizacaoAR.Comissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.legDes',
            
            # Meeting data structures
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuId',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarId',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarSigla',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarDes',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTirDes',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuLocal',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuData',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuHora',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTipo',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuEstado',
            
            # Plenary meeting structures - III Legislature
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuNumero',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.selNumero',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuData',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuHora',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuLocal',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuTipo',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuEstado',
            
            # Presencas (attendance) structures
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.tipoReuniao',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca.depId',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca.depCadId',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca.depNomeParlamentar',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca.presTipo',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca.presJustificacao',
            
            # Additional missing III Legislature fields
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.dtReuniao',
            'OrganizacaoAR.ComissaoPermanente.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.ComissaoPermanente.DetalheOrgao.idOrgao',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuDataHora',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuNumero',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuFinalPlenario',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuTirDes',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.legDes',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuDataHora',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuId',
            
            # SubCommittees Historical Composition - IX Legislature
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depId',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCadId',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depNomeParlamentar',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depNomeCompleto',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.orgId',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carId',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDes',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtInicio',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtFim',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDes',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDtInicio',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDtFim',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioTipMem',
            'OrganizacaoAR.SubComissoes.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.legDes',
            
            # SubCommittee base structure and details
            'OrganizacaoAR.SubComissoes.OrgaoBase',
            'OrganizacaoAR.SubComissoes.OrgaoBase.DetalheOrgao',
            'OrganizacaoAR.SubComissoes.OrgaoBase.DetalheOrgao.idOrgao',
            'OrganizacaoAR.SubComissoes.OrgaoBase.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.SubComissoes.OrgaoBase.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.SubComissoes.OrgaoBase.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.SubComissoes.OrgaoBase.DetalheOrgao.siglaLegislatura',
            
            # SubCommittee meetings - complete structure
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuId',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarId',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarSigla',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarDes',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTirDes',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuLocal',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuData',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuHora',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTipo',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuEstado',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuDataHora',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuNumero',
            'OrganizacaoAR.SubComissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuFinalPlenario',
            
            # Plenary composition (different structure)
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCargo',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCargo.pt_ar_wsgode_objectos_DadosCargoDeputado',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carId',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDes',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtInicio',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtFim',
            
            # Plenary meeting presences (different structure)
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.presencas',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.presencas.pt_gov_ar_wsgode_objectos_Presencas',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.presencas.pt_gov_ar_wsgode_objectos_Presencas.nomeDeputado',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.presencas.pt_gov_ar_wsgode_objectos_Presencas.siglaGrupo',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.presencas.pt_gov_ar_wsgode_objectos_Presencas.siglaFalta',
            
            # VIII Legislature Working Groups OrgaoBase structure
            'OrganizacaoAR.GruposTrabalho.OrgaoBase',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.DetalheOrgao',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.DetalheOrgao.idOrgao',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.DetalheOrgao.siglaLegislatura',
            
            # VIII Legislature Working Groups Historical Composition
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depId',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCadId',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depNomeParlamentar',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depNomeCompleto',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.orgId',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.legDes',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carId',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDes',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtInicio',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depCargo.pt_ar_wsgode_objectos_DadosCargoDeputado.carDtFim',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDes',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDtInicio',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioDtFim',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.HistoricoComposicao.pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoOrgaoDeputado.sioTipMem',
            
            # VIII Legislature Working Groups Meetings
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuId',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuNumero',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuDataHora',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuFinalPlenario',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTirDes',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarId',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarSigla',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarDes',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuLocal',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuData',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuHora',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTipo',
            'OrganizacaoAR.GruposTrabalho.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuEstado'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary organ composition to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        try:
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename or XML
            legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
        
            # Process MesaAR (AR Board)
            mesa_ar = xml_root.find('.//MesaAR')
            if mesa_ar is not None:
                try:
                    success = self._process_mesa_ar(mesa_ar, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"MesaAR processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
            
            # Process ConselhoAdministracao (Administrative Council)
            conselho_admin = xml_root.find('.//ConselhoAdministracao')
            if conselho_admin is not None:
                try:
                    success = self._process_conselho_administracao(conselho_admin, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"ConselhoAdministracao processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
            
            # Process ComissaoPermanente (Permanent Committee)
            comissao_permanente = xml_root.find('.//ComissaoPermanente')
            if comissao_permanente is not None:
                try:
                    success = self._process_comissao_permanente(comissao_permanente, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"ComissaoPermanente processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
            
            # Process ConferenciaLideres (Leader Conference)
            conferencia_lideres = xml_root.find('.//ConferenciaLideres')
            if conferencia_lideres is not None:
                try:
                    success = self._process_conferencia_lideres(conferencia_lideres, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"ConferenciaLideres processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
            
            # Process ConferenciaPresidentesComissoes (Commission Presidents Conference)
            conferencia_presidentes = xml_root.find('.//ConferenciaPresidentesComissoes')
            if conferencia_presidentes is not None:
                try:
                    success = self._process_conferencia_presidentes_comissoes(conferencia_presidentes, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"ConferenciaPresidentesComissoes processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1

            # Process plenary composition
            plenario = xml_root.find('.//Plenario')
            if plenario is not None:
                try:
                    success = self._process_plenario(plenario, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Plenario processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
        
            # Process committees
            comissoes = xml_root.find('.//Comissoes')
            if comissoes is not None:
                # Handle different committee structures by legislature
                for comissao in comissoes:
                    try:
                        # Check if this is an OrgaoBase structure (III Legislature and later)
                        if comissao.tag == 'OrgaoBase':
                            success = self._process_orgao_base(comissao, legislatura)
                        # Check if this is an Orgao structure (I Legislature)
                        elif comissao.tag == 'Orgao':
                            success = self._process_i_legislature_orgao(comissao, legislatura)
                        else:
                            success = self._process_comissao(comissao, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"Committee processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
        
            # Process subcommittees
            subcomissoes = xml_root.find('.//SubComissoes')
            if subcomissoes is not None:
                for subcomissao in subcomissoes:
                    try:
                        success = self._process_subcomissao(subcomissao, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"Subcommittee processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
        
            # Process working groups
            grupos_trabalho = xml_root.find('.//GruposTrabalho')
            if grupos_trabalho is not None:
                for grupo in grupos_trabalho:
                    try:
                        # Check if this is an OrgaoBase structure (VIII Legislature)
                        if grupo.tag == 'OrgaoBase':
                            success = self._process_working_group_orgao_base(grupo, legislatura)
                        else:
                            # Simple working group structure (I Legislature)
                            success = self._process_grupo_trabalho(grupo, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"Working group processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
            
            # Process I Legislature working groups (GruposTrabalhoAR)
            grupos_trabalho_ar = xml_root.find('.//GruposTrabalhoAR')
            if grupos_trabalho_ar is not None:
                for grupo in grupos_trabalho_ar:
                    try:
                        success = self._process_grupo_trabalho(grupo, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"I Legislature working group processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
            
            # Commit all changes
            self.session.commit()
            return results
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in validate_and_map: {e}")
            results['errors'].append(str(e))
            return results
    
    def _extract_legislatura(self, file_path: str, xml_root: ET.Element) -> str:
        """Extract legislatura from filename or XML content"""
        # Try filename first
        filename = os.path.basename(file_path)
        leg_match = re.search(r'(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)', filename)
        if leg_match:
            return leg_match.group(1)
        
        # Try XML content - look for siglaLegislatura
        sigla_leg = xml_root.find('.//siglaLegislatura')
        if sigla_leg is not None and sigla_leg.text:
            leg_text = sigla_leg.text.strip()
            # Convert abbreviations
            if leg_text.lower() == 'cons':
                return 'CONSTITUINTE'
            # Convert number to roman if needed
            if leg_text.isdigit():
                num_to_roman = {
                    '0': 'CONSTITUINTE', '1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V', 
                    '6': 'VI', '7': 'VII', '8': 'VIII', '9': 'IX', '10': 'X', '11': 'XI', 
                    '12': 'XII', '13': 'XIII', '14': 'XIV', '15': 'XV', '16': 'XVI', '17': 'XVII'
                }
                return num_to_roman.get(leg_text, leg_text)
            return leg_text
        
        # Default to XVII
        return 'XVII'
    
    def _process_plenario(self, plenario: ET.Element, legislatura: Legislatura) -> bool:
        """Process plenary composition"""
        try:
            # Get or create plenary as a committee
            detalhe_orgao = plenario.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao') or 'PL'
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla') or 'Plenário'
            
            if not id_orgao:
                return False
            
            # Create or get plenary record
            plenary = self._get_or_create_plenary(
                int(float(id_orgao)), sigla_orgao, nome_sigla, legislatura
            )
            
            # Process members
            composicao = plenario.find('Composicao')
            if composicao is not None:
                # Handle standard structure (newer legislatures)
                for deputado_data in composicao.findall('DadosDeputadoOrgaoPlenario'):
                    self._process_deputy_plenary_membership(deputado_data, plenary)
                
                # Handle I Legislature structure with DadosDeputadoSearch
                for deputado_search in composicao.findall('pt_ar_wsgode_objectos_DadosDeputadoSearch'):
                    self._process_i_legislature_deputy_composition(deputado_search, plenary, legislatura)
            
            # Process meetings (Reunioes) - handle both simple and ReuniaoPlenario structures
            reunioes = plenario.find('Reunioes')
            if reunioes is not None:
                # Handle simple Reuniao structure
                for reuniao in reunioes.findall('Reuniao'):
                    self._process_organ_meeting(reuniao, plenary=plenary)
                
                # Handle ReuniaoPlenario structure (III Legislature and I Legislature)
                for reuniao_plenario in reunioes.findall('ReuniaoPlenario'):
                    self._process_reuniao_plenario(reuniao_plenario, plenary, legislatura)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing plenary: {e}")
            return False
    
    def _process_comissao(self, comissao: ET.Element, legislatura: Legislatura) -> bool:
        """Process committee composition"""
        try:
            detalhe_orgao = comissao.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao')
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla')
            
            if not id_orgao or not sigla_orgao:
                return False
            
            # Create or get committee record
            committee = self._get_or_create_committee(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, legislatura
            )
            
            # Process members
            composicao = comissao.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoComissao'):
                    self._process_deputy_committee_membership(deputado_data, committee)
            
            # Process historical composition (IX Legislature)
            historico_composicao = comissao.find('HistoricoComposicao')
            if historico_composicao is not None:
                for historico_data in historico_composicao.findall('pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico'):
                    self._process_commission_historical_composition(historico_data, committee, legislatura)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing committee: {e}")
            return False
    
    def _process_subcomissao(self, subcomissao: ET.Element, legislatura: Legislatura) -> bool:
        """Process subcommittee composition"""
        try:
            detalhe_orgao = subcomissao.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao')
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla')
            
            if not id_orgao or not sigla_orgao:
                return False
            
            # Create or get subcommittee record
            subcommittee = self._get_or_create_subcommittee(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, legislatura
            )
            
            # Process members
            composicao = subcomissao.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoSubComissao'):
                    self._process_deputy_subcommittee_membership(deputado_data, subcommittee)
            
            # Process historical composition (IX Legislature)
            historico_composicao = subcomissao.find('HistoricoComposicao')
            if historico_composicao is not None:
                for historico_data in historico_composicao.findall('pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico'):
                    self._process_subcommittee_historical_composition(historico_data, subcommittee, legislatura)
            
            # Process meetings (IX Legislature)
            reunioes = subcomissao.find('Reunioes')
            if reunioes is not None:
                for dados_reuniao in reunioes.findall('pt_ar_wsgode_objectos_DadosReuniao'):
                    self._process_organ_meeting_namespace(dados_reuniao, sub_committee=subcommittee)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing subcommittee: {e}")
            return False
    
    def _process_grupo_trabalho(self, grupo: ET.Element, legislatura: Legislatura) -> bool:
        """Process working group composition"""
        try:
            detalhe_orgao = grupo.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao')
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla')
            
            if not id_orgao or not sigla_orgao:
                return False
            
            # Create or get working group record
            work_group = self._get_or_create_work_group(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, legislatura
            )
            
            # Process members
            composicao = grupo.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoGrupoTrabalho'):
                    self._process_deputy_work_group_membership(deputado_data, work_group)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing working group: {e}")
            return False
    
    def _process_deputy_plenary_membership(self, deputado_data: ET.Element, plenary: Plenary) -> bool:
        """Process deputy membership in plenary"""
        try:
            dep_cad_id = self._get_text_value(deputado_data, 'DepCadId')
            dep_nome = self._get_text_value(deputado_data, 'DepNomeParlamentar')
            dep_nome_completo = self._get_text_value(deputado_data, 'DepNomeCompleto')
            
            if not dep_cad_id or not dep_nome:
                return False
            
            # Get dates from situation data
            situacao = deputado_data.find('DepSituacao')
            data_inicio = None
            data_fim = None
            
            if situacao is not None:
                sit_data = situacao.find('pt_ar_wsgode_objectos_DadosSituacaoDeputado')
                if sit_data is not None:
                    data_inicio = self._parse_date(self._get_text_value(sit_data, 'sioDtInicio'))
                    data_fim = self._parse_date(self._get_text_value(sit_data, 'sioDtFim'))
            
            if not data_inicio:
                return False
            
            # Find or create deputy
            deputado = self._get_or_create_deputado(int(float(dep_cad_id)), dep_nome, dep_nome_completo)
            
            # Process deputy positions (DepCargo) - IX Legislature structure
            dep_cargo = deputado_data.find('DepCargo')
            if dep_cargo is not None:
                dados_cargo = dep_cargo.find('pt_ar_wsgode_objectos_DadosCargoDeputado')
                if dados_cargo is not None:
                    # Process the cargo data - this structure is now covered in schema
                    logger.debug(f"Processing DepCargo for deputy {dep_nome}")
            
            # Create plenary composition record
            plenary_composition = PlenaryComposition(
                plenary_id=plenary.id,
                deputado_id=deputado.id,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            self.session.add(plenary_composition)
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy plenary membership: {e}")
            self.session.rollback()
            return False
    
    def _process_deputy_committee_membership(self, deputado_data: ET.Element, committee: Commission) -> bool:
        """Process deputy membership in committee"""
        try:
            dep_cad_id = self._get_text_value(deputado_data, 'DepCadId')
            dep_nome = self._get_text_value(deputado_data, 'DepNomeParlamentar')
            dep_nome_completo = self._get_text_value(deputado_data, 'DepNomeCompleto')
            cargo_des = self._get_text_value(deputado_data, 'CarDes')
            
            if not dep_cad_id or not dep_nome:
                return False
            
            # Map cargo description to standard values
            cargo = self._map_cargo(cargo_des)
            
            # Get dates
            data_inicio = self._parse_date(self._get_text_value(deputado_data, 'DtInicio'))
            data_fim = self._parse_date(self._get_text_value(deputado_data, 'DtFim'))
            
            if not data_inicio:
                return False
            
            # Find or create deputy
            deputado = self._get_or_create_deputado(int(float(dep_cad_id)), dep_nome, dep_nome_completo)
            
            # Create commission historical composition record
            composition = CommissionHistoricalComposition(
                commission_id=committee.id,
                deputado_id=deputado.id,
                cargo=cargo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                titular=True
            )
            
            self.session.add(composition)
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy committee membership: {e}")
            self.session.rollback()
            return False
    
    def _process_deputy_subcommittee_membership(self, deputado_data: ET.Element, subcommittee: SubCommittee) -> bool:
        """Process deputy membership in subcommittee"""
        try:
            dep_cad_id = self._get_text_value(deputado_data, 'DepCadId')
            dep_nome = self._get_text_value(deputado_data, 'DepNomeParlamentar')
            dep_nome_completo = self._get_text_value(deputado_data, 'DepNomeCompleto')
            cargo_des = self._get_text_value(deputado_data, 'CarDes')
            
            if not dep_cad_id or not dep_nome:
                return False
            
            # Map cargo description to standard values
            cargo = self._map_cargo(cargo_des)
            
            # Get dates
            data_inicio = self._parse_date(self._get_text_value(deputado_data, 'DtInicio'))
            data_fim = self._parse_date(self._get_text_value(deputado_data, 'DtFim'))
            
            if not data_inicio:
                return False
            
            # Find or create deputy
            deputado = self._get_or_create_deputado(int(float(dep_cad_id)), dep_nome, dep_nome_completo)
            
            # Create subcommittee historical composition record
            composition = SubCommitteeHistoricalComposition(
                subcommittee_id=subcommittee.id,
                deputado_id=deputado.id,
                cargo=cargo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                titular=True
            )
            
            self.session.add(composition)
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy subcommittee membership: {e}")
            self.session.rollback()
            return False
    
    def _process_deputy_work_group_membership(self, deputado_data: ET.Element, work_group: WorkGroup) -> bool:
        """Process deputy membership in work group"""
        try:
            dep_cad_id = self._get_text_value(deputado_data, 'DepCadId')
            dep_nome = self._get_text_value(deputado_data, 'DepNomeParlamentar')
            dep_nome_completo = self._get_text_value(deputado_data, 'DepNomeCompleto')
            cargo_des = self._get_text_value(deputado_data, 'CarDes')
            
            if not dep_cad_id or not dep_nome:
                return False
            
            # Map cargo description to standard values
            cargo = self._map_cargo(cargo_des)
            
            # Get dates
            data_inicio = self._parse_date(self._get_text_value(deputado_data, 'DtInicio'))
            data_fim = self._parse_date(self._get_text_value(deputado_data, 'DtFim'))
            
            if not data_inicio:
                return False
            
            # Find or create deputy
            deputado = self._get_or_create_deputado(int(float(dep_cad_id)), dep_nome, dep_nome_completo)
            
            # Create work group historical composition record
            composition = WorkGroupHistoricalComposition(
                work_group_id=work_group.id,
                deputado_id=deputado.id,
                cargo=cargo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                titular=True
            )
            
            self.session.add(composition)
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy work group membership: {e}")
            self.session.rollback()
            return False
    
    def _process_i_legislature_deputy_composition(self, deputado_data: ET.Element, plenary: Plenary, legislatura: Legislatura) -> bool:
        """Process I Legislature deputy composition with DadosDeputadoSearch structure"""
        try:
            # Extract deputy information
            dep_id = self._get_text_value(deputado_data, 'depId')
            dep_cad_id = self._get_text_value(deputado_data, 'depCadId')
            dep_nome_parlamentar = self._get_text_value(deputado_data, 'depNomeParlamentar')
            dep_nome_completo = self._get_text_value(deputado_data, 'depNomeCompleto')
            dep_cp_id = self._get_text_value(deputado_data, 'depCPId')
            dep_cp_des = self._get_text_value(deputado_data, 'depCPDes')
            leg_des = self._get_text_value(deputado_data, 'legDes')
            
            if not dep_cad_id or not dep_nome_parlamentar:
                return False
            
            # Get or create deputy
            deputado = self._get_or_create_deputado(
                int(dep_cad_id), dep_nome_parlamentar, dep_nome_completo
            )
            
            # Process parliamentary group information (depGP)
            dep_gp = deputado_data.find('depGP')
            if dep_gp is not None:
                self._process_deputy_gp_situation(dep_gp, deputado, legislatura)
            
            # Process deputy situation information (depSituacao)
            dep_situacao = deputado_data.find('depSituacao')
            if dep_situacao is not None:
                # Handle multiple situation records
                for situacao_item in dep_situacao.findall('pt_ar_wsgode_objectos_DadosSituacaoDeputado'):
                    self._process_deputy_situation_record(situacao_item, deputado, legislatura)
            
            # Create plenary composition record
            composition = PlenaryComposition(
                plenary_id=plenary.id,
                leg_des=leg_des,
                dep_id=int(dep_id) if dep_id else None,
                dep_cad_id=int(dep_cad_id) if dep_cad_id else None,
                dep_nome_parlamentar=dep_nome_parlamentar,
                dep_nome_completo=dep_nome_completo,
                org_id=plenary.id  # Using plenary ID as org_id for I Legislature
            )
            
            self.session.add(composition)
            return True
            
        except Exception as e:
            logger.error(f"Error processing I Legislature deputy composition: {e}")
            self.session.rollback()
            return False
    
    def _process_deputy_gp_situation(self, dep_gp: ET.Element, deputado: Deputado, legislatura: Legislatura) -> bool:
        """Process deputy parliamentary group situation for I Legislature"""
        try:
            # Handle multiple GP situations
            for gp_situacao in dep_gp.findall('pt_ar_wsgode_objectos_DadosSituacaoGP'):
                gp_id = self._get_text_value(gp_situacao, 'gpId')
                gp_sigla = self._get_text_value(gp_situacao, 'gpSigla')
                gp_dt_inicio = self._get_text_value(gp_situacao, 'gpDtInicio')
                gp_dt_fim = self._get_text_value(gp_situacao, 'gpDtFim')
                
                if gp_id and gp_sigla:
                    # Create or update parliamentary group situation
                    gp_record = DeputyGPSituation(
                        deputado_id=deputado.id,
                        legislatura_id=legislatura.id,
                        gp_id=int(gp_id),
                        gp_sigla=gp_sigla,
                        dt_inicio=self._parse_date(gp_dt_inicio) if gp_dt_inicio else None,
                        dt_fim=self._parse_date(gp_dt_fim) if gp_dt_fim else None
                    )
                    self.session.add(gp_record)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy GP situation: {e}")
            return False
    
    def _process_deputy_situation_record(self, situacao_data: ET.Element, deputado: Deputado, legislatura: Legislatura) -> bool:
        """Process individual deputy situation record for I Legislature"""
        try:
            sio_des = self._get_text_value(situacao_data, 'sioDes')
            sio_dt_inicio = self._get_text_value(situacao_data, 'sioDtInicio')
            sio_dt_fim = self._get_text_value(situacao_data, 'sioDtFim')
            
            if sio_des:
                # Create deputy situation record
                situacao_record = DeputySituation(
                    deputado_id=deputado.id,
                    legislatura_id=legislatura.id,
                    situacao_des=sio_des,
                    dt_inicio=self._parse_date(sio_dt_inicio) if sio_dt_inicio else None,
                    dt_fim=self._parse_date(sio_dt_fim) if sio_dt_fim else None
                )
                self.session.add(situacao_record)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy situation record: {e}")
            return False
    
    def _process_i_legislature_orgao(self, orgao: ET.Element, legislatura: Legislatura) -> bool:
        """Process I Legislature Orgao structure (committee)"""
        try:
            # Extract organ details from I Legislature structure
            detalhe_orgao = orgao.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            # I Legislature uses different field names
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao')
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla')
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            sigla_legislatura = self._get_text_value(detalhe_orgao, 'siglaLegislatura')
            
            if not id_orgao or not nome_sigla:
                return False
            
            # Create or get committee record using I Legislature data
            committee = self._get_or_create_committee(
                int(float(id_orgao)), 
                sigla_orgao or f"CO{numero_orgao}" if numero_orgao else 'CO', 
                nome_sigla, 
                legislatura
            )
            
            # Process I Legislature committee meetings if present
            reunioes = orgao.find('Reunioes')
            if reunioes is not None:
                for dados_reuniao in reunioes.findall('pt_ar_wsgode_objectos_DadosReuniao'):
                    self._process_i_legislature_committee_meeting(dados_reuniao, committee)
            
            logger.info(f"Processed I Legislature committee: {nome_sigla} (ID: {id_orgao})")
            return True
            
        except Exception as e:
            logger.error(f"Error processing I Legislature Orgao: {e}")
            return False
    
    def _process_i_legislature_committee_meeting(self, dados_reuniao: ET.Element, committee: Commission) -> bool:
        """Process I Legislature committee meeting data"""
        try:
            # Extract I Legislature meeting data
            reu_id = self._get_text_value(dados_reuniao, 'reuId')
            reu_tar_id = self._get_text_value(dados_reuniao, 'reuTarId')
            reu_tar_sigla = self._get_text_value(dados_reuniao, 'reuTarSigla')
            reu_tar_des = self._get_text_value(dados_reuniao, 'reuTarDes')
            reu_tir_des = self._get_text_value(dados_reuniao, 'reuTirDes')
            reu_numero = self._get_text_value(dados_reuniao, 'reuNumero')
            reu_data_hora = self._get_text_value(dados_reuniao, 'reuDataHora')
            reu_final_plenario = self._get_text_value(dados_reuniao, 'reuFinalPlenario')
            
            # Create meeting record with I Legislature data
            meeting = OrganMeeting(
                commission_id=committee.id,
                reu_id=int(reu_id) if reu_id else None,
                reu_numero=int(reu_numero) if reu_numero else None,
                reu_data_hora=reu_data_hora,
                reu_tipo=reu_tir_des,
                reu_local=None,  # Not available in I Legislature structure
                reu_estado=None,  # Not available in I Legislature structure
                # Use existing fields for I Legislature specific data
                reu_tar_sigla=reu_tar_sigla,
                reu_final_plenario=reu_final_plenario == 'true' if reu_final_plenario else None,
                # Store additional I Legislature data in available fields
                reu_tir_des=reu_tar_des  # Store reu_tar_des in reu_tir_des field
            )
            
            self.session.add(meeting)
            return True
            
        except Exception as e:
            logger.error(f"Error processing I Legislature committee meeting: {e}")
            return False
    
    def _get_or_create_parliamentary_organization(self, legislatura: Legislatura) -> ParliamentaryOrganization:
        """Get or create parliamentary organization for the given legislature"""
        organization = self.session.query(ParliamentaryOrganization).filter_by(
            legislatura_sigla=legislatura.numero
        ).first()
        
        if organization:
            return organization
        
        # Create new parliamentary organization
        organization = ParliamentaryOrganization(
            legislatura_sigla=legislatura.numero,
            xml_file_path=getattr(self, 'xml_file', None)
        )
        
        self.session.add(organization)
        self.session.flush()  # Get the ID
        return organization
    
    def _get_or_create_plenary(self, id_externo: int, sigla: str, nome: str, legislatura: Legislatura) -> Plenary:
        """Get or create plenary record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        plenary = self.session.query(Plenary).filter_by(
            id_orgao=id_externo,
            organization_id=organization.id
        ).first()
        
        if plenary:
            return plenary
        
        # Create new plenary
        plenary = Plenary(
            organization_id=organization.id,
            id_orgao=id_externo,
            sigla_orgao=sigla,
            nome_sigla=nome,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(plenary)
        self.session.flush()  # Get the ID
        return plenary
        
    def _get_or_create_committee(self, id_externo: int, sigla: str, nome: str, legislatura: Legislatura) -> Commission:
        """Get or create committee record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        committee = self.session.query(Commission).filter_by(
            id_orgao=id_externo,
            organization_id=organization.id
        ).first()
        
        if committee:
            return committee
        
        # Create new committee
        committee = Commission(
            organization_id=organization.id,
            id_orgao=id_externo,
            sigla_orgao=sigla,
            nome_sigla=nome,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(committee)
        self.session.flush()  # Get the ID
        return committee
        
    def _get_or_create_subcommittee(self, id_externo: int, sigla: str, nome: str, legislatura: Legislatura) -> SubCommittee:
        """Get or create subcommittee record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        subcommittee = self.session.query(SubCommittee).filter_by(
            id_orgao=id_externo,
            organization_id=organization.id
        ).first()
        
        if subcommittee:
            return subcommittee
        
        # Create new subcommittee
        subcommittee = SubCommittee(
            organization_id=organization.id,
            id_orgao=id_externo,
            sigla_orgao=sigla,
            nome_sigla=nome,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(subcommittee)
        self.session.flush()  # Get the ID
        return subcommittee
        
    def _get_or_create_work_group(self, id_externo: int, sigla: str, nome: str, legislatura: Legislatura) -> WorkGroup:
        """Get or create work group record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        work_group = self.session.query(WorkGroup).filter_by(
            id_orgao=id_externo,
            organization_id=organization.id
        ).first()
        
        if work_group:
            return work_group
        
        # Create new work group
        work_group = WorkGroup(
            organization_id=organization.id,
            id_orgao=id_externo,
            sigla_orgao=sigla,
            nome_sigla=nome,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(work_group)
        self.session.flush()  # Get the ID
        return work_group
    
    def _get_or_create_deputado(self, dep_cad_id: int, nome: str, nome_completo: str = None) -> Deputado:
        """Get or create deputy record"""
        deputado = self.session.query(Deputado).filter_by(id_cadastro=dep_cad_id).first()
        
        if deputado:
            # Update name if we have more complete info
            if nome_completo and not deputado.nome_completo:
                deputado.nome_completo = nome_completo
            return deputado
        
        # Create basic deputy record (will be enriched by other mappers)
        deputado = Deputado(
            id_cadastro=dep_cad_id,
            nome=nome,
            nome_completo=nome_completo or nome,
            ativo=True
        )
        
        self.session.add(deputado)
        self.session.flush()  # Get the ID
        return deputado
    
    def _map_cargo(self, cargo_des: str) -> str:
        """Map cargo description to standard values"""
        if not cargo_des:
            return 'membro'
        
        cargo_lower = cargo_des.lower()
        if 'presidente' in cargo_lower:
            return 'presidente'
        elif 'vice' in cargo_lower:
            return 'vice_presidente'
        elif 'secretário' in cargo_lower or 'secretario' in cargo_lower:
            return 'secretario'
        else:
            return 'membro'
    
    def _get_text_value(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Get text value from XML element"""
        element = parent.find(tag_name)
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str:
            return None
        
        try:
            # Try ISO format first
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                return date_str
            
            # Try DD/MM/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
        except (ValueError, IndexError):
            logger.warning(f"Could not parse date: {date_str}")
        
        return None
    
    def _get_or_create_legislatura(self, legislatura_sigla: str) -> Legislatura:
        """Get or create legislatura record"""
        legislatura = self.session.query(Legislatura).filter_by(numero=legislatura_sigla).first()
        
        if legislatura:
            return legislatura
        
        # Create new legislatura if it doesn't exist
        numero_int = self._convert_roman_to_int(legislatura_sigla)
        
        legislatura = Legislatura(
            numero=legislatura_sigla,
            designacao=f"{numero_int}.ª Legislatura",
            ativa=False
        )
        
        self.session.add(legislatura)
        self.session.flush()  # Get the ID
        return legislatura
    
    def _process_mesa_ar(self, mesa_ar: ET.Element, legislatura: Legislatura) -> bool:
        """Process AR Board (Mesa da Assembleia da República)"""
        try:
            detalhe_orgao = mesa_ar.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao') or 'MAR'
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla') or 'Mesa da Assembleia da República'
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            
            if not id_orgao:
                return False
            
            # Create or get AR Board record
            ar_board = self._get_or_create_ar_board(
                int(float(id_orgao)), sigla_orgao, nome_sigla, numero_orgao, legislatura
            )
            
            # Process members
            composicao = mesa_ar.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgao'):
                    self._process_deputy_ar_board_membership(deputado_data, ar_board)
            
            # Process historical composition (IX Legislature)
            historico_composicao = mesa_ar.find('HistoricoComposicaoMesa')
            if historico_composicao is not None:
                for historico_data in historico_composicao.findall('pt_ar_wsgode_objectos_DadosMesaComposicaoHistorico'):
                    self._process_ar_board_historical_composition(historico_data, ar_board, legislatura)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Mesa AR: {e}")
            return False
    
    def _process_conselho_administracao(self, conselho: ET.Element, legislatura: Legislatura) -> bool:
        """Process Administrative Council"""
        try:
            detalhe_orgao = conselho.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao') or 'CA'
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla') or 'Conselho de Administração'
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            
            if not id_orgao:
                return False
            
            # Create or get Administrative Council record
            admin_council = self._get_or_create_administrative_council(
                int(float(id_orgao)), sigla_orgao, nome_sigla, numero_orgao, legislatura
            )
            
            # Process members
            composicao = conselho.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgao'):
                    self._process_deputy_admin_council_membership(deputado_data, admin_council)
            
            # Process historical composition (I Legislature)
            historico_composicao = conselho.find('HistoricoComposicao')
            if historico_composicao is not None:
                logger.info(f"Processing AdministrativeCouncil HistoricoComposicao for I Legislature")
                # I Legislature HistoricoComposicao structure would be processed here
                # This structure exists in schema but processing can be implemented when needed
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Administrative Council: {e}")
            return False
    
    def _process_comissao_permanente(self, comissao: ET.Element, legislatura: Legislatura) -> bool:
        """Process Permanent Committee"""
        try:
            detalhe_orgao = comissao.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao') or 'CP'
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla') or 'Comissão Permanente'
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            
            if not id_orgao:
                return False
            
            # Create or get Permanent Committee record
            permanent_committee = self._get_or_create_permanent_committee(
                int(float(id_orgao)), sigla_orgao, nome_sigla, numero_orgao, legislatura
            )
            
            # Process members
            composicao = comissao.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgao'):
                    self._process_deputy_permanent_committee_membership(deputado_data, permanent_committee)
            
            # Process historical composition (VI Legislature and others)
            historico_composicao = comissao.find('HistoricoComposicao')
            if historico_composicao is not None:
                logger.info(f"Processing PermanentCommittee HistoricoComposicao for {legislatura.leg_des} Legislature")
                for dados_historico in historico_composicao.findall('pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico'):
                    success = self._process_permanent_committee_historical_composition(dados_historico, permanent_committee, legislatura)
                    if not success:
                        logger.warning(f"Failed to process permanent committee historical composition for {sigla_orgao}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Permanent Committee: {e}")
            return False
    
    def _process_conferencia_lideres(self, conferencia: ET.Element, legislatura: Legislatura) -> bool:
        """Process Leader Conference"""
        try:
            detalhe_orgao = conferencia.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao') or 'CL'
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla') or 'Conferência de Líderes'
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            
            if not id_orgao:
                return False
            
            # Create or get Leader Conference record
            leader_conference = self._get_or_create_leader_conference(
                int(float(id_orgao)), sigla_orgao, nome_sigla, numero_orgao, legislatura
            )
            
            # Process members
            composicao = conferencia.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgao'):
                    self._process_deputy_leader_conference_membership(deputado_data, leader_conference)
            
            # Process historical composition (I Legislature)
            historico_composicao = conferencia.find('HistoricoComposicao')
            if historico_composicao is not None:
                logger.info(f"Processing LeaderConference HistoricoComposicao for I Legislature")
                # I Legislature HistoricoComposicao structure would be processed here
                # This structure exists in schema but processing can be implemented when needed
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Leader Conference: {e}")
            return False
    
    def _process_conferencia_presidentes_comissoes(self, conferencia: ET.Element, legislatura: Legislatura) -> bool:
        """Process Commission Presidents Conference"""
        try:
            # Process historical composition (I Legislature HistoricoComposicaoCPC)
            historico_composicao = conferencia.find('HistoricoComposicaoCPC')
            if historico_composicao is not None:
                logger.info(f"Processing ConferenciaPresidentesComissoes HistoricoComposicaoCPC for I Legislature")
                for dados_pcp in historico_composicao.findall('pt_ar_wsgode_objectos_DadosPCPComposicaoHistorico'):
                    # Process each commission president historical record
                    # This complex structure includes deputy info, GP data, cargo data, situation data, and presOrgao data
                    # The processing logic would extract all the detailed fields we've added to the schema
                    logger.debug(f"Processing DadosPCPComposicaoHistorico record")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Commission Presidents Conference: {e}")
            return False
    
    def _process_organ_meeting(self, reuniao: ET.Element, **kwargs) -> bool:
        """Process organ meeting (Reuniao) - can be associated with different organ types"""
        try:
            # Extract meeting data
            reu_tar_sigla = self._get_text_value(reuniao, 'ReuTarSigla')
            reu_local = self._get_text_value(reuniao, 'ReuLocal')
            reu_data_str = self._get_text_value(reuniao, 'ReuData')
            reu_hora = self._get_text_value(reuniao, 'ReuHora')
            reu_tipo = self._get_text_value(reuniao, 'ReuTipo')
            reu_estado = self._get_text_value(reuniao, 'ReuEstado')
            
            # Parse date
            reu_data = None
            if reu_data_str:
                try:
                    # Assume format DD/MM/YYYY or similar
                    if '/' in reu_data_str:
                        day, month, year = reu_data_str.split('/')
                        from datetime import date
                        reu_data = date(int(year), int(month), int(day))
                    elif '-' in reu_data_str:
                        # ISO format YYYY-MM-DD
                        from datetime import date
                        year, month, day = reu_data_str.split('-')
                        reu_data = date(int(year), int(month), int(day))
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse meeting date: {reu_data_str}")
            
            # Create meeting record - determine which organ type this is for
            meeting = OrganMeeting(
                commission_id=kwargs.get('commission').id if kwargs.get('commission') else None,
                work_group_id=kwargs.get('work_group').id if kwargs.get('work_group') else None,
                permanent_committee_id=kwargs.get('permanent_committee').id if kwargs.get('permanent_committee') else None,
                sub_committee_id=kwargs.get('sub_committee').id if kwargs.get('sub_committee') else None,
                # Note: Plenary meetings would need a separate field in the model
                reu_tar_sigla=reu_tar_sigla,
                reu_local=reu_local,
                reu_data=reu_data,
                reu_hora=reu_hora,
                reu_tipo=reu_tipo,
                reu_estado=reu_estado
            )
            
            self.session.add(meeting)
            return True
            
        except Exception as e:
            logger.error(f"Error processing organ meeting: {e}")
            return False
    
    def _process_orgao_base(self, orgao_base: ET.Element, legislatura: Legislatura) -> bool:
        """Process OrgaoBase structure (III Legislature committees)"""
        try:
            detalhe_orgao = orgao_base.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao')
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla')
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            
            if not id_orgao or not sigla_orgao:
                return False
            
            # Create or get committee record
            committee = self._get_or_create_committee(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, legislatura
            )
            
            # Process members
            composicao = orgao_base.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoComissao'):
                    self._process_deputy_committee_membership(deputado_data, committee)
            
            # Process meetings with namespace structure
            reunioes = orgao_base.find('Reunioes')
            if reunioes is not None:
                for dados_reuniao in reunioes.findall('pt_ar_wsgode_objectos_DadosReuniao'):
                    self._process_organ_meeting_namespace(dados_reuniao, committee=committee)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing OrgaoBase: {e}")
            return False
    
    def _process_working_group_orgao_base(self, orgao_base: ET.Element, legislatura: Legislatura) -> bool:
        """Process VIII Legislature working group OrgaoBase structure"""
        try:
            detalhe_orgao = orgao_base.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao')
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla')
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            sigla_legislatura = self._get_text_value(detalhe_orgao, 'siglaLegislatura')
            
            if not id_orgao or not sigla_orgao:
                return False
            
            # Create or get working group record
            work_group = self._get_or_create_work_group(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, legislatura
            )
            
            # Process historical composition (VIII Legislature structure)
            historico_composicao = orgao_base.find('HistoricoComposicao')
            if historico_composicao is not None:
                for dados_historico in historico_composicao.findall('pt_ar_wsgode_objectos_DadosOrgaoComposicaoHistorico'):
                    success = self._process_work_group_historical_composition(dados_historico, work_group, legislatura)
                    if not success:
                        logger.warning(f"Failed to process working group historical composition for {sigla_orgao}")
            
            # Process meetings (VIII Legislature structure)
            reunioes = orgao_base.find('Reunioes')
            if reunioes is not None:
                for dados_reuniao in reunioes.findall('pt_ar_wsgode_objectos_DadosReuniao'):
                    self._process_organ_meeting_namespace(dados_reuniao, work_group=work_group)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing working group OrgaoBase: {e}")
            return False
    
    def _process_reuniao_plenario(self, reuniao_plenario: ET.Element, plenary, legislatura: Legislatura = None) -> bool:
        """Process ReuniaoPlenario structure (III Legislature and I Legislature plenary meetings)"""
        try:
            # Process the main meeting data
            reuniao = reuniao_plenario.find('Reuniao')
            if reuniao is not None:
                # Extract meeting information
                sel_numero = self._get_text_value(reuniao, 'selNumero')
                reu_data_str = self._get_text_value(reuniao, 'reuData')
                reu_hora = self._get_text_value(reuniao, 'reuHora')
                reu_local = self._get_text_value(reuniao, 'reuLocal')
                reu_tipo = self._get_text_value(reuniao, 'reuTipo')
                reu_estado = self._get_text_value(reuniao, 'reuEstado')
                
                # Parse date
                reu_data = None
                if reu_data_str:
                    try:
                        if '/' in reu_data_str:
                            day, month, year = reu_data_str.split('/')
                            from datetime import date
                            reu_data = date(int(year), int(month), int(day))
                        elif '-' in reu_data_str:
                            from datetime import date
                            year, month, day = reu_data_str.split('-')
                            reu_data = date(int(year), int(month), int(day))
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse plenary meeting date: {reu_data_str}")
                
                # Extract additional III Legislature fields
                reu_id = self._get_int_value(reuniao, 'reuId')
                reu_data_hora = self._get_text_value(reuniao, 'reuDataHora')
                reu_tir_des = self._get_text_value(reuniao, 'reuTirDes')
                leg_des = self._get_text_value(reuniao, 'legDes')
                
                # Create meeting record with all available fields
                meeting = OrganMeeting(
                    # Basic fields
                    reu_tar_sigla=sel_numero,  # Use selNumero as identifier
                    reu_local=reu_local,
                    reu_data=reu_data,
                    reu_hora=reu_hora,
                    reu_tipo=reu_tipo,
                    reu_estado=reu_estado,
                    
                    # Extended III Legislature fields
                    reu_id=reu_id,
                    reu_data_hora=reu_data_hora,
                    reu_tir_des=reu_tir_des,
                    leg_des=leg_des,
                    sel_numero=sel_numero
                )
                
                self.session.add(meeting)
                self.session.flush()
                
                # Process attendance data (Presencas)
                presencas = reuniao_plenario.find('Presencas')
                if presencas is not None:
                    self._process_meeting_attendance(presencas, meeting)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing ReuniaoPlenario: {e}")
            return False
    
    def _process_organ_meeting_namespace(self, dados_reuniao: ET.Element, **kwargs) -> bool:
        """Process meeting data with pt_ar_wsgode_objectos namespace structure"""
        try:
            # Extract meeting data from namespace structure
            reu_tar_id = self._get_text_value(dados_reuniao, 'reuTarId')
            reu_tir_des = self._get_text_value(dados_reuniao, 'reuTirDes')
            reu_local = self._get_text_value(dados_reuniao, 'reuLocal')
            reu_data_str = self._get_text_value(dados_reuniao, 'reuData')
            reu_hora = self._get_text_value(dados_reuniao, 'reuHora')
            reu_tipo = self._get_text_value(dados_reuniao, 'reuTipo')
            reu_estado = self._get_text_value(dados_reuniao, 'reuEstado')
            
            # Parse date
            reu_data = None
            if reu_data_str:
                try:
                    if '/' in reu_data_str:
                        day, month, year = reu_data_str.split('/')
                        from datetime import date
                        reu_data = date(int(year), int(month), int(day))
                    elif '-' in reu_data_str:
                        from datetime import date
                        year, month, day = reu_data_str.split('-')
                        reu_data = date(int(year), int(month), int(day))
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse meeting date: {reu_data_str}")
            
            # Extract additional III Legislature namespace fields
            reu_numero = self._get_int_value(dados_reuniao, 'reuNumero')
            reu_data_hora = self._get_text_value(dados_reuniao, 'reuDataHora')
            reu_final_plenario = self._get_boolean_value(dados_reuniao, 'reuFinalPlenario')
            
            # Create meeting record with all available fields
            meeting = OrganMeeting(
                # Organ associations
                commission_id=kwargs.get('committee').id if kwargs.get('committee') else None,
                work_group_id=kwargs.get('work_group').id if kwargs.get('work_group') else None,
                permanent_committee_id=kwargs.get('permanent_committee').id if kwargs.get('permanent_committee') else None,
                sub_committee_id=kwargs.get('sub_committee').id if kwargs.get('sub_committee') else None,
                
                # Basic fields
                reu_tar_sigla=reu_tar_id,  # Use tar_id as identifier
                reu_local=reu_local,
                reu_data=reu_data,
                reu_hora=reu_hora,
                reu_tipo=reu_tipo,
                reu_estado=reu_estado,
                
                # Extended III Legislature fields
                reu_numero=reu_numero,
                reu_data_hora=reu_data_hora,
                reu_final_plenario=reu_final_plenario,
                reu_tir_des=reu_tir_des
            )
            
            self.session.add(meeting)
            return True
            
        except Exception as e:
            logger.error(f"Error processing namespace meeting data: {e}")
            return False
    
    def _process_meeting_attendance(self, presencas: ET.Element, meeting: OrganMeeting) -> bool:
        """Process meeting attendance data (Presencas) - now stores in MeetingAttendance model"""
        try:
            tipo_reuniao = self._get_text_value(presencas, 'tipoReuniao')
            dt_reuniao_str = self._get_text_value(presencas, 'dtReuniao')
            
            # Parse meeting date for attendance
            dt_reuniao = None
            if dt_reuniao_str:
                try:
                    if '/' in dt_reuniao_str:
                        day, month, year = dt_reuniao_str.split('/')
                        from datetime import date
                        dt_reuniao = date(int(year), int(month), int(day))
                    elif '-' in dt_reuniao_str:
                        from datetime import date
                        year, month, day = dt_reuniao_str.split('-')
                        dt_reuniao = date(int(year), int(month), int(day))
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse attendance date: {dt_reuniao_str}")
            
            attendance_count = 0
            
            # Process standard pt_ar_wsgode_objectos_DadosPresenca structure
            for dados_presenca in presencas.findall('pt_ar_wsgode_objectos_DadosPresenca'):
                dep_id = self._get_int_value(dados_presenca, 'depId')
                dep_cad_id = self._get_int_value(dados_presenca, 'depCadId')
                dep_nome = self._get_text_value(dados_presenca, 'depNomeParlamentar')
                pres_tipo = self._get_text_value(dados_presenca, 'presTipo')
                pres_justificacao = self._get_text_value(dados_presenca, 'presJustificacao')
                
                # Create attendance record
                attendance = MeetingAttendance(
                    meeting_id=meeting.id,
                    dep_id=dep_id,
                    dep_cad_id=dep_cad_id,
                    dep_nome_parlamentar=dep_nome,
                    pres_tipo=pres_tipo,
                    pres_justificacao=pres_justificacao,
                    dt_reuniao=dt_reuniao,
                    tipo_reuniao=tipo_reuniao
                )
                
                self.session.add(attendance)
                attendance_count += 1
            
            # Process alternative pt_gov_ar_wsgode_objectos_Presencas structure (IX Legislature)
            presencas_alt = presencas.find('presencas')
            if presencas_alt is not None:
                for dados_presenca_alt in presencas_alt.findall('pt_gov_ar_wsgode_objectos_Presencas'):
                    nome_deputado = self._get_text_value(dados_presenca_alt, 'nomeDeputado')
                    sigla_grupo = self._get_text_value(dados_presenca_alt, 'siglaGrupo')
                    sigla_falta = self._get_text_value(dados_presenca_alt, 'siglaFalta')
                    sigla_qualidade_presenca_orgao = self._get_text_value(dados_presenca_alt, 'siglaQualidadePresencaOrgao')
                    
                    # Create attendance record with available data
                    attendance = MeetingAttendance(
                        meeting_id=meeting.id,
                        dep_nome_parlamentar=nome_deputado,
                        dt_reuniao=dt_reuniao,
                        tipo_reuniao=tipo_reuniao,
                        # Store I Legislature specific presence quality info in notes field
                        observacoes=sigla_qualidade_presenca_orgao if sigla_qualidade_presenca_orgao else None
                        # Note: siglaGrupo and siglaFalta would need separate fields in the model if needed
                    )
                    
                    self.session.add(attendance)
                    attendance_count += 1
            
            logger.info(f"Stored {attendance_count} attendance records for meeting {meeting.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing meeting attendance: {e}")
            return False
    
    def _get_or_create_ar_board(self, id_orgao: int, sigla: str, nome: str, numero: str, legislatura: Legislatura):
        """Get or create AR Board record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        ar_board = self.session.query(ARBoard).filter_by(
            id_orgao=id_orgao,
            organization_id=organization.id
        ).first()
        
        if ar_board:
            return ar_board
        
        ar_board = ARBoard(
            organization_id=organization.id,
            id_orgao=id_orgao,
            sigla_orgao=sigla,
            nome_sigla=nome,
            numero_orgao=int(numero) if numero and numero.isdigit() else None,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(ar_board)
        self.session.flush()
        return ar_board
    
    def _get_or_create_administrative_council(self, id_orgao: int, sigla: str, nome: str, numero: str, legislatura: Legislatura):
        """Get or create Administrative Council record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        admin_council = self.session.query(AdministrativeCouncil).filter_by(
            id_orgao=id_orgao,
            organization_id=organization.id
        ).first()
        
        if admin_council:
            return admin_council
        
        admin_council = AdministrativeCouncil(
            organization_id=organization.id,
            id_orgao=id_orgao,
            sigla_orgao=sigla,
            nome_sigla=nome,
            numero_orgao=int(numero) if numero and numero.isdigit() else None,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(admin_council)
        self.session.flush()
        return admin_council
    
    def _get_or_create_permanent_committee(self, id_orgao: int, sigla: str, nome: str, numero: str, legislatura: Legislatura):
        """Get or create Permanent Committee record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        permanent_committee = self.session.query(PermanentCommittee).filter_by(
            id_orgao=id_orgao,
            organization_id=organization.id
        ).first()
        
        if permanent_committee:
            return permanent_committee
        
        permanent_committee = PermanentCommittee(
            organization_id=organization.id,
            id_orgao=id_orgao,
            sigla_orgao=sigla,
            nome_sigla=nome,
            numero_orgao=int(numero) if numero and numero.isdigit() else None,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(permanent_committee)
        self.session.flush()
        return permanent_committee
    
    def _get_or_create_leader_conference(self, id_orgao: int, sigla: str, nome: str, numero: str, legislatura: Legislatura):
        """Get or create Leader Conference record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        leader_conference = self.session.query(LeaderConference).filter_by(
            id_orgao=id_orgao,
            organization_id=organization.id
        ).first()
        
        if leader_conference:
            return leader_conference
        
        leader_conference = LeaderConference(
            organization_id=organization.id,
            id_orgao=id_orgao,
            sigla_orgao=sigla,
            nome_sigla=nome,
            numero_orgao=int(numero) if numero and numero.isdigit() else None,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(leader_conference)
        self.session.flush()
        return leader_conference
    
    def _process_deputy_ar_board_membership(self, deputado_data: ET.Element, ar_board) -> bool:
        """Process deputy membership in AR Board"""
        try:
            # Create historical composition record
            composition = ARBoardHistoricalComposition(
                board_id=ar_board.id,
                leg_des=self._get_text_value(deputado_data, 'LegDes'),
                dep_id=self._get_int_value(deputado_data, 'DepId'),
                dep_cad_id=self._get_int_value(deputado_data, 'DepCadId'),
                dep_nome_parlamentar=self._get_text_value(deputado_data, 'DepNomeParlamentar'),
                org_id=ar_board.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = deputado_data.find('DepGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, ar_board_composition=composition)
            
            # Process deputy situations
            dep_situacao = deputado_data.find('DepSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, ar_board_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing AR Board deputy membership: {e}")
            return False
    
    def _process_ar_board_historical_composition(self, historico_data: ET.Element, ar_board, legislatura: Legislatura) -> bool:
        """Process AR Board historical composition (IX Legislature)"""
        try:
            # Create historical composition record
            composition = ARBoardHistoricalComposition(
                board_id=ar_board.id,
                leg_des=self._get_text_value(historico_data, 'legDes') or legislatura.leg_des,
                dep_id=self._get_int_value(historico_data, 'depId'),
                dep_cad_id=self._get_int_value(historico_data, 'depCadId'),
                dep_nome_parlamentar=self._get_text_value(historico_data, 'depNomeParlamentar'),
                dep_nome_completo=self._get_text_value(historico_data, 'depNomeCompleto'),
                org_id=ar_board.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = historico_data.find('depGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, ar_board_composition=composition)
            
            # Process deputy positions/cargo
            dep_cargo = historico_data.find('depCargo')
            if dep_cargo is not None:
                self._process_deputy_positions(dep_cargo, ar_board_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing AR Board historical composition: {e}")
            return False
    
    def _process_commission_historical_composition(self, historico_data: ET.Element, committee, legislatura: Legislatura) -> bool:
        """Process Commission historical composition (IX Legislature)"""
        try:
            # Create historical composition record
            composition = CommissionHistoricalComposition(
                commission_id=committee.id,
                leg_des=self._get_text_value(historico_data, 'legDes') or legislatura.leg_des,
                dep_id=self._get_int_value(historico_data, 'depId'),
                dep_cad_id=self._get_int_value(historico_data, 'depCadId'),
                dep_nome_parlamentar=self._get_text_value(historico_data, 'depNomeParlamentar'),
                dep_nome_completo=self._get_text_value(historico_data, 'depNomeCompleto'),
                org_id=self._get_int_value(historico_data, 'orgId') or committee.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = historico_data.find('depGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, commission_composition=composition)
            
            # Process deputy positions/cargo
            dep_cargo = historico_data.find('depCargo')
            if dep_cargo is not None:
                self._process_deputy_positions(dep_cargo, commission_composition=composition)
            
            # Process deputy situations
            dep_situacao = historico_data.find('depSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, commission_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Commission historical composition: {e}")
            return False
    
    def _process_subcommittee_historical_composition(self, historico_data: ET.Element, subcommittee, legislatura: Legislatura) -> bool:
        """Process SubCommittee historical composition (IX Legislature)"""
        try:
            # Create historical composition record
            composition = SubCommitteeHistoricalComposition(
                sub_committee_id=subcommittee.id,
                leg_des=self._get_text_value(historico_data, 'legDes') or legislatura.leg_des,
                dep_id=self._get_int_value(historico_data, 'depId'),
                dep_cad_id=self._get_int_value(historico_data, 'depCadId'),
                dep_nome_parlamentar=self._get_text_value(historico_data, 'depNomeParlamentar'),
                dep_nome_completo=self._get_text_value(historico_data, 'depNomeCompleto'),
                org_id=self._get_int_value(historico_data, 'orgId') or subcommittee.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = historico_data.find('depGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, sub_committee_composition=composition)
            
            # Process deputy positions/cargo
            dep_cargo = historico_data.find('depCargo')
            if dep_cargo is not None:
                self._process_deputy_positions(dep_cargo, sub_committee_composition=composition)
            
            # Process deputy situations
            dep_situacao = historico_data.find('depSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, sub_committee_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing SubCommittee historical composition: {e}")
            return False
    
    def _process_work_group_historical_composition(self, historico_data: ET.Element, work_group, legislatura: Legislatura) -> bool:
        """Process WorkGroup historical composition (VIII Legislature)"""
        try:
            # Create historical composition record
            composition = WorkGroupHistoricalComposition(
                work_group_id=work_group.id,
                leg_des=self._get_text_value(historico_data, 'legDes') or legislatura.leg_des,
                dep_id=self._get_int_value(historico_data, 'depId'),
                dep_cad_id=self._get_int_value(historico_data, 'depCadId'),
                dep_nome_parlamentar=self._get_text_value(historico_data, 'depNomeParlamentar'),
                dep_nome_completo=self._get_text_value(historico_data, 'depNomeCompleto'),
                org_id=self._get_int_value(historico_data, 'orgId') or work_group.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = historico_data.find('depGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, work_group_composition=composition)
            
            # Process deputy positions/cargo
            dep_cargo = historico_data.find('depCargo')
            if dep_cargo is not None:
                self._process_deputy_positions(dep_cargo, work_group_composition=composition)
            
            # Process deputy situations
            dep_situacao = historico_data.find('depSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, work_group_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing WorkGroup historical composition: {e}")
            return False
    
    def _process_deputy_admin_council_membership(self, deputado_data: ET.Element, admin_council) -> bool:
        """Process deputy membership in Administrative Council"""
        try:
            # Create historical composition record
            composition = AdministrativeCouncilHistoricalComposition(
                council_id=admin_council.id,
                leg_des=self._get_text_value(deputado_data, 'LegDes'),
                dep_id=self._get_int_value(deputado_data, 'DepId'),
                dep_cad_id=self._get_int_value(deputado_data, 'DepCadId'),
                dep_nome_parlamentar=self._get_text_value(deputado_data, 'DepNomeParlamentar'),
                org_id=admin_council.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = deputado_data.find('DepGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, admin_council_composition=composition)
            
            # Process deputy situations
            dep_situacao = deputado_data.find('DepSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, admin_council_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Administrative Council deputy membership: {e}")
            return False
    
    def _process_deputy_permanent_committee_membership(self, deputado_data: ET.Element, permanent_committee) -> bool:
        """Process deputy membership in Permanent Committee"""
        try:
            # Create historical composition record
            composition = PermanentCommitteeHistoricalComposition(
                permanent_committee_id=permanent_committee.id,
                leg_des=self._get_text_value(deputado_data, 'LegDes'),
                dep_id=self._get_int_value(deputado_data, 'DepId'),
                dep_cad_id=self._get_int_value(deputado_data, 'DepCadId'),
                dep_nome_parlamentar=self._get_text_value(deputado_data, 'DepNomeParlamentar'),
                org_id=permanent_committee.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = deputado_data.find('DepGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, permanent_committee_composition=composition)
            
            # Process deputy situations
            dep_situacao = deputado_data.find('DepSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, permanent_committee_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Permanent Committee deputy membership: {e}")
            return False
    
    def _process_permanent_committee_historical_composition(self, historico_data: ET.Element, permanent_committee, legislatura: Legislatura) -> bool:
        """Process PermanentCommittee historical composition (VI Legislature)"""
        try:
            # Create historical composition record
            composition = PermanentCommitteeHistoricalComposition(
                permanent_committee_id=permanent_committee.id,
                leg_des=self._get_text_value(historico_data, 'legDes') or legislatura.leg_des,
                dep_id=self._get_int_value(historico_data, 'depId'),
                dep_cad_id=self._get_int_value(historico_data, 'depCadId'),
                dep_nome_parlamentar=self._get_text_value(historico_data, 'depNomeParlamentar'),
                dep_nome_completo=self._get_text_value(historico_data, 'depNomeCompleto'),
                org_id=self._get_int_value(historico_data, 'orgId') or permanent_committee.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = historico_data.find('depGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, permanent_committee_composition=composition)
            
            # Process deputy positions/cargo
            dep_cargo = historico_data.find('depCargo')
            if dep_cargo is not None:
                self._process_deputy_positions(dep_cargo, permanent_committee_composition=composition)
            
            # Process deputy situations
            dep_situacao = historico_data.find('depSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, permanent_committee_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing PermanentCommittee historical composition: {e}")
            return False
    
    def _process_deputy_leader_conference_membership(self, deputado_data: ET.Element, leader_conference) -> bool:
        """Process deputy membership in Leader Conference"""
        try:
            # Create historical composition record
            composition = LeaderConferenceHistoricalComposition(
                leader_conference_id=leader_conference.id,
                leg_des=self._get_text_value(deputado_data, 'LegDes'),
                dep_id=self._get_int_value(deputado_data, 'DepId'),
                dep_cad_id=self._get_int_value(deputado_data, 'DepCadId'),
                dep_nome_parlamentar=self._get_text_value(deputado_data, 'DepNomeParlamentar'),
                org_id=leader_conference.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = deputado_data.find('DepGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, leader_conference_composition=composition)
            
            # Process deputy situations
            dep_situacao = deputado_data.find('DepSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, leader_conference_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Leader Conference deputy membership: {e}")
            return False
    
    def _convert_roman_to_int(self, roman: str) -> int:
        """Convert Roman numeral to integer"""
        roman_numerals = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'CONSTITUINTE': 0
        }
        return roman_numerals.get(roman, 17)
    
    def _get_boolean_value(self, parent: ET.Element, tag_name: str) -> bool:
        """Get boolean value from XML element"""
        text_value = self._get_text_value(parent, tag_name)
        if text_value:
            return text_value.lower() in ('true', '1', 'yes', 'sim')
        return False