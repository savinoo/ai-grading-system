import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthLayout } from '@presentation/components/layout/AuthLayout';
import { Button } from '@presentation/components/ui/Button';
import { useAuth } from '@presentation/hooks/useAuth';

export const VerifyRecoveryCodePage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { validateRecoveryCode, generateRecoveryCode } = useAuth();
  
  const email = location.state?.email as string | undefined;
  
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [countdown, setCountdown] = useState(90); // 1min30s

  // Redirect if no email
  useEffect(() => {
    if (!email) {
      navigate('/forgot-password');
    }
  }, [email, navigate]);

  // Timer countdown
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleCodeChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return; // Only digits
    
    const newCode = [...code];
    newCode[index] = value.slice(-1); // Only last digit
    setCode(newCode);
    
    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`code-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      const prevInput = document.getElementById(`code-${index - 1}`);
      prevInput?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newCode = [...code];
    
    for (let i = 0; i < 6; i++) {
      newCode[i] = pastedData[i] || '';
    }
    
    setCode(newCode);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const fullCode = code.join('');
    
    if (fullCode.length !== 6) {
      setError('Digite o código completo de 6 dígitos');
      return;
    }

    if (!email) {
      setError('Email não disponível. Por favor, tente novamente.');
      return;
    }

    setIsValidating(true);
    setError(null);

    try {
      await validateRecoveryCode(email, fullCode);
      navigate('/forgot-password/reset', { state: { email, code: fullCode } });
    } catch (err: any) {
      console.error('Validate code error:', err);
      
      // Tratamento específico de erros por código HTTP
      const status = err.response?.status;
      let errorMessage = 'Código inválido ou expirado';

      if (status === 404) {
        errorMessage = 'Código não encontrado ou expirado. Solicite um novo código.';
      } else if (status === 400) {
        errorMessage = err.response?.data?.error?.replace('unauthorized: ', '') || 'Código inválido';
      } else if (status === 500) {
        errorMessage = 'Erro no servidor. Tente novamente mais tarde.';
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error.replace('unauthorized: ', '');
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      setCode(['', '', '', '', '', '']);
      document.getElementById('code-0')?.focus();
    } finally {
      setIsValidating(false);
    }
  };

  const handleResendCode = async () => {
    if (countdown > 0 || !email) return;

    setIsResending(true);
    setError(null);

    try {
      await generateRecoveryCode(email);
      setCountdown(90);
      setCode(['', '', '', '', '', '']);
      document.getElementById('code-0')?.focus();
    } catch (err: any) {
      console.error('Resend code error:', err);
      setError(err.response?.data?.detail || err.message || 'Erro ao reenviar código');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <AuthLayout>
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl shadow-slate-200/50 dark:shadow-none p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
              <span className="material-symbols-outlined text-4xl text-primary">password</span>
            </div>
            <h1 className="text-slate-900 dark:text-white text-2xl font-extrabold leading-tight mb-2">
              Digite o código
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm">
              Enviamos um código de 6 dígitos para{' '}
              <span className="font-bold text-slate-900 dark:text-white">{email}</span>
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
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Code Inputs */}
            <div className="flex gap-2 justify-center" onPaste={handlePaste}>
              {code.map((digit, index) => (
                <input
                  key={index}
                  id={`code-${index}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleCodeChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  disabled={isValidating}
                  className="w-12 h-14 text-center text-2xl font-bold border-2 border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all disabled:opacity-50"
                />
              ))}
            </div>

            <div className="flex flex-col items-center space-y-5">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={isValidating}
                disabled={code.join('').length !== 6}
              >
                Verificar Código
              </Button>

              <div className="text-center space-y-2">
                <button
                  type="button"
                  onClick={handleResendCode}
                  disabled={countdown > 0 || isResending}
                  className="text-sm text-primary dark:text-primary-light font-bold hover:underline transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:no-underline"
                >
                  {isResending 
                    ? 'Reenviando...' 
                    : countdown > 0 
                      ? `Reenviar código em ${countdown}s`
                      : 'Reenviar código'
                  }
                </button>
                
                <div>
                  <button
                    type="button"
                    onClick={() => navigate('/forgot-password')}
                    className="text-sm text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
                    disabled={isValidating}
                  >
                    Voltar
                  </button>
                </div>
              </div>
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
              O código é válido por tempo limitado. Caso não tenha recebido, verifique sua pasta de spam.
            </p>
          </div>
        </div>
      </div>
    </AuthLayout>
  );
};
