import React, { useState } from 'react';

interface PlagiarismAlert {
  studentAnswerId: number;
  similarAnswerId: number;
  similarityScore: number;
  detectionMethod: string;
  examName: string;
}

export const PlagiarismPage: React.FC = () => {
  const [alerts] = useState<PlagiarismAlert[]>([]);

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Detecção de Plágio
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Análise de similaridade entre respostas dos alunos (TF-IDF + Cosine Similarity)
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg">
          <span className="material-symbols-outlined text-amber-600 text-base">info</span>
          <span className="text-xs text-amber-700">Threshold: 90% similaridade</span>
        </div>
      </div>

      {/* Info card */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined text-blue-600 mt-0.5">info</span>
          <div>
            <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
              Como funciona a detecção?
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              O sistema compara automaticamente as respostas discursivas de cada aluno com as demais
              respostas da mesma questão usando TF-IDF + similaridade cosseno. Respostas com
              similaridade ≥ 90% são sinalizadas para revisão do professor.
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      {alerts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="rounded-full bg-green-100 dark:bg-green-900/30 p-4 mb-4">
            <span className="material-symbols-outlined text-green-600 text-4xl">verified</span>
          </div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
            Nenhuma ocorrência detectada
          </h3>
          <p className="text-sm text-slate-500 max-w-sm">
            Não foram encontradas respostas com similaridade acima do threshold configurado.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {alerts.map((alert, idx) => (
            <div
              key={idx}
              className="bg-white dark:bg-slate-800 border border-red-200 dark:border-red-800 rounded-xl p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="flex items-center gap-2 text-red-600 font-medium text-sm">
                  <span className="material-symbols-outlined text-base">warning</span>
                  Similaridade: {(alert.similarityScore * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-slate-500">{alert.examName}</span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm text-slate-600 dark:text-slate-400">
                <div>
                  <span className="font-medium">Resposta:</span> #{alert.studentAnswerId}
                </div>
                <div>
                  <span className="font-medium">Similar a:</span> #{alert.similarAnswerId}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
