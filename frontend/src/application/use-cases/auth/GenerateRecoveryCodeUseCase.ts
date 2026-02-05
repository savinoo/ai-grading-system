import { IAuthRepository } from '@domain/repositories/IAuthRepository';

export class GenerateRecoveryCodeUseCase {
  constructor(private authRepository: IAuthRepository) {}

  async execute(email: string): Promise<{ message: string; email: string }> {
    if (!email || email.trim() === '') {
      throw new Error('Email é obrigatório');
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      throw new Error('Email inválido');
    }

    const result = await this.authRepository.generateRecoveryCode(email);
    return result;
  }
}
