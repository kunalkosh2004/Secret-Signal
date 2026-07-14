import type { ReactNode } from 'react'

interface SectionHeaderProps {
  title: string
  subtitle?: string
  action?: ReactNode
}

export function SectionHeader({ title, subtitle, action }: SectionHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-3">
      <div>
        <h2 className="text-[11px] font-mono font-bold text-gray-300 uppercase tracking-wider">
          {title}
        </h2>
        {subtitle && (
          <p className="text-[10px] font-mono text-gray-600 mt-0.5">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  )
}
