# Categorias de Dados Abertos do Parlamento Português

## Categorias Identificadas

Baseado na análise do site https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx

### 1. Agenda Parlamentar
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAAgendaParl.aspx
- **Descrição**: Atividades que irão decorrer nos próximos dias na AR (Reuniões Plenárias, Reuniões de Comissão, Reuniões dos Grupos de Trabalho, Visitas à AR, Agenda do Presidente da AR, Outros eventos)
- **Dados**: eventos atuais e futuros

### 2. Atividades
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAatividades.aspx
- **Descrição**: Atividades que decorrem na AR de acordo com o Regimento do Parlamento
- **Tipos**: Apreciação de relatórios entregues por entidades externas, Audições, Audições Parlamentares, Conta Geral do Estado, Debates, Declarações Políticas, Defesa Nacional, Deslocações no âmbito das Comissões, Deslocações do Presidente da República, Eleição e composição para órgãos externos, Eventos no âmbito de Comissões, Grandes Opções do Concelho Estratégico da Defesa Nacional, Interpelações ao Governo, Orientação e Conta de Gerência da AR, Orientação e Conta Orçamental, Perguntas ao Governo, Perguntas de Trabalho, Orçamento do Estado, Perguntas Internas, Programa Interno

### 3. Atividade do Deputado
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAatividadeDeputado.aspx
- **Descrição**: Atividade individual de cada deputado

### 4. Boletim Informativo
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DABoletimInformativo.aspx
- **Descrição**: Boletins informativos

### 5. Composição de Órgãos
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAComposicaoOrgaos.aspx
- **Descrição**: Composição dos órgãos parlamentares

### 6. Cooperação Parlamentar
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DACooperacaoParlamentar.aspx
- **Descrição**: Atividades de cooperação parlamentar

### 7. Delegações Eventuais
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DADelegacoesEventuais.aspx
- **Descrição**: Delegações eventuais

### 8. Delegações Permanentes
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DADelegacoesPermanentes.aspx
- **Descrição**: Delegações permanentes

### 9. DAR (Diário da Assembleia da República)
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAdar.aspx
- **Descrição**: Diário da Assembleia da República

### 10. Diplomas Aprovados
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DADiplomasAprovados.aspx
- **Descrição**: Diplomas aprovados pelo parlamento

### 11. GPA (Grupos Parlamentares de Amizade)
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAGPA.aspx
- **Descrição**: Grupos Parlamentares de Amizade

### 12. Informação Base
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAInformacaoBase.aspx
- **Descrição**: Informação base sobre deputados, partidos, círculos eleitorais
- **Status**: ✅ JÁ IMPLEMENTADO

### 13. Iniciativas
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAIniciativas.aspx
- **Descrição**: Iniciativas legislativas e não legislativas
- **Status**: ✅ JÁ ANALISADO

### 14. Intervenções
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAIntervencoes.aspx
- **Descrição**: Intervenções dos deputados em plenário

### 15. OE (Orçamento do Estado)
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAOE.aspx
- **Descrição**: Dados sobre o Orçamento do Estado

### 16. Petições
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAPeticoes.aspx
- **Descrição**: Petições apresentadas ao parlamento

### 17. Perguntas e Requerimentos
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAPerguntasRequerimentos.aspx
- **Descrição**: Perguntas e requerimentos dos deputados

### 18. Registo Biográfico
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DARegistoBiografico.aspx
- **Descrição**: Informação biográfica dos deputados

### 19. Reuniões e Visitas
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAReunioesVisitas.aspx
- **Descrição**: Reuniões e visitas parlamentares

### 20. Votações
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAVotacoes.aspx
- **Descrição**: Resultados das votações parlamentares

### 21. Votos
- **URL**: https://www.parlamento.pt/Cidadania/Paginas/DAVotos.aspx
- **Descrição**: Votos individuais dos deputados

## Relações Identificadas

### Relações Principais para Implementar:

1. **Deputado → Atividades**
   - Intervenções do deputado
   - Iniciativas apresentadas
   - Perguntas e requerimentos
   - Votações individuais

2. **Partido → Deputados → Atividades**
   - Navegação hierárquica completa

3. **Iniciativas → Votações**
   - Relação entre propostas e seus resultados

4. **Agenda → Atividades → Resultados**
   - Agenda diária com ordens de trabalho e resultados

5. **Deputado → Presenças/Faltas**
   - Atividade individual e assiduidade

6. **Comissões → Deputados → Atividades**
   - Trabalho em comissões parlamentares

## Prioridades para Implementação

### Alta Prioridade:
1. **Votações** - Para mostrar como cada deputado/partido votou
2. **Intervenções** - Discursos e participações
3. **Iniciativas** - Propostas de lei e sua autoria
4. **Agenda Parlamentar** - Atividades diárias

### Média Prioridade:
5. **Perguntas e Requerimentos** - Atividade de fiscalização
6. **Atividade do Deputado** - Resumo individual
7. **Petições** - Participação cidadã

### Baixa Prioridade:
8. **Registo Biográfico** - Informação pessoal
9. **Reuniões e Visitas** - Atividades protocolares
10. **Cooperação Parlamentar** - Relações internacionais

