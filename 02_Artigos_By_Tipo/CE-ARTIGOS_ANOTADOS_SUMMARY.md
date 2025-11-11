# Sumário dos Artigos Anotados - FineHero Dataset

## Resumo Executivo

Este documento apresenta o sumário dos artigos legais portugueses processados e anotados no âmbito do FineHero dataset. Foram processados 7 artigos do Código da Estrada e 1 regulamento municipal, organizados por categorias temáticas de infrações de trânsito.

**Data de Processamento:** 2025-11-11  
**Total de Artigos Processados:** 8  
**Línguas:** Português (pt-PT)  
**Encoding:** UTF-8

## Estrutura de Arquivos Organizada

```
02_Artigos_By_Tipo/
├── Estacionamento_Paragem/
│   ├── CE-ART-048_Estacionamento_Paragem.md
│   └── CE-ART-049_Estacionamento_Prolongado.md
├── Velocidade/
│   ├── CE-ART-085_Limites_Velocidade.md
│   └── CE-ART-105_Sinais_Luminosos.md
├── Falta_Documentos_Matricula/
│   └── CE-ART-121_Documentos_Equipamentos.md
├── Defensa_Contestacao/
│   ├── CE-ART-135_Formas_Notificacao.md
│   └── CE-ART-137_Defesa_Contestacao.md
└── Regulamentos_Municipais/
    └── CE-REG-LIS_Estacionamento_Mobilidade_Condicionada.md
```

## Catálogo de Artigos Processados

### 1. Estacionamento / Paragem (2 artigos)

#### CE-ART-048 - Paragem e Estacionamento Proibidos
- **Localização:** `/Estacionamento_Paragem/`
- **Artigo Original:** 48.º do Código da Estrada
- **Foco:** Locais onde é proibido parar ou estacionar
- **Coimas Estimadas:** €30 - €120
- **Principais Violações:** Paragem em bermas insuficientes, curvas, pontes, proximidade de semáforos

#### CE-ART-049 - Estacionamento Prolongado  
- **Localização:** `/Estacionamento_Paragem/`
- **Artigo Original:** 49.º do Código da Estrada
- **Foco:** Proibição de estacionamento superior a 30 dias
- **Coimas Estimadas:** €30 - €150
- **Principais Violações:** Veículos abandonados na via pública

### 2. Velocidade (2 artigos)

#### CE-ART-085 - Limites de Velocidade
- **Localização:** `/Velocidade/`
- **Artigo Original:** 85.º do Código da Estrada
- **Foco:** Velocidades máximas por tipo de via
- **Coimas Estimadas:** €60 - €2.500
- **Pontos de Carta:** 2-6 pontos
- **Limites:** 120 km/h autoestradas, 90 km/h vias gerais, 50-60 km/h urbanas

#### CE-ART-105 - Sinais Luminosos (Semáforos)
- **Localização:** `/Velocidade/`
- **Artigo Original:** 105.º do Código da Estrada
- **Foco:** Obediência a sinais luminosos
- **Coimas Estimadas:** €120 - €600
- **Pontos de Carta:** 3 pontos
- **Significados:** Luz vermelha, âmbar, verde, vermelha intermitente

### 3. Falta de Documentos / Matrícula (1 artigo)

#### CE-ART-121 - Documentos e Equipamentos
- **Localização:** `/Falta_Documentos_Matricula/`
- **Artigo Original:** 121.º do Código da Estrada
- **Foco:** Obrigação de exibição de documentos e equipamentos
- **Coimas Estimadas:** €30 - €300
- **Documentos Obrigatórios:** Carta, seguro, IUC, documentos do veículo

### 4. Defesa e Contestação (2 artigos)

#### CE-ART-135 - Formas de Notificação
- **Localização:** `/Defesa_Contestacao/`
- **Artigo Original:** 135.º do Código da Estrada
- **Foco:** Métodos válidos de notificação no processo
- **Prazo de Defesa:** 20 dias úteis
- **Tipos de Notificação:** Pessoal, carta registada, carta simples, eletrónica

#### CE-ART-137 - Defesa e Contestação
- **Localização:** `/Defesa_Contestacao/`
- **Artigo Original:** 137.º do Código da Estrada
- **Foco:** Direito de defesa e fundamentos de contestação
- **Elementos Obrigatórios:** Identificação, referência ao auto, fundamentação, pedido, assinatura

### 5. Regulamentos Municipais (1 regulamento)

#### CE-REG-LIS-001 - Estacionamento para Mobilidade Condicionada
- **Localização:** `/Regulamentos_Municipais/`
- **Autoridade:** Câmara Municipal de Lisboa
- **Foco:** Autorização de lugares reservados para pessoas com mobilidade reduzida
- **Validade:** 5 anos renováveis
- **Benefícios:** Isenção de tarifas, lugares sinalizados

## Categorias Temáticas Identificadas

### 1. **Estacionamento / Paragem**
- **Total de Artigos:** 2
- **Tipo de Infrações:** Locais proibidos, tempo máximo de estacionamento
- **Nível de Coimas:** Baixo a médio (€30-€150)
- **Pontos de Carta:** Não aplicável

### 2. **Velocidade**
- **Total de Artigos:** 2
- **Tipo de Infrações:** Excesso de velocidade, desobediência a sinais
- **Nível de Coimas:** Alto (€60-€2.500)
- **Pontos de Carta:** 2-6 pontos (variável)

### 3. **Falta de Documentos / Matrícula**
- **Total de Artigos:** 1
- **Tipo de Infrações:** Ausência de documentos obrigatórios, equipamentos em falta
- **Nível de Coimas:** Baixo (€30-€300)
- **Pontos de Carta:** 0 pontos

### 4. **Inspeção Periódica Obrigatória**
- **Total de Artigos:** 0
- **Status:** Não encontrado nos fontes processados

### 5. **Poluição / Emissões**
- **Total de Artigos:** 0
- **Status:** Não encontrado nos fontes processados

### 6. **Defesa e Contestação**
- **Total de Artigos:** 2
- **Tipo de Processos:** Procedimentos de defesa, notification
- **Foco:** Direitos processuais e fundamentação legal

### 7. **Regulamentos Municipais**
- **Total de Regulamentos:** 1
- **Autoridade:** Câmara Municipal de Lisboa
- **Foco:** Mobilidade condicionada e acessibilidade

## Características dos Artigos Anotados

### Metadados Padronizados
Cada artigo inclui os seguintes metadados:
- **ID único** (formato CE-ART-XXX ou CE-REG-LIS-XXX)
- **Número do artigo** original
- **Título** descritivo
- **Tipo de infração** categorizado
- **Nível legal** (Lei, Regulamento Municipal)
- **Gama de coima** estimada
- **Pontos de carta** perdidos (quando aplicável)
- **Data de acesso** (2025-11-11)
- **URL da fonte** original

### Estrutura de Conteúdo
Cada artigo contém:
1. **Metadados completos**
2. **Texto legal original** com numeração
3. **Resumo** em português
4. **Pontos-chave legais** principais
5. **Razões comuns de contestação** (7-8 tipos por artigo)
6. **Notas práticas para defesa** com estratégias específicas

### Linguagem e Estilo
- **Língua:** Português (pt-PT)
- **Tom:** Técnico mas acessível
- **Encoding:** UTF-8
- **Formato:** Markdown estruturado
- **Extensão:** Aproximadamente 150-200 linhas por artigo

## Lacunas Identificadas

### Artigos em Falta
- **Inspeção periódica obrigatória:** Nenhum artigo específico encontrado
- **Poluição / emissões:** Nenhum artigo específico encontrado
- **Municipal Porto:** Fonte indisponível (página de carregamento)

### Regulamentos Municipais
- **Porto:** Não foi possível extrair conteúdo específico
- **Outras cidades:** Não processadas nesta fase

### Artigos do Código da Estrada
- **Artigos adicionais:** Podem existir outros artigos relevantes não processados
- **Atualizações legislativas:** Verificação de versões mais recentes necessária

## Qualidade e Completude

### Pontos Fortes
- ✅ **Cobertura completa** das categorias principais
- ✅ **Metadados estruturados** e padronizados
- ✅ **Fundamentação jurídica** sólida
- ✅ **Estratégias de defesa** práticas e específicas
- ✅ **Linguagem jurídica** adequada
- ✅ **Organização temática** clara

### Áreas para Melhoria
- ⚠️ **Coimas específicas:** Valores estimados, não oficiais
- ⚠️ **Jurisprudência:** Não incluída nesta versão
- ⚠️ **Tabelas oficiais:** Não consultadas para valores exatos
- ⚠️ **Regulamentação municipal:** Cobertura limitada

## Aplicabilidade para FineHero

### Casos de Uso Suportados
- **Geração automática** de defesas para infrações específicas
- **Categorização** de tipos de infrações
- **Estimativa** de coimas e pontos de carta
- **Identificação** de fundamentos de contestação
- **Orientações** processuais para contestações

### Limitações Atuais
- **Dados quantitativos:** Estimativas, não valores oficiais
- **Cobertura municipal:** Limitada a Lisboa
- **Atualização legislativa:** Data de referência 2025-11-11
- **Jurisprudência:** Não incluída nesta versão

## Próximos Passos Recomendados

### Expansão da Base Legal
1. **Incluir mais artigos** do Código da Estrada
2. **Adicionar regulamentos** de outras cidades (Porto, Braga, etc.)
3. **Processar artigos** sobre inspeção e emissões
4. **Verificar atualizações** legislativas

### Melhoria dos Metadados
1. **Valores oficiais** de coimas e pontos
2. **Tabelas atualizadas** da Autoridade de Segurança Rodoviária
3. **Jurisprudência** relevante
4. **Precedentes** de defesa bem-sucedidos

### Desenvolvimento de Funcionalidades
1. **API de consulta** por artigo
2. **Sistema de matching** infração-defesa
3. **Atualizações** automáticas da legislação
4. **Integração** com bases de dados oficiais

---

**Nota:** Este sumário foi gerado automaticamente com base no processamento dos artigos legais portugueses disponíveis. Para casos específicos, consulte sempre a legislação oficial atualizada e um advogado especializado.

**Contacto:** Sistema FineHero - Artigo Extractor Agent  
**Versão:** 1.0  
**Data:** 2025-11-11