import { IAuthRepository } from '@domain/repositories/IAuthRepository';

export class ValidateRecoveryCodeUseCase {
  constructor(private authRepository: IAuthRepository) {}

  async execute(email: string, code: string): Promise<{ message: string; email: string }> {
    if (!email || email.trim() === '') {
      throw new Error('Email é obrigatório');
    }

    if (!code || code.trim() === '') {
      throw new Error('Código é obrigatório');
    }

    // Code validation (6 digits)
    if (!/^\d{6}$/.test(code)) {
      throw new Error('Código deve ter 6 dígitos');
    }

    const result = await this.authRepository.validateRecoveryCode(email, code);
    return result;
  }
}
