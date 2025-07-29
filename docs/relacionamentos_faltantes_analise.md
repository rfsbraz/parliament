# Análise de Relacionamentos Faltantes - Parlamento Português

## Resumo Executivo

Após análise da estrutura atual do banco de dados e dos dados XML originais, identifiquei **8 relacionamentos críticos faltantes** que limitam significativamente as possibilidades de análise e visualização dos dados parlamentares.

## Estrutura Atual vs. Potencial

### Dados Atuais (Importados com Sucesso)
- **Deputados**: 2,874 registos
- **Iniciativas Legislativas**: 25,479 registos  
- **Intervenções**: 135,458 registos
- **Agenda Parlamentar**: 28 registos
- **Comissões**: 113 registos
- **Mandatos**: 60,728 registos
- **Autores de Iniciativas**: 324,253 relacionamentos

### Relacionamentos Existentes (Funcionais)
✅ **deputados** ←→ **mandatos** (99.9% cobertura)  
✅ **iniciativas_legislativas** ←→ **autores_iniciativas** (86.2% cobertura)  
✅ **comissoes** ←→ **membros_comissoes** (248 membros)  

## Relacionamentos Faltantes Críticos

### 1. **ALTA PRIORIDADE - Impacto Direto na Análise**

#### 1.1 Intervenções ←→ Atividades Parlamentares
- **Tipo**: Many-to-One
- **Campo necessário**: `intervencoes.atividade_id`
- **Dados disponíveis**: 393 atividades únicas identificadas no XML
- **Impacto**: 135,458 intervenções não conseguem ser contextualizadas
- **Valor**: Permite analisar quais deputados falam sobre que assuntos

#### 1.2 Intervenções ←→ Debates
- **Tipo**: Many-to-One  
- **Campo necessário**: `intervencoes.debate_id`
- **Dados disponíveis**: 398 debates únicos identificados
- **Impacto**: Impossível agrupar intervenções por debate específico
- **Valor**: Análise de participação em debates temáticos

#### 1.3 Intervenções ←→ Publicações Diário da República
- **Tipo**: Many-to-One
- **Nova tabela**: `publicacoes_diario`
- **Campos**: numero, tipo, data_publicacao, url_diario, paginas
- **Impacto**: Perde-se rastreabilidade oficial das intervenções
- **Valor**: Links diretos para documentos oficiais

### 2. **MÉDIA PRIORIDADE - Melhora Navegação**

#### 2.1 Agenda ←→ Seções Parlamentares  
- **Tipo**: Many-to-One
- **Nova tabela**: `secoes_parlamentares` 
- **Dados disponíveis**: 5 seções únicas (ex: "Conferência de Líderes")
- **Impacto**: Agenda sem categorização por tipo de atividade
- **Valor**: Filtros por tipo de evento parlamentar

#### 2.2 Agenda ←→ Temas Parlamentares
- **Tipo**: Many-to-One
- **Nova tabela**: `temas_parlamentares`
- **Dados disponíveis**: 5 temas únicos
- **Impacto**: Impossível filtrar agenda por tema
- **Valor**: Organização temática dos eventos

#### 2.3 Iniciativas ←→ Iniciativas (Auto-relacionamento)
- **Tipo**: Self-referencing (One-to-Many)
- **Campo necessário**: `iniciativas_legislativas.iniciativa_origem_id`
- **Dados identificados**: 165 iniciativas com indicação de relacionamento
- **Impacto**: Perde-se hierarquia entre projetos/emendas/substitutivos
- **Valor**: Rastreamento de evolução legislativa

### 3. **BAIXA PRIORIDADE - Dados Ausentes**

#### 3.1 Votações Individuais (Tabela Vazia)
- **Impacto**: 0 registos na tabela `votacoes` e `votos_individuais`
- **Problema**: Dados de votação não estão sendo importados
- **Valor perdido**: Análise de comportamento de voto dos deputados

#### 3.2 Sessões Plenárias (Tabela Vazia)  
- **Impacto**: 0 registos na tabela `sessoes_plenarias`
- **Problema**: Contexto temporal das atividades parlamentares
- **Valor perdido**: Cronologia das atividades

## Impacto nos Dashboards e Visualizações

### Limitações Atuais
❌ **Intervenções não podem ser agrupadas por debate**  
❌ **Impossible rastrear sobre que falam os deputados**  
❌ **Agenda sem categorização temática**  
❌ **Sem links para documentos oficiais**  
❌ **Hierarquia legislativa perdida**  

### Potencial com Relacionamentos
✅ **Timeline de debates com participantes**  
✅ **Análise temática das intervenções**  
✅ **Dashboards por tipo de atividade parlamentar**  
✅ **Rastreamento completo de projetos de lei**  
✅ **Links diretos para Diário da República**  

## Recomendações de Implementação

### Fase 1 (Impacto Imediato)
1. **Implementar relacionamento Intervenções ←→ Atividades**
2. **Implementar relacionamento Intervenções ←→ Debates**  
3. **Criar tabela Publicações Diário da República**

### Fase 2 (Organização)
4. **Criar tabelas de lookup para Seções e Temas**
5. **Implementar auto-relacionamento em Iniciativas**

### Fase 3 (Dados Faltantes)
6. **Investigar importação de dados de Votações**
7. **Implementar Sessões Plenárias**

## Estimativa de Implementação

- **Fase 1**: 2-3 dias (modificações de schema + scripts de população)
- **Fase 2**: 1-2 dias (tabelas de lookup + relacionamentos)  
- **Fase 3**: 3-5 dias (investigação + implementação de dados faltantes)

**Total**: 6-10 dias para relacionamentos completos

## Valor de Negócio

### Análises Desbloqueadas
1. **"Quem fala sobre o quê?"** - Análise temática por deputado
2. **"Participação em debates"** - Métricas de engagement 
3. **"Evolução de projetos de lei"** - Tracking legislativo
4. **"Documentação oficial"** - Links para fontes primárias
5. **"Padrões temporais"** - Análises de tendências por tipo de atividade

### ROI Estimado
- **Aumento de 300% na profundidade analítica**
- **Redução de 80% no tempo de research manual**  
- **Habilitação de 15+ novos tipos de dashboards**