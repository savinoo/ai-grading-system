// Domain Value Object - Authentication Credentials
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_uuid: string;
  email: string;
  user_type: string;
}

export interface VerifyEmailResponse {
  message: string;
  already_verified: boolean;
  access_token: string;
  token_type: string;
  expires_in: number;
  user_uuid: string;
  email: string;
  user_type: string;
}

export interface ResendVerificationResponse {
  message: string;
  email: string;
  already_verified: boolean;
}

export interface GenerateRecoveryCodeResponse {
  message: string;
  email: string;
}

export interface ValidateRecoveryCodeResponse {
  message: string;
  email: string;
}

export interface ResetPasswordResponse {
  message: string;
  email: string;
}

export interface AuthSession {
  user: {
    uuid: string;
    email: string;
    user_type: string;
  };
  token: AuthToken;
  isAuthenticated: boolean;
}
