import { useCallback } from 'react';
import { useAuthStore } from '@presentation/store/authStore';
import { LoginUseCase } from '@application/use-cases/auth/LoginUseCase';
import { LogoutUseCase } from '@application/use-cases/auth/LogoutUseCase';
import { GetCurrentUserUseCase } from '@application/use-cases/auth/GetCurrentUserUseCase';
import { RegisterUseCase } from '@application/use-cases/auth/RegisterUseCase';
import { VerifyEmailUseCase } from '@application/use-cases/auth/VerifyEmailUseCase';
import { ResendVerificationEmailUseCase } from '@application/use-cases/auth/ResendVerificationEmailUseCase';
import { GenerateRecoveryCodeUseCase } from '@application/use-cases/auth/GenerateRecoveryCodeUseCase';
import { ValidateRecoveryCodeUseCase } from '@application/use-cases/auth/ValidateRecoveryCodeUseCase';
import { ResetPasswordUseCase } from '@application/use-cases/auth/ResetPasswordUseCase';
import { AuthRepository } from '@infrastructure/repositories/AuthRepository';
import { HttpClient } from '@infrastructure/http/HttpClient';
import { LocalStorageService } from '@infrastructure/services/LocalStorageService';
import { RegisterData } from '@domain/repositories/IAuthRepository';

// Dependency Injection (seguindo princípios SOLID)
const storageService = new LocalStorageService();
const httpClient = new HttpClient(storageService);
const authRepository = new AuthRepository(httpClient, storageService);

const loginUseCase = new LoginUseCase(authRepository);
const logoutUseCase = new LogoutUseCase(authRepository);
const getCurrentUserUseCase = new GetCurrentUserUseCase(authRepository);
const registerUseCase = new RegisterUseCase(authRepository);
const verifyEmailUseCase = new VerifyEmailUseCase(authRepository);
const resendVerificationEmailUseCase = new ResendVerificationEmailUseCase(authRepository);
const generateRecoveryCodeUseCase = new GenerateRecoveryCodeUseCase(authRepository);
const validateRecoveryCodeUseCase = new ValidateRecoveryCodeUseCase(authRepository);
const resetPasswordUseCase = new ResetPasswordUseCase(authRepository);

export const useAuth = () => {
  const { user, isAuthenticated, isLoading, error, setUser, setLoading, setError, clearAuth } = useAuthStore();

  const login = useCallback(async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const { user } = await loginUseCase.execute({ email, password });
      setUser(user);
      return user;
    } catch (err: any) {
      // Tratamento específico de erros por código HTTP
      const status = err.response?.status;
      let errorMessage = 'Erro ao fazer login';

      if (status === 401) {
        errorMessage = 'Email ou senha incorretos. Verifique suas credenciais e tente novamente.';
      } else if (status === 403) {
        errorMessage = 'Acesso negado. Verifique se seu email foi verificado.';
      } else if (status === 429) {
        errorMessage = 'Muitas tentativas de login. Aguarde alguns minutos e tente novamente.';
      } else if (status === 500) {
        errorMessage = 'Erro no servidor. Tente novamente mais tarde.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err instanceof Error && err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setUser, setLoading, setError]);

  const logout = useCallback(async () => {
    try {
      setLoading(true);
      await logoutUseCase.execute();
      clearAuth();
    } catch (err) {
      console.error('Logout error:', err);
      // Mesmo com erro, limpa a autenticação
      clearAuth();
    } finally {
      setLoading(false);
    }
  }, [clearAuth, setLoading]);

  const loadCurrentUser = useCallback(async () => {
    try {
      setLoading(true);
      const currentUser = await getCurrentUserUseCase.execute();
      setUser(currentUser);
    } catch (err) {
      console.error('Load user error:', err);
      clearAuth();
    } finally {
      setLoading(false);
    }
  }, [setUser, clearAuth, setLoading]);

  const register = useCallback(async (data: RegisterData) => {
    try {
      setLoading(true);
      setError(null);
      
      await registerUseCase.execute(data);
    } catch (err: any) {
      const status = err.response?.status;
      let errorMessage = 'Erro ao criar conta';

      if (status === 409 || status === 400) {
        // Backend retorna { error: '...', code: 'conflict', context: {...} }
        const responseData = err.response?.data;
        if (typeof responseData === 'string') {
          errorMessage = responseData;
        } else if (typeof responseData === 'object') {
          // Se error for string, usa ela; se for objeto, tenta pegar a mensagem
          if (typeof responseData.error === 'string') {
            errorMessage = responseData.error;
          } else if (typeof responseData.detail === 'string') {
            errorMessage = responseData.detail;
          } else if (typeof responseData.message === 'string') {
            errorMessage = responseData.message;
          } else {
            errorMessage = 'Este email já está cadastrado.';
          }
        }
      } else if (status === 422) {
        errorMessage = 'Dados inválidos. Verifique as informações e tente novamente.';
      } else if (status === 500) {
        errorMessage = 'Erro no servidor. Tente novamente mais tarde.';
      } else if (err.response?.data) {
        const data = err.response.data;
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (typeof data.error === 'string') {
          errorMessage = data.error;
        } else if (typeof data.detail === 'string') {
          errorMessage = data.detail;
        } else if (typeof data.message === 'string') {
          errorMessage = data.message;
        }
      } else if (err instanceof Error && err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      // Rejeita a promise sem fazer throw, permitindo melhor controle no componente
      return Promise.reject(err);
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  const verifyEmail = useCallback(async (uuid: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await verifyEmailUseCase.execute(uuid);
      setUser(result.user);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao verificar email';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setUser, setLoading, setError]);

  const resendVerificationEmail = useCallback(async (email: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await resendVerificationEmailUseCase.execute(email);
      return result;
    } catch (err: any) {
      const status = err.response?.status;
      let errorMessage = 'Erro ao reenviar email';

      if (status === 404) {
        errorMessage = 'Email não encontrado. Verifique e tente novamente.';
      } else if (status === 400) {
        errorMessage = err.response?.data?.detail || 'Email já verificado ou inválido.';
      } else if (status === 429) {
        errorMessage = 'Muitas tentativas. Aguarde alguns minutos antes de solicitar novo email.';
      } else if (status === 500) {
        errorMessage = 'Erro no servidor. Tente novamente mais tarde.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err instanceof Error && err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  const generateRecoveryCode = useCallback(async (email: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await generateRecoveryCodeUseCase.execute(email);
      return result;
    } catch (err: any) {
      const status = err.response?.status;
      let errorMessage = 'Erro ao gerar código de recuperação';

      if (status === 404) {
        errorMessage = 'Email não encontrado. Verifique e tente novamente.';
      } else if (status === 429) {
        errorMessage = 'Muitas tentativas. Aguarde alguns minutos antes de solicitar novo código.';
      } else if (status === 500) {
        errorMessage = 'Erro no servidor. Tente novamente mais tarde.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err instanceof Error && err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  const validateRecoveryCode = useCallback(async (email: string, code: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await validateRecoveryCodeUseCase.execute(email, code);
      return result;
    } catch (err: any) {
      const status = err.response?.status;
      let errorMessage = 'Erro ao validar código';

      if (status === 401 || status === 400) {
        errorMessage = 'Código inválido ou expirado. Tente novamente ou solicite um novo código.';
      } else if (status === 404) {
        errorMessage = 'Código não encontrado. Solicite um novo código de recuperação.';
      } else if (status === 500) {
        errorMessage = 'Erro no servidor. Tente novamente mais tarde.';
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error.replace('unauthorized: ', '');
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err instanceof Error && err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  const changePassword = useCallback(async (currentPassword: string, newPassword: string) => {
    try {
      setLoading(true);
      setError(null);

      await httpClient.getClient().patch('/users/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
    } catch (err: any) {
      const status = err.response?.status;
      let errorMessage = 'Erro ao alterar senha';

      if (status === 401) {
        errorMessage = err.response?.data?.error || 'Senha atual incorreta.';
      } else if (status === 400) {
        errorMessage = err.response?.data?.error || 'Dados inválidos.';
      } else if (status === 500) {
        errorMessage = 'Erro no servidor. Tente novamente mais tarde.';
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error;
      } else if (err instanceof Error && err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  const resetPassword = useCallback(async (email: string, code: string, newPassword: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await resetPasswordUseCase.execute(email, code, newPassword);
      return result;
    } catch (err: any) {
      const status = err.response?.status;
      let errorMessage = 'Erro ao redefinir senha';

      if (status === 404) {
        errorMessage = 'Código de recuperação não encontrado ou expirado.';
      } else if (status === 400) {
        errorMessage = err.response?.data?.detail || 'Dados inválidos. Verifique sua senha.';
      } else if (status === 500) {
        errorMessage = 'Erro no servidor. Tente novamente mais tarde.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err instanceof Error && err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    loadCurrentUser,
    register,
    verifyEmail,
    resendVerificationEmail,
    generateRecoveryCode,
    validateRecoveryCode,
    resetPassword,
    changePassword,
  };
};
