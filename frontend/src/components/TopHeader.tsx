import { motion } from 'framer-motion'
import { Bell, CircleHelp, Search } from 'lucide-react'

interface TopHeaderProps {
  backendAvailable: boolean
  hasAnalysis: boolean
  hasSimulation: boolean
}

export function TopHeader({ backendAvailable, hasAnalysis, hasSimulation }: TopHeaderProps) {
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const statuses = [
    backendAvailable && 'RECOVERY ENGINE ONLINE',
    backendAvailable && 'API CONNECTED',
    hasAnalysis || hasSimulation ? 'ADAPTIVE POLICY ACTIVE' : null,
  ].filter(Boolean) as string[]

  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="border-b border-[#2D3139] bg-[#0A0B0D] px-5 py-4"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="shrink-0">
          <div className="text-xl font-semibold tracking-tight text-slate-50">Recovery Workspace</div>
          <div className="mt-1 font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">AI Revenue Operations</div>
        </div>

        <div className="flex min-w-0 flex-1 items-center justify-center xl:px-8">
          <label className="relative w-full max-w-md">
            <span className="sr-only">Search cases and strategies</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#908FA0]" />
            <input className="w-full rounded border border-[#2D3139] bg-[#14161A] py-2 pl-10 pr-3 text-sm text-slate-100 outline-none placeholder:text-[#908FA0] focus:border-indigo-400" placeholder="Search case ID, strategy..." type="search" />
          </label>
        </div>

        <div className="flex flex-wrap items-center justify-end gap-2 text-[10px] uppercase tracking-[0.12em] text-slate-300">
          <span className="ops-chip">Environment: Production</span>
          <button className="rounded p-2 text-[#C7C4D7] hover:bg-[#1C1F26] hover:text-indigo-300" aria-label="Notifications" type="button"><Bell className="h-4 w-4" /></button>
          <button className="rounded p-2 text-[#C7C4D7] hover:bg-[#1C1F26] hover:text-indigo-300" aria-label="Help" type="button"><CircleHelp className="h-4 w-4" /></button>
          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[#2D3139] bg-[#1C1F26] font-mono text-[10px] text-indigo-200" aria-label="Revenue operations user">RO</div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2 font-mono text-[10px] uppercase tracking-[0.12em] text-slate-300">
        {statuses.map((status) => (
          <span key={status} className="ops-chip border-emerald-500/30 bg-emerald-500/[0.06] text-emerald-200">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            {status}
          </span>
        ))}
        <span className={`ops-chip ${backendAvailable ? 'border-emerald-500/30 text-emerald-200' : 'border-red-500/30 text-red-300'}`}>
          <span className={`h-2 w-2 rounded-full ${backendAvailable ? 'bg-emerald-400' : 'bg-red-400'}`} />
          API {backendAvailable ? 'Connected' : 'Offline'}
        </span>
        <span className="ml-auto text-[#908FA0]">Session {timestamp}</span>
      </div>
    </motion.header>
  )
}
