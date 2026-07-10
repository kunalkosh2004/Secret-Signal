import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useAuthStore } from '../../../stores/authStore'
import { useWebSocket } from '../../../hooks/useWebSocket'
import { getRoom } from '../../room/services/roomApi'
import { advancePhase } from '../../room/services/gameApi'
import { PhaseBanner } from '../components/PhaseBanner'
import { RoleReveal } from '../components/RoleReveal'
import { ChatPanel } from '../../chat/components/ChatPanel'
import { VotePanel } from '../components/VotePanel'
import { MissionPanel } from '../components/MissionPanel'
import type { RoomResponse } from '../../room/types/room.types'
import type { MissionData } from '../../room/types/game.types'

const PHASE_FLOW: Record<string, string | null> = {
  role_assignment: 'round_start',
  round_start: 'interaction',
  interaction: 'evaluation',
  evaluation: 'discussion',
  discussion: 'voting',
  voting: 'result',
  result: null, // host chooses: advance to round_start or game_over
}

import type { VoteResults } from '../../room/types/game.types'

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
  const [finalResult, setFinalResult] = useState<{ winner: string; reason: string } | null>(null)
  const [voteResults, setVoteResults] = useState<VoteResults | null>(null)
  const [myVote, setMyVote] = useState<number | null>(null)
  const [advancing, setAdvancing] = useState(false)

  // Derived values (defined before effects that reference them)
  const gamePhase = phase || lastPhaseChanged?.game?.phase || 'role_assignment'
  const gameRound = round || lastPhaseChanged?.game?.round_number || 1
  const isHost = user?.id === room?.host_id
  const isCoordinator = role === 'coordinator'
  const playerList = lastRoomState?.players ?? []
  const gameId = lastRoleAssignment?.game_id ?? lastGameState?.game.id ?? lastGameOver?.game.id ?? 0

  // Redirect to auth if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/auth', { replace: true })
    }
  }, [isAuthenticated, navigate])

  // Fetch room metadata
  useEffect(() => {
    if (!isAuthenticated || !code) return
    getRoom(code).then(setRoom).catch(() => navigate('/lobby', { replace: true }))
  }, [isAuthenticated, code, navigate])

  // Update room state from WS
  useEffect(() => {
    if (lastRoomState) setRoom(lastRoomState.room)
  }, [lastRoomState])

  // Handle private role assignment (only set role — phase/round managed by GAME_STATE)
  useEffect(() => {
    if (lastRoleAssignment) {
      setRole(lastRoleAssignment.role)
    }
  }, [lastRoleAssignment])

  // Sync phase/round from GAME_STATE (covers initial connect + reconnect)
  useEffect(() => {
    if (lastGameState) {
      setPhase(lastGameState.game.phase)
      setRound(lastGameState.game.round_number)
    }
  }, [lastGameState])

  // Handle phase changes
  useEffect(() => {
    if (lastPhaseChanged) {
      setPhase('')
      setMissionFeedback(null)
      setVoteResults(null)
      setMyVote(null)
      setAdvancing(false)
      const timer = setTimeout(() => {
        setPhase(lastPhaseChanged.game.phase)
        setRound(lastPhaseChanged.game.round_number)
      }, 50)
      return () => clearTimeout(timer)
    }
  }, [lastPhaseChanged])

  // Handle mission assignment
  useEffect(() => {
    if (lastMissionAssignment) {
      setMissions(lastMissionAssignment.missions)
    }
  }, [lastMissionAssignment])

  // Handle mission progress
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

  // Handle vote results
  useEffect(() => {
    if (lastVoteResults) {
      setVoteResults(lastVoteResults.results)
    }
  }, [lastVoteResults])

  // Track own vote
  useEffect(() => {
    if (lastVoteCast) {
      setMyVote(lastVoteCast.target_user_id)
    }
  }, [lastVoteCast])

  // Auto-advance from role_assignment → round_start after 6s (role reveal animation)
  useEffect(() => {
    if (!isHost || gamePhase !== 'role_assignment' || !role) return
    const timer = setTimeout(() => {
      const next = PHASE_FLOW['role_assignment']
      if (!next || !gameId) return
      setAdvancing(true)
      advancePhase(gameId, next).then(() => setAdvancing(false)).catch(() => setAdvancing(false))
    }, 6000)
    return () => clearTimeout(timer)
  }, [isHost, gamePhase, role, gameId])

  // Handle game over
  useEffect(() => {
    if (lastGameOver) {
      setPhase('game_over')
      setRound(lastGameOver.game.round_number)
      setFinalResult({ winner: lastGameOver.winner, reason: lastGameOver.reason })
    }
  }, [lastGameOver])

  const handleSendMessage = useCallback((content: string) => {
    sendMessage({ type: 'SEND_MESSAGE', content })
  }, [sendMessage])

  const handleVote = useCallback((targetUserId: number) => {
    sendMessage({ type: 'CAST_VOTE', payload: { target_user_id: targetUserId } })
  }, [sendMessage])

  const handleAdvancePhase = async () => {
    const nextPhase = PHASE_FLOW[phase]
    if (!nextPhase || !gameId) return
    setAdvancing(true)
    try {
      await advancePhase(gameId, nextPhase)
    } catch {
      // Phase change will come via WS on success
    }
    setAdvancing(false)
  }

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
              {isHost && (
                <button
                  onClick={handleAdvancePhase}
                  disabled={advancing}
                  className="mt-6 px-6 py-2 border border-accent/50 rounded text-sm font-mono text-gray-900 bg-accent/10 hover:bg-accent/20 disabled:opacity-40 transition-all"
                >
                  START INTERACTION
                </button>
              )}
            </div>
          )}

          {/* ============ INTERACTION ============ */}
          {gamePhase === 'interaction' && (
            <div className="space-y-4">
              {/* Player strip */}
              <div className="flex flex-wrap gap-2 items-center">
                {playerList.map((p) => (
                  <div
                    key={p.id}
                    className="px-3 py-1.5 border border-gray-400/30 rounded bg-gray-100 text-xs font-mono flex items-center gap-1.5"
                  >
                    <span className="text-gray-900">{p.username}</span>
                    {p.id === user?.id && <span className="text-gray-500">(YOU)</span>}
                  </div>
                ))}
              </div>

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

              {/* Host controls */}
              {isHost && (
                <div className="flex justify-center">
                  <button
                    onClick={handleAdvancePhase}
                    disabled={advancing}
                    className="px-6 py-2 border border-accent/50 rounded text-sm font-mono text-gray-900 bg-accent/10 hover:bg-accent/20 disabled:opacity-40 transition-all"
                  >
                    END INTERACTION
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ============ EVALUATION ============ */}
          {gamePhase === 'evaluation' && (
            <div className="text-center py-16 space-y-4 animate-fade-in">
              <div className="text-sm font-mono tracking-wider text-gray-600">
                EVALUATION
              </div>
              <p className="text-sm font-mono text-gray-600 max-w-md mx-auto leading-relaxed">
                Missions are being evaluated. Discuss with other players before the voting phase.
              </p>
              {isCoordinator && missions.length > 0 && <MissionPanel missions={missions} />}

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

              {isHost && (
                <button
                  onClick={handleAdvancePhase}
                  disabled={advancing}
                  className="mt-4 px-6 py-2 border border-accent/50 rounded text-sm font-mono text-gray-900 bg-accent/10 hover:bg-accent/20 disabled:opacity-40 transition-all"
                >
                  START DISCUSSION
                </button>
              )}
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

              {isHost && (
                <div className="flex justify-center">
                  <button
                    onClick={handleAdvancePhase}
                    disabled={advancing}
                    className="px-6 py-2 border border-accent/50 rounded text-sm font-mono text-gray-900 bg-accent/10 hover:bg-accent/20 disabled:opacity-40 transition-all"
                  >
                    START VOTING
                  </button>
                </div>
              )}
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
              {isHost && (
                <div className="flex justify-center">
                  <button
                    onClick={handleAdvancePhase}
                    disabled={advancing}
                    className="px-6 py-2 border border-accent/50 rounded text-sm font-mono text-gray-900 bg-accent/10 hover:bg-accent/20 disabled:opacity-40 transition-all"
                  >
                    REVEAL RESULTS
                  </button>
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

              {isHost && (
                <div className="flex gap-3 justify-center mt-4">
                  {gameRound < 5 && (
                    <button
                      onClick={handleAdvancePhase}
                      disabled={advancing}
                      className="px-6 py-2 border border-accent/50 rounded text-sm font-mono text-gray-900 bg-accent/10 hover:bg-accent/20 disabled:opacity-40 transition-all"
                    >
                      NEXT ROUND
                    </button>
                  )}
                  <button
                    onClick={async () => {
                      if (!gameId) return
                      setAdvancing(true)
                      try {
                        await advancePhase(gameId, 'game_over')
                      } catch {}
                      setAdvancing(false)
                    }}
                    disabled={advancing}
                    className="px-6 py-2 border border-red-500/50 rounded text-sm font-mono text-red-400 bg-red-500/10 hover:bg-red-500/20 disabled:opacity-40 transition-all"
                  >
                    END GAME
                  </button>
                </div>
              )}
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

              <Link
                to="/lobby"
                className="inline-block mt-6 px-6 py-2 border border-gray-400/30 rounded text-sm font-mono text-gray-600 hover:text-gray-900 hover:border-gray-400 transition-all"
              >
                BACK TO LOBBY
              </Link>
            </div>
          )}

          {/* ============ WAITING FOR HOST ============ */}
          {!['role_assignment', 'game_over', 'interaction', 'discussion', 'voting'].includes(gamePhase) && !isHost && (
            <div className="text-center py-8 text-[10px] font-mono text-gray-600 animate-pulse">
              Waiting for host to advance the phase...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
