import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthLayout } from '@presentation/components/layout/AuthLayout';
import { Button } from '@presentation/components/ui/Button';
import { Input } from '@presentation/components/ui/Input';
import { useAuth } from '@presentation/hooks/useAuth';

export const ResetPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { resetPassword } = useAuth();
  
  const email = location.state?.email as string | undefined;
  const code = location.state?.code as string | undefined;
  
  const [formData, setFormData] = useState({
    newPassword: '',
    confirmPassword: '',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Redirect if no email or code
  useEffect(() => {
    if (!email || !code) {
      navigate('/forgot-password');
    }
  }, [email, code, navigate]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error for this field
    if (formErrors[name]) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    const errors: Record<string, string> = {};
    
    if (!formData.newPassword) {
      errors.newPassword = 'Nova senha é obrigatória';
    } else if (formData.newPassword.length < 8) {
      errors.newPassword = 'Senha deve ter no mínimo 8 caracteres';
    }
    
    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Confirme sua senha';
    } else if (formData.newPassword !== formData.confirmPassword) {
      errors.confirmPassword = 'As senhas não coincidem';
    }
    
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    if (!email || !code) {
      setError('Informações de recuperação não disponíveis. Tente novamente.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await resetPassword(email, code, formData.newPassword);
      navigate('/login', { 
        state: { 
          message: 'Senha redefinida com sucesso! Faça login com sua nova senha.' 
        } 
      });
    } catch (err: any) {
      console.error('Reset password error:', err);
      
      // Tratamento específico de erros por código HTTP
      const status = err.response?.status;
      let errorMessage = 'Erro ao redefinir senha. Tente novamente.';

      if (status === 404) {
        errorMessage = 'Código de recuperação não encontrado ou expirado. Solicite um novo código.';
        setTimeout(() => navigate('/forgot-password'), 3000);
      } else if (status === 400) {
        errorMessage = err.response?.data?.detail || 'Dados inválidos. Verifique sua senha.';
      } else if (status === 500) {
        errorMessage = 'Erro no servidor. Tente novamente mais tarde.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
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
              Nova senha
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm">
              Digite sua nova senha
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
              id="newPassword"
              name="newPassword"
              type="password"
              label="Nova senha"
              placeholder="Digite sua nova senha"
              value={formData.newPassword}
              onChange={handleChange}
              error={formErrors.newPassword}
              disabled={isSubmitting}
              showPasswordToggle
            />

            <Input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              label="Confirmar senha"
              placeholder="Digite novamente sua senha"
              value={formData.confirmPassword}
              onChange={handleChange}
              error={formErrors.confirmPassword}
              disabled={isSubmitting}
              showPasswordToggle
            />

            <div className="flex flex-col items-center space-y-5">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={isSubmitting}
              >
                Redefinir Senha
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
              Sua nova senha deve ter no mínimo 8 caracteres. Use uma senha forte e única.
            </p>
          </div>
        </div>
      </div>
    </AuthLayout>
  );
};
