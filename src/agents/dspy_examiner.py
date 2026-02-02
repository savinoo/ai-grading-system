import dspy
import logging
import asyncio
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.domain.schemas import AgentCorrection, AgentID
from src.domain.state import GraphState
from src.config.settings import settings
from src.config.prompts import format_rubric_text, format_rag_context
# from src.infrastructure.dspy_config import configure_dspy # REMOVIDO: Configuração deve ser global no main

logger = logging.getLogger(__name__)

# Garante a configuração
# configure_dspy()

class GradingSignature(dspy.Signature):
    """
    Avalie a resposta do aluno com base na rubrica detalhada.
    IMPORTANTE: Sua saída deve ser ESTRITAMENTE um objeto JSON válido seguindo o schema de AgentCorrection.
    NÃO escreva introduções, markdown ou texto livre fora do JSON.
    Campos obrigatórios: reasoning_chain, criteria_scores (lista), total_score, feedback_text.
    """
    question_statement = dspy.InputField(desc="O enunciado da questão da prova")
    rubric_formatted = dspy.InputField(desc="A rubrica de avaliação detalhada com critérios e pesos")
    rag_context_formatted = dspy.InputField(desc="Trechos relevantes do material didático (RAG)")
    student_answer = dspy.InputField(desc="A resposta discursiva submetida pelo aluno")
    
    correction = dspy.OutputField(desc="A correção estruturada (JSON)", type=AgentCorrection)

class DSPyExaminerModule(dspy.Module):
    def __init__(self):
        super().__init__()
        # Ajuste para compatibilidade com versões do DSPy onde TypedPredictor foi renomeado ou integrado
        # Em DSPy moderno, ChainOfThought com assinatura tipada já tenta fazer o parsing
        try:
             self.grading = dspy.TypedPredictor(GradingSignature)
        except AttributeError:
             # Fallback para versão onde TypedPredictor não está no topo ou v3+ que usa Predict integrado
             # Usamos ChainOfThought que é melhor para nossa usecase (precisa de raciocínio)
             self.grading = dspy.ChainOfThought(GradingSignature)

    def forward(self, question_statement, rubric_formatted, rag_context_formatted, student_answer):
        return self.grading(
            question_statement=question_statement,
            rubric_formatted=rubric_formatted,
            rag_context_formatted=rag_context_formatted,
            student_answer=student_answer
        )

class DSPyExaminerAgent:
    """
    Versão DSPy do ExaminerAgent.
    Substitui o pipeline LangChain pelo dspy.TypedPredictor para melhor otimização e estrutura.
    """
    def __init__(self):
        self.module = DSPyExaminerModule()

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(10),
        reraise=True
    )
    @traceable(name="DSPy Examiner Evaluation", run_type="chain")
    async def evaluate(self, state: GraphState, agent_id: AgentID) -> AgentCorrection:
        """
        Executa a avaliação usando DSPy.
        """
        question = state["question"]
        student_answer = state["student_answer"]
        rag_context = state["rag_context"]

        formatted_rubric = format_rubric_text(question.rubric)
        formatted_context = format_rag_context(rag_context)

        logger.info(f"[{agent_id}] (DSPy) Iniciando avaliação da questão {question.id}...")

        # Execução síncrona do DSPy encapsulada em thread para não bloquear o loop async
        loop = asyncio.get_event_loop()
        
        def run_prediction():
            return self.module(
                question_statement=question.statement,
                rubric_formatted=formatted_rubric,
                rag_context_formatted=formatted_context,
                student_answer=student_answer.text
            )

        try:
            prediction = await loop.run_in_executor(None, run_prediction)
            
            # Tratamento robusto para retorno do DSPy (Objeto vs String vs Dict)
            raw_result = prediction.correction
            
            if isinstance(raw_result, AgentCorrection):
                result = raw_result
            elif isinstance(raw_result, str):
                # Se voltou string (às vezes acontece em fallbacks), parseamos manualmente
                # Remove markdown code blocks se houver
                clean_json = raw_result.replace("```json", "").replace("```", "").strip()
                
                # Tentativa de 'Rescue': Se não começar com '{', é texto solto (Markdown do Gemini).
                if not clean_json.strip().startswith("{"):
                    logger.warning(f"[{agent_id}] Modelo retornou texto livre. Tentando estruturar manual.")
                    # Cria um objeto 'pobre' mas funcional para não quebrar o fluxo
                    import re
                    # Tenta achar nota tipo "Nota: 0.8/2.0" ou "Total: 10"
                    score_match = re.search(r"(?:Nota|Total|Score)[:\s]*(\d+[\.,]?\d*)", clean_json, re.IGNORECASE)
                    score = float(score_match.group(1).replace(",", ".")) if score_match else 0.0
                    
                    result = AgentCorrection(
                        agent_id=agent_id,
                        reasoning_chain=clean_json, # O texto todo vira o raciocínio
                        criteria_scores=[],
                        total_score=score,
                        feedback_text="[Sistema] Correção gerada em formato texto (fallback aplicado)."
                    )
                else:
                    result = AgentCorrection.model_validate_json(clean_json)
                    
            else:
                # Fallback universal para Dict ou Objetos DSPy
                # Converte para dict se não for
                if hasattr(raw_result, "model_dump"):
                    data = raw_result.model_dump()
                elif hasattr(raw_result, "to_dict"):
                    data = raw_result.to_dict()
                elif isinstance(raw_result, dict):
                    data = raw_result
                else:
                    data = dict(raw_result) # Tenta cast direto

                # --- SANITIZAÇÃO DE TIPOS (FLASH FIX) ---
                # 1. Reasoning Chain (Lista -> String)
                if "reasoning_chain" in data and isinstance(data["reasoning_chain"], list):
                    data["reasoning_chain"] = "\n".join(data["reasoning_chain"])
                
                # 2. Criteria Scores (Lista de Dicts -> Dict)
                if "criteria_scores" in data and isinstance(data["criteria_scores"], list):
                    new_scores = {}
                    for item in data["criteria_scores"]:
                        if isinstance(item, dict):
                            # Tenta pegar chaves/valores de forma resiliente
                            k = item.get('criterion') or item.get('name') or (list(item.keys())[0] if item else "Unknown")
                            v = item.get('score') or item.get('value') or (list(item.values())[0] if item else 0.0)
                            new_scores[str(k)] = float(v)
                    data["criteria_scores"] = new_scores

                # 3. Agent ID (Injeção)
                if "agent_id" not in data:
                    data["agent_id"] = agent_id

                result = AgentCorrection.model_validate(data)

            # Garante que o ID do agente está correto e recupera CoT antigo se vier separado
            # Se usou ChainOfThought, o raciocínio pode estar em prediction.rationale ou prediction.reasoning
            if hasattr(prediction, 'rationale'):
                 # Se o reasoning dentro do JSON estiver vazio, usamos o do DSPy
                 if not result.reasoning_chain: 
                     result.reasoning_chain = prediction.rationale

            result.agent_id = agent_id
            
            # Recalcula total score por segurança (via validador do Pydantic)
            result.calculate_total_if_missing()
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no DSPy Examiner: {e}")
            raise e
