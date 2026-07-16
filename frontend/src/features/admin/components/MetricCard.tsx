import type { ServiceStatus } from '../types/admin.types'

interface MetricCardProps {
  label: string
  value: string | number
  unit?: string
  change?: number
  changeLabel?: string
  status?: ServiceStatus
  compact?: boolean
}

export function MetricCard({
  label,
  value,
  unit,
  change,
  changeLabel,
  compact,
}: MetricCardProps) {
  const changeColor =
    change === undefined
      ? ''
      : change > 0
        ? 'text-green-400'
        : change < 0
          ? 'text-red-400'
          : 'text-gray-500'

  return (
    <div
      className={`border border-gray-800/50 rounded bg-gray-950 ${
        compact ? 'p-2.5' : 'p-3'
      } hover:border-gray-700/50 transition-colors`}
    >
      <div className="text-[10px] font-mono text-gray-600 uppercase tracking-wider mb-1.5 truncate">
        {label}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span
          className={`font-mono font-bold text-gray-200 ${
            compact ? 'text-lg' : 'text-xl'
          }`}
        >
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {unit && (
          <span className="text-[10px] font-mono text-gray-600">{unit}</span>
        )}
      </div>
      {change !== undefined && (
        <div className={`mt-1 text-[10px] font-mono ${changeColor}`}>
          {change > 0 ? '+' : ''}
          {change.toFixed(1)}%
          {changeLabel && (
            <span className="text-gray-600 ml-1">{changeLabel}</span>
          )}
        </div>
      )}
    </div>
  )
}
