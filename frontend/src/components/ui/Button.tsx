import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  icon?: ReactNode
}

export function Button({ variant = 'primary', icon, className = '', children, ...props }: ButtonProps) {
  const styles = {
    primary:
      'bg-[#1D4ED8] text-white shadow-sm hover:bg-[#1E40AF]',
    secondary:
      'border border-[#CBD5E1] bg-white text-[#334155] hover:border-[#94A3B8] hover:bg-[#F8FAFC]',
    ghost: 'text-[#475569] hover:bg-[#F1F5F9]',
  }

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-colors duration-200 ${styles[variant]} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </button>
  )
}
