# Mapa de Campos - Template de Cartas de Recurso

## Campos Mapeáveis para Objetos JSON

### Campos Identificação Pessoal
- `[NOME COMPLETO]` → `identificacao.nome_completo`
- `[DATA]` → `identificacao.data_nascimento`
- `[MORADA COMPLETA]` → `identificacao.morada_completa`
- `[EMAIL]` → `identificacao.email`
- `[TELEFONE]` → `identificacao.telefone`

### Campos do Documento
- `[NÚMERO]` → `identificacao.numero_documento` (CC/B.I.)
- `[LOCAL]` → `jurisdicao.local` (ex: "Lisboa", "Porto")

### Campos Temporais
- `[DATA]` → `data_infracao` (data da infração)
- `[HORA]` → `hora_infracao` (hora da infração)

## Campos Específicos por Tipo de Infração

### Estacionamento
- `[LOCALIZAÇÃO ESPECÍFICA]` → `local_infracao.endereco_detalhado`

### Velocidade
- `[VELOCIDADE]` → `dados_tecnicos.velocidade_medida`
- `[VELOCIDADE MÁXIMA]` → `dados_tecnicos.velocidade_limite`

## Campos Críticos - Mapeamento Manual Necessário

### Campo Problema Identificado
- `[NÚMERO DO AUTO]` → **REQUER MAPEAMENTO MANUAL**
  - **Problema**: Não existe campo direto no objeto da multa
  - **Solução**: Mapear para campo personalizado do sistema
  - **Exemplo**: `numero_processo` ou `auto_referencia`

### Campos de Fundamentação
- `[CIRCUNSTÂNCIAS ESPECÍFICAS]` → **TEXTO LIVRE**
- `[FUNDAMENTOS ESPECÍFICOS]` → **TEXTO LIVRE**
- `[FUNDAMENTO ESPECÍFICO]` → **TEXTO LIVRE**

## Campos com Opções Pré-definidas

### Tipos de Infração
- `[TIPO DE INFRAÇÃO]` → Mapear para enum baseado no artigo violado

### Níveis de Dificuldade
- **Básico**: Estacionamento, Documentos
- **Intermediário**: Velocidade (condições gerais)
- **Avançado**: Velocidade (questões técnicas), Semáforos

## Recomendações de Implementação

1. **Campo [NÚMERO DO AUTO]**: Implementar como campo customizado no sistema
2. **Campos de Texto Livre**: Interface de seleção para argumentos pré-definidos
3. **Validação**: Verificar se todos os campos obrigatórios foram preenchidos
4. **Mapeamento Automático**: Tentar mapear campos automaticamente onde possível

## Status de Mapeamento dos Templates

- ✅ cart_001_estacionamento_proibido.md - REQUER CORREÇÃO
- ✅ cart_002_excesso_velocidade.md - REQUER CORREÇÃO  
- ✅ cart_003_falta_documentos.md - REQUER CORREÇÃO
- ✅ cart_004_violacao_semaforos.md - REQUER CORREÇÃO
- 🔄 cart_005_estacionamento_prolongado.md - PENDENTE
- 🔄 cart_006_defesa_geral.md - PENDENTE
- 🔄 cart_007_velocidade_tecnica.md - PENDENTE
- 🔄 cart_008_forca_maior.md - PENDENTE