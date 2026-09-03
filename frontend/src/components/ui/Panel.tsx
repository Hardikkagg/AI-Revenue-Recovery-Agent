import type { ReactNode } from 'react'

interface PanelProps {
  title?: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}

export function Panel({ title, subtitle, action, children, className = '' }: PanelProps) {
  return (
    <section className={`panel-surface p-5 ${className}`}>
      {(title || subtitle || action) && (
        <div className="mb-4 flex items-start justify-between gap-4 border-b border-[#2D3139] pb-3">
          <div>
            {title && <h3 className="font-mono text-xs font-medium uppercase tracking-[0.12em] text-[#C7C4D7]">{title}</h3>}
            {subtitle && <p className="mt-1.5 text-sm text-[#908FA0]">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  )
}
