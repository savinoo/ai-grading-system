import { IAuthRepository } from '@domain/repositories/IAuthRepository';

// Use Case following Single Responsibility Principle (SOLID)
export class LogoutUseCase {
  constructor(private authRepository: IAuthRepository) {}

  async execute(): Promise<void> {
    await this.authRepository.logout();
  }
}
