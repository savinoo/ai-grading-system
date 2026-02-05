import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthLayout } from '@presentation/components/layout/AuthLayout';
import { Button } from '@presentation/components/ui/Button';
import { Input } from '@presentation/components/ui/Input';
import { useAuth } from '@presentation/hooks/useAuth';

export const ForgotPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const { generateRecoveryCode } = useAuth();
  
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setError('Email é obrigatório');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Email inválido');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await generateRecoveryCode(email);
      navigate('/forgot-password/verify-code', { state: { email } });
    } catch (err: any) {
      console.error('Generate recovery code error:', err);
      setError(err.response?.data?.detail || err.message || 'Erro ao enviar código. Tente novamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout>
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl shadow-slate-200/50 dark:shadow-none p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
              <span className="material-symbols-outlined text-4xl text-primary">lock_reset</span>
            </div>
            <h1 className="text-slate-900 dark:text-white text-2xl font-extrabold leading-tight mb-2">
              Esqueceu a senha?
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm">
              Insira seu email para receber um código de recuperação
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="flex items-start gap-3">
                <span className="material-symbols-outlined text-red-600 dark:text-red-400 text-xl flex-shrink-0">
                  error
                </span>
                <p className="text-sm text-red-600 dark:text-red-400 font-medium">{error}</p>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              id="email"
              type="email"
              label="Email"
              placeholder="seu@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSubmitting}
            />

            <div className="flex flex-col items-center space-y-5">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={isSubmitting}
              >
                Enviar Código
              </Button>

              <button
                type="button"
                onClick={() => navigate('/login')}
                className="text-sm text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
                disabled={isSubmitting}
              >
                Voltar para o login
              </button>
            </div>
          </form>
        </div>

        {/* Info */}
        <div className="mt-6 p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg">
          <div className="flex items-start gap-3">
            <span className="material-symbols-outlined text-slate-400 text-xl flex-shrink-0">
              info
            </span>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Enviaremos um código de 6 dígitos para seu email. Use esse código para redefinir sua senha.
            </p>
          </div>
        </div>
      </div>
    </AuthLayout>
  );
};
