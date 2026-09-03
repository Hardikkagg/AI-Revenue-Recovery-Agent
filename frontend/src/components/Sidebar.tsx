import { Activity, Gauge, Layers3, Settings, ShieldCheck, Sparkles, TrendingUp } from 'lucide-react'

const navItems = [
  { label: 'Overview', icon: Gauge },
  { label: 'Recovery Operations', icon: Activity, active: true },
  { label: 'Simulations', icon: Layers3 },
  { label: 'Learning', icon: TrendingUp },
  { label: 'Strategy Performance', icon: Sparkles },
  { label: 'Settings', icon: ShieldCheck },
]

export function Sidebar() {
  return (
    <aside className="hidden w-[260px] shrink-0 border-r border-[#2D3139] bg-[#14161A] lg:flex lg:flex-col">
      <div className="border-b border-[#2D3139] px-6 py-7">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded border border-indigo-400/60 bg-indigo-500/10 text-indigo-300">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <div className="font-semibold tracking-tight text-slate-50">Recovery Agent</div>
            <div className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Fintech Console</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-5">
        {navItems.map(({ label, icon: Icon, active }) => (
          <button
            key={label}
            className={`flex w-full items-center gap-3 rounded px-3 py-2.5 text-left text-sm transition-colors duration-200 ${
              active
                ? 'border-l-2 border-indigo-400 bg-[#1C1F26] text-indigo-200'
                : 'border-l-2 border-transparent text-[#C7C4D7] hover:bg-[#1C1F26] hover:text-slate-50'
            }`}
            type="button"
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="border-t border-[#2D3139] px-3 py-4">
        <button className="flex w-full items-center gap-3 rounded px-3 py-2.5 text-left text-sm text-[#C7C4D7] transition-colors hover:bg-[#1C1F26] hover:text-slate-50" type="button">
          <Settings className="h-4 w-4" />
          <span>Settings</span>
        </button>
        <div className="mt-4 border border-[#2D3139] bg-[#0A0B0D] p-3">
          <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            System status
          </div>
          <div className="mt-2 text-sm font-medium text-slate-100">Recovery Engine Online</div>
        </div>
      </div>
    </aside>
  )
}
