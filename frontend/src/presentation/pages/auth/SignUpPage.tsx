import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AuthLayout } from '@presentation/components/layout/AuthLayout';
import { Input } from '@presentation/components/ui/Input';
import { Button } from '@presentation/components/ui/Button';
import { useAuth } from '@presentation/hooks/useAuth';

export const SignUpPage: React.FC = () => {
  const navigate = useNavigate();
  const { register, isLoading, error } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    confirmPassword: '',
    user_type: 'teacher' as 'admin' | 'teacher' | 'student', // Tipo padrão: teacher
  });
  
  const [formErrors, setFormErrors] = useState({
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    confirmPassword: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
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
      first_name: '',
      last_name: '',
      password: '',
      confirmPassword: '',
    };
    
    if (!formData.email) {
      errors.email = 'Email é obrigatório';
    }
    
    if (!formData.first_name) {
      errors.first_name = 'Nome é obrigatório';
    }
    
    if (!formData.last_name) {
      errors.last_name = 'Sobrenome é obrigatório';
    }
    
    if (!formData.password) {
      errors.password = 'Senha é obrigatória';
    } else if (formData.password.length < 8) {
      errors.password = 'Senha deve ter no mínimo 8 caracteres';
    }
    
    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Confirme sua senha';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'As senhas não coincidem';
    }
    
    if (errors.email || errors.first_name || errors.last_name || errors.password || errors.confirmPassword) {
      setFormErrors(errors);
      return;
    }

    try {
      await register({
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
        password: formData.password,
        user_type: formData.user_type,
      });
      // Só navega se não houver erro
      navigate('/email-verification', { state: { email: formData.email } });
    } catch (err) {
      console.error('Register error:', err);
      // Erro já está sendo tratado pelo useAuth e mostrado na tela
    }
  };

  return (
    <AuthLayout>
      <div className="w-full max-w-[520px]">
        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl shadow-slate-200/50 dark:shadow-none p-8 md:p-10">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-slate-900 dark:text-white tracking-tight text-3xl font-extrabold leading-tight pb-2">
              Criar conta
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium leading-normal">
              Cadastre-se para começar a usar o Corretum AI
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-red-600 dark:text-red-400 text-sm font-medium">
                {typeof error === 'string' ? error : 'Erro ao criar conta. Tente novamente.'}
              </p>
            </div>
          )}

          {/* Form */}
          <form className="space-y-5" onSubmit={handleSubmit}>
            <Input
              label="Nome"
              name="first_name"
              type="text"
              placeholder="João"
              value={formData.first_name}
              onChange={handleInputChange}
              error={formErrors.first_name}
            />

            <Input
              label="Sobrenome"
              name="last_name"
              type="text"
              placeholder="Silva"
              value={formData.last_name}
              onChange={handleInputChange}
              error={formErrors.last_name}
            />

            <Input
              label="Email institucional"
              name="email"
              type="email"
              placeholder="seu.email@instituicao.edu.br"
              value={formData.email}
              onChange={handleInputChange}
              error={formErrors.email}
            />

            <Input
              label="Senha"
              name="password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleInputChange}
              error={formErrors.password}
              helperText="Mínimo de 8 caracteres, com maiúscula, minúscula e número"
              showPasswordToggle
            />

            <Input
              label="Confirmar senha"
              name="confirmPassword"
              type="password"
              placeholder="••••••••"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              error={formErrors.confirmPassword}
              showPasswordToggle
            />

            <div className="pt-4">
              <Button
                type="submit"
                fullWidth
                size="lg"
                loading={isLoading}
                icon={<span className="material-symbols-outlined text-lg">person_add</span>}
                iconPosition="right"
              >
                Criar Conta
              </Button>
            </div>
          </form>

          {/* Terms */}
          <p className="mt-6 text-center text-xs text-slate-500 dark:text-slate-400">
            Ao criar uma conta, você concorda com nossos{' '}
            <Link to="/terms" className="text-primary dark:text-primary-light font-bold hover:underline">
              Termos de Serviço
            </Link>{' '}
            e{' '}
            <Link to="/privacy" className="text-primary dark:text-primary-light font-bold hover:underline">
              Política de Privacidade
            </Link>
          </p>
        </div>

        {/* Footer Links */}
        <div className="mt-8 text-center">
          <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">
            Já tem uma conta?{' '}
            <Link to="/login" className="text-primary dark:text-primary-light font-bold hover:underline transition-all px-1">
              Fazer login
            </Link>
          </p>
        </div>
      </div>
    </AuthLayout>
  );
};
