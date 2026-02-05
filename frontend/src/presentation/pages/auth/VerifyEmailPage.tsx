import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { AuthLayout } from "@presentation/components/layout/AuthLayout";
import { Button } from "@presentation/components/ui/Button";
import { useAuth } from "@presentation/hooks/useAuth";

export const VerifyEmailPage: React.FC = () => {
  const { uuid } = useParams<{ uuid: string }>();
  const navigate = useNavigate();
  const { verifyEmail } = useAuth();

  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'404' | '500' | 'other' | null>(null);
  const [success, setSuccess] = useState(false);
  const [alreadyVerified, setAlreadyVerified] = useState(false);

  // Validar UUID na montagem
  useEffect(() => {
    if (!uuid) {
      setError("Link de verificação inválido");
    }
  }, [uuid]);

  const handleVerifyEmail = async () => {
    if (!uuid) {
      setError("Link de verificação inválido");
      return;
    }

    setIsVerifying(true);
    setError(null);

    try {
      const result = await verifyEmail(uuid);

      if (result.alreadyVerified) {
        setAlreadyVerified(true);
        setSuccess(true);
        // Redireciona após 2 segundos
        setTimeout(() => {
          navigate("/dashboard");
        }, 2000);
      } else {
        setSuccess(true);
        // Redireciona após 1.5 segundos
        setTimeout(() => {
          navigate("/dashboard");
        }, 1500);
      }
    } catch (err: any) {
      console.error("Verify email error:", err);
      
      // Tratamento específico de erros por código HTTP
      const status = err.response?.status;
      let errorMessage = "Erro ao verificar email. Tente novamente.";
      let errType: '404' | '500' | 'other' = 'other';

      if (status === 404) {
        errorMessage = "Link de verificação inválido ou expirado. Solicite um novo email de verificação.";
        errType = '404';
      } else if (status === 400) {
        errorMessage = err.response?.data?.detail || "Dados de verificação inválidos.";
      } else if (status === 500) {
        errorMessage = "Erro no servidor. Por favor, tente novamente mais tarde.";
        errType = '500';
      } else if (err.message) {
        errorMessage = err.message;
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }

      setError(errorMessage);
      setErrorType(errType);
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <AuthLayout>
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl shadow-slate-200/50 dark:shadow-none p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
              <span className="material-symbols-outlined text-4xl text-primary">
                {success ? "check_circle" : "mark_email_read"}
              </span>
            </div>
            <h1 className="text-slate-900 dark:text-white text-2xl font-extrabold leading-tight mb-2">
              {success ? "Email Verificado!" : "Verificar Email"}
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm">
              {success
                ? alreadyVerified
                  ? "Seu email já estava verificado. Redirecionando..."
                  : "Seu email foi verificado com sucesso! Redirecionando..."
                : "Clique no botão abaixo para verificar seu email e ativar sua conta"}
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="flex items-start gap-3">
                <span className="material-symbols-outlined text-red-600 dark:text-red-400 text-xl flex-shrink-0">
                  error
                </span>
                <div className="flex-1">
                  <p className="text-sm text-red-600 dark:text-red-400 font-medium">
                    {error}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-start gap-3">
                <span className="material-symbols-outlined text-green-600 dark:text-green-400 text-xl flex-shrink-0">
                  check_circle
                </span>
                <div className="flex-1">
                  <p className="text-sm text-green-600 dark:text-green-400 font-medium">
                    {alreadyVerified
                      ? "Email já verificado anteriormente"
                      : "Email verificado com sucesso!"}
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    Você será redirecionado para o dashboard...
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Verify Button */}
          {!success && (
            <div className="space-y-4 flex flex-col items-center">
              <Button
                type="button"
                variant="primary"
                size="lg"
                loading={isVerifying}
                onClick={handleVerifyEmail}
                disabled={!uuid || isVerifying}
              >
                {isVerifying ? "Verificando..." : "Verificar Meu Email"}
              </Button>

              <div className="text-center space-y-2">
                {/* Botão para solicitar novo link se for erro 404 */}
                {errorType === '404' && (
                  <button
                    type="button"
                    onClick={() => navigate('/email-verification')}
                    className="block w-full text-sm text-primary hover:text-primary/80 font-medium transition-colors"
                  >
                    Solicitar novo link de verificação
                  </button>
                )}
                
                <button
                  type="button"
                  onClick={() => navigate("/login")}
                  className="text-sm text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
                  disabled={isVerifying}
                >
                  Voltar para o login
                </button>
              </div>
            </div>
          )}

          {/* Loading State */}
          {success && (
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          )}
        </div>

        {/* Info Box */}
        {!success && !error && (
          <div className="mt-6 p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg">
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-slate-400 text-xl flex-shrink-0">
                info
              </span>
              <div className="flex-1">
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Após a verificação, você será automaticamente conectado e
                  redirecionado para o dashboard.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </AuthLayout>
  );
};
