from __future__ import annotations

from src.models.repositories.auth_refresh_token_repository import AuthRefreshTokenRepository
from src.models.repositories.user_repository import UserRepository

from src.services.auth.revoke_by_jti import RevokeByJtiService
from src.services.auth.refresh_token_service import RefreshTokenService
from src.services.auth.user_login import UserLoginService
from src.services.auth.get_me import GetMeService

from src.controllers.auth.revoke_by_jti_controller import RevokeByJtiController
from src.controllers.auth.refresh_token_controller import RefreshTokenController
from src.controllers.auth.user_login_controller import UserLoginController
from src.controllers.auth.get_me_controller import GetMeController

def make_revoke_by_jti_controller() -> RevokeByJtiController:
    repo = AuthRefreshTokenRepository()
    service = RevokeByJtiService(repo)
    controller = RevokeByJtiController(service)
    return controller

def make_refresh_token_controller() -> RefreshTokenController:
    repo = AuthRefreshTokenRepository()
    service = RefreshTokenService(repo)
    controller = RefreshTokenController(service)
    return controller

def make_user_login_controller() -> UserLoginController:
    token_repo = AuthRefreshTokenRepository()
    user_repo = UserRepository()
    service = UserLoginService(user_repository=user_repo, refresh_token_repository=token_repo)
    controller = UserLoginController(service)
    return controller

def make_get_me_controller() -> GetMeController:
    user_repo = UserRepository()
    service = GetMeService(repo=user_repo)
    controller = GetMeController(service)
    return controller
