import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useAuthStore } from '../../../stores/authStore'
import { useWebSocket } from '../../../hooks/useWebSocket'
import { getRoom } from '../../room/services/roomApi'
import { PhaseBanner } from '../components/PhaseBanner'
import { RoleReveal } from '../components/RoleReveal'
import { ChatPanel } from '../../chat/components/ChatPanel'
import type { RoomResponse } from '../../room/types/room.types'

export function GamePage() {
  const { code } = useParams<{ code: string }>()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    lastRoomState,
    lastRoleAssignment,
    lastPhaseChanged,
    isConnected,
    chatMessages,
    sendMessage,
  } = useWebSocket(code ?? null)

  const [room, setRoom] = useState<RoomResponse | null>(null)
  const [role, setRole] = useState<string | null>(null)
  const [phase, setPhase] = useState<string>('role_assignment')
  const [round, setRound] = useState(1)
  const [revealed, setRevealed] = useState(false)

  // Fetch room metadata
  useEffect(() => {
    if (!isAuthenticated || !code) return
    getRoom(code).then(setRoom).catch(() => navigate('/lobby', { replace: true }))
  }, [isAuthenticated, code, navigate])

  // Update room state from WS
  useEffect(() => {
    if (lastRoomState) setRoom(lastRoomState.room)
  }, [lastRoomState])

  // Handle private role assignment
  useEffect(() => {
    if (lastRoleAssignment) {
      setRole(lastRoleAssignment.role)
      setPhase('role_assignment')
      setRound(1)
      setRevealed(false)

      // Auto-reveal after a brief delay
      const timer = setTimeout(() => setRevealed(true), 600)
      return () => clearTimeout(timer)
    }
  }, [lastRoleAssignment])

  // Handle phase changes
  useEffect(() => {
    if (lastPhaseChanged) {
      // Animate by briefly clearing then setting
      setPhase('')
      const timer = setTimeout(() => {
        setPhase(lastPhaseChanged.phase)
        setRound(lastPhaseChanged.round_number)
      }, 50)
      return () => clearTimeout(timer)
    }
  }, [lastPhaseChanged])

  if (!isAuthenticated) {
    navigate('/auth', { replace: true })
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

  const handleSendMessage = useCallback((content: string) => {
    sendMessage({ type: 'SEND_MESSAGE', content })
  }, [sendMessage])

  const players = lastRoomState?.players ?? []
  const gamePhase = phase || lastPhaseChanged?.phase || 'role_assignment'
  const gameRound = round || lastPhaseChanged?.round_number || 1

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
          {gamePhase === 'role_assignment' && role && !revealed && (
            <div className="text-center py-12 text-sm font-mono text-gray-600 animate-pulse">
              <span className="text-accent">{'//'}</span> ASSIGNING ROLES...
            </div>
          )}

          {gamePhase === 'role_assignment' && role && revealed && (
            <div className="space-y-6">
              <RoleReveal role={role} />
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

          {/* Non-role-assignment phases: show player strip + chat */}
          {gamePhase !== 'role_assignment' && (
            <div className="space-y-4">
              {/* Player strip */}
              <div className="flex flex-wrap gap-2">
                {players.map((p) => (
                  <div
                    key={p.id}
                    className="px-3 py-1.5 border border-gray-400/30 rounded bg-gray-100 text-xs font-mono flex items-center gap-1.5"
                  >
                    <span className="text-gray-900">{p.username}</span>
                    {p.id === user?.id && (
                      <span className="text-gray-500">(YOU)</span>
                    )}
                  </div>
                ))}
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

              <div className="text-center text-[10px] font-mono text-gray-600 animate-pulse mt-2">
                {isConnected
                  ? 'Waiting for host to advance the phase...'
                  : 'Reconnecting...'}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
