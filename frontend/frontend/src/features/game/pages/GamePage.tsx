import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useAuthStore } from '../../../stores/authStore'
import { useWebSocket } from '../../../hooks/useWebSocket'
import { getRoom } from '../../room/services/roomApi'
import { PhaseBanner } from '../components/PhaseBanner'
import { RoleReveal } from '../components/RoleReveal'
import { ChatPanel } from '../../chat/components/ChatPanel'
import { VotePanel } from '../components/VotePanel'
import { MissionPanel } from '../components/MissionPanel'
import { ScoreBoard } from '../components/ScoreBoard'
import type { RoomResponse } from '../../room/types/room.types'
import type { MissionData, GameScore, VoteResults } from '../../room/types/game.types'

function Timer({ endsAt }: { endsAt: string | null }) {
  const [remaining, setRemaining] = useState<number>(-1)

  useEffect(() => {
    if (!endsAt) {
      setRemaining(-1)
      return
    }

    const update = () => {
      const end = new Date(endsAt).getTime()
      const now = Date.now()
      const diff = Math.max(0, Math.ceil((end - now) / 1000))
      setRemaining(diff)
    }

    update()
    const interval = setInterval(update, 1000)
    return () => clearInterval(interval)
  }, [endsAt])

  if (remaining < 0) return null

  const minutes = Math.floor(remaining / 60)
  const seconds = remaining % 60
  const isLow = remaining <= 10

  return (
    <div className={`text-center mb-4 ${isLow ? 'animate-pulse' : ''}`}>
      <span className={`text-3xl font-mono font-bold tracking-wider ${
        isLow ? 'text-red-500' : 'text-gray-900'
      }`}>
        {minutes}:{seconds.toString().padStart(2, '0')}
      </span>
      <div className="text-[10px] font-mono text-gray-500 mt-1">TIME REMAINING</div>
    </div>
  )
}

export function GamePage() {
  const { code } = useParams<{ code: string }>()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    lastRoomState,
    lastRoleAssignment,
    lastGameState,
    lastPhaseChanged,
    lastGameOver,
    lastMissionAssignment,
    lastMissionProgress,
    lastVoteResults,
    lastVoteCast,
    lastTimerUpdated,
    isConnected,
    chatMessages,
    sendMessage,
  } = useWebSocket(code ?? null)

  const [room, setRoom] = useState<RoomResponse | null>(null)
  const [role, setRole] = useState<string | null>(null)
  const [phase, setPhase] = useState<string>('role_assignment')
  const [round, setRound] = useState(1)
  const [missions, setMissions] = useState<MissionData[]>([])
  const [missionFeedback, setMissionFeedback] = useState<string | null>(null)
  const [finalResult, setFinalResult] = useState<{ winner: string; reason: string; scores?: GameScore[] } | null>(null)
  const [voteResults, setVoteResults] = useState<VoteResults | null>(null)
  const [myVote, setMyVote] = useState<number | null>(null)
  const [timerEndsAt, setTimerEndsAt] = useState<string | null>(null)

  const gamePhase = phase || lastPhaseChanged?.game?.phase || 'role_assignment'
  const gameRound = round || lastPhaseChanged?.game?.round_number || 1
  const isCoordinator = role === 'coordinator'
  const playerList = lastRoomState?.players ?? []
  const gameId = lastRoleAssignment?.game_id ?? lastGameState?.game.id ?? lastGameOver?.game.id ?? 0

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/auth', { replace: true })
    }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    if (!isAuthenticated || !code) return
    getRoom(code).then(setRoom).catch(() => navigate('/lobby', { replace: true }))
  }, [isAuthenticated, code, navigate])

  useEffect(() => {
    if (lastRoomState) setRoom(lastRoomState.room)
  }, [lastRoomState])

  useEffect(() => {
    if (lastRoleAssignment) {
      setRole(lastRoleAssignment.role)
    }
  }, [lastRoleAssignment])

  useEffect(() => {
    if (lastGameState) {
      setPhase(lastGameState.game.phase)
      setRound(lastGameState.game.round_number)
    }
  }, [lastGameState])

  useEffect(() => {
    if (lastPhaseChanged) {
      setPhase('')
      setMissionFeedback(null)
      setVoteResults(null)
      setMyVote(null)
      setTimerEndsAt(null)
      const timer = setTimeout(() => {
        setPhase(lastPhaseChanged.game.phase)
        setRound(lastPhaseChanged.game.round_number)
      }, 50)
      return () => clearTimeout(timer)
    }
  }, [lastPhaseChanged])

  useEffect(() => {
    if (lastTimerUpdated) {
      setTimerEndsAt(lastTimerUpdated.ends_at)
    }
  }, [lastTimerUpdated])

  useEffect(() => {
    if (lastMissionAssignment) {
      setMissions(lastMissionAssignment.missions)
    }
  }, [lastMissionAssignment])

  useEffect(() => {
    if (lastMissionProgress) {
      setMissions((prev) =>
        prev.map((m) =>
          m.id === lastMissionProgress.mission.id
            ? { ...m, current_value: lastMissionProgress.mission.current_value, status: lastMissionProgress.mission.status }
            : m,
        ),
      )
      if (lastMissionProgress.mission.status === 'completed') {
        setMissionFeedback('Mission complete!')
        const timer = setTimeout(() => setMissionFeedback(null), 3000)
        return () => clearTimeout(timer)
      }
    }
  }, [lastMissionProgress])

  useEffect(() => {
    if (lastVoteResults) {
      setVoteResults(lastVoteResults.results)
    }
  }, [lastVoteResults])

  useEffect(() => {
    if (lastVoteCast) {
      setMyVote(lastVoteCast.target_user_id)
    }
  }, [lastVoteCast])

  useEffect(() => {
    if (lastGameOver) {
      setPhase('game_over')
      setRound(lastGameOver.game.round_number)
      setFinalResult({
        winner: lastGameOver.winner,
        reason: lastGameOver.reason,
        scores: lastGameOver.scores,
      })
    }
  }, [lastGameOver])

  const handleSendMessage = useCallback((content: string) => {
    sendMessage({ type: 'SEND_MESSAGE', content })
  }, [sendMessage])

  const handleVote = useCallback((targetUserId: number) => {
    sendMessage({ type: 'CAST_VOTE', payload: { target_user_id: targetUserId } })
  }, [sendMessage])

  if (!isAuthenticated) {
    return null
  }

  if (!room || !code) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-sm font-mono tracking-wider text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> LOADING GAME...
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 bg-grid">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Top bar */}
        <div className="flex items-center justify-between mb-6 animate-fade-in-up">
          <div className="flex items-center gap-3">
            <Link
              to="/lobby"
              className="text-xs font-mono text-gray-600 hover:text-gray-900 transition-colors"
            >
              {'<'} LOBBY
            </Link>
            <span className="text-gray-600">|</span>
            <div className="text-sm font-mono tracking-[0.2em] text-gray-900">{code}</div>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-gray-600">
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500 animate-pulse-dot' : 'bg-red-500'
              }`}
            />
            {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
          </div>
        </div>

        {/* Phase banner */}
        <div className="mb-6 animate-fade-in-up" style={{ animationDelay: '0.1s' }} key={`banner-${gamePhase}-${gameRound}`}>
          <PhaseBanner phase={gamePhase} round={gameRound} />
        </div>

        {/* Player strip — always visible */}
        {playerList.length > 0 && (
          <div className="flex flex-wrap gap-2 items-center mb-4 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
            {playerList.map((p) => (
              <div
                key={p.id}
                className={`px-3 py-1.5 border rounded text-xs font-mono flex items-center gap-1.5 ${
                  p.id === user?.id
                    ? 'border-accent/40 bg-accent/10 text-accent'
                    : 'border-gray-400/30 bg-gray-100 text-gray-700'
                }`}
              >
                <span>{p.username}</span>
                {p.id === user?.id && <span className="opacity-50">(YOU)</span>}
              </div>
            ))}
          </div>
        )}

        {/* Timer */}
        {timerEndsAt && gamePhase !== 'game_over' && gamePhase !== 'voting' && (
          <Timer endsAt={timerEndsAt} />
        )}

        {/* Content */}
        <div className="animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
          {/* ============ ROLE ASSIGNMENT ============ */}
          {gamePhase === 'role_assignment' && role && (
            <div className="space-y-6">
              <RoleReveal role={role} />
              {isCoordinator && missions.length > 0 && <MissionPanel missions={missions} />}
              <div className="h-[300px]">
                {user && (
                  <ChatPanel
                    messages={chatMessages}
                    onSend={handleSendMessage}
                    currentUserId={user.id}
                  />
                )}
              </div>
            </div>
          )}

          {gamePhase === 'role_assignment' && !role && (
            <div className="text-center py-12 text-sm font-mono text-gray-600 animate-pulse">
              <span className="text-accent">{'//'}</span> WAITING FOR ROLE ASSIGNMENT...
            </div>
          )}

          {/* ============ ROUND START ============ */}
          {gamePhase === 'round_start' && (
            <div className="text-center py-16 space-y-4 animate-fade-in">
              <div className="text-lg font-mono font-bold tracking-wider text-gray-900">
                ROUND {gameRound}
              </div>
              <p className="text-sm font-mono text-gray-600 max-w-md mx-auto leading-relaxed">
                The next round is beginning. Get ready to interact and complete your objectives.
              </p>
              {isCoordinator && missions.length > 0 && (
                <div className="max-w-md mx-auto mt-4">
                  <MissionPanel missions={missions} />
                </div>
              )}
            </div>
          )}

          {/* ============ INTERACTION ============ */}
          {gamePhase === 'interaction' && (
            <div className="space-y-4">
              {/* Coordinator mission panel */}
              {isCoordinator && missions.length > 0 && <MissionPanel missions={missions} />}

              {/* Mission feedback toast */}
              {missionFeedback && (
                <div className="p-3 bg-green-900/20 border border-green-500/30 rounded animate-slide-down text-center">
                  <span className="text-xs font-mono text-green-400">{missionFeedback}</span>
                </div>
              )}

              {/* Chat */}
              <div className="h-[400px]">
                {user && (
                  <ChatPanel
                    messages={chatMessages}
                    onSend={handleSendMessage}
                    currentUserId={user.id}
                  />
                )}
              </div>
            </div>
          )}

          {/* ============ DISCUSSION ============ */}
          {gamePhase === 'discussion' && (
            <div className="space-y-4">
              <div className="text-center text-sm font-mono text-gray-600">
                Discuss who you think the Coordinator is.
              </div>

              {/* Chat */}
              <div className="h-[400px]">
                {user && (
                  <ChatPanel
                    messages={chatMessages}
                    onSend={handleSendMessage}
                    currentUserId={user.id}
                  />
                )}
              </div>
            </div>
          )}

          {/* ============ VOTING ============ */}
          {gamePhase === 'voting' && (
            <div className="space-y-4">
              <div className="text-center text-sm font-mono text-gray-600">
                Vote for who you think the Coordinator is.
              </div>
              <VotePanel
                players={playerList}
                currentUserId={user?.id ?? 0}
                onVote={handleVote}
                disabled={gamePhase !== 'voting'}
                targetUserId={myVote}
              />
              {myVote && (
                <div className="text-center text-xs font-mono text-gray-500">
                  Waiting for other players to vote...
                </div>
              )}
            </div>
          )}

          {/* ============ RESULT ============ */}
          {gamePhase === 'result' && (
            <div className="text-center py-16 space-y-4 animate-fade-in">
              <div className="text-sm font-mono tracking-wider text-gray-600">ROUND {gameRound} RESULT</div>
              {isCoordinator && missions.length > 0 && (
                <div className="max-w-md mx-auto">
                  <MissionPanel missions={missions} />
                </div>
              )}

              {/* Vote results */}
              {voteResults && (
                <div className="max-w-md mx-auto">
                  <VotePanel
                    players={playerList}
                    currentUserId={user?.id ?? 0}
                    onVote={() => {}}
                    disabled
                    results={voteResults}
                  />
                </div>
              )}

              {/* Chat */}
              <div className="h-[300px] mt-4">
                {user && (
                  <ChatPanel
                    messages={chatMessages}
                    onSend={handleSendMessage}
                    currentUserId={user.id}
                  />
                )}
              </div>
            </div>
          )}

          {/* ============ GAME OVER ============ */}
          {gamePhase === 'game_over' && (
            <div className="text-center py-16 space-y-6 animate-scale-in">
              <div className="text-xs font-mono tracking-widest text-gray-500">GAME OVER</div>
              {finalResult && (
                <>
                  <div className={`text-2xl font-mono font-bold tracking-wider ${
                    finalResult.winner === 'coordinator' ? 'text-accent' : 'text-cyan-500'
                  }`}>
                    {finalResult.winner === 'coordinator' ? 'COORDINATOR WINS' : 'INVESTIGATION TEAM WINS'}
                  </div>
                  <div className="text-sm font-mono text-gray-600">{finalResult.reason}</div>
                </>
              )}
              <div className="text-sm font-mono text-gray-600">
                Your role was: <strong className="text-gray-900">{role?.toUpperCase()}</strong>
              </div>

              {/* Scores */}
              {finalResult?.scores && finalResult.scores.length > 0 && (
                <div className="max-w-md mx-auto text-left">
                  <div className="text-[10px] font-mono tracking-wider text-gray-500 mb-2 text-center">FINAL SCORES</div>
                  <ScoreBoard players={finalResult.scores} />
                </div>
              )}

              {/* Chat */}
              <div className="h-[300px] mt-4">
                {user && (
                  <ChatPanel
                    messages={chatMessages}
                    onSend={handleSendMessage}
                    currentUserId={user.id}
                  />
                )}
              </div>

              <div className="flex gap-3 justify-center">
                <Link
                  to="/lobby"
                  className="px-6 py-2 border border-gray-400/30 rounded text-sm font-mono text-gray-600 hover:text-gray-900 hover:border-gray-400 transition-all"
                >
                  BACK TO LOBBY
                </Link>
                {gameId > 0 && (
                  <Link
                    to={`/game/${gameId}/analysis`}
                    className="px-6 py-2 border border-accent/50 rounded text-sm font-mono text-accent bg-accent/10 hover:bg-accent/20 transition-all"
                  >
                    VIEW AI ANALYSIS
                  </Link>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
