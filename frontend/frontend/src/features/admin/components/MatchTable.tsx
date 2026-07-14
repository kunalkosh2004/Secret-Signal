import { useNavigate } from 'react-router-dom'
import type { ActiveMatch, GamePhase } from '../types/admin.types'

const PHASE_LABELS: Record<GamePhase, string> = {
  role_assignment: 'ROLE ASGN',
  round_start: 'ROUND ST',
  interaction: 'INTERACT',
  discussion: 'DISCUSS',
  voting: 'VOTING',
  result: 'RESULT',
  game_over: 'OVER',
}

const PHASE_COLORS: Record<GamePhase, string> = {
  role_assignment: 'text-purple-400',
  round_start: 'text-blue-400',
  interaction: 'text-green-400',
  discussion: 'text-yellow-400',
  voting: 'text-red-400',
  result: 'text-cyan-400',
  game_over: 'text-gray-400',
}

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

interface MatchTableProps {
  matches: ActiveMatch[]
}

export function MatchTable({ matches }: MatchTableProps) {
  const navigate = useNavigate()

  return (
    <div className="border border-gray-800/50 rounded bg-gray-950 overflow-hidden">
      <div className="px-3 py-2 border-b border-gray-800/50">
        <span className="text-[10px] font-mono text-gray-600 uppercase tracking-wider">
          Active Matches
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left" role="table">
          <thead>
            <tr className="border-b border-gray-800/50">
              <th className="px-3 py-2 text-[9px] font-mono text-gray-600 uppercase tracking-wider">
                Room
              </th>
              <th className="px-3 py-2 text-[9px] font-mono text-gray-600 uppercase tracking-wider">
                Players
              </th>
              <th className="px-3 py-2 text-[9px] font-mono text-gray-600 uppercase tracking-wider">
                Round
              </th>
              <th className="px-3 py-2 text-[9px] font-mono text-gray-600 uppercase tracking-wider">
                Phase
              </th>
              <th className="px-3 py-2 text-[9px] font-mono text-gray-600 uppercase tracking-wider">
                Elapsed
              </th>
              <th className="px-3 py-2 text-[9px] font-mono text-gray-600 uppercase tracking-wider">
                Latency
              </th>
              <th className="px-3 py-2 text-[9px] font-mono text-gray-600 uppercase tracking-wider">
                AI
              </th>
              <th className="px-3 py-2 text-[9px] font-mono text-gray-600 uppercase tracking-wider">
                Replay
              </th>
            </tr>
          </thead>
          <tbody>
            {matches.map((match) => (
              <tr
                key={match.game_id}
                onClick={() => navigate(`/admin/matches/${match.game_id}`)}
                className="border-b border-gray-800/30 hover:bg-gray-800/20 cursor-pointer transition-colors"
              >
                <td className="px-3 py-2">
                  <span className="text-[11px] font-mono text-accent font-medium">
                    {match.room_code}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <div className="flex gap-1">
                    {match.players.map((p: { user_id: number; username: string; role: string; is_alive: boolean }) => (
                      <span
                        key={p.user_id}
                        className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          p.role === 'coordinator'
                            ? 'bg-red-500/10 text-red-400'
                            : 'bg-gray-800 text-gray-400'
                        } ${!p.is_alive ? 'opacity-40 line-through' : ''}`}
                        title={`${p.username} (${p.role})`}
                      >
                        {p.username.slice(0, 3)}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-3 py-2">
                  <span className="text-[11px] font-mono text-gray-400">
                    {match.current_round}/{match.total_rounds}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <span
                    className={`text-[10px] font-mono font-medium ${PHASE_COLORS[match.current_phase]}`}
                  >
                    {PHASE_LABELS[match.current_phase]}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <span className="text-[11px] font-mono text-gray-400">
                    {formatElapsed(match.elapsed_seconds)}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <span className="text-[11px] font-mono text-gray-400">
                    {match.avg_latency_ms}ms
                  </span>
                </td>
                <td className="px-3 py-2">
                  <span className="text-[11px] font-mono text-gray-400">
                    {match.signal_ai_usage}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <span
                    className={`text-[10px] font-mono ${
                      match.replay_available ? 'text-green-400' : 'text-gray-600'
                    }`}
                  >
                    {match.replay_available ? 'YES' : 'PENDING'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
