import { IAuthRepository } from '@domain/repositories/IAuthRepository';

export class ResetPasswordUseCase {
  constructor(private authRepository: IAuthRepository) {}

  async execute(email: string, code: string, newPassword: string): Promise<{ message: string; email: string }> {
    if (!email || email.trim() === '') {
      throw new Error('Email é obrigatório');
    }

    if (!code || code.trim() === '') {
      throw new Error('Código é obrigatório');
    }

    if (!newPassword || newPassword.trim() === '') {
      throw new Error('Nova senha é obrigatória');
    }

    // Password validation
    if (newPassword.length < 8) {
      throw new Error('Senha deve ter no mínimo 8 caracteres');
    }

    const result = await this.authRepository.resetPassword(email, code, newPassword);
    return result;
  }
}
