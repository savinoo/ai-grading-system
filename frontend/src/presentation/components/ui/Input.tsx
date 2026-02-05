import React, { InputHTMLAttributes, forwardRef, useState } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
  showPasswordToggle?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, icon, showPasswordToggle, className = '', type = 'text', ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const inputType = showPasswordToggle ? (showPassword ? 'text' : 'password') : type;

    return (
      <div className="flex flex-col gap-2">
        {label && (
          <label className="text-slate-900 dark:text-slate-200 text-sm font-bold leading-normal px-1">
            {label}
          </label>
        )}
        
        <div className="relative group">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              {icon}
            </div>
          )}
          
          <input
            ref={ref}
            type={inputType}
            className={`
              form-input flex w-full rounded-lg text-slate-900 dark:text-white 
              border ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/10' : 'border-slate-200 dark:border-slate-700 focus:border-primary focus:ring-primary/10'}
              bg-white dark:bg-slate-800/50 
              focus:ring-4 h-14 
              placeholder:text-slate-400 
              ${icon ? 'pl-10' : 'pl-4'} 
              ${showPasswordToggle ? 'pr-12' : 'pr-4'} 
              py-3.5
              text-base font-normal leading-normal transition-all
              ${className}
            `}
            {...props}
          />
          
          {showPasswordToggle && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-primary cursor-pointer flex items-center transition-colors"
            >
              <span className="material-symbols-outlined text-xl">
                {showPassword ? 'visibility_off' : 'visibility'}
              </span>
            </button>
          )}
        </div>
        
        {error && (
          <p className="text-red-500 text-xs font-medium px-1">{error}</p>
        )}
        
        {helperText && !error && (
          <p className="text-slate-500 text-xs px-1">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
