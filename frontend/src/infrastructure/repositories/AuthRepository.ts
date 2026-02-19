import { IAuthRepository, RegisterData } from '@domain/repositories/IAuthRepository';
import { User } from '@domain/entities/User';
import { 
  LoginCredentials, 
  AuthToken, 
  LoginResponse, 
  VerifyEmailResponse, 
  ResendVerificationResponse,
  GenerateRecoveryCodeResponse,
  ValidateRecoveryCodeResponse,
  ResetPasswordResponse
} from '@domain/entities/Auth';
import { HttpClient } from '@infrastructure/http/HttpClient';
import { IStorageService } from '@domain/services/IStorageService';

export class AuthRepository implements IAuthRepository {
  private httpClient: HttpClient;
  private storageService: IStorageService;

  constructor(httpClient: HttpClient, storageService: IStorageService) {
    this.httpClient = httpClient;
    this.storageService = storageService;
  }

  async register(data: RegisterData): Promise<void> {
    await this.httpClient.getClient().post('/users/register', {
      email: data.email,
      first_name: data.first_name,
      last_name: data.last_name,
      password: data.password,
      user_type: data.user_type,
    });
    // Retorna apenas após 201 Created
  }

  async login(credentials: LoginCredentials): Promise<{ user: User; token: AuthToken }> {
    const response = await this.httpClient.getClient().post<LoginResponse>('/auth/login', {
      email: credentials.email,
      password: credentials.password,
    });

    const { access_token, token_type, expires_in, user_uuid, email, user_type } = response.data;

    // Armazena apenas o access_token (refresh_token vem em cookie httpOnly)
    this.storageService.setItem('access_token', access_token);

    // Busca os dados completos do usuário
    const userResponse = await this.httpClient.getClient().get<User>('/auth/me');
    const userData = userResponse.data;

    // Armazena dados do usuário
    this.storageService.setItem('user', JSON.stringify(userData));

    const user: User = userData;

    const token: AuthToken = {
      access_token,
      token_type,
      expires_in,
    };

    return { user, token };
  }

  async logout(): Promise<void> {
    try {
      // Chama o endpoint de logout (revoga o refresh_token no backend)
      await this.httpClient.getClient().post('/auth/logout');
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      // Remove dados locais
      this.storageService.removeItem('access_token');
      this.storageService.removeItem('user');
    }
  }

  async refreshToken(refreshToken: string): Promise<AuthToken> {
    // O refresh_token vem do cookie, então não precisamos enviar
    const response = await this.httpClient.getClient().post<{
      access_token: string;
      token_type: string;
      expires_in: number;
    }>('/auth/refresh');

    const { access_token, token_type, expires_in } = response.data;

    this.storageService.setItem('access_token', access_token);

    return {
      access_token,
      token_type,
      expires_in,
    };
  }

  async getCurrentUser(): Promise<User | null> {
    const userJson = this.storageService.getItem('user');
    if (userJson) {
      try {
        const userData = JSON.parse(userJson);
        // Se o cache já contém first_name, retorna diretamente
        if (userData?.first_name) {
          return userData;
        }
        // Cache antigo sem first_name — invalida para re-buscar do backend
        this.storageService.removeItem('user');
      } catch {
        this.storageService.removeItem('user');
      }
    }

    // Busca dados atualizados do backend
    try {
      const response = await this.httpClient.getClient().get<User>('/auth/me');
      const userData = response.data;
      this.storageService.setItem('user', JSON.stringify(userData));
      return userData;
    } catch {
      return null;
    }
  }

  async validateToken(token: string): Promise<boolean> {
    try {
      await this.httpClient.getClient().get('/auth/me');
      return true;
    } catch {
      return false;
    }
  }

  async verifyEmail(uuid: string): Promise<{ user: User; token: AuthToken; alreadyVerified: boolean }> {
    const response = await this.httpClient.getClient().put<VerifyEmailResponse>(`/users/verify-email/${uuid}`);

    const { access_token, token_type, expires_in, already_verified } = response.data;

    // Armazena apenas o access_token (refresh_token vem em cookie httpOnly)
    this.storageService.setItem('access_token', access_token);

    // Busca os dados completos do usuário
    const userResponse = await this.httpClient.getClient().get<User>('/auth/me');
    const userData = userResponse.data;

    // Armazena dados do usuário
    this.storageService.setItem('user', JSON.stringify(userData));

    const user: User = userData;

    const token: AuthToken = {
      access_token,
      token_type,
      expires_in,
    };

    return { user, token, alreadyVerified: already_verified };
  }

  async resendVerificationEmail(email: string): Promise<{ message: string; email: string; alreadyVerified: boolean }> {
    const response = await this.httpClient.getClient().post<ResendVerificationResponse>('/users/resend-verification', {
      email,
    });

    const { message, email: responseEmail, already_verified } = response.data;

    return { 
      message, 
      email: responseEmail, 
      alreadyVerified: already_verified 
    };
  }

  async generateRecoveryCode(email: string): Promise<{ message: string; email: string }> {
    const response = await this.httpClient.getClient().post<GenerateRecoveryCodeResponse>('/users/generate-recovery-code', {
      email,
    });

    const { message, email: responseEmail } = response.data;

    return { message, email: responseEmail };
  }

  async validateRecoveryCode(email: string, code: string): Promise<{ message: string; email: string }> {
    const response = await this.httpClient.getClient().post<ValidateRecoveryCodeResponse>('/users/validate-recovery-code', {
      email,
      code,
    });

    const { message, email: responseEmail } = response.data;

    return { message, email: responseEmail };
  }

  async resetPassword(email: string, code: string, newPassword: string): Promise<{ message: string; email: string }> {
    const response = await this.httpClient.getClient().post<ResetPasswordResponse>('/users/password/reset', {
      email,
      code,
      new_password: newPassword,
    });

    const { message, email: responseEmail } = response.data;

    return { message, email: responseEmail };
  }
}
