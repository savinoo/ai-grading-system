import { IAuthRepository } from '@domain/repositories/IAuthRepository';

export class ResendVerificationEmailUseCase {
  constructor(private authRepository: IAuthRepository) {}

  async execute(email: string): Promise<{ message: string; email: string; alreadyVerified: boolean }> {
    if (!email || email.trim() === '') {
      throw new Error('Email é obrigatório');
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      throw new Error('Email inválido');
    }

    const result = await this.authRepository.resendVerificationEmail(email);
    return result;
  }
}
