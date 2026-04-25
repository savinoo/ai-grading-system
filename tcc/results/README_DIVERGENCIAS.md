# Análise de Divergências: Condição COM RAG vs SEM RAG

## Visão Geral

Este diretório contém a análise completa de divergências de notas entre experimentos de correção automática com LLM em duas condições:
- **Condição A (COM RAG)**: Sistema com Retrieval-Augmented Generation habilitado
- **Condição B (SEM RAG)**: Sistema sem RAG

## Achados Principais

### Estatísticas Gerais
- **Total de divergências significativas**: 18 (diferença >= 1.0 ponto)
- **Questões afetadas**: 3 de 3
- **Alunos afetados**: 2 de 4 (Aluno 3 e Aluno 4)
- **Alunos NÃO afetados**: Aluno 1 (Excelente) e Aluno 2 (Intermediário)

### Descoberta Crítica
**Em 100% das 18 comparações: Nota COM RAG < Nota SEM RAG**

Padrão não-aleatório, determinístico, reproduzível em múltiplas replicas.

## Questões Críticas

### Q1: Array vs Lista Encadeada Simples
- **UUID**: `b5d3b240-86a2-49cb-8667-fa2361da9971`
- **Maior divergência**: 8.5 pontos (Aluno 3, múltiplas replicas)
- **Padrão**: Resposta COM RAG inverte completamente os conceitos
  - Array alocação: COM RAG diz "dispersa", correto é "contígua"
  - Array acesso: COM RAG diz "O(n)", correto é "O(1)"
  - Lista alocação: COM RAG diz "contígua", correto é "não-contígua"
  - Lista acesso: COM RAG diz "O(1)", correto é "O(n)"

### Q2: Merge Sort vs Quick Sort
- **UUID**: `708e41c2-bff8-4f96-80f2-625d51cf370d`
- **Maior divergência**: 7.0 pontos (Aluno 3)
- **Padrão**: Resposta COM RAG inverte propriedades dos algoritmos
  - Merge Sort: COM RAG diz "instável", correto é "estável"
  - Quick Sort: COM RAG diz "estável", correto é "instável"

### Q3: Árvore Binária de Busca Balanceada
- **UUID**: `0c9d7938-7e05-4a5c-8c3a-f120556698d9`
- **Maior divergência**: 6.5 pontos (Aluno 3)
- **Padrão**: Degradação sistemática com RAG

## Correlação com Qualidade do Aluno

| Aluno | Qualidade | Divergências | Questões Afetadas |
|-------|-----------|:---:|:---:|
| Aluno 1 | Excelente | 0 | 0 |
| Aluno 2 | Intermediário | 0 | 0 |
| Aluno 3 | Fraco | 16 | 3 |
| Aluno 4 | Off-topic | 2 | 1 |

**Conclusão**: RAG afeta negativamente principalmente alunos com respostas fracas.

## Arquivos de Análise

### 1. `ANALISE_DIVERGENCIAS_RAG_vs_SEM_RAG.txt`
Relatório executivo completo com:
- Resumo executivo
- Tabelas de divergências por questão
- Análise detalhada de conceitos invertidos
- Padrões observados
- Recomendações urgentes

### 2. `TABELA_DIVERGENCIAS_RESUMIDA.csv`
Tabela em formato CSV com todas as 18 divergências:
- ID da comparação
- UUID e nome da questão
- Nome do aluno
- Notas em ambas as condições
- Diferença em pontos
- Arquivos comparados

### 3. `divergencias_analise.json`
Dados estruturados em JSON incluindo:
- Resumo estatístico
- Divergências agrupadas por aluno
- Divergências agrupadas por questão
- Lista completa de todas as divergências

## Como Usar os Arquivos

### Para Relatório Executivo
Abra: `ANALISE_DIVERGENCIAS_RAG_vs_SEM_RAG.txt`

### Para Análise de Dados
Abra: `divergencias_analise.json` (em um editor ou processador JSON)

### Para Visualização em Planilha
Abra: `TABELA_DIVERGENCIAS_RESUMIDA.csv` (em Excel, Google Sheets, etc.)

## Recomendações Imediatas

1. **Auditar a Base RAG**: Verificar documentos recuperados para Q1, Q2 e Q3 procurando por inversões
2. **Validar Fonte**: Comparar informações do RAG com documentação oficial
3. **Revisar Prompt**: Adicionar instrução para validar informações contraditórias
4. **Desabilitar RAG**: Para alunos com qualidade "Fraco" até problema ser resolvido

## Replicabilidade

As divergências foram encontradas em múltiplas replicas:
- experiment_QA4_9, 10, 11 (3 replicas R1/3, R2/3, R3/3)
- experiment_A_pareado_3 (pareado)
- experiment_A_v3_13 (v3 definitivo)
- experiment_A_final_6 (final + paralelo)

Todas comparadas contra: experiment_B_final_7 (SEM RAG)

## Conclusão

Padrão **determinístico e reproduzível** de degradação de qualidade quando RAG está habilitado, particularmente para alunos com respostas fracas. Inversão sistemática de conceitos fundamentais sugere problema não em variação aleatória, mas em como RAG está sendo integrado.

**Status**: CRÍTICO - Não recomendado usar RAG em produção até resolução.

