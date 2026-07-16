import type { ServiceStatus } from '../types/admin.types'

interface HealthIndicatorProps {
  status: ServiceStatus
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const STATUS_CONFIG: Record<ServiceStatus, { color: string; label: string; pulse: boolean }> = {
  healthy: { color: 'bg-green-500', label: 'Healthy', pulse: false },
  degraded: { color: 'bg-yellow-500', label: 'Degraded', pulse: true },
  down: { color: 'bg-red-500', label: 'Down', pulse: true },
  unknown: { color: 'bg-gray-500', label: 'Unknown', pulse: false },
}

const SIZES = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-2.5 h-2.5',
}

export function HealthIndicator({ status, size = 'md', showLabel = false }: HealthIndicatorProps) {
  const config = STATUS_CONFIG[status]

  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={`rounded-full ${config.color} ${SIZES[size]} ${
          config.pulse ? 'animate-pulse' : ''
        }`}
      />
      {showLabel && (
        <span className="text-[10px] font-mono text-gray-500">{config.label}</span>
      )}
    </span>
  )
}
