import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  icon?: ReactNode
}

export function Button({ variant = 'primary', icon, className = '', children, ...props }: ButtonProps) {
  const styles = {
    primary:
      'bg-gradient-to-r from-blue-500 via-violet-500 to-indigo-500 text-white shadow-[0_12px_30px_rgba(96,165,250,0.35)] hover:brightness-110',
    secondary:
      'border border-slate-700 bg-slate-900/80 text-slate-100 hover:border-slate-600 hover:bg-slate-800/80',
    ghost: 'text-slate-200 hover:bg-slate-800/60',
  }

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200 ${styles[variant]} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </button>
  )
}
