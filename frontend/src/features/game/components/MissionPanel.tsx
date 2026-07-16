import type { MissionData } from '../../room/types/game.types'

interface MissionPanelProps {
  missions: MissionData[]
}

export function MissionPanel({ missions }: MissionPanelProps) {
  if (missions.length === 0) return null

  return (
    <div className="border border-accent/30 rounded overflow-hidden animate-fade-in">
      <div className="bg-accent/10 px-4 py-2 border-b border-accent/20 flex items-center justify-between">
        <span className="text-xs font-mono tracking-wider text-accent">YOUR MISSION</span>
        <span className="text-[10px] font-mono text-accent/60">COORDINATOR — PRIVATE</span>
      </div>
      <div className="divide-y divide-accent/10">
        {missions.map((m) => {
          const progress = m.target_value > 0 ? Math.round((m.current_value / m.target_value) * 100) : 0
          const done = m.status === 'completed'
          return (
            <div key={m.id} className="px-4 py-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono text-gray-900">{m.title}</span>
                <span className={`text-xs font-mono ${done ? 'text-green-500' : 'text-accent'}`}>
                  {done ? 'COMPLETE' : `${m.current_value}/${m.target_value}`}
                </span>
              </div>
              <p className="text-xs font-mono text-gray-600 leading-relaxed">{m.description}</p>
              <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${done ? 'bg-green-500' : 'bg-accent'}`}
                  style={{ width: `${Math.min(progress, 100)}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
