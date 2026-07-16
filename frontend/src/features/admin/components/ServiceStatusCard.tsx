import type { ServiceStatus } from '../types/admin.types'

const STATUS_STYLES: Record<ServiceStatus, { dot: string; text: string; border: string }> = {
  healthy: {
    dot: 'bg-green-500',
    text: 'text-green-400',
    border: 'border-green-500/20',
  },
  degraded: {
    dot: 'bg-yellow-500',
    text: 'text-yellow-400',
    border: 'border-yellow-500/20',
  },
  down: {
    dot: 'bg-red-500',
    text: 'text-red-400',
    border: 'border-red-500/20',
  },
  unknown: {
    dot: 'bg-gray-500',
    text: 'text-gray-400',
    border: 'border-gray-500/20',
  },
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  if (days > 0) return `${days}d ${hours}h`
  return `${hours}h ${Math.floor((seconds % 3600) / 60)}m`
}

interface ServiceStatusCardProps {
  name: string
  status: ServiceStatus
  latency_ms: number
  version: string
  uptime_seconds: number
  deployment_target?: string
}

export function ServiceStatusCard({
  name,
  status,
  latency_ms,
  version,
  uptime_seconds,
  deployment_target,
}: ServiceStatusCardProps) {
  const style = STATUS_STYLES[status]

  return (
    <div
      className={`border rounded bg-gray-950 p-3 hover:border-gray-700/50 transition-colors ${style.border}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${style.dot}`} />
          <span className="text-[11px] font-mono font-medium text-gray-300 truncate">
            {name}
          </span>
        </div>
        <span className={`text-[10px] font-mono uppercase ${style.text}`}>
          {status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px] font-mono">
        <div className="flex justify-between">
          <span className="text-gray-600">Latency</span>
          <span className="text-gray-400">{latency_ms}ms</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Version</span>
          <span className="text-gray-400">{version}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Uptime</span>
          <span className="text-gray-400">{formatUptime(uptime_seconds)}</span>
        </div>
        {deployment_target && (
          <div className="flex justify-between">
            <span className="text-gray-600">Deploy</span>
            <span className="text-gray-400 truncate">{deployment_target}</span>
          </div>
        )}
      </div>
    </div>
  )
}
