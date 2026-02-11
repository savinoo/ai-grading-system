# Performance Optimization Guide

## 🚀 Otimizações Implementadas

### 1. ✅ RAG Cache
**Localização:** `src/rag/retriever.py`

- Cache em memória para resultados de busca RAG
- Chave: `(query[:160], discipline, k)`
- FIFO eviction quando atinge 128 entradas
- **Impacto:** Reduz 30 chamadas RAG → 3 chamadas (uma por questão)

**Logs:**
```
RAG: cache hit
```

---

### 2. ✅ Paralelização Otimizada
**Localização:** `src/utils/helpers.py`

- Semaphore aumentado de **2 → 10** (default)
- Configurável via `API_CONCURRENCY` env var
- Throttle configurável via `API_THROTTLE_SLEEP` (default 0.2s)

**Como ajustar:**
```bash
export API_CONCURRENCY=15  # Aumenta paralelismo
export API_THROTTLE_SLEEP=0.1  # Reduz delay entre chamadas
```

**Atenção:**
- Se receber **429 (Rate Limit)**: reduza `API_CONCURRENCY` ou aumente `API_THROTTLE_SLEEP`
- Gemini free-tier: recomendado `API_CONCURRENCY=5` e `API_THROTTLE_SLEEP=0.5`

---

### 3. ✅ Performance Logging
**Localização:** 
- `src/utils/helpers.py` (`measure_time` context manager)
- `src/agents/dspy_examiner.py`
- `src/agents/dspy_arbiter.py`
- `src/rag/retriever.py`

**Logs de Tempo:**
```
⏳ Iniciando: DSPy Examiner CORRETOR_1 - Question Q1...
✅ Concluído: DSPy Examiner CORRETOR_1 - Question Q1 em 3.2456 segundos.

⏳ Iniciando: RAG Retrieval (Similarity Search)...
✅ Concluído: RAG Retrieval (Similarity Search) em 0.1234 segundos.
```

**Como usar:**
```python
from src.utils.helpers import measure_time

with measure_time("Nome da Operação"):
    # código aqui
    pass
```

---

### 4. ✅ Streamlit Progress Streaming
**Localização:** `app/main.py`

- Progress bars durante geração de questões
- Progress bars durante simulação de respostas
- Progress bars durante correção
- Status containers com feedback visual em tempo real

**Features:**
- `st.status()` com expansão automática
- `st.progress()` com percentual
- Mensagens de feedback por fase (RAG, Corretor 1, Corretor 2, Árbitro)

---

### 5. ✅ Batch Processing Otimizado
**Localização:** `app/main.py` (Batch Processing mode)

**Estratégias:**
- **Chunking:** Processa alunos em lotes (default: 4)
- **Cooldown:** Pausa entre lotes para evitar rate limits
- **Paralelismo por questão:** Todos os alunos respondem Q1 em paralelo, depois Q2, etc.

**Configuração:**
```bash
export BATCH_CHUNK_SIZE=4  # Alunos por lote
export BATCH_COOLDOWN_SLEEP=0.0  # Pausa entre lotes (segundos)
```

**Exemplo de fluxo:**
1. **Gerar 5 questões** → 5 chamadas LLM sequenciais
2. **Simular 30 alunos × 5 questões:**
   - Loop: Q1 → 30 alunos em paralelo (usando `safe_gather`)
   - Loop: Q2 → 30 alunos em paralelo
   - ...
   - Total: 150 chamadas em 5 lotes
3. **Corrigir 30 alunos × 5 questões:**
   - Q1: 30 correções em chunks de 4 → ~8 lotes
   - Cada correção = 2 corretores + árbitro (se divergir)
   - Total: ~300-450 chamadas (dependendo de divergências)

---

## 📊 Benchmarks Esperados

### Antes da Otimização
- 10 alunos × 3 questões = **~10 minutos**
- Rate limits frequentes (429)
- UI congelada sem feedback

### Depois da Otimização
- 10 alunos × 3 questões = **~2-3 minutos**
- Cache RAG reduz 90% das buscas
- Paralelismo 5x maior (2 → 10)
- Feedback visual em tempo real

### Gemini Free-Tier (Recomendado)
```bash
export API_CONCURRENCY=5
export API_THROTTLE_SLEEP=0.5
export BATCH_CHUNK_SIZE=3
export BATCH_COOLDOWN_SLEEP=1.0
```

Tempo esperado: **~4-5 minutos** para 10 alunos × 3 questões

---

## 🔍 Como Monitorar Performance

### 1. Logs de Tempo
```bash
streamlit run app/main.py 2>&1 | grep "Concluído:"
```

### 2. Cache Hits
```bash
streamlit run app/main.py 2>&1 | grep "cache hit"
```

### 3. Rate Limits
```bash
streamlit run app/main.py 2>&1 | grep -E "(429|rate limit)"
```

---

## 🛠️ Troubleshooting

### Erro: 429 Too Many Requests
**Solução:**
```bash
export API_CONCURRENCY=3
export API_THROTTLE_SLEEP=1.0
export BATCH_COOLDOWN_SLEEP=2.0
```

### Lentidão: Cache não está funcionando
**Debug:**
```python
# Adicione em retriever.py
logger.info(f"Cache size: {len(_RAG_CACHE)}")
logger.info(f"Cache keys: {list(_RAG_CACHE.keys())}")
```

### UI congelando no Streamlit
**Causa:** Loop de evento bloqueado  
**Solução:** Todas as operações async já usam `run_async()` que cria novo event loop

---

## 📈 Próximas Otimizações (Opcional)

### 1. Persistent Cache (Redis/SQLite)
- Cache sobrevive a restarts do Streamlit
- Compartilhável entre sessões

### 2. Embedding Cache
- Cachear embeddings de questões
- Reduz latência de RAG ainda mais

### 3. Batch Embeddings
- Processar múltiplos textos em uma chamada
- Suportado por OpenAI e Gemini

### 4. LLM Response Caching
- Cachear respostas do LLM por (question, answer, rubric)
- Útil para demonstrações repetidas

### 5. Observability Dashboard
- Grafana/Prometheus para métricas em tempo real
- Tokens consumidos, latências, cache hit rate

---

## 📝 Changelog

### 2026-02-10
- ✅ Aumentado `API_CONCURRENCY` de 2 → 10
- ✅ Adicionado `measure_time` em DSPy Examiner e Arbiter
- ✅ Cache RAG já estava implementado (verificado)
- ✅ Streamlit progress já estava implementado (verificado)
- ✅ Documentação criada (este arquivo)

---

**Autor:** Alan Turing (AI Assistant)  
**Projeto:** ai-grading-system (TCC Lucas Savino)  
**Repo:** https://github.com/savinoo/ai-grading-system
