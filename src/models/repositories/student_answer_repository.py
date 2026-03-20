# pylint: disable=C0121
from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface

from src.models.entities.student_answers import StudentAnswer

from src.core.logging_config import get_logger

class StudentAnswerRepository(StudentAnswerRepositoryInterface):
    """
    Repositório para operações CRUD da entidade StudentAnswer.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

    def get_by_id(self, db: Session, answer_id: int) -> StudentAnswer:
        """
        Busca resposta por ID.
        
        Args:
            db: Sessão do banco de dados
            answer_id: ID da resposta
            
        Returns:
            StudentAnswer: Entidade da resposta
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a resposta não existir
        """
        try:
            stmt = select(StudentAnswer).where(StudentAnswer.id == answer_id)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Resposta encontrada: ID=%s", answer_id)
            return result

        except NoResultFound:
            self.__logger.warning("Resposta não encontrada: ID=%s", answer_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar resposta por ID: %s", e, exc_info=True)
            raise

    def get_by_uuid(self, db: Session, uuid: UUID) -> StudentAnswer:
        """
        Busca resposta por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da resposta
            
        Returns:
            StudentAnswer: Entidade da resposta
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a resposta não existir
        """
        try:
            stmt = select(StudentAnswer).where(StudentAnswer.uuid == uuid)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Resposta encontrada: UUID=%s", uuid)
            return result

        except NoResultFound:
            self.__logger.warning("Resposta não encontrada: UUID=%s", uuid)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar resposta por UUID: %s", e, exc_info=True)
            raise

    def get_by_exam(
        self,
        db: Session,
        exam_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[StudentAnswer]:
        """
        Lista respostas de uma prova específica.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[StudentAnswer]: Lista de respostas da prova
        """
        try:
            stmt = select(StudentAnswer).where(StudentAnswer.exam_uuid == exam_uuid)
            stmt = stmt.offset(skip).limit(limit).order_by(StudentAnswer.created_at.desc())
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d respostas da prova %s", len(result), exam_uuid)
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar respostas da prova: %s", e, exc_info=True)
            raise

    def get_by_student_and_exam(
        self,
        db: Session,
        student_uuid: UUID,
        exam_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[StudentAnswer]:
        """
        Lista respostas de um aluno em uma prova específica.
        
        Args:
            db: Sessão do banco de dados
            student_uuid: UUID do aluno
            exam_uuid: UUID da prova
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[StudentAnswer]: Lista de respostas do aluno na prova
        """
        try:
            stmt = select(StudentAnswer).where(
                and_(
                    StudentAnswer.student_uuid == student_uuid,
                    StudentAnswer.exam_uuid == exam_uuid
                )
            )
            stmt = stmt.offset(skip).limit(limit).order_by(StudentAnswer.created_at)
            result = db.execute(stmt).scalars().all()
            self.__logger.debug(
                "Listadas %d respostas do aluno %s na prova %s", 
                len(result),
                student_uuid,
                exam_uuid
            )
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar respostas do aluno na prova: %s", e, exc_info=True)
            raise

    def get_by_question(
        self,
        db: Session,
        question_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[StudentAnswer]:
        """
        Lista respostas de uma questão específica.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[StudentAnswer]: Lista de respostas da questão
        """
        try:
            stmt = select(StudentAnswer).where(StudentAnswer.question_uuid == question_uuid)
            stmt = stmt.offset(skip).limit(limit).order_by(StudentAnswer.created_at)
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d respostas da questão %s", len(result), question_uuid)
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar respostas da questão: %s", e, exc_info=True)
            raise

    def count_by_exam(self, db: Session, exam_uuid: UUID) -> int:
        """
        Conta o total de respostas de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            int: Total de respostas da prova
        """
        try:
            stmt = select(func.count(StudentAnswer.id)).where(StudentAnswer.exam_uuid == exam_uuid)  # pylint: disable=not-callable
            result = db.execute(stmt).scalar()
            self.__logger.debug("Total de respostas da prova %s: %d", exam_uuid, result)
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar respostas da prova: %s", e, exc_info=True)
            raise

    def has_answers_for_exam(self, db: Session, exam_uuid: UUID) -> bool:
        """
        Verifica se existem respostas para uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            bool: True se existem respostas, False caso contrário
        """
        try:
            count = self.count_by_exam(db, exam_uuid)
            return count > 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao verificar respostas da prova: %s", e, exc_info=True)
            raise

    def count_by_exam_and_graded(self, db: Session, exam_uuid: UUID, is_graded: bool) -> int:
        """
        Conta respostas de uma prova por status de correção.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            is_graded: True para contar corrigidas, False para não corrigidas
            
        Returns:
            int: Total de respostas
        """
        try:
            stmt = select(func.count(StudentAnswer.id)).where(  # pylint: disable=not-callable
                StudentAnswer.exam_uuid == exam_uuid,
                StudentAnswer.is_graded == is_graded
            )
            result = db.execute(stmt).scalar()
            self.__logger.debug(
                "Total de respostas %s da prova %s: %d",
                "corrigidas" if is_graded else "não corrigidas",
                exam_uuid,
                result
            )
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar respostas por status de correção: %s", e, exc_info=True)
            raise

    def count_by_exam_and_status(self, db: Session, exam_uuid: UUID, status: str) -> int:
        """
        Conta respostas de uma prova por status.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            status: Status da resposta
            
        Returns:
            int: Total de respostas com o status especificado
        """
        try:
            stmt = select(func.count(StudentAnswer.id)).where(  # pylint: disable=not-callable
                StudentAnswer.exam_uuid == exam_uuid,
                StudentAnswer.status == status
            )
            result = db.execute(stmt).scalar()
            self.__logger.debug(
                "Total de respostas da prova %s com status %s: %d",
                exam_uuid,
                status,
                result
            )
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar respostas por status: %s", e, exc_info=True)
            raise

    def count_by_teacher(self, db: Session, teacher_uuid: UUID) -> int:
        """
        Conta total de respostas de provas de um professor.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            
        Returns:
            int: Total de respostas
        """
        try:
            from src.models.entities.exams import Exams
            
            stmt = select(func.count(StudentAnswer.id)).join(  # pylint: disable=not-callable
                Exams,
                StudentAnswer.exam_uuid == Exams.uuid
            ).where(
                Exams.created_by == teacher_uuid,
                Exams.active == True
            )
            result = db.execute(stmt).scalar()
            self.__logger.debug("Total de respostas para professor %s: %d", teacher_uuid, result)
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar respostas do professor: %s", e, exc_info=True)
            raise

    def count_by_teacher_and_graded(self, db: Session, teacher_uuid: UUID, is_graded: bool) -> int:
        """
        Conta respostas de provas de um professor por status de correção.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            is_graded: True para contar corrigidas, False para não corrigidas
            
        Returns:
            int: Total de respostas
        """
        try:
            from src.models.entities.exams import Exams
            
            stmt = select(func.count(StudentAnswer.id)).join(  # pylint: disable=not-callable
                Exams,
                StudentAnswer.exam_uuid == Exams.uuid
            ).where(
                Exams.created_by == teacher_uuid,
                Exams.active == True
            )
            
            if is_graded is not None:
                stmt = stmt.where(StudentAnswer.is_graded == is_graded)
                
            result = db.execute(stmt).scalar()
            self.__logger.debug(
                "Total de respostas %s para professor %s: %d",
                "corrigidas" if is_graded else "não corrigidas",
                teacher_uuid,
                result
            )
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar respostas do professor por correção: %s", e, exc_info=True)
            raise

    def count_by_teacher_and_status(self, db: Session, teacher_uuid: UUID, status: str) -> int:
        """
        Conta respostas de provas de um professor por status.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            status: Status da resposta
            
        Returns:
            int: Total de respostas com o status especificado
        """
        try:
            from src.models.entities.exams import Exams
            
            stmt = select(func.count(StudentAnswer.id)).join(  # pylint: disable=not-callable
                Exams,
                StudentAnswer.exam_uuid == Exams.uuid
            ).where(
                Exams.created_by == teacher_uuid,
                Exams.active == True,
                StudentAnswer.status == status
            )
            result = db.execute(stmt).scalar()
            self.__logger.debug(
                "Total de respostas para professor %s com status %s: %d",
                teacher_uuid,
                status,
                result
            )
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar respostas do professor por status: %s", e, exc_info=True)
            raise

    # ==================== CREATE OPERATIONS ====================

    def create(
        self,
        db: Session,
        *,
        uuid: UUID,
        exam_uuid: UUID,
        question_uuid: UUID,
        student_uuid: UUID,
        answer: Optional[str] = None,
        status: str = "SUBMITTED",
        score: Optional[float] = None,
        feedback: Optional[str] = None,
        graded_at: Optional[datetime] = None,
        graded_by: Optional[UUID] = None
    ) -> StudentAnswer:
        """
        Cria uma nova resposta de aluno.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da resposta
            exam_uuid: UUID da prova
            question_uuid: UUID da questão
            student_uuid: UUID do aluno
            answer: Resposta do aluno
            status: Status da resposta (SUBMITTED, GRADED, INVALID)
            score: Pontuação obtida
            feedback: Feedback da correção
            graded_at: Data/hora da correção
            graded_by: UUID do corretor
            
        Returns:
            StudentAnswer: Resposta criada
        """
        try:
            new_answer = StudentAnswer(
                uuid=uuid,
                exam_uuid=exam_uuid,
                question_uuid=question_uuid,
                student_uuid=student_uuid,
                answer=answer,
                status=status,
                score=score,
                feedback=feedback,
                graded_at=graded_at,
                graded_by=graded_by
            )

            db.add(new_answer)
            db.flush()
            db.refresh(new_answer)

            self.__logger.info(
                "Resposta criada: UUID=%s (Aluno: %s, Prova: %s, Questão: %s)",
                uuid,
                student_uuid,
                exam_uuid,
                question_uuid
            )
            return new_answer

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao criar resposta: %s", e, exc_info=True)
            raise

    # ==================== UPDATE OPERATIONS ====================

    def update(self, db: Session, answer_id: int, **updates) -> StudentAnswer:
        """
        Atualiza uma resposta.
        
        Args:
            db: Sessão do banco de dados
            answer_id: ID da resposta
            **updates: Campos a atualizar
            
        Returns:
            StudentAnswer: Resposta atualizada
        """
        try:
            answer_obj = self.get_by_id(db, answer_id)

            for key, value in updates.items():
                if hasattr(answer_obj, key):
                    setattr(answer_obj, key, value)

            db.flush()
            db.refresh(answer_obj)

            self.__logger.info("Resposta atualizada: ID=%s", answer_id)
            return answer_obj

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar resposta: %s", e, exc_info=True)
            raise

    # ==================== DELETE OPERATIONS ====================

    def delete(self, db: Session, answer_id: int) -> None:
        """
        Remove uma resposta.
        
        Args:
            db: Sessão do banco de dados
            answer_id: ID da resposta
        """
        try:
            answer_obj = self.get_by_id(db, answer_id)
            db.delete(answer_obj)
            db.flush()

            self.__logger.info("Resposta removida: ID=%s", answer_id)

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao remover resposta: %s", e, exc_info=True)
            raise
