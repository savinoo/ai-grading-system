import { IAuthRepository } from '@domain/repositories/IAuthRepository';
import { LoginCredentials } from '@domain/entities/Auth';
import { User } from '@domain/entities/User';

// Use Case following Single Responsibility Principle (SOLID)
export class LoginUseCase {
  constructor(private authRepository: IAuthRepository) {}

  async execute(credentials: LoginCredentials): Promise<{ user: User; accessToken: string }> {
    // Validação de entrada
    this.validateCredentials(credentials);

    // Executa o login através do repositório
    const { user, token } = await this.authRepository.login(credentials);

    return {
      user,
      accessToken: token.access_token,
    };
  }

  private validateCredentials(credentials: LoginCredentials): void {
    if (!credentials.email || !credentials.email.trim()) {
      throw new Error('Email é obrigatório');
    }

    if (!this.isValidEmail(credentials.email)) {
      throw new Error('Email inválido');
    }

    if (!credentials.password || credentials.password.length < 6) {
      throw new Error('Senha deve ter no mínimo 6 caracteres');
    }
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}
