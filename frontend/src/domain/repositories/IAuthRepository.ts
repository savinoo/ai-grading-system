import { User } from '../entities/User';
import { LoginCredentials, AuthToken } from '../entities/Auth';

export interface RegisterData {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  user_type: 'admin' | 'teacher' | 'student';
}

// Repository Interface following Dependency Inversion Principle (SOLID)
export interface IAuthRepository {
  login(credentials: LoginCredentials): Promise<{ user: User; token: AuthToken }>;
  logout(): Promise<void>;
  refreshToken(refreshToken: string): Promise<AuthToken>;
  getCurrentUser(): Promise<User | null>;
  validateToken(token: string): Promise<boolean>;
  register(data: RegisterData): Promise<void>;
  verifyEmail(uuid: string): Promise<{ user: User; token: AuthToken; alreadyVerified: boolean }>;
  resendVerificationEmail(email: string): Promise<{ message: string; email: string; alreadyVerified: boolean }>;
  generateRecoveryCode(email: string): Promise<{ message: string; email: string }>;
  validateRecoveryCode(email: string, code: string): Promise<{ message: string; email: string }>;
  resetPassword(email: string, code: string, newPassword: string): Promise<{ message: string; email: string }>;
}
