from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.interfaces.services.users.create_user_service_interface import CreateUserServiceInterface
from src.interfaces.repositories.user_repository_interface import UserRepositoryInterface

from src.models.entities.user import User

from src.domain.requests.users.user_create_request import UserCreateRequest
from src.domain.responses.users.user_response import UserResponse

from src.errors.domain.already_existing import AlreadyExistingError
from src.errors.domain.sql_error import SqlError

from src.core.security.hash_password import HashPasswordHandler
from src.core.brevo_handler import BrevoHandler
from src.core.logging_config import get_logger

class CreateUserService(CreateUserServiceInterface):
    """
    Serviço para criação de usuários.
    
    Centraliza a lógica de negócio relacionada a criação usuários,
    incluindo criação e formatação de respostas.
    """
    
    def __init__(self, repository: UserRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)
        self.__hash_handler = HashPasswordHandler()
        self.__brevo_handler = BrevoHandler()
    
    async def create_user(self, db: Session, request: UserCreateRequest) -> UserResponse:
        """
        Cria um novo usuário.
        
        Args:
            db: Sessão do banco de dados
            request: Dados do usuário a ser criado
            
        Returns:
            UserResponse: Dados do usuário criado
            
        Raises:
            AlreadyExistingError: Se o email já estiver cadastrado
            SqlError: Para erros de banco de dados
        """
        try:
            self.__logger.info("Criando novo usuário: %s", request.email)
            
            # Verifica se o email já existe
            if self.__repository.exists_by_email(db, request.email):
                self.__logger.warning("Tentativa de criar usuário com email duplicado: %s", request.email)
                raise AlreadyExistingError(
                    message=f"Email {request.email} já está cadastrado",
                    context={"email": request.email}
                )
            
            # Hash da senha
            password_hash = self.__hash_password(request.password)
            
            # Cria o usuário
            user = self.__repository.create(
                db,
                uuid=uuid4(),
                email=request.email,
                first_name=request.first_name,
                last_name=request.last_name,
                password_hash=password_hash,
                user_type=request.user_type,
                active=True,
                email_verified=False
            )
            
            self.__logger.info("Usuário criado com sucesso: ID=%s, email=%s", user.id, user.email)
            
            # Cria contato na Brevo e envia email de verificação
            await self.__send_verification_email(user)
            
            # Formata e retorna a resposta
            return self.__format_user_response(user)
            
        except AlreadyExistingError:
            raise
        except IntegrityError as e:
            self.__logger.error("Erro de integridade ao criar usuário: %s", e, exc_info=True)
            raise AlreadyExistingError(
                message="Email já está cadastrado",
                context={"email": request.email},
                cause=e
            ) from e
        except Exception as e:
            self.__logger.error("Erro ao criar usuário: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao criar usuário no banco de dados",
                context={"email": request.email},
                cause=e
            ) from e
    
    def __hash_password(self, password: str) -> str:
        """
        Gera hash da senha usando bcrypt.
        
        Args:
            password: Senha em texto plano
            
        Returns:
            str: Senha hash
        """
        return self.__hash_handler.generate_password_hash(password)
    
    def __format_user_response(self, user: User) -> UserResponse:
        """
        Formata a entidade User em UserResponse.
        
        Args:
            user: Entidade do usuário
            
        Returns:
            UserResponse: Resposta formatada
        """
        return UserResponse.model_validate(user)
    
    async def __send_verification_email(self, user: User) -> None:
        """
        Envia email de verificação para o usuário via Brevo.
        
        Args:
            user: Entidade do usuário
        """
        try:
            # Cria/atualiza contato na Brevo
            contact_created = await self.__brevo_handler.create_or_update_contact(
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                user_uuid=user.uuid,
                user_type=user.user_type
            )
            
            if not contact_created:
                self.__logger.warning(
                    "Falha ao criar contato na Brevo para %s, mas continuando...",
                    user.email
                )
            
            # Envia email de verificação
            email_sent = await self.__brevo_handler.send_verification_email(
                email=user.email,
                user_uuid=user.uuid
            )
            
            if email_sent:
                self.__logger.info("Email de verificação enviado para %s", user.email)
            else:
                self.__logger.warning(
                    "Falha ao enviar email de verificação para %s",
                    user.email
                )
                
        except Exception as e:
            # Não falha o cadastro se o email falhar
            self.__logger.error(
                "Erro ao enviar email de verificação para %s: %s",
                user.email, str(e),
                exc_info=True
            )
