import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthLayout } from '@presentation/components/layout/AuthLayout';
import { useAuth } from '@presentation/hooks/useAuth';

export const EmailVerificationPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { resendVerificationEmail } = useAuth();
  
  const email = location.state?.email as string | undefined;
  
  // Redireciona para signup se não tiver email
  useEffect(() => {
    if (!email) {
      navigate('/signup', { replace: true });
    }
  }, [email, navigate]);
  
  const [isResending, setIsResending] = useState(false);
  const [resendError, setResendError] = useState<string | null>(null);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [countdown, setCountdown] = useState(0);

  // Timer countdown
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleResendEmail = async () => {
    if (!email) {
      setResendError('Email não disponível. Por favor, faça o cadastro novamente.');
      return;
    }

    if (countdown > 0) {
      return;
    }

    setIsResending(true);
    setResendError(null);
    setResendSuccess(false);

    try {
      const result = await resendVerificationEmail(email);
      
      if (result.alreadyVerified) {
        // Email já verificado, redireciona para login
        navigate('/login', { 
          state: { 
            message: 'Email já foi verificado. Faça login para continuar.' 
          } 
        });
      } else {
        // Email enviado com sucesso
        setResendSuccess(true);
        setCountdown(60); // Inicia o countdown de 60 segundos
        
        // Remove a mensagem de sucesso após 5 segundos
        setTimeout(() => {
          setResendSuccess(false);
        }, 5000);
      }
    } catch (err: any) {
      console.error('Resend email error:', err);
      setResendError(err.response?.data?.detail || err.message || 'Erro ao reenviar email. Tente novamente.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <AuthLayout>
      <div className="w-full max-w-[520px]">
        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl shadow-slate-200/50 dark:shadow-none p-8 md:p-10">
          {/* Success Icon */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
              <span className="material-symbols-outlined text-5xl text-primary">mark_email_unread</span>
            </div>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-slate-900 dark:text-white tracking-tight text-3xl font-extrabold leading-tight pb-3">
              Verifique seu email
            </h1>
            <p className="text-slate-600 dark:text-slate-400 text-base font-medium leading-relaxed">
              Enviamos um link de verificação para{' '}
              {email ? (
                <span className="font-bold text-slate-900 dark:text-white">{email}</span>
              ) : (
                'o seu email'
              )}
              . Por favor, verifique sua caixa de entrada e clique no link para ativar sua conta.
            </p>
          </div>

          {/* Error Message */}
          {resendError && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="flex items-start gap-3">
                <span className="material-symbols-outlined text-red-600 dark:text-red-400 text-xl flex-shrink-0">
                  error
                </span>
                <div className="flex-1">
                  <p className="text-sm text-red-600 dark:text-red-400 font-medium">
                    {resendError}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Success Message */}
          {resendSuccess && (
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-start gap-3">
                <span className="material-symbols-outlined text-green-600 dark:text-green-400 text-xl flex-shrink-0">
                  check_circle
                </span>
                <div className="flex-1">
                  <p className="text-sm text-green-600 dark:text-green-400 font-medium">
                    Email de verificação enviado com sucesso!
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    Verifique sua caixa de entrada
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-6 mb-6 space-y-3">
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-primary mt-0.5">check_circle</span>
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-white">
                  Verifique sua caixa de entrada
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                  O email pode levar alguns minutos para chegar
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-primary mt-0.5">folder_special</span>
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-white">
                  Confira a pasta de spam
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                  Às vezes o email pode ir para a pasta de spam ou lixo eletrônico
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-primary mt-0.5">link</span>
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-white">
                  Clique no link de ativação
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                  O link é válido por 24 horas
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-3">
            <button
              onClick={() => navigate('/login')}
              className="w-full flex items-center justify-center gap-2 rounded-lg h-12 bg-primary text-white text-base font-bold leading-normal hover:bg-opacity-90 active:scale-[0.98] transition-all shadow-lg shadow-primary/20"
            >
              <span className="material-symbols-outlined text-lg">login</span>
              Ir para o Login
            </button>
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-6 text-center">
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Não recebeu o email?{' '}
            <button 
              onClick={handleResendEmail}
              disabled={countdown > 0 || isResending || !email}
              className="text-primary font-bold hover:underline transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:no-underline"
            >
              {isResending 
                ? 'Enviando...' 
                : countdown > 0 
                  ? `Reenviar em ${countdown}s`
                  : 'Reenviar email de verificação'
              }
            </button>
          </p>
        </div>
      </div>
    </AuthLayout>
  );
};
