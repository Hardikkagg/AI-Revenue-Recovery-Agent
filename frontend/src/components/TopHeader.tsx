import { motion } from 'framer-motion'
import { Bell, CircleHelp, Search } from 'lucide-react'

interface TopHeaderProps {
  backendAvailable: boolean | null
  hasAnalysis: boolean
  hasSimulation: boolean
}

export function TopHeader({ backendAvailable }: TopHeaderProps) {
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="border-b border-[#D9E0E7] bg-white px-5 py-4"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="shrink-0">
          <div className="text-xl font-semibold tracking-tight text-[#172033]">Recovery</div>
          <div className="mt-1 text-sm text-[#64748B]">Review failed revenue and take the next approved action.</div>
        </div>

        <div className="flex min-w-0 flex-1 items-center justify-center xl:px-8">
          <label className="relative w-full max-w-md">
            <span className="sr-only">Search cases and strategies</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#908FA0]" />
            <input className="w-full rounded-md border border-[#CBD5E1] bg-white py-2 pl-10 pr-3 text-sm text-[#172033] outline-none placeholder:text-[#94A3B8] focus:border-[#2563EB]" placeholder="Search cases..." type="search" />
          </label>
        </div>

        <div className="flex flex-wrap items-center justify-end gap-2 text-[10px] uppercase tracking-[0.12em] text-slate-300">
          <span className="ops-chip">Production</span>
          <button className="cursor-not-allowed rounded p-2 text-[#908FA0] opacity-60" aria-label="Notifications unavailable" title="Notifications are not configured" type="button" disabled><Bell className="h-4 w-4" /></button>
          <button className="cursor-not-allowed rounded p-2 text-[#908FA0] opacity-60" aria-label="Help unavailable" title="Help is not configured" type="button" disabled><CircleHelp className="h-4 w-4" /></button>
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#E2E8F0] text-xs font-semibold text-[#475569]" aria-label="Revenue operations user">RO</div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-[#64748B]">
          <span className={`ops-chip ${backendAvailable === true ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : backendAvailable === false ? 'border-red-200 bg-red-50 text-red-700' : ''}`}>
            <span className={`h-2 w-2 rounded-full ${backendAvailable === true ? 'bg-emerald-500' : backendAvailable === false ? 'bg-red-500' : 'bg-slate-400'}`} />
            {backendAvailable === true ? 'Connected' : backendAvailable === false ? 'API unavailable' : 'Checking connection'}
        </span>
        <span className="ml-auto">Updated {timestamp}</span>
      </div>
    </motion.header>
  )
}
