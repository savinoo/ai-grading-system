"""
Service de alto nível para workflow de correção automática.
Wrapper do LangGraph que gerencia execução e persistência.
"""

import logging
from typing import Dict, List
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.agent_schemas import AgentCorrection
from src.domain.ai.schemas import QuestionMetadata, EvaluationCriterion
from src.models.repositories.student_answer_repository import StudentAnswerRepository
from src.models.repositories.exam_question_repository import ExamQuestionRepository
from src.models.repositories.grading_criteria_repository import GradingCriteriaRepository
from src.models.repositories.exam_criteria_repository import ExamCriteriaRepository
from src.models.entities.student_answer_criteria_scores import StudentAnswerCriteriaScore
from .workflow.graph import get_grading_graph
from .workflow.state import GradingState

logger = logging.getLogger(__name__)


class GradingWorkflowService:
    """
    Service wrapper para o LangGraph de correção.
    
    Responsabilidades:
    - Inicializar estado do grafo
    - Executar workflow completo
    - Persistir resultados no banco de dados
    - Gerenciar transações e rollback
    """
    
    def __init__(self, db: Session):
        """
        Inicializa service com conexão ao banco.
        
        Args:
            db: Sessão SQLAlchemy ativa
        """
        self.db = db
        self.graph = get_grading_graph()
        self.student_answer_repo = StudentAnswerRepository()
        self.exam_question_repo = ExamQuestionRepository()
        self.grading_criteria_repo = GradingCriteriaRepository()
        self.exam_criteria_repo = ExamCriteriaRepository()
    
    async def grade_single_answer(
        self,
        exam_uuid: UUID,
        question: ExamQuestion,
        student_answer: StudentAnswer
    ) -> Dict:
        """
        Executa workflow completo de correção usando LangGraph.
        
        Fluxo:
        1. Criar estado inicial
        2. Executar grafo (RAG → C1+C2 → Divergence → Árbitro → Consenso)
        3. Persistir resultado no DB
        
        Args:
            exam_uuid: UUID da prova (para filtrar RAG)
            question: Questão com enunciado e rubrica
            student_answer: Resposta do aluno (deve conter student_answer.id para persistência)
        
        Returns:
            {
                "final_score": float,
                "all_corrections": List[AgentCorrection],
                "divergence_detected": bool
            }
        
        Raises:
            Exception: Erros do LangGraph ou persistência
        """
        logger.info(
            "Iniciando workflow LangGraph: aluno=%s, questão=%s",
            student_answer.student_id, question.id
        )
        
        # === Criar estado inicial ===
        initial_state: GradingState = {
            "exam_uuid": exam_uuid,
            "question": question,
            "student_answer": student_answer,
            "rag_contexts": None,
            "correction_1": None,
            "correction_2": None,
            "correction_arbiter": None,
            "divergence_detected": False,
            "divergence_value": None,
            "all_corrections": [],
            "final_score": None,
            "error": None
        }
        
        # === Executar grafo ===
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            # === Persistir resultado ===
            if student_answer.id:
                await self._persist_result(
                    student_answer_uuid=student_answer.id,
                    final_score=final_state['final_score'],
                    corrections=final_state['all_corrections'],
                    question=question
                )
            else:
                logger.warning(
                    "student_answer.id não fornecido - resultado não será persistido"
                )
            
            logger.info(
                "Workflow concluído: nota=%.2f, árbitro=%s",
                final_state['final_score'],
                final_state.get('correction_arbiter') is not None
            )
            
            return {
                "final_score": final_state['final_score'],
                "all_corrections": final_state['all_corrections'],
                "divergence_detected": final_state['divergence_detected']
            }
            
        except Exception as e:
            logger.error(
                "Erro no workflow: %s",
                str(e),
                exc_info=True
            )
            raise
    
    async def _persist_result(
        self,
        student_answer_uuid: UUID,
        final_score: float,
        corrections: List[AgentCorrection],
        question: ExamQuestion
    ):
        """
        Persiste resultado no DB (student_answers + criteria_scores).
        
        Transação atômica:
        - UPDATE student_answers SET score, is_graded, graded_at
        - INSERT INTO student_answer_criteria_scores (uma linha por critério)
        - COMMIT ou ROLLBACK em caso de erro
        
        Args:
            student_answer_uuid: UUID da resposta do aluno
            final_score: Nota final consensuada
            corrections: Lista de AgentCorrection (2 ou 3)
            question: Questão com rubrica
        """
        try:
            # === 1. Buscar resposta no banco ===
            answer_entity = self.student_answer_repo.get_by_uuid(
                self.db,
                student_answer_uuid
            )
            
            # === 2. Atualizar student_answers ===
            self.student_answer_repo.update(
                self.db,
                answer_entity.id,
                score=final_score,
                is_graded=True,
                graded_at=datetime.utcnow(),
                status="GRADED"
            )
            
            logger.info(
                "Resposta atualizada: UUID=%s, nota=%.2f",
                student_answer_uuid, final_score
            )
            
            # === 3. Preparar mapeamento de critérios (nome → UUID + peso) ===
            # Usamos a última correção (árbitro se existir, senão C2)
            final_correction = corrections[-1]
            
            # Mapear critérios: nome → (uuid, weight)
            criteria_map = {}
            weight_map = {}
            
            for rubric_criterion in question.rubric:
                # Buscar UUID do critério no banco pelo nome
                try:
                    criteria_entity = self.grading_criteria_repo.get_by_code(
                        self.db,
                        rubric_criterion.name  # Assumindo que name é o code
                    )
                    criteria_map[rubric_criterion.name] = criteria_entity.uuid
                    weight_map[rubric_criterion.name] = rubric_criterion.weight
                except Exception as e:
                    logger.warning(
                        "Critério '%s' não encontrado no banco: %s",
                        rubric_criterion.name, e
                    )
                    # Se não encontrar, criar UUID temporário e usar peso da rubrica
                    criteria_map[rubric_criterion.name] = uuid4()
                    weight_map[rubric_criterion.name] = rubric_criterion.weight
            
            # === 4. Inserir criteria_scores ===
            for criterion_score in final_correction.criteria_scores:
                criteria_uuid = criteria_map.get(criterion_score.criterion_name)
                criterion_weight = weight_map.get(criterion_score.criterion_name, 1.0)
                
                if not criteria_uuid:
                    logger.warning(
                        "UUID não encontrado para critério '%s' - pulando",
                        criterion_score.criterion_name
                    )
                    continue
                
                # Calcular weighted_score = raw_score * weight
                weighted_score = criterion_score.score * criterion_weight
                
                # Criar registro de score por critério
                score_entity = StudentAnswerCriteriaScore(
                    uuid=uuid4(),
                    student_answer_uuid=student_answer_uuid,
                    criteria_uuid=criteria_uuid,
                    raw_score=criterion_score.score,
                    weighted_score=weighted_score,
                    feedback=criterion_score.feedback
                )
                
                self.db.add(score_entity)
            
            # === 5. Commit da transação ===
            self.db.commit()
            
            logger.info(
                "Persistência concluída: %d critérios salvos para resposta %s",
                len(final_correction.criteria_scores),
                student_answer_uuid
            )
            
        except SQLAlchemyError as e:
            logger.error(
                "Erro ao persistir resultado: %s - fazendo rollback",
                str(e),
                exc_info=True
            )
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(
                "Erro inesperado ao persistir resultado: %s",
                str(e),
                exc_info=True
            )
            self.db.rollback()
            raise
    
    async def grade_exam(self, exam_uuid: UUID) -> Dict:
        """
        Corrige todas as respostas de todas as questões da prova.
        
        Fluxo:
        1. Buscar todas as questões do exame
        2. Para cada questão, buscar todas as respostas de alunos
        3. Chamar grade_single_answer para cada (questão, resposta)
        4. Agregar estatísticas (média, desvio padrão, distribuição)
        
        Args:
            exam_uuid: UUID da prova a ser corrigida
        
        Returns:
            {
                "total_questions": int,
                "total_answers": int,
                "graded_answers": int,
                "failed_answers": int,
                "average_score": float,
                "min_score": float,
                "max_score": float
            }
        """
        logger.info("Iniciando correção completa da prova %s", exam_uuid)
        
        try:
            # === 1. Buscar questões da prova ===
            questions = self.exam_question_repo.get_by_exam(
                self.db,
                exam_uuid,
                active_only=True,
                limit=1000  # Ajustar se necessário
            )
            
            if not questions:
                logger.warning("Nenhuma questão encontrada para prova %s", exam_uuid)
                return {
                    "total_questions": 0,
                    "total_answers": 0,
                    "graded_answers": 0,
                    "failed_answers": 0,
                    "average_score": 0.0,
                    "min_score": 0.0,
                    "max_score": 0.0
                }
            
            logger.info("Encontradas %d questões na prova", len(questions))
            
            # === 2. Estatísticas ===
            total_answers = 0
            graded_answers = 0
            failed_answers = 0
            scores: List[float] = []
            
            # === 3. Iterar por questões e respostas ===
            for question_entity in questions:
                # Buscar respostas para esta questão
                answers = self.student_answer_repo.get_by_question(
                    self.db,
                    question_entity.uuid,
                    limit=1000
                )
                
                logger.info(
                    "Questão %s: %d respostas para corrigir",
                    question_entity.uuid, len(answers)
                )
                
                for answer_entity in answers:
                    total_answers += 1
                    
                    # Converter entidades DB → schemas Pydantic
                    question_schema = self._convert_question_to_schema(question_entity)
                    answer_schema = StudentAnswer(
                        id=answer_entity.uuid,
                        student_id=answer_entity.student_uuid,
                        question_id=answer_entity.question_uuid,
                        text=answer_entity.answer or ""
                    )
                    
                    try:
                        # Executar workflow de correção
                        result = await self.grade_single_answer(
                            exam_uuid=exam_uuid,
                            question=question_schema,
                            student_answer=answer_schema
                        )
                        
                        graded_answers += 1
                        scores.append(result['final_score'])
                        
                        logger.debug(
                            "Resposta %s corrigida: nota=%.2f",
                            answer_entity.uuid, result['final_score']
                        )
                        
                    except Exception as e:
                        failed_answers += 1
                        logger.error(
                            "Erro ao corrigir resposta %s: %s",
                            answer_entity.uuid, str(e),
                            exc_info=True
                        )
            
            # === 4. Calcular estatísticas agregadas ===
            avg_score = sum(scores) / len(scores) if scores else 0.0
            min_score = min(scores) if scores else 0.0
            max_score = max(scores) if scores else 0.0
            
            result = {
                "total_questions": len(questions),
                "total_answers": total_answers,
                "graded_answers": graded_answers,
                "failed_answers": failed_answers,
                "average_score": round(avg_score, 2),
                "min_score": round(min_score, 2),
                "max_score": round(max_score, 2)
            }
            
            logger.info(
                "Correção da prova %s concluída: %d/%d respostas corrigidas (%.1f%% sucesso)",
                exam_uuid,
                graded_answers,
                total_answers,
                (graded_answers / total_answers * 100) if total_answers > 0 else 0
            )
            logger.info(
                "Estatísticas: média=%.2f, min=%.2f, max=%.2f",
                avg_score, min_score, max_score
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Erro fatal ao corrigir prova %s: %s",
                exam_uuid, str(e),
                exc_info=True
            )
            raise
    
    def _convert_question_to_schema(self, question_entity) -> ExamQuestion:
        """
        Converte entidade ExamQuestion do DB para schema Pydantic.
        
        Busca os critérios reais da prova via exam_criteria e converte para rubrica.
        
        Args:
            question_entity: Entidade do banco
        
        Returns:
            ExamQuestion schema Pydantic com rubrica completa
        """
        # === 1. Buscar critérios da prova do banco ===
        exam_criteria_list = self.exam_criteria_repo.get_by_exam(
            self.db,
            question_entity.exam_uuid,
            active_only=True,
            limit=100
        )
        
        # === 2. Converter ExamCriteria → EvaluationCriterion ===
        rubric = []
        for exam_criterion in exam_criteria_list:
            # exam_criterion.grading_criteria já vem carregado (lazy="joined")
            grading_criterion = exam_criterion.grading_criteria
            
            # Calcular max_score: usar max_points se definido, senão weight * points da questão
            max_score = exam_criterion.max_points if exam_criterion.max_points else (
                float(exam_criterion.weight) * float(question_entity.points)
            )
            
            rubric.append(
                EvaluationCriterion(
                    name=grading_criterion.code,  # Usar code como identificador
                    description=grading_criterion.description or grading_criterion.name,
                    weight=float(exam_criterion.weight),
                    max_score=float(max_score)
                )
            )
        
        # === 3. Fallback: se não houver critérios, criar um genérico ===
        if not rubric:
            logger.warning(
                "Nenhum critério encontrado para prova %s - usando critério genérico",
                question_entity.exam_uuid
            )
            rubric = [
                EvaluationCriterion(
                    name="CRITERIO_GERAL",
                    description="Critério genérico de avaliação",
                    weight=1.0,
                    max_score=float(question_entity.points)
                )
            ]
        
        # === 4. Construir metadata (extrair de campos se existirem) ===
        # TODO: Se ExamQuestion tiver campos discipline/topic/difficulty, usar aqui
        metadata = QuestionMetadata(
            discipline="Geral",
            topic="Geral",
            difficulty_level="medio"
        )
        
        return ExamQuestion(
            id=question_entity.uuid,
            statement=question_entity.statement or "Questão sem enunciado",
            rubric=rubric,
            metadata=metadata
        )
