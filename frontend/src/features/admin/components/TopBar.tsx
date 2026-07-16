interface AdminTopBarProps {
  title: string
  subtitle?: string
  actions?: React.ReactNode
}

export function AdminTopBar({ title, subtitle, actions }: AdminTopBarProps) {
  return (
    <header className="flex items-center justify-between h-10 px-4 border-b border-gray-800/50 bg-gray-950/80 shrink-0">
      <div className="flex items-center gap-3 min-w-0">
        <h1 className="text-xs font-mono font-bold tracking-wider text-gray-300 uppercase truncate">
          {title}
        </h1>
        {subtitle && (
          <span className="text-[10px] font-mono text-gray-600 hidden sm:inline">
            {subtitle}
          </span>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {actions}
        <div className="flex items-center gap-1.5 pl-2 border-l border-gray-800/50">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          <span className="text-[10px] font-mono text-gray-500">LIVE</span>
        </div>
      </div>
    </header>
  )
}
