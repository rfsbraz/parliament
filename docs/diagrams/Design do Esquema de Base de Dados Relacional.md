# Design do Esquema de Base de Dados Relacional
## Sistema de Análise de Dados Parlamentares Portugueses

**Autor**: Manus AI  
**Data**: 25 de Julho de 2025  
**Versão**: 1.0

## 1. Introdução e Objetivos

Este documento apresenta o design detalhado do esquema de base de dados relacional para o sistema de análise de dados parlamentares portugueses. O objetivo principal é criar uma estrutura de dados normalizada e eficiente que permita armazenar, relacionar e analisar todos os aspectos da atividade parlamentar da Assembleia da República.

A base de dados foi concebida para suportar análises complexas sobre padrões de votação, atividade legislativa, participação de deputados, eficácia partidária e correlações entre diferentes tipos de atividades parlamentares. O esquema segue os princípios de normalização de bases de dados relacionais, garantindo integridade referencial e minimizando redundância de dados.

## 2. Análise dos Requisitos de Dados

Com base na análise detalhada dos ficheiros XML fornecidos pela Assembleia da República, identificámos as seguintes entidades principais e os seus relacionamentos:

### 2.1 Entidades Fundamentais
- **Legislaturas**: Períodos legislativos com informação temporal
- **Deputados**: Representantes eleitos com dados biográficos e mandatos
- **Partidos**: Organizações políticas com informação histórica
- **Círculos Eleitorais**: Divisões geográficas para eleições
- **Comissões**: Órgãos especializados do parlamento

### 2.2 Entidades de Atividade
- **Iniciativas**: Propostas e projetos legislativos
- **Votações**: Processos de decisão com resultados detalhados
- **Eventos da Agenda**: Atividades programadas e realizadas
- **Intervenções**: Participações em debates e sessões
- **Petições**: Solicitações da sociedade civil

### 2.3 Relacionamentos Complexos
- Deputados pertencem a partidos e representam círculos eleitorais
- Iniciativas são votadas em múltiplas ocasiões com votos individuais
- Eventos da agenda envolvem grupos parlamentares e deputados
- Comissões analisam iniciativas e organizam audiências
- Petições podem influenciar iniciativas legislativas

## 3. Arquitetura do Esquema de Dados

### 3.1 Princípios de Design

O esquema foi desenvolvido seguindo os seguintes princípios fundamentais:

**Normalização**: Aplicação das formas normais para eliminar redundância e garantir consistência dos dados. As tabelas estão normalizadas até à terceira forma normal, com algumas exceções justificadas por requisitos de performance.

**Integridade Referencial**: Todas as relações entre tabelas são enforçadas através de chaves estrangeiras com políticas de cascata apropriadas para manter a consistência dos dados.

**Flexibilidade Temporal**: O esquema suporta dados históricos e mudanças ao longo do tempo, permitindo análises longitudinais da atividade parlamentar.

**Escalabilidade**: A estrutura foi concebida para suportar grandes volumes de dados e consultas complexas, com índices estrategicamente posicionados.

**Extensibilidade**: O design permite a adição de novas categorias de dados sem impacto significativo na estrutura existente.

### 3.2 Convenções de Nomenclatura

- **Tabelas**: Nomes em português, no plural, usando snake_case (ex: `deputados`, `iniciativas_legislativas`)
- **Colunas**: Nomes descritivos em português, usando snake_case
- **Chaves Primárias**: Sempre denominadas `id` com tipo INTEGER AUTOINCREMENT
- **Chaves Estrangeiras**: Formato `{tabela_referenciada}_id`
- **Índices**: Prefixo `idx_` seguido do nome da tabela e coluna(s)

## 4. Estrutura Detalhada das Tabelas

### 4.1 Tabelas de Referência Base


#### 4.1.1 Tabela: legislaturas

Esta tabela armazena informação sobre os períodos legislativos da Assembleia da República.

```sql
CREATE TABLE legislaturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero VARCHAR(10) NOT NULL UNIQUE,           -- Ex: "XVII", "XVI"
    designacao VARCHAR(100) NOT NULL,             -- Nome completo da legislatura
    data_inicio DATE NOT NULL,                    -- Data de início da legislatura
    data_fim DATE,                                -- Data de fim (NULL se ativa)
    ativa BOOLEAN DEFAULT FALSE,                  -- Se é a legislatura atual
    observacoes TEXT,                             -- Notas adicionais
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.2 Tabela: partidos

Armazena informação sobre os partidos políticos e suas características.

```sql
CREATE TABLE partidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sigla VARCHAR(20) NOT NULL UNIQUE,            -- Ex: "PS", "PSD", "BE"
    designacao_completa VARCHAR(200) NOT NULL,    -- Nome completo do partido
    data_constituicao DATE,                       -- Data de fundação
    cor_representativa VARCHAR(7),                -- Código hexadecimal da cor
    ideologia VARCHAR(50),                        -- Classificação ideológica
    ativo BOOLEAN DEFAULT TRUE,                   -- Se ainda existe
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.3 Tabela: circulos_eleitorais

Define as divisões geográficas para as eleições parlamentares.

```sql
CREATE TABLE circulos_eleitorais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    designacao VARCHAR(100) NOT NULL UNIQUE,     -- Ex: "Lisboa", "Porto"
    tipo VARCHAR(30) NOT NULL,                    -- "territorial", "emigracao"
    numero_mandatos INTEGER,                      -- Número de deputados eleitos
    regiao VARCHAR(50),                           -- Região geográfica
    ativo BOOLEAN DEFAULT TRUE,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.4 Tabela: comissoes

Informação sobre as comissões parlamentares permanentes e eventuais.

```sql
CREATE TABLE comissoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sigla VARCHAR(20) NOT NULL,                   -- Sigla da comissão
    designacao VARCHAR(200) NOT NULL,            -- Nome completo
    tipo VARCHAR(30) NOT NULL,                    -- "permanente", "eventual"
    area_competencia TEXT,                        -- Descrição das competências
    data_criacao DATE,
    data_extincao DATE,                           -- NULL se ativa
    ativa BOOLEAN DEFAULT TRUE,
    legislatura_id INTEGER,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (legislatura_id) REFERENCES legislaturas(id)
);
```

### 4.2 Tabelas de Pessoas e Mandatos

#### 4.2.1 Tabela: deputados

Armazena informação biográfica e política dos deputados.

```sql
CREATE TABLE deputados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_completo VARCHAR(200) NOT NULL,         -- Nome civil completo
    nome_parlamentar VARCHAR(200),               -- Nome usado no parlamento
    data_nascimento DATE,
    sexo CHAR(1) CHECK (sexo IN ('M', 'F')),    -- Masculino/Feminino
    profissao VARCHAR(100),                      -- Profissão principal
    habilitacoes_literarias VARCHAR(100),        -- Nível de escolaridade
    naturalidade VARCHAR(100),                   -- Local de nascimento
    foto_url VARCHAR(500),                       -- URL da fotografia oficial
    biografia TEXT,                              -- Biografia detalhada
    ativo BOOLEAN DEFAULT TRUE,                  -- Se ainda é deputado
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.2.2 Tabela: mandatos

Relaciona deputados com partidos, círculos e legislaturas, permitindo histórico completo.

```sql
CREATE TABLE mandatos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deputado_id INTEGER NOT NULL,
    partido_id INTEGER NOT NULL,
    circulo_eleitoral_id INTEGER NOT NULL,
    legislatura_id INTEGER NOT NULL,
    data_inicio DATE NOT NULL,                   -- Início do mandato
    data_fim DATE,                               -- Fim do mandato (NULL se ativo)
    motivo_fim VARCHAR(50),                      -- "fim_legislatura", "renuncia", etc.
    numero_votos INTEGER,                        -- Votos recebidos na eleição
    posicao_lista INTEGER,                       -- Posição na lista eleitoral
    ativo BOOLEAN DEFAULT TRUE,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deputado_id) REFERENCES deputados(id),
    FOREIGN KEY (partido_id) REFERENCES partidos(id),
    FOREIGN KEY (circulo_eleitoral_id) REFERENCES circulos_eleitorais(id),
    FOREIGN KEY (legislatura_id) REFERENCES legislaturas(id),
    UNIQUE(deputado_id, legislatura_id)          -- Um deputado por legislatura
);
```

### 4.3 Tabelas de Atividade Legislativa

#### 4.3.1 Tabela: tipos_iniciativa

Define os diferentes tipos de iniciativas legislativas.

```sql
CREATE TABLE tipos_iniciativa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(10) NOT NULL UNIQUE,          -- Ex: "P", "PL", "PR"
    designacao VARCHAR(100) NOT NULL,            -- "Proposta de Lei", etc.
    descricao TEXT,                              -- Descrição detalhada
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.3.2 Tabela: iniciativas_legislativas

Armazena todas as iniciativas apresentadas no parlamento.

```sql
CREATE TABLE iniciativas_legislativas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero INTEGER NOT NULL,                     -- Número sequencial
    tipo_iniciativa_id INTEGER NOT NULL,
    legislatura_id INTEGER NOT NULL,
    sessao_legislativa INTEGER NOT NULL,
    titulo TEXT NOT NULL,                        -- Título da iniciativa
    sumario TEXT,                                -- Resumo do conteúdo
    data_entrada DATE NOT NULL,                  -- Data de entrada
    data_publicacao DATE,                        -- Data de publicação
    estado VARCHAR(50) NOT NULL,                 -- "em_tramitacao", "aprovada", etc.
    tem_texto_substituto BOOLEAN DEFAULT FALSE,
    link_texto_original VARCHAR(500),            -- URL do documento
    link_texto_final VARCHAR(500),               -- URL da versão final
    comissao_id INTEGER,                         -- Comissão responsável
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tipo_iniciativa_id) REFERENCES tipos_iniciativa(id),
    FOREIGN KEY (legislatura_id) REFERENCES legislaturas(id),
    FOREIGN KEY (comissao_id) REFERENCES comissoes(id),
    UNIQUE(numero, tipo_iniciativa_id, legislatura_id)
);
```

#### 4.3.3 Tabela: autores_iniciativas

Relaciona iniciativas com seus autores (deputados, governo, etc.).

```sql
CREATE TABLE autores_iniciativas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iniciativa_id INTEGER NOT NULL,
    tipo_autor VARCHAR(20) NOT NULL,             -- "deputado", "governo", "grupo_parlamentar"
    deputado_id INTEGER,                         -- Se autor é deputado
    partido_id INTEGER,                          -- Se autor é partido/grupo
    entidade_externa VARCHAR(200),               -- Se autor é entidade externa
    papel VARCHAR(30) DEFAULT 'autor',           -- "autor", "co_autor", "subscritor"
    ordem INTEGER DEFAULT 1,                     -- Ordem de autoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (iniciativa_id) REFERENCES iniciativas_legislativas(id) ON DELETE CASCADE,
    FOREIGN KEY (deputado_id) REFERENCES deputados(id),
    FOREIGN KEY (partido_id) REFERENCES partidos(id)
);
```

### 4.4 Tabelas de Votações

#### 4.4.1 Tabela: sessoes_votacao

Armazena informação sobre as sessões onde ocorrem votações.

```sql
CREATE TABLE sessoes_votacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_reuniao INTEGER NOT NULL,
    tipo_reuniao VARCHAR(50) NOT NULL,           -- "plenaria", "comissao"
    data_sessao DATE NOT NULL,
    hora_inicio TIME,
    hora_fim TIME,
    legislatura_id INTEGER NOT NULL,
    sessao_legislativa INTEGER NOT NULL,
    comissao_id INTEGER,                         -- NULL se plenária
    presidente_sessao_id INTEGER,                -- Deputado que presidiu
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (legislatura_id) REFERENCES legislaturas(id),
    FOREIGN KEY (comissao_id) REFERENCES comissoes(id),
    FOREIGN KEY (presidente_sessao_id) REFERENCES deputados(id)
);
```

#### 4.4.2 Tabela: votacoes

Regista cada votação individual que ocorre numa sessão.

```sql
CREATE TABLE votacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iniciativa_id INTEGER NOT NULL,
    sessao_votacao_id INTEGER NOT NULL,
    numero_votacao INTEGER NOT NULL,             -- Número sequencial na sessão
    objeto_votacao TEXT NOT NULL,                -- O que está a ser votado
    resultado VARCHAR(20) NOT NULL,              -- "aprovada", "rejeitada", "retirada"
    tipo_votacao VARCHAR(30) NOT NULL,           -- "global", "artigo", "emenda"
    foi_unanime BOOLEAN DEFAULT FALSE,
    total_votos_favor INTEGER DEFAULT 0,
    total_votos_contra INTEGER DEFAULT 0,
    total_abstencoes INTEGER DEFAULT 0,
    total_ausencias INTEGER DEFAULT 0,
    data_votacao TIMESTAMP NOT NULL,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (iniciativa_id) REFERENCES iniciativas_legislativas(id),
    FOREIGN KEY (sessao_votacao_id) REFERENCES sessoes_votacao(id)
);
```

#### 4.4.3 Tabela: votos_individuais

Armazena o voto de cada deputado em cada votação.

```sql
CREATE TABLE votos_individuais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    votacao_id INTEGER NOT NULL,
    deputado_id INTEGER NOT NULL,
    tipo_voto VARCHAR(20) NOT NULL,              -- "favor", "contra", "abstencao", "ausencia"
    justificacao TEXT,                           -- Justificação do voto (opcional)
    voto_partido VARCHAR(20),                    -- Orientação do partido
    disciplina_partidaria BOOLEAN,               -- Se seguiu orientação do partido
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (votacao_id) REFERENCES votacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (deputado_id) REFERENCES deputados(id),
    UNIQUE(votacao_id, deputado_id)              -- Um voto por deputado por votação
);
```


### 4.5 Tabelas de Agenda e Eventos

#### 4.5.1 Tabela: tipos_evento

Define os diferentes tipos de eventos da agenda parlamentar.

```sql
CREATE TABLE tipos_evento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    designacao VARCHAR(100) NOT NULL,            -- "Audiencia", "Reuniao_Plenaria", etc.
    descricao TEXT,
    cor_representativa VARCHAR(7),               -- Para visualizações
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.5.2 Tabela: eventos_agenda

Armazena todos os eventos da agenda parlamentar.

```sql
CREATE TABLE eventos_agenda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo VARCHAR(500) NOT NULL,
    subtitulo VARCHAR(500),
    tipo_evento_id INTEGER NOT NULL,
    data_inicio DATE NOT NULL,
    hora_inicio TIME,
    data_fim DATE,
    hora_fim TIME,
    todo_o_dia BOOLEAN DEFAULT FALSE,
    local VARCHAR(200),
    descricao_html TEXT,                         -- Conteúdo HTML do evento
    link_relacionado VARCHAR(500),
    legislatura_id INTEGER NOT NULL,
    comissao_id INTEGER,                         -- Se é evento de comissão
    estado VARCHAR(30) DEFAULT 'agendado',       -- "agendado", "realizado", "cancelado"
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tipo_evento_id) REFERENCES tipos_evento(id),
    FOREIGN KEY (legislatura_id) REFERENCES legislaturas(id),
    FOREIGN KEY (comissao_id) REFERENCES comissoes(id)
);
```

#### 4.5.3 Tabela: participantes_eventos

Relaciona deputados e grupos parlamentares com eventos da agenda.

```sql
CREATE TABLE participantes_eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    deputado_id INTEGER,                         -- Se participante é deputado
    partido_id INTEGER,                          -- Se participante é partido/grupo
    entidade_externa VARCHAR(200),               -- Se participante é entidade externa
    tipo_participacao VARCHAR(50) NOT NULL,     -- "organizador", "participante", "convidado"
    confirmado BOOLEAN DEFAULT FALSE,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evento_id) REFERENCES eventos_agenda(id) ON DELETE CASCADE,
    FOREIGN KEY (deputado_id) REFERENCES deputados(id),
    FOREIGN KEY (partido_id) REFERENCES partidos(id)
);
```

### 4.6 Tabelas de Petições

#### 4.6.1 Tabela: peticoes

Armazena informação sobre petições apresentadas à Assembleia da República.

```sql
CREATE TABLE peticoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero INTEGER NOT NULL,
    legislatura_id INTEGER NOT NULL,
    sessao_legislativa INTEGER NOT NULL,
    assunto TEXT NOT NULL,
    resumo TEXT,
    data_entrada DATE NOT NULL,
    data_admissao DATE,
    estado VARCHAR(50) NOT NULL,                 -- "admitida", "rejeitada", "em_analise"
    numero_subscritores INTEGER DEFAULT 0,
    tipo_peticao VARCHAR(50),                    -- "individual", "coletiva", "eletronica"
    comissao_id INTEGER,                         -- Comissão que analisa
    link_documento VARCHAR(500),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (legislatura_id) REFERENCES legislaturas(id),
    FOREIGN KEY (comissao_id) REFERENCES comissoes(id),
    UNIQUE(numero, legislatura_id)
);
```

#### 4.6.2 Tabela: peticoes_iniciativas

Relaciona petições com iniciativas legislativas que possam ter sido influenciadas.

```sql
CREATE TABLE peticoes_iniciativas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peticao_id INTEGER NOT NULL,
    iniciativa_id INTEGER NOT NULL,
    tipo_relacao VARCHAR(50) NOT NULL,           -- "originou", "influenciou", "relacionada"
    descricao_relacao TEXT,
    data_relacao DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (peticao_id) REFERENCES peticoes(id),
    FOREIGN KEY (iniciativa_id) REFERENCES iniciativas_legislativas(id),
    UNIQUE(peticao_id, iniciativa_id)
);
```

### 4.7 Tabelas de Intervenções e Debates

#### 4.7.1 Tabela: intervencoes

Armazena intervenções de deputados em sessões plenárias e comissões.

```sql
CREATE TABLE intervencoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deputado_id INTEGER,                         -- NULL se intervenção de convidado
    nome_interveniente VARCHAR(200),             -- Nome se não for deputado
    cargo_interveniente VARCHAR(100),            -- Cargo se não for deputado
    sessao_votacao_id INTEGER,
    evento_agenda_id INTEGER,                    -- Se intervenção em evento específico
    data_intervencao TIMESTAMP NOT NULL,
    tipo_intervencao VARCHAR(50) NOT NULL,       -- "debate", "pergunta", "resposta", etc.
    tema VARCHAR(500),                           -- Tema da intervenção
    conteudo_texto TEXT,                         -- Transcrição da intervenção
    duracao_segundos INTEGER,                    -- Duração em segundos
    link_video VARCHAR(500),                     -- Link para vídeo
    link_audio VARCHAR(500),                     -- Link para áudio
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deputado_id) REFERENCES deputados(id),
    FOREIGN KEY (sessao_votacao_id) REFERENCES sessoes_votacao(id),
    FOREIGN KEY (evento_agenda_id) REFERENCES eventos_agenda(id)
);
```

## 5. Índices para Otimização de Performance

Para garantir performance adequada nas consultas mais frequentes, são criados os seguintes índices:

```sql
-- Índices para consultas temporais
CREATE INDEX idx_mandatos_legislatura ON mandatos(legislatura_id);
CREATE INDEX idx_mandatos_deputado_ativo ON mandatos(deputado_id, ativo);
CREATE INDEX idx_votacoes_data ON votacoes(data_votacao);
CREATE INDEX idx_eventos_data ON eventos_agenda(data_inicio, data_fim);

-- Índices para análises de votação
CREATE INDEX idx_votos_individuais_deputado ON votos_individuais(deputado_id);
CREATE INDEX idx_votos_individuais_tipo ON votos_individuais(tipo_voto);
CREATE INDEX idx_votacoes_resultado ON votacoes(resultado);
CREATE INDEX idx_votacoes_iniciativa ON votacoes(iniciativa_id);

-- Índices para consultas de atividade
CREATE INDEX idx_iniciativas_estado ON iniciativas_legislativas(estado);
CREATE INDEX idx_iniciativas_tipo ON iniciativas_legislativas(tipo_iniciativa_id);
CREATE INDEX idx_iniciativas_data ON iniciativas_legislativas(data_entrada);

-- Índices compostos para consultas complexas
CREATE INDEX idx_mandatos_partido_legislatura ON mandatos(partido_id, legislatura_id);
CREATE INDEX idx_votos_votacao_tipo ON votos_individuais(votacao_id, tipo_voto);
CREATE INDEX idx_eventos_tipo_data ON eventos_agenda(tipo_evento_id, data_inicio);
```

## 6. Views para Análises Frequentes

### 6.1 View: deputados_ativos

Mostra deputados atualmente em exercício com informação completa.

```sql
CREATE VIEW deputados_ativos AS
SELECT 
    d.id,
    d.nome_completo,
    d.nome_parlamentar,
    d.sexo,
    d.profissao,
    p.sigla as partido_sigla,
    p.designacao_completa as partido_nome,
    ce.designacao as circulo_eleitoral,
    l.numero as legislatura,
    m.data_inicio as inicio_mandato
FROM deputados d
JOIN mandatos m ON d.id = m.deputado_id AND m.ativo = TRUE
JOIN partidos p ON m.partido_id = p.id
JOIN circulos_eleitorais ce ON m.circulo_eleitoral_id = ce.id
JOIN legislaturas l ON m.legislatura_id = l.id
WHERE d.ativo = TRUE;
```

### 6.2 View: estatisticas_votacao_deputado

Calcula estatísticas de votação por deputado na legislatura atual.

```sql
CREATE VIEW estatisticas_votacao_deputado AS
SELECT 
    d.id as deputado_id,
    d.nome_parlamentar,
    p.sigla as partido,
    COUNT(vi.id) as total_votacoes,
    SUM(CASE WHEN vi.tipo_voto = 'favor' THEN 1 ELSE 0 END) as votos_favor,
    SUM(CASE WHEN vi.tipo_voto = 'contra' THEN 1 ELSE 0 END) as votos_contra,
    SUM(CASE WHEN vi.tipo_voto = 'abstencao' THEN 1 ELSE 0 END) as abstencoes,
    SUM(CASE WHEN vi.tipo_voto = 'ausencia' THEN 1 ELSE 0 END) as ausencias,
    ROUND(
        (COUNT(vi.id) - SUM(CASE WHEN vi.tipo_voto = 'ausencia' THEN 1 ELSE 0 END)) * 100.0 / 
        COUNT(vi.id), 2
    ) as taxa_presenca,
    ROUND(
        SUM(CASE WHEN vi.disciplina_partidaria = TRUE THEN 1 ELSE 0 END) * 100.0 / 
        COUNT(vi.id), 2
    ) as taxa_disciplina_partidaria
FROM deputados d
JOIN mandatos m ON d.id = m.deputado_id AND m.ativo = TRUE
JOIN partidos p ON m.partido_id = p.id
LEFT JOIN votos_individuais vi ON d.id = vi.deputado_id
LEFT JOIN votacoes v ON vi.votacao_id = v.id
LEFT JOIN sessoes_votacao sv ON v.sessao_votacao_id = sv.id
WHERE sv.legislatura_id = (SELECT id FROM legislaturas WHERE ativa = TRUE)
GROUP BY d.id, d.nome_parlamentar, p.sigla;
```

### 6.3 View: eficacia_legislativa_partido

Analisa a eficácia legislativa por partido.

```sql
CREATE VIEW eficacia_legislativa_partido AS
SELECT 
    p.sigla,
    p.designacao_completa,
    COUNT(DISTINCT il.id) as total_iniciativas,
    SUM(CASE WHEN il.estado = 'aprovada' THEN 1 ELSE 0 END) as iniciativas_aprovadas,
    SUM(CASE WHEN il.estado = 'rejeitada' THEN 1 ELSE 0 END) as iniciativas_rejeitadas,
    SUM(CASE WHEN il.estado IN ('em_tramitacao', 'em_comissao') THEN 1 ELSE 0 END) as iniciativas_pendentes,
    ROUND(
        SUM(CASE WHEN il.estado = 'aprovada' THEN 1 ELSE 0 END) * 100.0 / 
        COUNT(DISTINCT il.id), 2
    ) as taxa_aprovacao
FROM partidos p
JOIN autores_iniciativas ai ON p.id = ai.partido_id
JOIN iniciativas_legislativas il ON ai.iniciativa_id = il.id
JOIN legislaturas l ON il.legislatura_id = l.id
WHERE l.ativa = TRUE
GROUP BY p.id, p.sigla, p.designacao_completa
HAVING COUNT(DISTINCT il.id) > 0
ORDER BY taxa_aprovacao DESC;
```

## 7. Triggers para Integridade e Auditoria

### 7.1 Trigger: atualizar_timestamp

Atualiza automaticamente o campo `updated_at` quando um registo é modificado.

```sql
CREATE TRIGGER atualizar_timestamp_deputados
    AFTER UPDATE ON deputados
    FOR EACH ROW
BEGIN
    UPDATE deputados SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Aplicar trigger similar a todas as tabelas com updated_at
```

### 7.2 Trigger: validar_mandato_unico

Garante que um deputado não pode ter mandatos sobrepostos.

```sql
CREATE TRIGGER validar_mandato_unico
    BEFORE INSERT ON mandatos
    FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN EXISTS (
            SELECT 1 FROM mandatos 
            WHERE deputado_id = NEW.deputado_id 
            AND legislatura_id = NEW.legislatura_id
            AND ativo = TRUE
        )
        THEN RAISE(ABORT, 'Deputado já tem mandato ativo nesta legislatura')
    END;
END;
```

## 8. Considerações de Segurança e Performance

### 8.1 Segurança de Dados

- **Controlo de Acesso**: Implementação de roles diferenciados (leitura, escrita, administração)
- **Auditoria**: Logs de todas as operações de modificação de dados
- **Backup**: Estratégia de backup incremental diário com retenção de 30 dias
- **Encriptação**: Dados sensíveis encriptados em repouso

### 8.2 Otimização de Performance

- **Particionamento**: Tabelas grandes particionadas por legislatura
- **Índices Estratégicos**: Índices otimizados para consultas mais frequentes
- **Cache**: Implementação de cache para views complexas
- **Análise de Consultas**: Monitorização regular de performance das consultas

## 9. Plano de Migração e Manutenção

### 9.1 Estratégia de Migração

1. **Fase 1**: Criação da estrutura base e importação de dados históricos
2. **Fase 2**: Implementação de triggers e views
3. **Fase 3**: Otimização de índices baseada em padrões de uso real
4. **Fase 4**: Implementação de funcionalidades avançadas de auditoria

### 9.2 Manutenção Contínua

- **Atualizações Regulares**: Importação automática de novos dados semanalmente
- **Limpeza de Dados**: Procedimentos de validação e correção de inconsistências
- **Monitorização**: Alertas para anomalias nos dados ou performance
- **Evolução do Esquema**: Processo controlado para adição de novas funcionalidades

## 10. Conclusão

Este esquema de base de dados foi concebido para ser robusto, escalável e flexível, permitindo análises profundas da atividade parlamentar portuguesa. A estrutura normalizada garante integridade dos dados enquanto as views e índices otimizam a performance para consultas analíticas complexas.

O design suporta tanto consultas operacionais simples quanto análises estatísticas avançadas, fornecendo uma base sólida para a aplicação de visualização e análise que será desenvolvida nas fases seguintes do projeto.

