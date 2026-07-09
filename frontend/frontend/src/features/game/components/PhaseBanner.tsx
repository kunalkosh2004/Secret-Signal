interface PhaseBannerProps {
  phase: string
  round: number
  key?: string
}

const PHASE_LABELS: Record<string, string> = {
  role_assignment: 'ROLE ASSIGNMENT',
  round_start: 'ROUND START',
  interaction: 'INTERACTION',
  evaluation: 'EVALUATION',
  discussion: 'DISCUSSION',
  voting: 'VOTING',
  result: 'RESULT',
  game_over: 'GAME OVER',
}

const PHASE_COLORS: Record<string, string> = {
  role_assignment: 'border-yellow-500/40 bg-yellow-500/10 text-yellow-500',
  round_start: 'border-blue-500/40 bg-blue-500/10 text-blue-500',
  interaction: 'border-cyan-500/40 bg-cyan-500/10 text-cyan-500',
  evaluation: 'border-purple-500/40 bg-purple-500/10 text-purple-500',
  discussion: 'border-orange-500/40 bg-orange-500/10 text-orange-500',
  voting: 'border-red-500/40 bg-red-500/10 text-red-500',
  result: 'border-green-500/40 bg-green-500/10 text-green-500',
  game_over: 'border-gray-500/40 bg-gray-500/10 text-gray-500',
}

export function PhaseBanner({ phase, round }: PhaseBannerProps) {
  const label = PHASE_LABELS[phase] ?? phase.toUpperCase()
  const colors = PHASE_COLORS[phase] ?? 'border-gray-500/40 bg-gray-500/10 text-gray-500'

  return (
    <div className={`rounded px-4 py-3 border ${colors} animate-phase-enter`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono tracking-wider">PHASE</span>
          <span className="w-px h-4 bg-current opacity-30" />
          <span className="text-sm font-mono font-bold tracking-wider">{label}</span>
        </div>
        <span className="text-xs font-mono opacity-70">ROUND {round}</span>
      </div>
    </div>
  )
}
