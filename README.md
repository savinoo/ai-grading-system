# AI Grading System (TCC)

Sistema de correção automática de avaliações discursivas utilizando Agentes de IA (LLMs), RAG (Retrieval-Augmented Generation) e orquestração via LangGraph. Desenvolvido como parte do Trabalho de Conclusão de Curso de Engenharia de Computação.

## 🚀 Funcionalidades

- **Correção Multi-Agente:** Utiliza dois corretores independentes e um árbitro para resolver divergências (Consenso/Divergência).
- **RAG (Retrieval-Augmented Generation):** Embasa as correções em material de referência (PDFs) carregados pelo usuário.
- **Modo Simulação:** Gera alunos e respostas sintéticas para validar a rubrica e o sistema em escala.
- **Observabilidade:** Integração nativa com **LangSmith** para rastreamento de execução e custos.
- **Interface Interativa:** Dashboard completo desenvolvido em Streamlit.

## 🛠️ Instalação

### Pré-requisitos
- Python 3.10+
- Chave de API da OpenAI ou Google Gemini

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone <repo-url>
   cd ai-grading-system
   ```

2. **Crie um ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   # .\venv\Scripts\activate  # Windows
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuração de Variáveis de Ambiente:**
   Crie um arquivo `.env` na raiz do projeto com as seguintes chaves:
   
   ```env
   # LLM Providers
   OPENAI_API_KEY=sk-...
   GOOGLE_API_KEY=AIza...

   # LangSmith (Opcional, mas recomendado para TCC)
   LANGSMITH_TRACING_ENABLED=true
   LANGSMITH_API_KEY=lsv2_...
   LANGSMITH_PROJECT_NAME=ai-grading-system
   ```

## ▶️ Execução

Para iniciar a interface web:

```bash
streamlit run app/main.py
```

O navegador abrirá automaticamente em `http://localhost:8501`.

## 📂 Estrutura do Projeto

- **`app/`**: Interface do usuário (Streamlit) e lógica de apresentação.
- **`src/`**: Núcleo do sistema.
  - **`agents/`**: Definição dos agentes (Corretores, Mock Data).
  - **`workflow/`**: Grafo de execução (LangGraph).
  - **`rag/`**: Lógica de indexação e busca vetorial.
  - **`infrastructure/`**: Configurações de LLM, Banco Vetorial e LangSmith.
- **`data/`**: Persistência local (SQLite/Arquivos).

## 🧪 Modos de Uso

1. **Single Student (Debug):** Ideal para testar prompts e rubricas em um caso isolado.
2. **Batch Processing (Turma):** Simula uma turma inteira, gerando respostas com diferentes perfis de qualidade ("Excellent", "Average", "Poor") e processa as correções em lote.

---
**Autor:** Lucas Lorenzo Savino
