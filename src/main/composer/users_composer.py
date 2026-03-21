from src.models.repositories.user_repository import UserRepository
from src.models.repositories.auth_refresh_token_repository import AuthRefreshTokenRepository

from src.services.users.create_user_service import CreateUserService
from src.services.users.verify_email_service import VerifyEmailService
from src.services.users.resend_verification_email_service import ResendVerificationEmailService
from src.services.users.generate_recovery_code_service import GenerateRecoveryCodeService
from src.services.users.validate_recovery_code_service import ValidateRecoveryCodeService
from src.services.users.reset_password_service import ResetPasswordService
from src.services.users.change_password_service import ChangePasswordService

from src.controllers.users.create_user_controller import CreateUserController
from src.controllers.users.verify_email_controller import VerifyEmailController
from src.controllers.users.resend_verification_email_controller import ResendVerificationEmailController
from src.controllers.users.generate_recovery_code_controller import GenerateRecoveryCodeController
from src.controllers.users.validate_recovery_code_controller import ValidateRecoveryCodeController
from src.controllers.users.reset_password_controller import ResetPasswordController
from src.controllers.users.change_password_controller import ChangePasswordController

def make_create_user_controller() -> CreateUserController:
    """
    Factory para criar uma instância de CreateUserController
    com suas dependências injetadas.
    
    Returns:
        CreateUserController: Instância do controlador de criação de usuários
    """
    user_repository = UserRepository()
    create_user_service = CreateUserService(user_repository)
    create_user_controller = CreateUserController(create_user_service)
    
    return create_user_controller

def make_verify_email_controller() -> VerifyEmailController:
    """
    Factory para criar uma instância de VerifyEmailController
    com suas dependências injetadas.
    
    Returns:
        VerifyEmailController: Instância do controlador de verificação de email
    """
    user_repository = UserRepository()
    refresh_token_repository = AuthRefreshTokenRepository()
    verify_email_service = VerifyEmailService(user_repository, refresh_token_repository)
    verify_email_controller = VerifyEmailController(verify_email_service)
    
    return verify_email_controller

def make_resend_verification_email_controller() -> ResendVerificationEmailController:
    """
    Factory para criar uma instância de ResendVerificationEmailController
    com suas dependências injetadas.
    
    Returns:
        ResendVerificationEmailController: Instância do controlador de reenvio de email
    """
    user_repository = UserRepository()
    resend_verification_service = ResendVerificationEmailService(user_repository)
    resend_verification_controller = ResendVerificationEmailController(resend_verification_service)
    
    return resend_verification_controller

def make_generate_recovery_code_controller() -> GenerateRecoveryCodeController:
    """
    Factory para criar uma instância de GenerateRecoveryCodeController
    com suas dependências injetadas.
    
    Returns:
        GenerateRecoveryCodeController: Instância do controlador de geração de código
    """
    user_repository = UserRepository()
    generate_recovery_code_service = GenerateRecoveryCodeService(user_repository)
    generate_recovery_code_controller = GenerateRecoveryCodeController(generate_recovery_code_service)
    
    return generate_recovery_code_controller

def make_validate_recovery_code_controller() -> ValidateRecoveryCodeController:
    """
    Factory para criar uma instância de ValidateRecoveryCodeController
    com suas dependências injetadas.
    
    Returns:
        ValidateRecoveryCodeController: Instância do controlador de validação de código
    """
    user_repository = UserRepository()
    validate_recovery_code_service = ValidateRecoveryCodeService(user_repository)
    validate_recovery_code_controller = ValidateRecoveryCodeController(validate_recovery_code_service)
    
    return validate_recovery_code_controller

def make_reset_password_controller() -> ResetPasswordController:
    """
    Factory para criar uma instância de ResetPasswordController
    com suas dependências injetadas.
    
    Returns:
        ResetPasswordController: Instância do controlador de reset de senha
    """
    user_repository = UserRepository()
    reset_password_service = ResetPasswordService(user_repository)
    reset_password_controller = ResetPasswordController(reset_password_service)
    
    return reset_password_controller

def make_change_password_controller() -> ChangePasswordController:
    """
    Factory para criar uma instância de ChangePasswordController
    com suas dependências injetadas.
    
    Returns:
        ChangePasswordController: Instância do controlador de troca de senha autenticada
    """
    user_repository = UserRepository()
    change_password_service = ChangePasswordService(user_repository)
    return ChangePasswordController(change_password_service)
