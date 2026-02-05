# src/config/alternative_prompts.py

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

"""
ALTERNATIVE PROMPTS (Caminho 'Mais Leve')
-----------------------------------------
Se não quisermos usar frameworks complexos como DSPy, podemos usar 
ChatPromptTemplates modulares com 'partials' e injeção de constantes.

Vantagens:
- Zero dependências extras.
- Controle total sobre o texto 'raw'.
- Fácil de debugar (what you see is what you get).

Esta abordagem foca em quebrar o prompt monolítico em componentes reutilizáveis.
"""

# Componentes Reutilizáveis (Lego Blocks do Prompt)
BASE_INSTRUCTIONS = """
Você é um Especialista em Avaliação Educacional.
Sua prioridade é verificar a COMPREENSÃO CONCEITUAL e não apenas correspondência de palavras-chave.
"""

RAG_INSTRUCTION_BLOCK = """
### CONTEXTO (MATERIAL DIDÁTICO):
O texto abaixo é sua referência de verdade.
{rag_context}
Use-o para validar definições técnicas. Se o aluno contradizer este texto, está errado.
"""

RUBRIC_INSTRUCTION_BLOCK = """
### CRITÉRIOS DE AVALIAÇÃO (RUBRICA):
{rubric}
Você deve pontuar CADA critério individualmente. Não dê nota global.
"""

OUTPUT_FORMAT_INSTRUCTION = """
### FORMATO DE SAÍDA:
Responda APENAS em JSON, seguindo estritamente este schema:
{{
    "reasoning_chain": "Passo a passo do pensamento...",
    "criteria_scores": {{"criterio_1": 1.5, "criterio_2": 2.0}},
    "total_score": 3.5,
    "feedback_text": "Texto para o aluno..."
}}
"""

# Montagem do Prompt "Leve"
def get_lightweight_corrector_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", BASE_INSTRUCTIONS),
        ("system", "O enunciado da questão é: {question_statement}"),
        ("system", RAG_INSTRUCTION_BLOCK),
        ("system", RUBRIC_INSTRUCTION_BLOCK),
        ("system", OUTPUT_FORMAT_INSTRUCTION),
        ("human", "Avalie esta resposta do aluno:\n{student_answer}")
    ])

# Exemplo de como usar (apenas documentação):
# prompt = get_lightweight_corrector_prompt()
# chain = prompt | llm
