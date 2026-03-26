# Auditoria TCC — AI Grading System (CorretumAI)

Data: 2026-03-25
Auditores: @architect (Aria), @analyst (Alex), @qa (Quinn)

---

## Status Geral

| Capítulo | Status | Nota |
|----------|--------|------|
| Cap 1 — Introdução | OK (1 fix menor) | Seção "Estrutura do Trabalho" vazia |
| Cap 2 — Fundamentação | OK (2 typos) | Sólido e bem referenciado |
| Cap 3 — Trabalhos Relacionados | OK | Protocolo PICOC, 7 estudos |
| Cap 4 — Metodologia | OK (1 fix técnico) | Rigoroso, QA1-QA4 |
| Cap 5 — Desenvolvimento | OK | Corresponde ao código |
| Cap 6 — Resultados | REESCRITO (estrutura) | Precisa de dados experimentais reais |
| Cap 7 — Conclusão | PLACEHOLDER (crítico) | Lorem ipsum + projeto errado |

---

## Problemas por Prioridade

### CRÍTICOS (bloqueiam entrega)

- [ ] **P1: Cap 6 — Dados experimentais ausentes**
  - Estrutura LaTeX reescrita com tabelas e seções QA1-QA4
  - FALTA: Rodar o sistema e coletar dados reais para preencher as tabelas
  - Arquivo: `tcc/textual/t6-resultados.tex`
  - Buscar TODOs no arquivo para saber o que preencher

- [ ] **P2: Cap 7 — Conclusão inteira é placeholder**
  - Contém Lorem Ipsum e texto de projeto de reciclagem (catadores/separadores)
  - Precisa ser escrito do zero: conclusão, contribuições, limitações, trabalhos futuros
  - Arquivo: `tcc/textual/t7-conclusoes.tex`

### SIGNIFICATIVOS (afetam credibilidade técnica)

- [x] **P3: Cap 4, Seção 4.5 — DSPy descrito como runtime** ✅ (2026-03-25)
  - Monografia diz: "agentes implementados com DSPy" (Seção 4.5, linha 86)
  - Realidade: DSPy foi REMOVIDO do runtime, agentes usam LangChain `with_structured_output`
  - DSPy está no código apenas para otimização offline (BootstrapFewShot)
  - Arquivo: `tcc/textual/t4-material.tex`, linhas 85-86
  - Fix: Reescrever seção explicando a evolução arquitetural (DSPy offline → LangChain runtime)

### MODERADOS (podem ser questionados na defesa)

- [x] **P4: Cap 1 — Seção "Estrutura do Trabalho" vazia** ✅ (2026-03-25)
  - Seção declarada mas sem conteúdo (deveria descrever cada capítulo)
  - Arquivo: `tcc/textual/t1-introducao.tex`
  - Fix: Adicionar 1 parágrafo descrevendo a organização dos capítulos

- [x] **P5: Cap 1 — Objetivo 3 fala em "interface integrada"** ✅ (2026-03-25)
  - Texto diz: "Disponibilizar uma interface integrada para revisão docente"
  - Realidade: Só existe API REST, frontend foi movido pra outro repo
  - Arquivo: `tcc/textual/t1-introducao.tex`, linha 29
  - Fix: Reformular como "API de revisão" ou reconhecer como limitação

- [x] **P6: Operador de divergência — monografia vs código** ✅ (2026-03-25)
  - Monografia (Cap 4, linha 205): `|C1-C2| >= 2,0`
  - Código (`divergence_checker.py`, linha 53): `diff > self.__threshold` (strict >)
  - Divergência de exatamente 2,0 NÃO aciona o árbitro no código
  - Fix: Alinhar um com o outro (mudar código para >= OU monografia para >)

- [x] **P7: Execução paralela vs sequencial dos corretores** ✅ (2026-03-25)
  - Monografia e docstring sugerem C1 e C2 em paralelo
  - Código (`graph.py`): execução sequencial (serializado pra respeitar TPM)
  - Fix: Esclarecer que são logicamente independentes mas sequenciais por rate limit

### MENORES (typos e detalhes)

- [x] **P8: Typo no Cap 2** ✅ (2026-03-25)
  - "Processamento de Liguagem Natural" → "Processamento de Linguagem Natural"
  - Arquivo: `tcc/textual/t2-fundamentacao.tex`, linha 162

- [x] **P9: Duplo dois-pontos no Cap 2** ✅ (2026-03-25)
  - "Word Embeddings::" → "Word Embeddings:"
  - Arquivo: `tcc/textual/t2-fundamentacao.tex`, linha 214

- [ ] **P10: Statuses não mencionados**
  - Código tem ACTIVE, GRADING, ARCHIVED no CheckConstraint
  - Monografia só menciona DRAFT → PUBLISHED → GRADED/WARNING → FINALIZED
  - Fix: Mencionar como status reservados ou remover do constraint

---

## Features no código NÃO mencionadas na monografia

Estas não são obrigatórias, mas poderiam fortalecer o trabalho se incluídas:

| Feature | Localização no código | Relevância |
|---------|----------------------|------------|
| Sistema de autenticação (JWT, bcrypt, sessões) | `src/services/auth/` | Baixa (fora do escopo do TCC) |
| Detecção de plágio | `src/services/analytics/plagiarism_service.py` | Alta (poderia ser mencionada) |
| Rastreamento de conhecimento do aluno | `src/services/analytics/student_knowledge_service.py` | Média |
| Cache FIFO no RAG (128 entradas) | `src/services/rag/retrieval_service.py` | Média (otimização relevante) |
| Controles de concorrência (semáforo API) | `src/core/settings.py` (API_CONCURRENCY) | Baixa |
| LangSmith observability | decorators `@traceable` nos agentes | Média |
| Suporte a Groq como provider | `src/core/llm_handler.py` | Baixa |
| Retry com backoff exponencial | `tenacity` nos agentes | Média (resiliência) |
| Gestão de turmas e alunos | `src/services/classes/` | Baixa (periférico) |

---

## Ordem sugerida de execução

1. **P3** (DSPy → LangChain) — fix rápido, alto impacto
2. **P4** (Estrutura do Trabalho) — fix rápido
3. **P8 + P9** (typos) — trivial
4. **P6** (operador divergência) — decisão simples
5. **P7** (paralelo vs sequencial) — ajuste de texto
6. **P5** (interface → API) — reformulação de objetivo
7. **P1** (dados experimentais) — requer rodar o sistema
8. **P2** (conclusão) — requer P1 pronto antes
9. **P10** (status extras) — opcional
