from src.models.repositories.exam_question_repository import ExamQuestionRepository
from src.models.repositories.exams_repository import ExamsRepository
from src.domain.responses.exam_questions.exam_question_response import ExamQuestionResponse
from fastapi import HTTPException


class ListExamQuestionsService:
    """
    Serviço para listar questões de uma prova.
    
    Responsibilities:
        - Validar que a prova existe e pertence ao professor
        - Buscar todas as questões da prova
        - Retornar as questões em formato de resposta
    """
    
    def __init__(self, 
                 exam_question_repository: ExamQuestionRepository,
                 exams_repository: ExamsRepository):
        """
        Constructor que injeta as dependências do repositório.
        
        Args:
            exam_question_repository (ExamQuestionRepository): Repositório de questões
            exams_repository (ExamsRepository): Repositório de provas
        """
        self.exam_question_repository = exam_question_repository
        self.exams_repository = exams_repository
    
    def execute(self, exam_uuid: str, teacher_uuid: str, db) -> list[ExamQuestionResponse]:
        """
        Executa o serviço de listagem de questões.
        
        Args:
            exam_uuid (str): UUID da prova
            teacher_uuid (str): UUID do professor autenticado
            db: Sessão do banco de dados
            
        Returns:
            list[ExamQuestionResponse]: Lista de questões da prova
            
        Raises:
            HTTPException: Se a prova não existe ou não pertence ao professor
        """
        # Validar que a prova existe e pertence ao professor
        exam = self.exams_repository.find_by_uuid(exam_uuid, db)
        if not exam:
            raise HTTPException(
                status_code=404,
                detail=f"Prova com UUID {exam_uuid} não encontrada"
            )
        
        # Verificar se a prova pertence ao professor
        if exam.teacher_uuid != teacher_uuid:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para acessar as questões desta prova"
            )
        
        # Buscar as questões
        questions = self.exam_question_repository.find_by_exam_uuid(exam_uuid, db)
        
        # Converter para response
        return [
            ExamQuestionResponse(
                uuid=q.uuid,
                exam_uuid=q.exam_uuid,
                title=q.title,
                description=q.description,
                max_score=q.max_score,
                question_number=q.question_number,
                created_at=q.created_at,
                updated_at=q.updated_at
            )
            for q in questions
        ]
