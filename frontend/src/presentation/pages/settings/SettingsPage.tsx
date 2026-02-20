import React, { useState } from 'react';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';

import { useAuth } from '@presentation/hooks/useAuth';
import { useToast } from '@presentation/components/ui/Toast';

type Tab = 'security';

interface PasswordForm {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

interface PasswordErrors {
  current_password?: string;
  new_password?: string;
  confirm_password?: string;
}

export const SettingsPage: React.FC = () => {
  const { user, changePassword } = useAuth();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<Tab>('security');

  const [form, setForm] = useState<PasswordForm>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [errors, setErrors] = useState<PasswordErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });

  const validate = (): boolean => {
    const newErrors: PasswordErrors = {};

    if (!form.current_password) {
      newErrors.current_password = 'Informe sua senha atual.';
    }
    if (!form.new_password) {
      newErrors.new_password = 'Informe a nova senha.';
    } else if (form.new_password.length < 8) {
      newErrors.new_password = 'A nova senha deve ter no mínimo 8 caracteres.';
    } else if (form.new_password === form.current_password) {
      newErrors.new_password = 'A nova senha não pode ser igual à senha atual.';
    }
    if (!form.confirm_password) {
      newErrors.confirm_password = 'Confirme a nova senha.';
    } else if (form.new_password !== form.confirm_password) {
      newErrors.confirm_password = 'As senhas não coincidem.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);

    try {
      await changePassword(form.current_password, form.new_password);
      setForm({ current_password: '', new_password: '', confirm_password: '' });
      toast({
        variant: 'success',
        title: 'Senha alterada!',
        description: 'Sua senha foi atualizada com sucesso.',
      });
    } catch (err: any) {
      toast({
        variant: 'error',
        title: 'Erro ao alterar senha',
        description: err.message || 'Tente novamente.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const tabs = [
    { id: 'security' as Tab, label: 'Segurança', icon: 'lock' },
  ];

  return (
    <DashboardLayout>
      <div className="p-6 max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Configurações</h1>
          <p className="text-slate-500 dark:text-slate-400">Gerencie sua conta e preferências de segurança</p>
        </div>
        {/* Layout com aside + conteúdo */}
        <div className="flex gap-6">
          {/* Sidebar de abas */}
          <aside className="w-52 flex-shrink-0">
            <nav className="flex flex-col gap-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left w-full ${
                    activeTab === tab.id
                      ? 'bg-primary text-white'
                      : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  <span className="material-symbols-outlined text-[20px]">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </aside>

          {/* Conteúdo da aba */}
          <div className="flex-1 min-w-0">
            {activeTab === 'security' && (
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                {/* Cabeçalho da seção */}
                <div className="px-6 py-5 border-b border-slate-200 dark:border-slate-700">
                  <h2 className="text-base font-bold text-slate-900 dark:text-white">Segurança</h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                    Gerencie sua senha de acesso.
                  </p>
                </div>

                {/* Informações da conta */}
                <div className="px-6 py-5 border-b border-slate-200 dark:border-slate-700">
                  <div className="flex items-center gap-4">
                    <div className="size-12 rounded-full bg-primary flex items-center justify-center text-white font-bold text-lg">
                      {user?.first_name?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900 dark:text-white">
                        {user?.first_name && user?.last_name
                          ? `${user.first_name} ${user.last_name}`
                          : user?.email}
                      </p>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{user?.email}</p>
                    </div>
                  </div>
                </div>

                {/* Formulário de troca de senha */}
                <form onSubmit={handleSubmit} className="px-6 py-5">
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-4">
                    Alterar senha
                  </h3>

                  <div className="flex flex-col gap-4 max-w-md">
                    {/* Senha atual */}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        Senha atual
                      </label>
                      <div className="relative">
                        <input
                          type={showPasswords.current ? 'text' : 'password'}
                          name="current_password"
                          value={form.current_password}
                          onChange={handleChange}
                          placeholder="Digite sua senha atual"
                          className={`w-full px-3 py-2.5 pr-10 rounded-lg border text-sm bg-white dark:bg-slate-900 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 transition-colors ${
                            errors.current_password
                              ? 'border-red-400 focus:ring-red-300'
                              : 'border-slate-300 dark:border-slate-600 focus:ring-primary/30 focus:border-primary'
                          }`}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPasswords((p) => ({ ...p, current: !p.current }))}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                        >
                          <span className="material-symbols-outlined text-[18px]">
                            {showPasswords.current ? 'visibility_off' : 'visibility'}
                          </span>
                        </button>
                      </div>
                      {errors.current_password && (
                        <p className="text-xs text-red-500">{errors.current_password}</p>
                      )}
                    </div>

                    {/* Nova senha */}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        Nova senha
                      </label>
                      <div className="relative">
                        <input
                          type={showPasswords.new ? 'text' : 'password'}
                          name="new_password"
                          value={form.new_password}
                          onChange={handleChange}
                          placeholder="Mínimo 8 caracteres"
                          className={`w-full px-3 py-2.5 pr-10 rounded-lg border text-sm bg-white dark:bg-slate-900 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 transition-colors ${
                            errors.new_password
                              ? 'border-red-400 focus:ring-red-300'
                              : 'border-slate-300 dark:border-slate-600 focus:ring-primary/30 focus:border-primary'
                          }`}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPasswords((p) => ({ ...p, new: !p.new }))}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                        >
                          <span className="material-symbols-outlined text-[18px]">
                            {showPasswords.new ? 'visibility_off' : 'visibility'}
                          </span>
                        </button>
                      </div>
                      {errors.new_password && (
                        <p className="text-xs text-red-500">{errors.new_password}</p>
                      )}
                      {/* Indicador de força */}
                      {form.new_password && (
                        <PasswordStrength password={form.new_password} />
                      )}
                    </div>

                    {/* Confirmar nova senha */}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        Confirmar nova senha
                      </label>
                      <div className="relative">
                        <input
                          type={showPasswords.confirm ? 'text' : 'password'}
                          name="confirm_password"
                          value={form.confirm_password}
                          onChange={handleChange}
                          placeholder="Repita a nova senha"
                          className={`w-full px-3 py-2.5 pr-10 rounded-lg border text-sm bg-white dark:bg-slate-900 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 transition-colors ${
                            errors.confirm_password
                              ? 'border-red-400 focus:ring-red-300'
                              : form.confirm_password && form.confirm_password === form.new_password
                              ? 'border-green-400 focus:ring-green-300'
                              : 'border-slate-300 dark:border-slate-600 focus:ring-primary/30 focus:border-primary'
                          }`}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPasswords((p) => ({ ...p, confirm: !p.confirm }))}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                        >
                          <span className="material-symbols-outlined text-[18px]">
                            {showPasswords.confirm ? 'visibility_off' : 'visibility'}
                          </span>
                        </button>
                      </div>
                      {errors.confirm_password && (
                        <p className="text-xs text-red-500">{errors.confirm_password}</p>
                      )}
                      {form.confirm_password && form.confirm_password === form.new_password && !errors.confirm_password && (
                        <p className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                          <span className="material-symbols-outlined text-[14px]">check_circle</span>
                          As senhas coincidem
                        </p>
                      )}
                    </div>

                    {/* Botão */}
                    <div className="flex justify-end pt-1">
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="flex items-center gap-2 px-5 py-2.5 bg-primary text-white text-sm font-semibold rounded-lg hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
                      >
                        {isSubmitting ? (
                          <>
                            <span className="material-symbols-outlined text-[18px] animate-spin">
                              progress_activity
                            </span>
                            Salvando...
                          </>
                        ) : (
                          <>
                            <span className="material-symbols-outlined text-[18px]">save</span>
                            Salvar nova senha
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

/* ---------- Componente auxiliar: indicador de força da senha ---------- */
const PasswordStrength: React.FC<{ password: string }> = ({ password }) => {
  const getStrength = (pwd: string): { score: number; label: string; color: string } => {
    let score = 0;
    if (pwd.length >= 8) score++;
    if (pwd.length >= 12) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;

    if (score <= 1) return { score, label: 'Muito fraca', color: 'bg-red-500' };
    if (score === 2) return { score, label: 'Fraca', color: 'bg-orange-400' };
    if (score === 3) return { score, label: 'Razoável', color: 'bg-yellow-400' };
    if (score === 4) return { score, label: 'Forte', color: 'bg-green-400' };
    return { score, label: 'Muito forte', color: 'bg-green-600' };
  };

  const { score, label, color } = getStrength(password);
  const bars = 5;

  return (
    <div className="flex flex-col gap-1">
      <div className="flex gap-1">
        {Array.from({ length: bars }).map((_, i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-colors ${
              i < score ? color : 'bg-slate-200 dark:bg-slate-700'
            }`}
          />
        ))}
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Força: <span className="font-medium text-slate-700 dark:text-slate-300">{label}</span>
      </p>
    </div>
  );
};

