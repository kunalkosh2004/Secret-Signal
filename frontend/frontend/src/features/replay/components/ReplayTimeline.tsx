import type { ReplayEvent } from '../types/replay.types'
import { EVENT_CATEGORY_COLORS, EVENT_CATEGORY_ICONS } from '../types/replay.types'

interface ReplayTimelineProps {
  events: ReplayEvent[]
  currentIndex: number
  onSelectEvent: (index: number) => void
  totalRounds: number
}

export function ReplayTimeline({ events, currentIndex, onSelectEvent, totalRounds }: ReplayTimelineProps) {
  const currentEvent = events[currentIndex]
  const currentRound = currentEvent?.round_number ?? 0

  return (
    <div className="border border-gray-300/50 rounded bg-gray-100 p-4">
      <div className="text-[10px] font-mono text-gray-500 mb-3 tracking-wider">TIMELINE</div>

      {/* Round markers */}
      <div className="flex gap-1 mb-2">
        {Array.from({ length: totalRounds }, (_, i) => i + 1).map((round) => (
          <button
            key={round}
            onClick={() => {
              const idx = events.findIndex((e) => e.round_number === round)
              if (idx >= 0) onSelectEvent(idx)
            }}
            className={`px-3 py-1 rounded text-xs font-mono transition-all ${
              currentRound === round
                ? 'bg-accent text-white'
                : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
            }`}
          >
            R{round}
          </button>
        ))}
      </div>

      {/* Event strip */}
      <div className="overflow-x-auto pb-2">
        <div className="flex gap-0.5 min-w-max">
          {events.map((event, idx) => {
            const colorClass = EVENT_CATEGORY_COLORS[event.category] ?? 'bg-gray-300'
            const isActive = idx === currentIndex
            return (
              <button
                key={event.sequence_number}
                onClick={() => onSelectEvent(idx)}
                title={`${event.label} — ${event.actor_name ?? 'System'}`}
                className={`w-3 h-8 rounded-sm transition-all hover:scale-y-110 ${
                  isActive ? `${colorClass} ring-2 ring-accent ring-offset-1` : colorClass
                }`}
              />
            )
          })}
        </div>
      </div>

      {/* Current event info */}
      {currentEvent && (
        <div className="mt-3 p-3 bg-gray-200 border border-gray-300/30 rounded">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm">{EVENT_CATEGORY_ICONS[currentEvent.category] ?? '\u2022'}</span>
            <span className="text-xs font-mono font-medium text-gray-900">{currentEvent.label}</span>
            <span className="text-[10px] font-mono text-gray-500">#{currentEvent.sequence_number}</span>
          </div>
          <div className="text-[10px] font-mono text-gray-600">
            {currentEvent.actor_name ?? 'System'}
            {currentEvent.round_number ? ` \u00B7 Round ${currentEvent.round_number}` : ''}
            {currentEvent.relative_time_seconds > 0
              ? ` \u00B7 ${Math.floor(currentEvent.relative_time_seconds)}s`
              : ''}
          </div>
        </div>
      )}
    </div>
  )
}
