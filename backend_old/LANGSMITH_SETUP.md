# LangSmith Integration Guide

Este guia explica como configurar e usar o LangSmith com a aplicação de correção automática.

## O que é LangSmith?

LangSmith é uma plataforma de observabilidade e debugging para aplicações LLM que oferece:

- **Rastreamento (Tracing)**: Visualize toda a cadeia de execução de prompts e respostas
- **Avaliação**: Compare diferentes versões de prompts e modelos
- **Feedback**: Registre feedback manual para melhorar o sistema
- **Análise**: Monitore latência, custo e qualidade das requisições

## Setup

### 1. Obter API Key

1. Acesse [https://smith.langchain.com](https://smith.langchain.com)
2. Faça login ou crie uma conta
3. Navegue até "Settings" → "API Keys"
4. Crie uma nova chave e copie

### 2. Configurar Variáveis de Ambiente

Adicione ao seu arquivo `.env`:

```bash
# LangSmith Configuration
LANGSMITH_API_KEY=your-api-key-here
LANGSMITH_TRACING_ENABLED=true
LANGSMITH_PROJECT_NAME=ai-grading-system
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

### 3. Instalar Dependência

```bash
pip install langsmith
```

Ou atualize via requirements.txt:

```bash
pip install -r requirements.txt
```

## Como Funciona

### Inicialização Automática

O LangSmith é automaticamente inicializado quando a aplicação inicia:

```python
from src.infrastructure.langsmith_config import initialize_langsmith
initialize_langsmith()
```

### Rastreamento Automático

Quando habilitado, **qualquer chamada ao LLM** será automaticamente rastreada, incluindo:

- ✓ Chamadas dos Corretores (Examiner Agents)
- ✓ Invocações do Árbitro
- ✓ Consultas RAG
- ✓ Processamento do LangGraph

Não é necessário modificar o código existente!

## Visualizar Traces

### Dashboard Web

Após executar a aplicação com `LANGSMITH_TRACING_ENABLED=true`:

1. Acesse [https://smith.langchain.com](https://smith.langchain.com)
2. Selecione o projeto `ai-grading-system` (ou o nome configurado)
3. Você verá todos os traces em tempo real

### Informações no Sidebar

A aplicação Streamlit exibe:

```
📊 Observabilidade
✓ LangSmith Ativo
Projeto: ai-grading-system
[Ver Dashboard]
```

## Estrutura de Traces

Um trace típico de correção inclui:

```
Trace: Correção de Questão
├── Retrieve Context Node
│   └── RAG Query
├── Corrector 1 Node
│   ├── Format Prompt
│   └── LLM Call (GPT-4o-mini)
├── Corrector 2 Node
│   ├── Format Prompt
│   └── LLM Call (GPT-4o-mini)
├── Calculate Divergence Node
├── (Condição) → Arbiter ou Finalize
└── Finalize Node
```

## Funcionalidades Avançadas

### Feedback Manual

Você pode marcar traces com feedback no dashboard:

1. Abra um trace
2. Clique em "Add feedback"
3. Marque como "Thumbs Up" ou "Thumbs Down"
4. Adicione notas

### Comparar Versões

Use o LangSmith para testar diferentes prompts:

1. No dashboard, entre em "Sessions"
2. Compare resultados lado a lado
3. Analise latência e qualidade

### Custos

Monitore consumo de tokens e custo das requisições no dashboard:

- Visualize custo por chamada
- Agregações por projeto
- Alertas de limite de orçamento

## Desabilitar LangSmith

Se quiser desabilitar o rastreamento sem remover a configuração:

```bash
LANGSMITH_TRACING_ENABLED=false
```

## Troubleshooting

### "LangSmith Desativado" no Sidebar

**Causa**: `LANGSMITH_API_KEY` não configurada ou `LANGSMITH_TRACING_ENABLED=false`

**Solução**:
```bash
export LANGSMITH_API_KEY=your-key-here
export LANGSMITH_TRACING_ENABLED=true
```

### Traces não aparecem no dashboard

**Causa**: Inicialização não ocorreu ou credenciais inválidas

**Verificar**:
```python
from src.infrastructure.langsmith_config import is_langsmith_enabled
print(is_langsmith_enabled())  # Deve retornar True
```

### Erro de autenticação

**Cause**: API Key inválida ou expirada

**Solução**: Gere uma nova chave em [https://smith.langchain.com/settings](https://smith.langchain.com/settings)

## Referências

- [Documentação LangSmith](https://docs.smith.langchain.com/)
- [LangChain Integração](https://python.langchain.com/docs/langsmith/)
- [Python SDK](https://docs.smith.langchain.com/reference/python/)

## Arquivos Modificados

- `requirements.txt` - Adicionado `langsmith`
- `src/config/settings.py` - Configurações LangSmith
- `src/infrastructure/langsmith_config.py` - Módulo de inicialização (novo)
- `app/main.py` - Integração no startup
- `.env.example` - Exemplo de configuração

---

**Nota**: O LangSmith está totalmente integrado e não requer mudanças no código existente. Funciona automaticamente uma vez configurado!
