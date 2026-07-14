import type { ReplayEvent } from '../types/replay.types'
import { EVENT_CATEGORY_COLORS } from '../types/replay.types'

interface ReplayInspectorProps {
  event: ReplayEvent | null
}

export function ReplayInspector({ event }: ReplayInspectorProps) {
  if (!event) {
    return (
      <div className="border border-gray-300/50 rounded bg-gray-100 p-4 h-full flex items-center justify-center">
        <div className="text-xs font-mono text-gray-500">Select an event to inspect</div>
      </div>
    )
  }

  const colorClass = EVENT_CATEGORY_COLORS[event.category] ?? 'bg-gray-300'

  return (
    <div className="border border-gray-300/50 rounded bg-gray-100 p-4 h-full overflow-y-auto">
      <div className="text-[10px] font-mono text-gray-500 mb-3 tracking-wider">EVENT INSPECTOR</div>

      {/* Event header */}
      <div className="flex items-center gap-2 mb-3">
        <span className={`w-3 h-3 rounded-full ${colorClass}`} />
        <span className="text-sm font-mono font-medium text-gray-900">{event.label}</span>
        <span className="text-[10px] font-mono text-gray-500">#{event.sequence_number}</span>
      </div>

      {/* Metadata */}
      <div className="space-y-2 text-xs font-mono">
        <div className="flex justify-between">
          <span className="text-gray-500">Type</span>
          <span className="text-gray-700">{event.event_type}</span>
        </div>
        {event.actor_name && (
          <div className="flex justify-between">
            <span className="text-gray-500">Actor</span>
            <span className="text-gray-700">{event.actor_name}</span>
          </div>
        )}
        {event.round_number && (
          <div className="flex justify-between">
            <span className="text-gray-500">Round</span>
            <span className="text-gray-700">{event.round_number}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-gray-500">Time</span>
          <span className="text-gray-700">{Math.floor(event.relative_time_seconds)}s</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Timestamp</span>
          <span className="text-gray-700 text-[10px]">
            {new Date(event.timestamp).toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Payload */}
      {Object.keys(event.payload).length > 0 && (
        <div className="mt-4">
          <div className="text-[10px] font-mono text-gray-500 mb-1">PAYLOAD</div>
          <pre className="p-3 bg-gray-200 border border-gray-300/30 rounded text-[11px] font-mono text-gray-700 overflow-x-auto whitespace-pre-wrap break-all">
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        </div>
      )}

      {/* Metadata */}
      {Object.keys(event.metadata).length > 0 && (
        <div className="mt-3">
          <div className="text-[10px] font-mono text-gray-500 mb-1">METADATA</div>
          <pre className="p-3 bg-gray-200 border border-gray-300/30 rounded text-[11px] font-mono text-gray-700 overflow-x-auto whitespace-pre-wrap break-all">
            {JSON.stringify(event.metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
