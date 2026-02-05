import { IAuthRepository } from '@domain/repositories/IAuthRepository';
import { User } from '@domain/entities/User';

// Use Case following Single Responsibility Principle (SOLID)
export class GetCurrentUserUseCase {
  constructor(private authRepository: IAuthRepository) {}

  async execute(): Promise<User | null> {
    return await this.authRepository.getCurrentUser();
  }
}
