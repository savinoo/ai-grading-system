from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.services.exam_questions.list_exam_questions_service import ListExamQuestionsService
from fastapi import HTTPException


class ListExamQuestionsController:
    """
    Controlador para listar questões de uma prova.
    
    Responsibilities:
        - Receber requisições para listar questões
        - Validar parâmetros
        - Chamar o serviço apropriado
        - Retornar resposta estruturada
    """
    
    def __init__(self, service: ListExamQuestionsService):
        """
        Constructor que injeta a dependência do serviço.
        
        Args:
            service (ListExamQuestionsService): Serviço de listagem de questões
        """
        self.service = service
    
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Manipula a requisição de listagem de questões.
        
        Args:
            http_request (HttpRequest): Requisição HTTP com parâmetros
            
        Returns:
            HttpResponse: Resposta HTTP com lista de questões
            
        Raises:
            HTTPException: Se houver erro no processamento
        """
        try:
            # Extrair parâmetros
            exam_uuid = http_request.param.get("exam_uuid")
            teacher_uuid = http_request.token_infos.get("sub")
            
            if not exam_uuid:
                raise HTTPException(
                    status_code=400,
                    detail="Parâmetro 'exam_uuid' é obrigatório"
                )
            
            if not teacher_uuid:
                raise HTTPException(
                    status_code=401,
                    detail="Usuário não autenticado"
                )
            
            # Executar serviço
            questions = self.service.execute(
                exam_uuid=exam_uuid,
                teacher_uuid=teacher_uuid,
                db=http_request.db
            )
            
            # Retornar resposta
            return HttpResponse(
                status_code=200,
                body=questions
            )
            
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao listar questões: {str(e)}"
            ) from e
