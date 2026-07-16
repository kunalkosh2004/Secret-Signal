import type { ActivityEvent } from '../types/admin.types'

function timeAgo(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  return `${hours}h ago`
}

const LEVEL_STYLES: Record<string, string> = {
  normal: '',
  highlight: 'border-l-2 border-l-accent/60',
  warning: 'border-l-2 border-l-yellow-500/60',
}

interface ActivityFeedProps {
  events: ActivityEvent[]
  maxItems?: number
}

export function ActivityFeed({ events, maxItems = 20 }: ActivityFeedProps) {
  const displayed = events.slice(0, maxItems)

  return (
    <div className="border border-gray-800/50 rounded bg-gray-950">
      <div className="px-3 py-2 border-b border-gray-800/50 flex items-center justify-between">
        <span className="text-[10px] font-mono text-gray-600 uppercase tracking-wider">
          Live Activity
        </span>
        <span className="text-[10px] font-mono text-gray-700">
          {events.length} events
        </span>
      </div>
      <div className="divide-y divide-gray-800/30 max-h-96 overflow-y-auto">
        {displayed.map((event) => (
          <div
            key={event.id}
            className={`px-3 py-2 hover:bg-gray-800/20 transition-colors ${LEVEL_STYLES[event.level ?? 'normal'] ?? ''}`}
          >
            <div className="flex items-start gap-2">
              <span className="text-xs mt-0.5 shrink-0">{event.icon}</span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono text-gray-300 truncate">
                    {event.label}
                  </span>
                  <span className="text-[9px] font-mono text-gray-600 shrink-0">
                    {timeAgo(event.timestamp)}
                  </span>
                </div>
                {event.details && (
                  <div className="text-[10px] font-mono text-gray-600 mt-0.5 truncate">
                    {Object.entries(event.details)
                      .map(([k, v]) => `${k}=${v}`)
                      .join(' ')}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
