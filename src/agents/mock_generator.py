import logging
import uuid

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log, after_log

from src.core.settings import settings
from src.domain.ai.schemas import EvaluationCriterion, ExamQuestion, QuestionMetadata, StudentAnswer
from src.core.llm_handler import get_chat_model
from src.utils.helpers import measure_time

_logger = logging.getLogger("mock_generator")


class MockDataGeneratorAgent:
    """
    Agente responsável por gerar dados sintéticos (Questões e Respostas)
    para fins de teste e desenvolvimento.

    Otimização CPU/Ollama:
    - llm: usado para geração de questões (num_predict=OLLAMA_NUM_PREDICT_QUESTIONS)
    - _llm_answer: instância separada com num_predict menor para respostas de alunos
      (max 5 linhas ≈ 180 tokens — muito menor que o default de correção)
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        # Instância para respostas de alunos
        self._llm_answer = get_chat_model(temperature=1)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
        before_sleep=before_sleep_log(_logger, logging.WARNING),
        after=after_log(_logger, logging.WARNING),
    )
    async def generate_exam_question(self, topic: str, discipline: str, difficulty: str = "médio") -> ExamQuestion:
        """
        Gera uma questão de prova completa com rubrica baseada no tópico.
        """

        # Schema para output estruturado (uma versão wrapper para facilitar a geração)
        class GeneratedQuestionStructure(BaseModel):
            statement: str = Field(..., description="O enunciado da questão discursiva")
            rubric: list[EvaluationCriterion] = Field(..., description="Critérios de avaliação detalhados")

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
            id=uuid.uuid4(),
            statement=result.statement,
            rubric=result.rubric,
            metadata=QuestionMetadata(
                discipline=discipline,
                topic=topic,
                difficulty_level=difficulty
            )
        )

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
        before_sleep=before_sleep_log(_logger, logging.WARNING),
        after=after_log(_logger, logging.WARNING),
    )
    async def generate_exam_questions(self, topic: str, discipline: str, difficulty: str = "médio", count: int = 5) -> list[ExamQuestion]:
        """
        Gera uma lista de questões de uma única vez, com RUBRICA UNIFICADA para toda a prova.
        """

        # 1. Definição do Schema para Prova (Rubrica Global + Questões)
        class ExamSchema(BaseModel):
            global_rubric: list[EvaluationCriterion] = Field(..., description="Critérios de avaliação que se aplicam a TODAS as questões da prova (ex: Domínio do Conteúdo, Clareza, Argumentação)")
            questions: list[str] = Field(..., description=f"Lista contendo exatamente {count} enunciados de questões distintas")

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
                id=uuid.uuid4(),
                statement=q_stmt,
                rubric=result.global_rubric,
                metadata=QuestionMetadata(
                    discipline=discipline,
                    topic=topic,
                    difficulty_level=difficulty
                )
            ))

        return final_questions

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
        before_sleep=before_sleep_log(_logger, logging.WARNING),
        after=after_log(_logger, logging.WARNING),
    )
    async def generate_student_answer(self, question: ExamQuestion, quality: str = "average", student_name: str = "Student") -> StudentAnswer:
        """
        Gera uma resposta de aluno simulada com base na qualidade desejada.
        quality: 'excellent' (nota alta), 'average' (nota média), 'poor' (nota baixa/errada)

        Otimização CPU: usa _llm_answer (num_predict=180) em vez de with_structured_output,
        evitando overhead de JSON mode para output que é apenas texto puro.
        """
        quality_prompts = {
            "excellent": "A resposta deve ser exemplar: correta, completa, demonstrando domínio total do conteúdo e usando terminologia técnica adequada. Aborde todos os pontos da rubrica com precisão.",
            "average": "A resposta deve ser INTERMEDIÁRIA: aborde APENAS 2 dos pontos solicitados na questão, ignorando os demais. Use terminologia correta nos pontos que abordar, mas deixe lacunas visíveis. NÃO seja completo — um aluno mediano não cobre tudo. Escreva no máximo 3 frases.",
            "poor": "A resposta deve ser FRACA e INCORRETA. Cometa erros técnicos específicos: confunda os conceitos principais (ex: se a questão pede diferença entre A e B, atribua características de A para B e vice-versa). Demonstre confusão clara entre os termos. Escreva no máximo 2 frases curtas e superficiais. NÃO acerte nenhum ponto da rubrica.",
            "off_topic": "A resposta deve ser COMPLETAMENTE FORA DO TEMA. Responda sobre um assunto totalmente diferente do que foi perguntado, como se tivesse confundido a questão. Por exemplo, se a pergunta é sobre algoritmos, fale sobre culinária ou esportes. NÃO mencione nenhum conceito relacionado à questão."
        }

        instruction = quality_prompts.get(quality, quality_prompts["average"])
        rubric_text = "\n".join([f"- {c.name}: {c.description}" for c in question.rubric])

        # Plain text prompt — sem JSON wrapper (menos tokens, sem overhead de structured output)
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"Você é um aluno fictício chamado {student_name} realizando uma prova. "
                       "Responda a questão abaixo em no MÁXIMO 4 linhas. "
                       "NUNCA escreva 'eu não sei' ou comentários sobre a questão. "
                       "Responda diretamente, sem preâmbulos."),
            ("user", f"Questão: {question.statement}\n"
                     f"Rubrica: {rubric_text}\n"
                     f"Instrução de nível: {instruction}\n"
                     "Sua resposta:")
        ])

        chain = prompt | self._llm_answer

        with measure_time(f"Gerar Resposta Aluno ({quality} - {student_name})"):
            result = await chain.ainvoke({})

        # AIMessage.content é o texto direto
        text = result.content if hasattr(result, "content") else str(result)
        import uuid as _uuid
        return StudentAnswer(
            student_id=_uuid.uuid5(_uuid.NAMESPACE_DNS, f"simulated_{student_name}"),
            question_id=question.id,
            text=text.strip()
        )
