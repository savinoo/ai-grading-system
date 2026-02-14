import React, { useEffect, useState } from 'react';

interface PublishSuccessModalProps {
  message: string;
  nextSteps: string[];
  onClose: () => void;
  examUuid: string;
  onStatusChange?: (newStatus: string) => void;
}

export const PublishSuccessModal: React.FC<PublishSuccessModalProps> = ({
  message,
  nextSteps,
  onClose,
  examUuid,
  onStatusChange,
}) => {
  const [status, setStatus] = useState<'processing' | 'warning' | 'success'>('processing');
  const [errorDetails, setErrorDetails] = useState<string | null>(null);

  useEffect(() => {
    // Poll para verificar o status da prova a cada 2 segundos
    const pollInterval = setInterval(async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/exams/${examUuid}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.ok) {
          const exam = await response.json();
          
          if (exam.status === 'WARNING') {
            setStatus('warning');
            setErrorDetails(
              'Houve um erro ao indexar os materiais da prova. ' +
              'Verifique se todos os arquivos PDF estão acessíveis e tente publicar novamente.'
            );
            onStatusChange?.(exam.status);
            clearInterval(pollInterval);
          } else if (exam.status === 'GRADED') {
            setStatus('success');
            onStatusChange?.(exam.status);
            // Auto-fechar após 3 segundos se for sucesso
            const timer = setTimeout(onClose, 3000);
            clearInterval(pollInterval);
            return () => clearTimeout(timer);
          }
        }
      } catch (error) {
        console.error('Erro ao verificar status da prova:', error);
      }
    }, 2000);

    // Limpar polling após 30 segundos se ainda estiver processando
    const timeoutId = setTimeout(() => {
      clearInterval(pollInterval);
    }, 30000);

    return () => {
      clearInterval(pollInterval);
      clearTimeout(timeoutId);
    };
  }, [examUuid, onClose, onStatusChange]);

  if (status === 'warning') {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[100]">
        <div className="bg-white dark:bg-slate-900 rounded-xl p-8 max-w-md w-full mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
          {/* Header com ícone de aviso */}
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-amber-100 dark:bg-amber-900/30 rounded-full">
              <span className="material-symbols-outlined text-amber-600 dark:text-amber-400 text-3xl">
                warning
              </span>
            </div>
            <div>
              <h2 className="text-2xl font-black text-amber-600 dark:text-amber-400">
                Aviso!
              </h2>
              <p className="text-xs text-slate-500 uppercase tracking-wider">
                Erro ao processar prova
              </p>
            </div>
          </div>

          {/* Mensagem de erro */}
          <div className="mb-6 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
            <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
              {errorDetails}
            </p>
          </div>

          {/* Próximas ações */}
          <div className="mb-6 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
              O que fazer?
            </h3>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li className="flex items-start gap-2">
                <span className="text-amber-600 mt-1">•</span>
                <span>Verifique se os arquivos PDF são válidos</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-600 mt-1">•</span>
                <span>Tente remover e re-adicionar os materiais</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-600 mt-1">•</span>
                <span>Publique novamente após resolver os problemas</span>
              </li>
            </ul>
          </div>

          {/* Botão de fechamento */}
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-bold text-sm transition-colors flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">close</span>
            Entendi
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[100]">
      <div className="bg-white dark:bg-slate-900 rounded-xl p-8 max-w-md w-full mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
        {/* Header com ícone de sucesso */}
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-full">
            <span className="material-symbols-outlined text-emerald-600 dark:text-emerald-400 text-3xl animate-spin">
              hourglass
            </span>
          </div>
          <div>
            <h2 className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
              Processando...
            </h2>
            <p className="text-xs text-slate-500 uppercase tracking-wider">
              Prova publicada
            </p>
          </div>
        </div>

        {/* Mensagem */}
        <div className="mb-6 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
          <p className="text-sm font-medium text-slate-900 dark:text-white">
            {message}
          </p>
        </div>

        {/* Próximos passos */}
        {nextSteps.length > 0 && (
          <div className="mb-6">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
              Próximos Passos
            </h3>
            <ul className="space-y-2">
              {nextSteps.map((step, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-400"
                >
                  <span className="flex-shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary/10 text-primary text-xs font-bold">
                    {index + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Informações sobre o processamento */}
        <div className="mb-6 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-xs text-blue-900 dark:text-blue-100 flex items-start gap-2">
            <span className="material-symbols-outlined text-sm mt-0.5">info</span>
            <span>
              A prova está sendo processada em background. Este processo pode levar alguns minutos.
              Se houver erro, o status mudará para "Aviso de Correção".
            </span>
          </p>
        </div>

        {/* Botão de fechamento */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-slate-700">
          <span className="text-xs text-slate-400">
            Monitorizando status...
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold text-sm transition-colors flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">close</span>
            OK
          </button>
        </div>
      </div>
    </div>
  );
};
