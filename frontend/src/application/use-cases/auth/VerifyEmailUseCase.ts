import { IAuthRepository } from '@domain/repositories/IAuthRepository';
import { User } from '@domain/entities/User';
import { AuthToken } from '@domain/entities/Auth';

export class VerifyEmailUseCase {
  constructor(private authRepository: IAuthRepository) {}

  async execute(uuid: string): Promise<{ user: User; token: AuthToken; alreadyVerified: boolean }> {
    if (!uuid || uuid.trim() === '') {
      throw new Error('UUID é obrigatório');
    }

    // UUID validation (basic format check)
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(uuid)) {
      throw new Error('UUID inválido');
    }

    const result = await this.authRepository.verifyEmail(uuid);
    return result;
  }
}
