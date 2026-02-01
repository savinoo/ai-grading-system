# AI Grading System: Multi-Agent Pedagogical Framework 🎓🤖

[![Thesis](https://img.shields.io/badge/Thesis-Computer_Engineering-blue)](https://github.com/savinoo/ai-grading-system)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange)](https://github.com/langchain-ai/langgraph)
[![DSPy](https://img.shields.io/badge/Optimization-DSPy-red)](https://github.com/stanfordnlp/dspy)
[![Observability](https://img.shields.io/badge/Observability-LangSmith-green)](https://www.langchain.com/langsmith)

An advanced automated grading system for open-ended (discursive) evaluations, developed as a Capstone Project (TCC) for Computer Engineering. This system leverages state-of-the-art Multi-Agent orchestration and RAG to provide objective, rubrics-based pedagogical feedback.

## 🔬 Project Overview

Traditional automated grading often fails to capture the nuances of discursive answers. This project addresses this by implementing a **Multi-Agent Consensus/Divergence** architecture. By using multiple independent LLM agents (Graders) and a centralized Referee, the system minimizes hallucination and ensures grading consistency aligned with official pedagogical materials.

## 🚀 Core Features

- **🎭 Multi-Agent Grading**: Employs independent agents that evaluate answers against a rubric. A 'Referee Agent' reconciles differences, ensuring a robust final grade.
- **📚 Pedagogical RAG**: Integrates Retrieval-Augmented Generation to ground every correction in the provided source material (PDFs/Courseware).
- **⚙️ DSPy Integration**: Utilizes Programmatic Prompt Optimization to ensure high-quality outputs across different LLM backends (OpenAI, Gemini).
- **📊 Simulation Suite**: Includes a "Synthetic Student" generator to pressure-test rubrics and grading consistency at scale.
- **🖥️ Streamlit Dashboard**: A complete interface for instructors to upload materials, define rubrics, and review automated grades with full transparency.
- **👁️ Deep Observability**: Native LangSmith integration for granular tracing of agent reasoning steps and cost management.

## 🛠️ Architecture

- **Engine**: LangGraph for stateful workflow orchestration.
- **Intelligence**: OpenAI GPT-4o / Google Gemini 1.5 Pro.
- **Vector Engine**: ChromaDB for context retrieval.
- **Frontend**: Streamlit.

## 📂 Project Structure

- `app/`: Streamlit UI and presentation layer.
- `src/agents/`: Specialized agent definitions (Graders, Synthetic Students).
- `src/workflow/`: The LangGraph state machine definition.
- `src/rag/`: Document ingestion and retrieval logic.
- `src/infrastructure/`: LLM abstraction and LangSmith configurations.

## 🚀 Setup & Usage

### Installation
```bash
git clone https://github.com/savinoo/ai-grading-system.git
cd ai-grading-system
pip install -r requirements.txt
```

### Environment Config
Copy `.env.example` to `.env` and provide your API keys:
```env
OPENAI_API_KEY=...
GOOGLE_API_KEY=...
LANGSMITH_API_KEY=...
```

### Run
```bash
streamlit run app/main.py
```

## 📈 Research Context
This system was designed to bridge the gap between AI and Education, focusing on:
1. **Fairness**: Reducing human bias in discursive grading.
2. **Efficiency**: Accelerating the feedback loop for students.
3. **Scalability**: Handling massive cohorts with consistent pedagogical standards.

---
**Author:** [Lucas Lorenzo Savino](https://github.com/savinoo)
*Computer Engineering Thesis Project*
