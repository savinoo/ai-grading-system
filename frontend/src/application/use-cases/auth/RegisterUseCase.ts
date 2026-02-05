import { IAuthRepository } from '@domain/repositories/IAuthRepository';

export interface RegisterData {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  user_type: 'admin' | 'teacher' | 'student';
}

// Use Case following Single Responsibility Principle (SOLID)
export class RegisterUseCase {
  constructor(private authRepository: IAuthRepository) {}

  async execute(data: RegisterData): Promise<void> {
    // Validação de entrada
    this.validateRegisterData(data);

    // Executa o registro através do repositório
    await this.authRepository.register(data);
  }

  private validateRegisterData(data: RegisterData): void {
    if (!data.email || !data.email.trim()) {
      throw new Error('Email é obrigatório');
    }

    if (!this.isValidEmail(data.email)) {
      throw new Error('Email inválido');
    }

    if (!data.first_name || !data.first_name.trim()) {
      throw new Error('Nome é obrigatório');
    }

    if (!data.last_name || !data.last_name.trim()) {
      throw new Error('Sobrenome é obrigatório');
    }

    if (!data.password || data.password.length < 8) {
      throw new Error('Senha deve ter no mínimo 8 caracteres');
    }

    if (!this.isValidPassword(data.password)) {
      throw new Error('Senha deve conter pelo menos uma letra maiúscula, uma letra minúscula e um número');
    }

    if (!data.user_type) {
      throw new Error('Tipo de usuário é obrigatório');
    }

    const validUserTypes = ['admin', 'teacher', 'student'];
    if (!validUserTypes.includes(data.user_type)) {
      throw new Error('Tipo de usuário inválido');
    }
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  private isValidPassword(password: string): boolean {
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    
    return hasUpperCase && hasLowerCase && hasNumber;
  }
}
