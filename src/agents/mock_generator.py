from typing import List, Optional
import asyncio
import uuid
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.domain.schemas import ExamQuestion, StudentAnswer, QuestionMetadata, EvaluationCriterion
from src.utils.helpers import measure_time

class MockDataGeneratorAgent:
    """
    Agente responsável por gerar dados sintéticos (Questões e Respostas)
    para fins de teste e desenvolvimento.
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def generate_exam_question(self, topic: str, discipline: str, difficulty: str = "Medium") -> ExamQuestion:
        """
        Gera uma questão de prova completa com rubrica baseada no tópico.
        """
        
        # Schema para output estruturado (uma versão wrapper para facilitar a geração)
        class GeneratedQuestionStructure(BaseModel):
            statement: str = Field(..., description="O enunciado da questão discursiva")
            rubric: List[EvaluationCriterion] = Field(..., description="Critérios de avaliação detalhados")
            
        structured_llm = self.llm.with_structured_output(GeneratedQuestionStructure)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um professor técnico criando uma questão de prova. "
                       "A questão deve ser discursiva, mas EXTREMAMENTE ESPECÍFICA e TÉCNICA. "
                       "Evite perguntas gerais como 'Explique X'. "
                       "Prefira perguntas que exijam listar componentes, diferenciar conceitos com critérios claros ou descrever um processo passo-a-passo. "
                       "IMPORTANTE: Não inclua numerações como 'Parte 1' no texto. "
                       "Crie uma rubrica de correção objetiva."),
            ("user", "Crie uma questão TÉCNICA sobre o tópico '{topic}' da disciplina '{discipline}'. "
                     "Nível de dificuldade: {difficulty}. "
                     "Gere o enunciado e a rubrica.")
        ])
        
        chain = prompt | structured_llm
        
        with measure_time(f"Gerar Questão Individual (Tópico: {topic})"):
            result = await chain.ainvoke({"topic": topic, "discipline": discipline, "difficulty": difficulty})
        
        # Monta o objeto final ExamQuestion
        return ExamQuestion(
            id=str(uuid.uuid4()),
            statement=result.statement,
            rubric=result.rubric,
            metadata=QuestionMetadata(
                discipline=discipline,
                topic=topic,
                difficulty_level=difficulty
            )
        )

    async def generate_exam_questions(self, topic: str, discipline: str, difficulty: str = "Medium", count: int = 5) -> List[ExamQuestion]:
        """
        Gera uma lista de questões de uma única vez, com RUBRICA UNIFICADA para toda a prova.
        """
        
        # 1. Definição do Schema para Prova (Rubrica Global + Questões)
        class ExamSchema(BaseModel):
            global_rubric: List[EvaluationCriterion] = Field(..., description="Critérios de avaliação que se aplicam a TODAS as questões da prova (ex: Domínio do Conteúdo, Clareza, Argumentação)")
            questions: List[str] = Field(..., description=f"Lista contendo exatamente {count} enunciados de questões distintas")

        # 2. Configuração do Modelo
        structured_llm = self.llm.with_structured_output(ExamSchema)
        
        # 3. Prompt Otimizado para Variedade
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um professor exigente elaborando uma prova técnica. "
                       "Sua tarefa é criar {count} questões sobre o tema. "
                       "REGRAS: \n"
                       "1. Defina uma **Rubrica Global** que sirva para avaliar o desempenho do aluno na prova como um todo.\n"
                       "2. A soma dos pesos/notas dos critérios deve totalizar **exatamente 10.0 pontos**.\n"
                       "3. Crie {count} questões discursivas **distintas** cobrindo diferentes sub-tópicos.\n"
                       "4. **ESPECIFICIDADE**: As questões devem ser TÉCNICAS e OBJETIVAS (mesmo que discursivas). Evite perguntas amplas como 'Fale sobre X'. Prefira 'Quais são os 3 componentes de X e sua função?', 'Diferencie X de Y considerando Z'.\n"
                       "5. O objetivo é testar se o aluno sabe ou não o conceito detalhado."),
            ("user", "Disciplina: {discipline}\n"
                     "Tópico Geral: {topic}\n"
                     "Dificuldade: {difficulty}\n"
                     "Quantidade: {count} questões.\n\n"
                     "Gere a prova agora.")
        ])
        
        # 4. Execução Única (Batch)
        chain = prompt | structured_llm
        
        with measure_time(f"Gerar {count} Questões (Batch)"):
            result = await chain.ainvoke({
                "topic": topic, 
                "discipline": discipline, 
                "difficulty": difficulty,
                "count": count
            })
        
        # 5. Conversão para Objetos de Domínio
        # A mesma rubrica global é distribuída para todas as questões (para manter compatibilidade com o schema atual)
        final_questions = []
        for q_stmt in result.questions:
            final_questions.append(ExamQuestion(
                id=str(uuid.uuid4()),
                statement=q_stmt,
                rubric=result.global_rubric, 
                metadata=QuestionMetadata(
                    discipline=discipline,
                    topic=topic,
                    difficulty_level=difficulty
                )
            ))
            
        return final_questions

    async def generate_student_answer(self, question: ExamQuestion, quality: str = "average", student_name: str = "Student") -> StudentAnswer:
        """
        Gera uma resposta de aluno simulada com base na qualidade desejada.
        quality: 'excellent' (nota alta), 'average' (nota média), 'poor' (nota baixa/errada)
        """
        
        # Schema simples apenas para o texto
        class GeneratedAnswerStructure(BaseModel):
            text: str = Field(..., description="A resposta do aluno")
            
        structured_llm = self.llm.with_structured_output(GeneratedAnswerStructure)
        
        quality_prompts = {
            "excellent": "A resposta deve ser exemplar: correta, completa, demonstrando domínio total do conteúdo e usando terminologia técnica adequada. Aborde todos os pontos da rubrica com precisão.",
            "average": "A resposta deve ser mediana: correta no geral, mas superficial. USE ESTRATÉGIAS DE GENERALIZAÇÃO para disfarçar o desconhecimento de detalhes específicos. Substitua termos técnicos precisos por explicações mais amplas e vagas, tentando 'enrolar' um pouco onde faltar profundidade, mas sem cometer erros graves.",
            "poor": "A resposta deve ser insatisfatória: apresente conceitos errados ou confunda fatos. USE ESTRATÉGIAS DE GENERALIZAÇÃO EXCESSIVA ('embromação') para esconder que não sabe a resposta. Tente parecer que sabe falando de coisas vagamente relacionadas ou inventando fatos com confiança para mascarar sua ignorância. Tente enganar o corretor."
        }
        
        instruction = quality_prompts.get(quality, quality_prompts["average"])
        
        rubric_text = "\n".join([f"- {c.name}: {c.description}" for c in question.rubric])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"Você é um aluno fictício chamado {student_name} realizando uma prova.\n"
                       "Sua tarefa é escrever a resposta da questão abaixo.\n\n"
                       "REGRA DE OURO (PERSONA):\n"
                       "- NUNCA escreva 'eu não sei', 'desculpe', 'não entendi' ou comentários sobre a questão.\n"
                       "- SEMPRE tente responder com convicção, mesmo que esteja falando bobagem (no caso de qualidade ruim).\n"
                       "- Imite o estilo de escrita de um estudante (pode ser formal ou um pouco coloquial, dependendo do nível).\n\n"
                       "DIRETRIZES DE TAMANHO:\n"
                       "- Máximo de 5 linhas.\n"
                       "- Seja direto."),
            ("user", f"Questão: {question.statement}\n\n"
                     f"Critérios de Avaliação (Rubrica):\n{rubric_text}\n\n"
                     f"INSTRUÇÃO DE PERFORMANCE PARA O ALUNO: {instruction}\n"
                     "Escreva APENAS a resposta do aluno.")
        ])
        
        chain = prompt | structured_llm
        
        with measure_time(f"Gerar Resposta Aluno ({quality} - {student_name})"):
            result = await chain.ainvoke({})
        
        return StudentAnswer(
            student_id=f"simulated_{student_name.lower().replace(' ', '_')}",
            question_id=question.id,
            text=result.text
        )
