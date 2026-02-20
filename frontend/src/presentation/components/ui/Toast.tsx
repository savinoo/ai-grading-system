import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

/* ─── Tipos ────────────────────────────────────────────────────── */
export type ToastVariant = 'success' | 'error' | 'info' | 'warning';

export interface ToastItem {
  id: string;
  variant: ToastVariant;
  title: string;
  description?: string;
  duration?: number; // ms – padrão 4000
}

interface ToastContextValue {
  toast: (options: Omit<ToastItem, 'id'>) => void;
}

/* ─── Contexto ─────────────────────────────────────────────────── */
const ToastContext = createContext<ToastContextValue | null>(null);

/* ─── Provider ─────────────────────────────────────────────────── */
export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback((options: Omit<ToastItem, 'id'>) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, duration: 4000, ...options }]);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {createPortal(
        <ToastList toasts={toasts} onDismiss={dismiss} />,
        document.body,
      )}
    </ToastContext.Provider>
  );
};

/* ─── Hook de acesso ───────────────────────────────────────────── */
export const useToast = (): ToastContextValue => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast deve ser usado dentro de <ToastProvider>');
  return ctx;
};

/* ─── Lista de toasts ──────────────────────────────────────────── */
const ToastList: React.FC<{ toasts: ToastItem[]; onDismiss: (id: string) => void }> = ({
  toasts,
  onDismiss,
}) => (
  <div
    className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-3 items-end"
    aria-live="polite"
    aria-label="Notificações"
  >
    {toasts.map((t) => (
      <ToastCard key={t.id} toast={t} onDismiss={onDismiss} />
    ))}
  </div>
);

/* ─── Card individual ──────────────────────────────────────────── */
const VARIANT_MAP: Record<
  ToastVariant,
  { icon: string; bar: string; iconBg: string; iconColor: string; border: string }
> = {
  success: {
    icon: 'check_circle',
    bar: 'bg-green-500',
    iconBg: 'bg-green-100 dark:bg-green-900/40',
    iconColor: 'text-green-600 dark:text-green-400',
    border: 'border-green-200 dark:border-green-800',
  },
  error: {
    icon: 'cancel',
    bar: 'bg-red-500',
    iconBg: 'bg-red-100 dark:bg-red-900/40',
    iconColor: 'text-red-600 dark:text-red-400',
    border: 'border-red-200 dark:border-red-800',
  },
  warning: {
    icon: 'warning',
    bar: 'bg-yellow-400',
    iconBg: 'bg-yellow-100 dark:bg-yellow-900/40',
    iconColor: 'text-yellow-600 dark:text-yellow-400',
    border: 'border-yellow-200 dark:border-yellow-800',
  },
  info: {
    icon: 'info',
    bar: 'bg-blue-500',
    iconBg: 'bg-blue-100 dark:bg-blue-900/40',
    iconColor: 'text-blue-600 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-800',
  },
};

const ToastCard: React.FC<{ toast: ToastItem; onDismiss: (id: string) => void }> = ({
  toast,
  onDismiss,
}) => {
  const { id, variant, title, description, duration = 4000 } = toast;
  const style = VARIANT_MAP[variant];

  /* animação de entrada/saída */
  const [visible, setVisible] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /* Entrada com pequeno delay para o CSS transition funcionar */
  useEffect(() => {
    const enterFrame = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(enterFrame);
  }, []);

  /* Auto-dismiss */
  const startTimer = useCallback(() => {
    timerRef.current = setTimeout(() => {
      setVisible(false);
      setTimeout(() => onDismiss(id), 300); // aguarda saída
    }, duration);
  }, [duration, id, onDismiss]);

  const clearTimer = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
  }, []);

  useEffect(() => {
    startTimer();
    return clearTimer;
  }, [startTimer, clearTimer]);

  const handleDismiss = () => {
    clearTimer();
    setVisible(false);
    setTimeout(() => onDismiss(id), 300);
  };

  return (
    <div
      onMouseEnter={clearTimer}
      onMouseLeave={startTimer}
      role="alert"
      className={`
        relative flex items-start gap-3 w-80 max-w-[calc(100vw-2.5rem)]
        bg-white dark:bg-slate-800
        border ${style.border}
        rounded-xl shadow-lg shadow-black/10 dark:shadow-black/30
        p-4 overflow-hidden cursor-pointer
        transition-all duration-300 ease-out
        ${visible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
      `}
      onClick={handleDismiss}
    >
      {/* Barra de progresso */}
      <ProgressBar duration={duration} paused={false} variant={style.bar} />

      {/* Ícone */}
      <div className={`size-9 rounded-lg flex-shrink-0 flex items-center justify-center ${style.iconBg}`}>
        <span className={`material-symbols-outlined text-[22px] ${style.iconColor}`}>
          {style.icon}
        </span>
      </div>

      {/* Conteúdo */}
      <div className="flex-1 min-w-0 pt-0.5">
        <p className="text-sm font-semibold text-slate-900 dark:text-white leading-snug">{title}</p>
        {description && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-snug">
            {description}
          </p>
        )}
      </div>

      {/* Botão de fechar */}
      <button
        onClick={(e) => { e.stopPropagation(); handleDismiss(); }}
        className="flex-shrink-0 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors mt-0.5"
        aria-label="Fechar notificação"
      >
        <span className="material-symbols-outlined text-[18px]">close</span>
      </button>
    </div>
  );
};

/* ─── Barra de progresso ───────────────────────────────────────── */
const ProgressBar: React.FC<{ duration: number; paused: boolean; variant: string }> = ({
  duration,
  variant,
}) => {
  const [width, setWidth] = useState(100);
  const startRef = useRef(Date.now());
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    const tick = () => {
      const elapsed = Date.now() - startRef.current;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setWidth(remaining);
      if (remaining > 0) frameRef.current = requestAnimationFrame(tick);
    };
    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [duration]);

  return (
    <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-slate-100 dark:bg-slate-700">
      <div
        className={`h-full ${variant} transition-none rounded-full`}
        style={{ width: `${width}%` }}
      />
    </div>
  );
};
