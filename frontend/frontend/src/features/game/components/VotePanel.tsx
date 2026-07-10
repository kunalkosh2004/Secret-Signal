import type { RoomPlayer } from '../../room/types/room.types'
import type { VoteResults } from '../../room/types/game.types'

interface VotePanelProps {
  players: RoomPlayer[]
  currentUserId: number
  onVote: (targetUserId: number) => void
  disabled: boolean
  results?: VoteResults | null
  targetUserId?: number | null
}

export function VotePanel({ players, currentUserId, onVote, disabled, results, targetUserId }: VotePanelProps) {
  const playerMap = new Map(players.map((p) => [p.id, p]))

  if (results) {
    const maxCount = Math.max(...results.tallies.map((t) => t.count), 0)
    const topTallies = results.tallies.filter((t) => t.count === maxCount && t.count > 0)
    const winner = topTallies.length === 1 ? playerMap.get(topTallies[0].target_user_id) : null

    return (
      <div className="space-y-4">
        {/* Winner announcement */}
        {winner ? (
          <div className="border-2 border-amber-500/40 rounded p-4 bg-amber-900/10 animate-scale-in text-center">
            <div className="text-xs font-mono tracking-wider text-amber-600 mb-2">VOTED OUT</div>
            <div className="flex items-center justify-center gap-3">
              <div className="w-10 h-10 rounded-full bg-amber-200 flex items-center justify-center text-lg font-mono font-bold text-amber-800">
                {winner.username.charAt(0).toUpperCase()}
              </div>
              <span className="text-lg font-mono font-bold text-amber-900">{winner.username}</span>
            </div>
            <div className="text-[10px] font-mono text-amber-600 mt-1">{maxCount} vote{maxCount !== 1 ? 's' : ''}</div>
          </div>
        ) : (
          <div className="border border-gray-400/30 rounded p-4 bg-gray-100/50 text-center">
            <div className="text-xs font-mono text-gray-600">NO ONE WAS VOTED OUT</div>
            {results.tallies.length === 0 && (
              <div className="text-[10px] font-mono text-gray-500 mt-1">No votes were cast</div>
            )}
          </div>
        )}

        {/* Tally bars */}
        <div className="border border-gray-400/30 rounded p-4 space-y-3">
          <div className="text-xs font-mono tracking-wider text-gray-600">
            VOTE TALLY — {results.total_votes} total
          </div>
          <div className="space-y-2">
            {results.tallies.map((tally) => {
              const player = playerMap.get(tally.target_user_id)
              const isTop = tally.count === maxCount && tally.count > 0
              return (
                <div
                  key={tally.target_user_id}
                  className={`flex items-center justify-between px-3 py-2 rounded ${
                    isTop ? 'bg-amber-900/20 border border-amber-500/30' : 'bg-gray-100/50 border border-gray-400/10'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-sm font-mono font-bold text-gray-700">
                      {(player?.username ?? '?').charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm font-mono text-gray-900">
                      {player?.username ?? `User #${tally.target_user_id}`}
                    </span>
                    {isTop && <span className="text-[10px] font-mono text-amber-600">MOST VOTES</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-500/60 rounded-full transition-all"
                        style={{ width: `${maxCount > 0 ? (tally.count / maxCount) * 100 : 0}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono font-bold text-gray-700 w-4 text-right">
                      {tally.count}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    )
  }

  const others = players.filter((p) => p.id !== currentUserId)

  return (
    <div className="border border-gray-400/30 rounded overflow-hidden">
      <div className="bg-gray-100 px-4 py-2 border-b border-gray-400/20">
        <span className="text-xs font-mono tracking-wider text-gray-600">CAST YOUR VOTE</span>
        {targetUserId && (
          <span className="text-xs font-mono text-green-600 ml-3">&#10003; Vote recorded</span>
        )}
      </div>
      <div className="divide-y divide-gray-400/10">
        {others.map((p) => {
          const isSelected = p.id === targetUserId
          return (
            <button
              key={p.id}
              onClick={() => onVote(p.id)}
              disabled={disabled || !!targetUserId}
              className={`w-full flex items-center justify-between px-4 py-3 transition-colors ${
                isSelected
                  ? 'bg-green-900/10 border-l-2 border-green-500'
                  : 'hover:bg-gray-100/80 border-l-2 border-transparent'
              } disabled:opacity-60 disabled:cursor-not-allowed`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-mono font-bold ${
                    isSelected ? 'bg-green-200 text-green-800' : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  {p.username.charAt(0).toUpperCase()}
                </div>
                <span className="text-sm font-mono text-gray-900">{p.username}</span>
              </div>
              <span
                className={`text-xs font-mono ${
                  isSelected ? 'text-green-600 font-bold' : 'text-gray-600'
                }`}
              >
                {isSelected ? 'VOTED' : 'VOTE'}
              </span>
            </button>
          )
        })}
        {others.length === 0 && (
          <div className="px-4 py-6 text-center text-xs font-mono text-gray-600">
            No other players to vote for
          </div>
        )}
      </div>
    </div>
  )
}
