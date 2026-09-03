import { Activity, Gauge, Layers3, ShieldCheck, Sparkles, TrendingUp } from 'lucide-react'

import type { WorkspaceView } from './SecondaryViews'

const navItems = [
  { label: 'Overview', icon: Gauge },
  { label: 'Recovery Operations', icon: Activity, active: true },
  { label: 'Simulations', icon: Layers3 },
  { label: 'Learning', icon: TrendingUp },
  { label: 'Strategy Performance', icon: Sparkles },
  { label: 'Settings', icon: ShieldCheck },
] as const

interface SidebarProps {
  activeView: WorkspaceView
  onNavigate: (view: WorkspaceView) => void
  backendAvailable: boolean | null
}

export function Sidebar({ activeView, onNavigate, backendAvailable }: SidebarProps) {
  return (
    <aside className="hidden w-[236px] shrink-0 border-r border-[#D9E0E7] bg-white lg:flex lg:flex-col">
      <div className="border-b border-[#D9E0E7] px-5 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[#1D4ED8] text-white">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <div className="font-semibold tracking-tight text-[#172033]">Recovery</div>
            <div className="mt-0.5 text-xs text-[#64748B]">Revenue operations</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-5">
        {navItems.map(({ label, icon: Icon }) => (
          <button
            key={label}
            className={`flex w-full items-center gap-3 rounded px-3 py-2.5 text-left text-sm transition-colors duration-200 ${
              activeView === label
                ? 'border-l-2 border-[#2563EB] bg-[#EFF6FF] text-[#1D4ED8]'
                : 'border-l-2 border-transparent text-[#475569] hover:bg-[#F8FAFC] hover:text-[#172033]'
            }`}
            type="button"
            onClick={() => onNavigate(label)}
            aria-current={activeView === label ? 'page' : undefined}
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="border-t border-[#D9E0E7] px-3 py-4">
        <div className="mt-4 border border-[#D9E0E7] bg-[#F8FAFC] p-3">
          <div className="flex items-center gap-2 text-xs text-[#64748B]">
            <span className={`h-2 w-2 rounded-full ${backendAvailable === true ? 'bg-emerald-400' : backendAvailable === false ? 'bg-red-400' : 'bg-[#908FA0]'}`} />
            System status
          </div>
          <div className="mt-2 text-sm font-medium text-[#172033]">{backendAvailable === true ? 'Connected' : backendAvailable === false ? 'Unavailable' : 'Checking connection'}</div>
        </div>
      </div>
    </aside>
  )
}
