import type { ReactNode } from 'react'

interface ChartCardProps {
  title: string
  subtitle?: string
  children: ReactNode
  className?: string
  action?: ReactNode
}

export function ChartCard({ title, subtitle, children, className = '', action }: ChartCardProps) {
  return (
    <div
      className={`border border-gray-800/50 rounded bg-gray-950 p-4 ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-[11px] font-mono font-medium text-gray-300 uppercase tracking-wider">
            {title}
          </div>
          {subtitle && (
            <div className="text-[10px] font-mono text-gray-600 mt-0.5">
              {subtitle}
            </div>
          )}
        </div>
        {action}
      </div>
      {children}
    </div>
  )
}
