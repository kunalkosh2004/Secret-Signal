import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuthStore } from '../../../stores/authStore'
import { getGameAnalysis } from '../services/analysisApi'
import type { GameAnalysis, PlayerAnalysis } from '../types/analysis.types'
import { ScoreBoard } from '../../game/components/ScoreBoard'

function SuspicionBar({ score, label }: { score: number; label: string }) {
  const color =
    score > 60
      ? 'bg-red-500'
      : score > 35
        ? 'bg-yellow-500'
        : score > 15
          ? 'bg-blue-500'
          : 'bg-green-500'

  return (
    <div className="flex items-center gap-3">
      <span className="w-20 text-xs font-mono text-gray-700 truncate">{label}</span>
      <div className="flex-1 h-4 bg-gray-200 border border-gray-300/50 rounded overflow-hidden">
        <div
          className={`h-full ${color} transition-all duration-700`}
          style={{ width: `${Math.min(100, score)}%` }}
        />
      </div>
      <span className="w-12 text-right text-xs font-mono text-gray-600">
        {score.toFixed(1)}%
      </span>
    </div>
  )
}

function PlayerCard({ player, playerName }: { player: PlayerAnalysis; playerName: string }) {
  return (
    <div className="p-4 border border-gray-300/50 rounded bg-gray-100">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 bg-accent rounded-full" />
          <span className="text-sm font-mono font-medium text-gray-900">{playerName}</span>
          <span className="text-[10px] font-mono text-gray-500 uppercase">({player.role})</span>
        </div>
        <span className="text-xs font-mono text-gray-600">{player.message_count} msgs</span>
      </div>

      <SuspicionBar score={player.suspicion_score} label="Suspicion" />

      <div className="mt-3 grid grid-cols-3 gap-2">
        <div className="text-center p-2 bg-gray-200 border border-gray-300/30 rounded">
          <div className="text-lg font-mono font-bold text-gray-900">{player.questions_asked}</div>
          <div className="text-[10px] font-mono text-gray-600">Questions</div>
        </div>
        <div className="text-center p-2 bg-gray-200 border border-gray-300/30 rounded">
          <div className="text-lg font-mono font-bold text-gray-900">{player.topic_initiations}</div>
          <div className="text-[10px] font-mono text-gray-600">Topic Shifts</div>
        </div>
        <div className="text-center p-2 bg-gray-200 border border-gray-300/30 rounded">
          <div className="text-lg font-mono font-bold text-gray-900">
            {(player.voting_accuracy * 100).toFixed(0)}%
          </div>
          <div className="text-[10px] font-mono text-gray-600">Vote Accuracy</div>
        </div>
      </div>

      {player.round_breakdown.length > 0 && (
        <div className="mt-3">
          <div className="text-[10px] font-mono text-gray-500 mb-1">MESSAGE ACTIVITY</div>
          <div className="flex gap-1">
            {player.round_breakdown.map((r) => (
                <div
                  key={r.round}
                  className="flex-1 h-10 bg-gray-200 border border-gray-300/30 rounded relative overflow-hidden"
                  title={`Round ${r.round}: ${r.message_count} msgs, ${r.questions} questions`}
                >
                  <div
                    className="absolute bottom-0 w-full bg-accent transition-all duration-500"
                    style={{ height: `${Math.min(100, (r.message_count / 8) * 100)}%` }}
                  />
                  <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono font-bold text-gray-900 z-10">
                    {r.message_count}
                  </span>
                </div>
            ))}
          </div>
          <div className="flex gap-1 mt-0.5">
            {player.round_breakdown.map((r) => (
              <div key={r.round} className="flex-1 text-center text-[8px] font-mono text-gray-500">
                R{r.round}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export function AnalysisPage() {
  const { gameId } = useParams<{ gameId: string }>()
  const { isAuthenticated } = useAuthStore()
  const [analysis, setAnalysis] = useState<GameAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    if (!gameId) return

    setLoading(true)
    setError(null)
    getGameAnalysis(Number(gameId))
      .then(setAnalysis)
      .catch((err) => setError(err.message ?? 'Failed to load analysis'))
      .finally(() => setLoading(false))
  }, [gameId, isAuthenticated])

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-sm font-mono text-gray-600">Please log in to view analysis.</div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-sm font-mono tracking-wider text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> ANALYZING GAME DATA...
        </div>
      </div>
    )
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="text-sm font-mono text-red-500">{error ?? 'Analysis not available'}</div>
          <Link
            to="/lobby"
            className="inline-block px-6 py-2 border border-gray-400/30 rounded text-sm font-mono text-gray-600 hover:text-gray-900 hover:border-gray-400 transition-all"
          >
            BACK TO LOBBY
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 bg-grid">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8 animate-fade-in-up">
          <div>
            <Link
              to="/lobby"
              className="text-xs font-mono text-gray-600 hover:text-gray-900 transition-colors"
            >
              {'<'} LOBBY
            </Link>
            <h1 className="mt-2 text-xl font-mono font-bold tracking-wider text-gray-900">
              <span className="text-accent">&gt;</span> POST-GAME ANALYSIS
            </h1>
            <p className="mt-1 text-xs font-mono text-gray-500">
              Game #{analysis.game_id} &middot; {analysis.total_rounds} rounds &middot;{' '}
              {analysis.completed_missions} missions completed
            </p>
          </div>
          <div className={`px-4 py-2 border rounded text-sm font-mono font-bold tracking-wider ${
            analysis.winner === 'coordinator'
              ? 'border-accent/50 text-accent bg-accent/10'
              : 'border-cyan-500/50 text-cyan-600 bg-cyan-500/10'
          }`}>
            {analysis.winner === 'coordinator' ? 'COORDINATOR WINS' : 'INVESTIGATION TEAM WINS'}
          </div>
        </div>

        {/* Summary */}
        <div className="mb-8 p-4 border border-gray-300/50 rounded bg-gray-100 animate-fade-in-up" style={{ animationDelay: '0.05s' }}>
          <div className="text-[10px] font-mono text-gray-500 mb-2 tracking-wider">AI SUMMARY</div>
          <p className="text-sm font-mono text-gray-700 leading-relaxed">{analysis.summary}</p>
          <div className="mt-3">
            <SuspicionBar score={analysis.coordination_score} label="Coordination" />
          </div>
        </div>

        {/* Scores */}
        <div className="mb-8 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          <h2 className="text-sm font-mono tracking-wider text-gray-700 mb-3">FINAL SCORES</h2>
          <ScoreBoard
            players={analysis.players.map((p) => ({
              user_id: p.user_id,
              role: p.role,
              username: p.username,
              score: p.score,
            }))}
          />
        </div>

        {/* Player Analysis */}
        <div className="space-y-4 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
          <h2 className="text-sm font-mono tracking-wider text-gray-700">PLAYER BEHAVIOR PROFILES</h2>
          {analysis.players
            .sort((a, b) => b.suspicion_score - a.suspicion_score)
            .map((player) => (
              <PlayerCard
                key={player.user_id}
                player={player}
                playerName={player.username}
              />
            ))}
        </div>

        {/* Voting Patterns */}
        <div className="mt-8 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <h2 className="text-sm font-mono tracking-wider text-gray-700 mb-3">VOTING PATTERNS</h2>
          <div className="space-y-2">
            {Object.entries(analysis.voting_patterns).map(([round, votes]) => (
              <div key={round} className="p-3 border border-gray-300/50 rounded bg-gray-100">
                <div className="text-[10px] font-mono text-gray-500 mb-2">ROUND {round}</div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(votes).map(([userId, count]) => {
                    const voter = analysis.players.find(p => p.user_id === Number(userId))
                    return (
                      <div
                        key={userId}
                        className="px-3 py-1 border border-gray-400/30 rounded bg-gray-200 text-xs font-mono text-gray-700"
                      >
                        {voter?.username ?? `Player ${userId}`}: {count} vote{count !== 1 ? 's' : ''}
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Back to Lobby */}
        <div className="mt-8 text-center animate-fade-in-up" style={{ animationDelay: '0.25s' }}>
          <div className="flex items-center justify-center gap-3">
            <Link
              to="/lobby"
              className="inline-block px-6 py-2 border border-gray-400/30 rounded text-sm font-mono text-gray-600 hover:text-gray-900 hover:border-gray-400 transition-all"
            >
              BACK TO LOBBY
            </Link>
            <Link
              to={`/game/${analysis.game_id}/replay`}
              className="inline-block px-6 py-2 border border-accent/50 rounded text-sm font-mono text-accent hover:bg-accent hover:text-white transition-all"
            >
              VIEW REPLAY
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
