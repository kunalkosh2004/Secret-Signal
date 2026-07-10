import type { GameScore } from '../../room/types/game.types'

interface ScoreBoardProps {
  players: GameScore[]
}

export function ScoreBoard({ players }: ScoreBoardProps) {
  const sorted = [...players].sort((a, b) => b.score - a.score)

  return (
    <div className="space-y-2">
      {sorted.map((player, index) => (
        <div
          key={player.user_id}
          className="flex items-center gap-3 p-3 border border-gray-300/50 rounded bg-gray-100"
        >
          <span className="w-6 text-center text-xs font-mono font-bold text-gray-400">
            {index === 0 ? '1st' : index === 1 ? '2nd' : index === 2 ? '3rd' : `${index + 1}th`}
          </span>
          <span className="w-2 h-2 rounded-full bg-accent" />
          <span className="text-sm font-mono text-gray-900 flex-1">
            Player {player.user_id}
          </span>
          <span className="text-[10px] font-mono text-gray-500 uppercase mr-4">
            {player.role}
          </span>
          <span className="text-sm font-mono font-bold text-gray-900">
            {player.score} pts
          </span>
        </div>
      ))}
    </div>
  )
}
