# Fluxogramas dos subprocessos (implementação atual)

Este documento descreve, em forma de fluxograma, **como os subprocessos acontecem hoje no projeto** (backend FastAPI + PostgreSQL + ChromaDB + LangGraph).

> Observação: o sistema executa a **correção automatizada** após a publicação da prova (processamento em background) e oferece **revisão docente** e **relatório Excel** em rotas específicas de revisão.

---

## 1) Subprocesso: Configuração da Prova

```mermaid
graph TD
  A[Professor] --> B[Cria prova - status DRAFT]
  
  subgraph Metadados
    B --> C[Define metadados da prova<br/>título/descrição/turma]
    C --> D[Envia materiais didáticos - PDF - como anexos]
    D --> E[Arquivo salvo no filesystem<br/>+ registro no banco]
    E --> F[Materiais anexados<br/>ainda não indexados para consulta]
    F --> G[Associa critérios de avaliação à prova<br/>pesos/parametrização]
  end
  subgraph Adição de Questões
    G --> H[Cadastra questões<br/>enunciado, pontos, ordem, metadados]
    H --> I[Opcional: override/ajuste de critérios por questão]
    I --> J[Questões persistidas no PostgreSQL e prontas para receber respostas]
  end

  subgraph Adição de Respostas Discursivas
    J --> K[Submete resposta discursiva por questão]
    K --> L[Resposta persistida no PostgreSQL]
  end
  
  L --> M[Prova pronta para publicação]
  M --> N[Publica prova]
  N --> O[SUBPROCESSO: CORREÇÃO DA PROVA]
```

---

## 2) Subprocesso: Correção da Prova (publicação + background + revisão)

```mermaid
graph TD
  A[Professor] --> P[Publica a prova]

  P --> V1[Valida se a prova está pronta<br/>status rascunho, questões e respostas]
  V1 -->|ok| S1[Marca a prova como publicada]
  V1 -->|falha| E1[Interrompe a publicação<br/>e informa inconsistências]

  S1 --> Q1[Inicia processamento assíncrono]

  subgraph "Processamento em background"
    Q1 --> I0[Prepara materiais didáticos]
    I0 --> I1[Indexa materiais para consulta no Banco de Dados Vetorial]
    I1 --> I2[Registra sucesso ou falha na indexação]

    I2 --> G0[Percorre questões]
    G0 --> GQ[Para cada questão<br/>recupera contexto dos materiais - RAG ]
    GQ --> GA[Para cada resposta da questão<br/>executa correção automática]
    GA --> G1[SUBPROCESSO DE CORREÇÃO DA RESPOSTA]

    G1 --> F0[Consolida o resultado final]
    F0 -->|há falhas| STW[Define status de atenção]
    F0 -->|sem falhas| STG[Define status de corrigida]
  end

  STG --> R0[Professor realiza revisão]
  STW --> R0

  R0 --> R1[Consulta resultados por aluno e questão]
  R1 --> R2[Opcional: ajusta nota manualmente]
  R1 --> R3[Opcional: aprova resposta revisada]

  R2 --> R4[Finaliza a revisão]
  R3 --> R4

  R4 --> R5[Marca prova e respostas como finalizadas]
  R4 -->|se solicitado| R7[Gera relatório em planilha]
```

---

## 3) Subprocesso: Correção da Resposta (workflow LangGraph)

```mermaid
graph TD
  A[Resposta do aluno] --> S0[Inicia a análise]
  S0 --> CTX[Usa contexto dos materiais da questão<br/>recuperado anteriormente]
  CTX --> C1[Corretor 1 avalia a resposta]
  CTX --> C2[Corretor 2 avalia a resposta]

  C1 --> DV[Verifica se divergência entre corretores ultrapassa o limiar]
  C2 --> DV

  DV -->|NÃO| FIN[Consolida a nota]
  DV -->|SIM| ARB[Corretor 3 - Árbitro - realiza uma terceira avaliação]

  ARB --> FIN

  FIN --> P0[Registra resultado]
  P0 --> OUT[Saída - nota final e justificativa]
```

---

## Notas de fidelidade (pontos que o diagrama respeita)

- A publicação só ocorre quando a prova está em rascunho e possui questões e respostas válidas.
- O processamento assíncrono prepara os materiais e executa a correção automática.
- A correção utiliza contexto recuperado dos materiais da própria prova, recuperado uma vez por questão e reutilizado nas respostas.
- O árbitro só é acionado quando há divergência relevante entre os dois primeiros corretores.
- A revisão docente permite ajustes e finalização, com opção de gerar relatório em planilha.
