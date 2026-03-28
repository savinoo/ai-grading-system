from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.interfaces.services.grading.grading_workflow_service_interface import GradingWorkflowServiceInterface

from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.agent_schemas import AgentCorrection
from src.domain.ai.schemas import QuestionMetadata, EvaluationCriterion
from src.domain.ai.rag_schemas import RetrievedContext
from src.domain.ai.workflow.graph import get_grading_graph
from src.domain.ai.workflow.state import GradingState

from src.services.rag.retrieval_service import RetrievalService

from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.grading_criteria_repository_interface import GradingCriteriaRepositoryInterface
from src.interfaces.repositories.exam_criteria_repository_interface import ExamCriteriaRepositoryInterface

from src.models.entities.student_answer_criteria_scores import StudentAnswerCriteriaScore

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger


class GradingWorkflowService(GradingWorkflowServiceInterface):
    """
    Serviço wrapper para o LangGraph de correção.
    
    Responsabilidades:
    - Inicializar estado do grafo
    - Executar workflow completo
    - Persistir resultados no banco de dados
    - Gerenciar transações e rollback
    """
    
    def __init__(
        self,
        student_answer_repository: StudentAnswerRepositoryInterface,
        exam_question_repository: ExamQuestionRepositoryInterface,
        grading_criteria_repository: GradingCriteriaRepositoryInterface,
        exam_criteria_repository: ExamCriteriaRepositoryInterface
    ) -> None:
        """
        Inicializa service com repositórios injetados.
        
        Args:
            student_answer_repository: Repositório de respostas de alunos
            exam_question_repository: Repositório de questões
            grading_criteria_repository: Repositório de critérios de avaliação
            exam_criteria_repository: Repositório de critérios por prova
        """
        self.__student_answer_repository = student_answer_repository
        self.__exam_question_repository = exam_question_repository
        self.__grading_criteria_repository = grading_criteria_repository
        self.__exam_criteria_repository = exam_criteria_repository
        self.__graph = None  # Lazy initialization
        self.__logger = get_logger("services")
    
    def _ensure_graph_initialized(self):
        """Lazy initialization do grafo (só compila quando usar)."""
        if self.__graph is None:
            self.__graph = get_grading_graph()
    
    async def grade_single_answer(
        self,
        db: Session,
        exam_uuid: UUID,
        question: ExamQuestion,
        student_answer: StudentAnswer,
        *,
        rag_contexts: Optional[List[RetrievedContext]] = None
    ) -> Dict:
        """
        Executa workflow completo de correção usando LangGraph.
        
        Fluxo:
        1. Criar estado inicial
        2. Executar grafo (RAG → C1+C2 → Divergence → Árbitro → Consenso)
        3. Persistir resultado no DB
        
        Args:
            db: Sessão do banco de dados
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
        self.__logger.info(
            "Iniciando workflow LangGraph: aluno=%s, questão=%s",
            student_answer.student_id, question.id
        )
        
        # === Garantir que o grafo está inicializado ===
        self._ensure_graph_initialized()
        
        # === Criar estado inicial ===
        initial_state: GradingState = {
            "exam_uuid": exam_uuid,
            "question": question,
            "student_answer": student_answer,
            "rag_contexts": rag_contexts,
            "correction_1": None,
            "correction_2": None,
            "correction_arbiter": None,
            "divergence_detected": False,
            "divergence_value": None,
            "all_corrections": [],
            "final_score": None,
            "error": None,
            "processing_metadata": None
        }
        
        # === Executar grafo ===
        try:
            final_state = await self.__graph.ainvoke(initial_state)
            
            # === Persistir resultado ===
            if student_answer.id:
                await self.__persist_result(
                    db=db,
                    student_answer_uuid=student_answer.id,
                    final_score=final_state['final_score'],
                    corrections=final_state['all_corrections'],
                    question=question,
                    correction_1=final_state.get('correction_1'),
                    correction_2=final_state.get('correction_2'),
                    correction_arbiter=final_state.get('correction_arbiter'),
                    divergence_detected=final_state.get('divergence_detected', False),
                    divergence_value=final_state.get('divergence_value'),
                )
            else:
                self.__logger.warning(
                    "student_answer.id não fornecido - resultado não será persistido"
                )
            
            self.__logger.info(
                "Workflow concluído: nota=%.2f, árbitro=%s",
                final_state['final_score'],
                final_state.get('correction_arbiter') is not None
            )
            
            return {
                "final_score": final_state['final_score'],
                "all_corrections": final_state['all_corrections'],
                "divergence_detected": final_state['divergence_detected'],
                "divergence_value": final_state.get('divergence_value'),
                "correction_1": final_state.get('correction_1'),
                "correction_2": final_state.get('correction_2'),
                "correction_arbiter": final_state.get('correction_arbiter'),
                "processing_metadata": final_state.get('processing_metadata') or {}
            }
            
        except Exception as e:
            self.__logger.error(
                "Erro crítico no workflow: %s",
                str(e),
                exc_info=True
            )
            raise SqlError(
                message="Erro crítico no workflow de correção",
                context={
                    "exam_uuid": str(exam_uuid),
                    "question_id": str(question.id),
                    "student_id": str(student_answer.student_id)
                },
                cause=e
            ) from e
    
    async def __persist_result(
        self,
        db: Session,
        student_answer_uuid: UUID,
        final_score: float,
        corrections: List[AgentCorrection],
        question: ExamQuestion,
        correction_1: AgentCorrection = None,
        correction_2: AgentCorrection = None,
        correction_arbiter: AgentCorrection = None,
        divergence_detected: bool = False,
        divergence_value: float = None,
    ):
        """
        Persiste resultado no DB (student_answers + criteria_scores).

        Transação atômica:
        - UPDATE student_answers SET score, c1/c2/arbiter scores, divergence, is_graded, graded_at
        - INSERT INTO student_answer_criteria_scores (uma linha por critério POR agente)
        - COMMIT ou ROLLBACK em caso de erro
        
        Args:
            db: Sessão do banco de dados
            student_answer_uuid: UUID da resposta do aluno
            final_score: Nota final consensuada
            corrections: Lista de AgentCorrection (2 ou 3)
            question: Questão com rubrica
        """
        try:
            # === 1. Buscar resposta no banco ===
            answer_entity = self.__student_answer_repository.get_by_uuid(
                db,
                student_answer_uuid
            )

            # === 2. Deletar scores antigos (caso seja uma recorreção) ===
            db.query(StudentAnswerCriteriaScore).filter(
                StudentAnswerCriteriaScore.student_answer_uuid == student_answer_uuid
            ).delete()

            self.__logger.info(
                "Scores antigos removidos para resposta %s",
                student_answer_uuid
            )

            # === 3. Preparar lista ordenada de critérios da rubrica com UUIDs ===
            # Usamos a última correção (árbitro se existir, senão C2)
            final_correction = corrections[-1]

            # Lista ordenada: [(uuid, weight, max_score), ...] — mesma ordem da rubrica enviada ao LLM.
            # O match com os criteria_scores do LLM é feito por POSIÇÃO (zip), não pelo nome
            # retornado pelo LLM, evitando erros de digitação/variações na resposta da IA.
            rubric_entries = []
            for rubric_criterion in question.rubric:
                try:
                    criteria_entity = self.__grading_criteria_repository.get_by_code(
                        db,
                        rubric_criterion.name  # name armazena o code (ex: "ANALISE_CRITICA")
                    )
                    rubric_entries.append((
                        criteria_entity.uuid,
                        rubric_criterion.weight,
                        rubric_criterion.max_score,
                    ))
                except Exception as e:
                    self.__logger.warning(
                        "Critério '%s' não encontrado no banco: %s — será ignorado",
                        rubric_criterion.name, e
                    )
                    rubric_entries.append(None)  # placeholder para manter alinhamento de posição

            # === 4. Calcular weighted_score por critério e acumular nota final normalizada ===
            #
            # Fórmula:
            #   raw_weighted_sum   = Σ (raw_score_i × weight_i)
            #   total_max_weighted = Σ (max_score_i  × weight_i)
            #   nota_final = raw_weighted_sum / total_max_weighted × question_points

            total_max_weighted = sum(
                c.max_score * c.weight
                for c in question.rubric
            )
            question_points = question.total_points

            if total_max_weighted <= 0:
                self.__logger.warning(
                    "total_max_weighted inválido (%.4f) — usando scale=1.0",
                    total_max_weighted
                )
                total_max_weighted = 1.0

            raw_weighted_sum = 0.0
            criteria_score_entities = []

            # Mapa nome → índice na rubrica para match por nome
            rubric_name_to_idx = {
                question.rubric[i].name: i
                for i in range(len(question.rubric))
            }

            # Match: tenta por nome exato primeiro; se não achar, usa posição
            def _resolve_entry(idx: int, criterion_name: str):
                named_idx = rubric_name_to_idx.get(criterion_name)
                if named_idx is not None and rubric_entries[named_idx] is not None:
                    return rubric_entries[named_idx]
                if idx < len(rubric_entries) and rubric_entries[idx] is not None:
                    self.__logger.warning(
                        "Critério '%s' não encontrado pelo nome — usando posição %d como fallback",
                        criterion_name, idx
                    )
                    return rubric_entries[idx]
                return None

            for idx, criterion_score in enumerate(final_correction.criteria_scores):
                rubric_entry = _resolve_entry(idx, criterion_score.criterion)
                if rubric_entry is None:
                    continue
                criteria_uuid, criterion_weight, _ = rubric_entry

                raw_weighted = criterion_score.score * criterion_weight
                raw_weighted_sum += raw_weighted

                criteria_score_entities.append(
                    StudentAnswerCriteriaScore(
                        uuid=uuid4(),
                        student_answer_uuid=student_answer_uuid,
                        criteria_uuid=criteria_uuid,
                        agent_id="consensus",
                        raw_score=criterion_score.score,
                        weighted_score=raw_weighted,  # será atualizado abaixo após normalização
                        feedback=criterion_score.feedback
                    )
                )

            # Normalizar para a escala real da questão
            scale_factor = question_points / total_max_weighted
            corrected_final_score = raw_weighted_sum * scale_factor

            # Atualizar weighted_score de cada entidade com o valor normalizado
            for entity in criteria_score_entities:
                entity.weighted_score = entity.weighted_score * scale_factor

            self.__logger.info(
                "Nota normalizada: raw_weighted=%.2f / max_weighted=%.2f × question_pts=%.2f = %.2f (IA reportou: %.2f)",
                raw_weighted_sum, total_max_weighted, question_points, corrected_final_score, final_score
            )

            # === 5. Calcular notas individuais dos corretores com a mesma normalização ===
            def _normalized_score(correction: AgentCorrection) -> Optional[float]:
                if correction is None:
                    return None
                raw_sum = 0.0
                for i, cs in enumerate(correction.criteria_scores):
                    entry = _resolve_entry(i, cs.criterion)
                    if entry is not None:
                        raw_sum += cs.score * entry[1]
                return raw_sum * scale_factor

            c1_total = _normalized_score(correction_1)
            c2_total = _normalized_score(correction_2)
            arb_total = _normalized_score(correction_arbiter)

            # Determinar método de consenso
            if correction_arbiter:
                consensus_method = "closest_pair_3"
            else:
                consensus_method = "mean_2"

            # === 6. Atualizar student_answers com nota + dados individuais ===
            answer_entity.score = corrected_final_score
            answer_entity.c1_score = c1_total
            answer_entity.c2_score = c2_total
            answer_entity.arbiter_score = arb_total
            answer_entity.divergence_detected = divergence_detected
            answer_entity.divergence_value = divergence_value
            answer_entity.consensus_method = consensus_method
            answer_entity.is_graded = True
            answer_entity.graded_at = datetime.utcnow()
            answer_entity.status = "GRADED"

            self.__logger.info(
                "Resposta atualizada: UUID=%s, nota=%.2f (C1=%.2f, C2=%.2f, Arb=%s)",
                student_answer_uuid, corrected_final_score,
                c1_total or 0, c2_total or 0,
                f"{arb_total:.2f}" if arb_total is not None else "N/A"
            )

            # === 7. Inserir criteria_scores do consenso ===
            for score_entity in criteria_score_entities:
                db.add(score_entity)

            # === 8. Inserir criteria_scores individuais de cada corretor ===
            individual_corrections = []
            if correction_1:
                individual_corrections.append(correction_1)
            if correction_2:
                individual_corrections.append(correction_2)
            if correction_arbiter:
                individual_corrections.append(correction_arbiter)

            for correction in individual_corrections:
                for i, criterion_score in enumerate(correction.criteria_scores):
                    rubric_entry = _resolve_entry(i, criterion_score.criterion)
                    if rubric_entry is None:
                        continue
                    criteria_uuid, criterion_weight, _ = rubric_entry
                    raw_weighted = criterion_score.score * criterion_weight

                    # Extrair agent_id de AgentCorrection (objeto) ou dict;
                    # se for Enum, usar .value — garantir string armazenada.
                    if isinstance(correction, dict):
                        agent_id_value = correction.get('agent_id')
                    else:
                        agent_id_value = getattr(correction, 'agent_id', None)

                    # Se for Enum, extrair .value
                    if hasattr(agent_id_value, 'value'):
                        agent_id_value = agent_id_value.value

                    db.add(
                        StudentAnswerCriteriaScore(
                            uuid=uuid4(),
                            student_answer_uuid=student_answer_uuid,
                            criteria_uuid=criteria_uuid,
                            agent_id=agent_id_value,
                            raw_score=criterion_score.score,
                            weighted_score=raw_weighted * scale_factor,
                            feedback=criterion_score.feedback,
                        )
                    )

            # === 9. Commit da transação ===
            db.commit()

            self.__logger.info(
                "Persistência concluída: %d critérios salvos para resposta %s",
                len(criteria_score_entities),
                student_answer_uuid
            )
            
        except SQLAlchemyError as e:
            self.__logger.error(
                "Erro ao persistir resultado: %s - fazendo rollback",
                str(e),
                exc_info=True
            )
            db.rollback()
            raise
        except Exception as e:
            self.__logger.error(
                "Erro inesperado ao persistir resultado: %s",
                str(e),
                exc_info=True
            )
            db.rollback()
            raise
    
    async def grade_exam(self, db: Session, exam_uuid: UUID) -> Dict:
        """
        Corrige todas as respostas de todas as questões da prova.
        
        Fluxo:
        1. Buscar todas as questões do exame
        2. Para cada questão, buscar todas as respostas de alunos
        3. Chamar grade_single_answer para cada (questão, resposta)
        4. Agregar estatísticas (média, desvio padrão, distribuição)
        
        Args:
            db: Sessão do banco de dados
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
        self.__logger.info("Iniciando correção completa da prova %s", exam_uuid)
        
        try:
            # === 1. Buscar questões da prova ===
            questions = self.__exam_question_repository.get_by_exam(
                db,
                exam_uuid,
                active_only=True,
                limit=1000  # Ajustar se necessário
            )
            
            if not questions:
                self.__logger.warning("Nenhuma questão encontrada para prova %s", exam_uuid)
                return {
                    "total_questions": 0,
                    "total_answers": 0,
                    "graded_answers": 0,
                    "failed_answers": 0,
                    "average_score": 0.0,
                    "min_score": 0.0,
                    "max_score": 0.0
                }
            
            self.__logger.info("Encontradas %d questões na prova", len(questions))
            
            # === 2. Estatísticas ===
            total_answers = 0
            graded_answers = 0
            failed_answers = 0
            scores: List[float] = []

            # Reutilizar um único serviço de RAG durante toda a correção
            rag_service = RetrievalService()
            
            # === 3. Iterar por questões e respostas ===
            for question_entity in questions:
                # Buscar respostas para esta questão
                answers = self.__student_answer_repository.get_by_question(
                    db,
                    question_entity.uuid,
                    limit=1000
                )
                
                self.__logger.info(
                    "Questão %s: %d respostas para corrigir",
                    question_entity.uuid, len(answers)
                )
                
                # Pré-converter schema da questão (evita re-conversão a cada resposta)
                question_schema = self.__convert_question_to_schema(db, question_entity)
                question_graded_successfully = False

                # Pré-buscar contexto RAG uma única vez por questão e reutilizar em todas as respostas
                # Observação: o node de RAG no grafo irá pular retrieval caso rag_contexts já esteja preenchido.
                question_rag_contexts: Optional[List[RetrievedContext]] = None
                try:
                    question_rag_contexts = await rag_service.search_context(
                        query=question_schema.statement,
                        exam_uuid=exam_uuid,
                        discipline="Geral",
                        topic=None,
                    )
                except Exception as e:
                    # Falha de RAG não deve interromper toda a correção; o grafo ainda pode rodar
                    # (e, se necessário, tentará fazer retrieval novamente).
                    self.__logger.warning(
                        "Falha ao pré-buscar contexto RAG para questão %s: %s",
                        question_schema.id,
                        str(e),
                    )

                # Persistir contexto RAG na questão (uma vez, compartilhado por todas as respostas)
                if question_rag_contexts is not None:
                    try:
                        import json as _json
                        question_entity.rag_contexts_json = _json.dumps(
                            [
                                {
                                    "content": ctx.content,
                                    "source_document": ctx.source_document,
                                    "page_number": ctx.page_number,
                                    "relevance_score": ctx.relevance_score,
                                    "chunk_index": ctx.chunk_index,
                                }
                                for ctx in question_rag_contexts
                            ],
                            ensure_ascii=False,
                        )
                        db.add(question_entity)
                        db.commit()
                    except Exception as e:
                        self.__logger.warning(
                            "Falha ao persistir rag_contexts_json para questão %s: %s",
                            question_entity.uuid, str(e),
                        )
                        db.rollback()

                for answer_entity in answers:
                    total_answers += 1

                    answer_schema = StudentAnswer(
                        id=answer_entity.uuid,
                        student_id=answer_entity.student_uuid,
                        question_id=answer_entity.question_uuid,
                        text=answer_entity.answer or ""
                    )

                    try:
                        # Executar workflow de correção
                        result = await self.grade_single_answer(
                            db=db,
                            exam_uuid=exam_uuid,
                            question=question_schema,
                            student_answer=answer_schema,
                            rag_contexts=question_rag_contexts
                        )

                        graded_answers += 1
                        question_graded_successfully = True
                        scores.append(result['final_score'])

                        self.__logger.debug(
                            "Resposta %s corrigida: nota=%.2f",
                            answer_entity.uuid, result['final_score']
                        )

                    except Exception as e:
                        failed_answers += 1
                        self.__logger.error(
                            "Erro ao corrigir resposta %s: %s",
                            answer_entity.uuid, str(e),
                            exc_info=True
                        )

                # Marcar questão como corrigida se ao menos uma resposta foi processada
                if question_graded_successfully:
                    try:
                        self.__exam_question_repository.update(
                            db,
                            question_entity.id,
                            is_graded=True
                        )
                        db.commit()
                        self.__logger.info(
                            "Questão %s marcada como corrigida (is_graded=True)",
                            question_entity.uuid
                        )
                    except Exception as e:
                        self.__logger.warning(
                            "Erro ao marcar questão %s como corrigida: %s",
                            question_entity.uuid, str(e)
                        )
                        db.rollback()
            
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
            
            self.__logger.info(
                "Correção da prova %s concluída: %d/%d respostas corrigidas (%.1f%% sucesso)",
                exam_uuid,
                graded_answers,
                total_answers,
                (graded_answers / total_answers * 100) if total_answers > 0 else 0
            )
            self.__logger.info(
                "Estatísticas: média=%.2f, min=%.2f, max=%.2f",
                avg_score, min_score, max_score
            )
            
            return result
            
        except Exception as e:
            self.__logger.error(
                "Erro fatal ao corrigir prova %s: %s",
                exam_uuid, str(e),
                exc_info=True
            )
            raise
    
    def __convert_question_to_schema(self, db: Session, question_entity) -> ExamQuestion:
        """
        Converte entidade ExamQuestion do DB para schema Pydantic.
        
        Busca os critérios reais da prova via exam_criteria e converte para rubrica.
        
        Args:
            db: Sessão do banco de dados
            question_entity: Entidade do banco
        
        Returns:
            ExamQuestion schema Pydantic com rubrica completa
        """
        # === 1. Buscar critérios da prova do banco ===
        exam_criteria_list = self.__exam_criteria_repository.get_by_exam(
            db,
            question_entity.exam_uuid,
            active_only=True,
            limit=100
        )
        
        # === 2. Converter ExamCriteria → EvaluationCriterion ===
        rubric = []
        for exam_criterion in exam_criteria_list:
            # exam_criterion.grading_criteria já vem carregado (lazy="joined")
            grading_criterion = exam_criterion.grading_criteria
            
            # Normalizar weight para decimal (0–1):
            # Se o valor armazenado for > 1 assume-se escala percentual (ex: 30 → 0.30),
            # caso contrário já está em decimal (ex: 0.30) e é usado diretamente.
            raw_weight = float(exam_criterion.weight)
            weight_decimal = raw_weight / 100.0 if raw_weight > 1.0 else raw_weight

            # Calcular max_score: usar max_points se definido, senão weight * points da questão
            max_score = exam_criterion.max_points if exam_criterion.max_points else (
                weight_decimal * float(question_entity.points)
            )

            rubric.append(
                EvaluationCriterion(
                    name=grading_criterion.code,
                    description=grading_criterion.description or grading_criterion.name,
                    weight=weight_decimal,
                    max_score=float(max_score)
                )
            )
        
        # === 3. Fallback: se não houver critérios, criar um genérico ===
        if not rubric:
            self.__logger.warning(
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
        # Nota: se ExamQuestion tiver campos discipline/topic/difficulty, usar aqui
        metadata = QuestionMetadata(
            discipline="Geral",
            topic="Geral",
            difficulty_level="medio"
        )
        
        return ExamQuestion(
            id=question_entity.uuid,
            statement=question_entity.statement or "Questão sem enunciado",
            total_points=float(question_entity.points) if question_entity.points else 10.0,
            rubric=rubric,
            metadata=metadata
        )
