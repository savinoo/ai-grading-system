import React from 'react';

interface ErrorAlertProps {
  message: string;
  type?: 'error' | 'warning' | 'info';
  onAction?: () => void;
  actionLabel?: string;
  onClose?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({ 
  message, 
  type = 'error',
  onAction,
  actionLabel,
  onClose,
}) => {
  const styles = {
    error: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800',
      text: 'text-red-600 dark:text-red-400',
      icon: 'error'
    },
    warning: {
      bg: 'bg-orange-50 dark:bg-orange-900/20',
      border: 'border-orange-200 dark:border-orange-800',
      text: 'text-orange-600 dark:text-orange-400',
      icon: 'warning'
    },
    info: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-800',
      text: 'text-blue-600 dark:text-blue-400',
      icon: 'info'
    }
  };

  const style = styles[type];

  return (
    <div className={`p-4 ${style.bg} border ${style.border} rounded-lg`}>
      <div className="flex items-start gap-3">
        <span className={`material-symbols-outlined ${style.text} text-xl flex-shrink-0`}>
          {style.icon}
        </span>
        <div className="flex-1">
          <p className={`text-sm ${style.text} font-medium`}>
            {message}
          </p>
          {onAction && actionLabel && (
            <button
              onClick={onAction}
              className={`mt-2 text-sm ${style.text} font-bold hover:underline`}
            >
              {actionLabel}
            </button>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className={`${style.text} hover:opacity-70 transition-opacity flex-shrink-0`}
            aria-label="Fechar"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        )}
      </div>
    </div>
  );
};
