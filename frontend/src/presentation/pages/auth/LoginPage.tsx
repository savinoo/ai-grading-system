import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AuthLayout } from '@presentation/components/layout/AuthLayout';
import { Input } from '@presentation/components/ui/Input';
import { Button } from '@presentation/components/ui/Button';
import { useAuth } from '@presentation/hooks/useAuth';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading, error } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  
  const [formErrors, setFormErrors] = useState({
    email: '',
    password: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    
    // Limpa erro do campo ao digitar
    if (formErrors[name as keyof typeof formErrors]) {
      setFormErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validação básica
    const errors = {
      email: '',
      password: '',
    };
    
    if (!formData.email) {
      errors.email = 'Email é obrigatório';
    }
    
    if (!formData.password) {
      errors.password = 'Senha é obrigatória';
    }
    
    if (errors.email || errors.password) {
      setFormErrors(errors);
      return;
    }

    try {
      await login(formData.email, formData.password);
      navigate('/dashboard');
    } catch (err) {
      // Erro será exibido pelo hook useAuth
      console.error('Login error:', err);
    }
  };

  return (
    <AuthLayout>
      <div className="w-full max-w-[480px]">
        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl shadow-slate-200/50 dark:shadow-none p-8 md:p-10">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-slate-900 dark:text-white tracking-tight text-3xl font-extrabold leading-tight pb-2">
              Bem-vindo de volta
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium leading-normal">
              Acesse sua conta de instrutor para gerenciar avaliações
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-red-600 dark:text-red-400 text-sm font-medium">{error}</p>
            </div>
          )}

          {/* Form */}
          <form className="space-y-5" onSubmit={handleSubmit}>
            <Input
              label="Email institucional"
              name="email"
              type="email"
              placeholder="nome@instituicao.edu.br"
              value={formData.email}
              onChange={handleInputChange}
              error={formErrors.email}
            />

            <div>
              <div className="flex justify-between items-center px-1 mb-2">
                <label className="text-slate-900 dark:text-slate-200 text-sm font-bold leading-normal">
                  Senha
                </label>
                <Link
                  to="/forgot-password"
                  className="text-primary text-xs font-bold hover:underline transition-all"
                >
                  Esqueceu a senha?
                </Link>
              </div>
              <Input
                name="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleInputChange}
                error={formErrors.password}
                showPasswordToggle
              />
            </div>

            <div className="pt-4">
              <Button
                type="submit"
                fullWidth
                size="lg"
                loading={isLoading}
                icon={<span className="material-symbols-outlined text-lg">login</span>}
                iconPosition="right"
              >
                Entrar
              </Button>
            </div>
          </form>
        </div>

        {/* Footer Links */}
        <div className="mt-8 text-center flex flex-col items-center gap-4">
          <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">
            Novo na plataforma?{' '}
            <Link to="/signup" className="text-primary font-bold hover:underline transition-all px-1">
              Criar uma conta
            </Link>
          </p>
        </div>
      </div>
    </AuthLayout>
  );
};
