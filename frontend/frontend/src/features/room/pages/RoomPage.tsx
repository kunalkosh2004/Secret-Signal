import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../../../stores/authStore'
import { useWebSocket } from '../../../hooks/useWebSocket'
import { getRoom, leaveRoom } from '../services/roomApi'
import { startGame } from '../services/gameApi'
import type { RoomResponse } from '../types/room.types'

export function RoomPage() {
  const { code } = useParams<{ code: string }>()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    lastRoomState,
    lastGameStart,
    isConnected,
    sendMessage,
  } = useWebSocket(code ?? null)

  const [room, setRoom] = useState<RoomResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [startError, setStartError] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)
  const [copied, setCopied] = useState(false)
  const [leaveError, setLeaveError] = useState<string | null>(null)
  const [isReady, setIsReady] = useState(false)
  const hostAutoReady = useRef(false)

  const isHost = user?.id === room?.host_id

  useEffect(() => {
    if (!isAuthenticated || !code) return
    getRoom(code)
      .then(setRoom)
      .catch((err) => setError(err.message))
  }, [isAuthenticated, code])

  // Update room data from WebSocket and sync ready state for current user
  useEffect(() => {
    if (lastRoomState) {
      setRoom(lastRoomState.room)
      const me = lastRoomState.players.find((p) => p.id === user?.id)
      if (me && !isHost) {
        setIsReady(me.is_ready ?? false)
      }
    }
  }, [lastRoomState, user, isHost])

  // Host auto-ready: once WS is connected, mark host as ready
  useEffect(() => {
    if (!room || !user || !isConnected) return
    if (user.id === room.host_id && !hostAutoReady.current) {
      setIsReady(true)
      sendMessage({ type: 'PLAYER_READY', payload: { ready: true } })
      hostAutoReady.current = true
    }
  }, [room, user, isConnected, sendMessage])

  // Redirect to auth if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/auth', { replace: true })
    }
  }, [isAuthenticated, navigate])

  // Handle GAME_START → navigate to game page
  useEffect(() => {
    if (lastGameStart && code) {
      navigate(`/game/${code}`, { replace: true })
    }
  }, [lastGameStart, code, navigate])

  if (!isAuthenticated) {
    return null
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-center max-w-md px-4 animate-fade-in">
          <div className="text-sm font-mono tracking-wider text-gray-600 mb-2">
            <span className="text-accent">{'//'}</span> ERROR
          </div>
          <p className="text-gray-900 font-mono text-sm mb-6">{error}</p>
          <button
            onClick={() => navigate('/lobby', { replace: true })}
            className="px-4 py-2 border border-accent/50 text-sm font-mono rounded-md text-gray-900 bg-accent/10 hover:bg-accent/20 transition-all"
          >
            BACK TO LOBBY
          </button>
        </div>
      </div>
    )
  }

  if (!room || !code) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-sm font-mono tracking-wider text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> LOADING ROOM...
        </div>
      </div>
    )
  }

  const players = lastRoomState?.players ?? []
  const playerCount = players.length
  const serverReadyCount = players.filter((p) => p.is_ready).length
  const readyCount = serverReadyCount + (isHost ? 1 : 0) // host always counts as ready
  const allNonHostReady = playerCount < 2 || players
    .filter((p) => p.id !== room.host_id)
    .every((p) => p.is_ready)
  const hostPlayer = players.find((p) => p.id === room.host_id)

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleToggleReady = () => {
    // Optimistic update: flip locally immediately
    const next = !isReady
    setIsReady(next)
    sendMessage({ type: 'PLAYER_READY', payload: { ready: next } })
  }

  const handleLeave = async () => {
    setLeaveError(null)
    try {
      await leaveRoom(code)
      navigate('/lobby', { replace: true })
    } catch (err) {
      setLeaveError(err instanceof Error ? err.message : 'Failed to leave room')
    }
  }

  const handleStartGame = async () => {
    if (!code) return
    setStartError(null)
    setStarting(true)
    try {
      await startGame(code)
      setStarting(false)
      navigate(`/game/${code}`, { replace: true })
    } catch (err) {
      setStartError(err instanceof Error ? err.message : 'Failed to start game')
      setStarting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 bg-grid">
      <div className="max-w-2xl mx-auto px-4 py-12">
        {/* Room header */}
        <div className="text-center mb-8 animate-fade-in-up">
          <div className="text-sm font-mono tracking-wider text-gray-600 mb-2">
            <span className="text-accent">{'//'}</span> ROOM
          </div>

          {/* Room code */}
          <div className="flex items-center justify-center gap-3 mt-4">
            <div className="bg-gray-100 border border-gray-400/30 rounded px-5 py-3">
              <span className="text-2xl font-mono tracking-[0.3em] text-gray-900 font-bold">
                {code}
              </span>
            </div>
            <button
              onClick={handleCopyCode}
              className="px-3 py-3 border border-gray-400/30 rounded text-xs font-mono text-gray-600 hover:text-gray-900 hover:border-gray-400 transition-colors"
            >
              {copied ? 'COPIED' : 'COPY'}
            </button>
          </div>

          {/* Room meta */}
          <div className="flex items-center justify-center gap-4 mt-4 text-xs font-mono text-gray-600">
            <span className="flex items-center gap-1.5">
              <span
                className={`inline-block w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-500 animate-pulse-dot' : 'bg-red-500'
                }`}
              />
              {isConnected ? 'ONLINE' : 'OFFLINE'}
            </span>
            <span className="text-gray-500">|</span>
            <span>
              {playerCount}/{room.max_players}
            </span>
            <span className="text-gray-500">|</span>
            <span>
              <span className={readyCount === playerCount ? 'text-green-500' : ''}>{readyCount}</span>/{playerCount}
            </span>
            <span className="text-gray-500">|</span>
            <span>
              {isHost ? (
                <span className="text-accent">HOST</span>
              ) : (
                <span>HOST: {hostPlayer?.username ?? room.host_id}</span>
              )}
            </span>
          </div>

          {/* Game settings display */}
          {room.settings && Object.keys(room.settings).length > 0 && (
            <div className="mt-4 flex items-center justify-center gap-3 text-xs font-mono text-gray-600">
              <span className="text-gray-500">|</span>
              <span>
                <span className="text-gray-500">ROUNDS:</span>{' '}
                <span className="text-gray-800">{(room.settings as Record<string, string | number>).max_rounds ?? 1}</span>
              </span>
              {(room.settings as Record<string, Record<string, number>>).phase_durations && (
                <>
                  <span className="text-gray-500">|</span>
                  <span>
                    <span className="text-gray-500">CHAT:</span>{' '}
                    <span className="text-gray-800">
                      {(() => {
                        const pd = (room.settings as Record<string, Record<string, unknown>>).phase_durations
                        const secs = (pd?.interaction as number) ?? 120
                        return secs >= 60 ? `${Math.floor(secs / 60)}m ${secs % 60 > 0 ? secs % 60 + 's' : ''}` : `${secs}s`
                      })()}
                    </span>
                  </span>
                </>
              )}
            </div>
          )}
        </div>

        {/* Player list */}
        <div className="border border-gray-400/30 rounded overflow-hidden animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          <div className="bg-gray-100 px-4 py-2 border-b border-gray-400/20 flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-gray-600">PLAYERS</span>
            <span className="text-xs font-mono text-gray-600">{readyCount}/{playerCount} READY</span>
          </div>
          <div className="divide-y divide-gray-400/10">
            {players.map((p, i) => (
              <div
                key={p.id}
                className="flex items-center justify-between px-4 py-3 animate-fade-in"
                style={{ animationDelay: `${0.15 + i * 0.05}s` }}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-mono font-bold
                      ${p.id === room.host_id
                        ? 'bg-accent/20 text-accent border border-accent/40'
                        : 'bg-gray-200 text-gray-700'}`}
                  >
                    {p.username.charAt(0).toUpperCase()}
                  </div>
                  <div className="text-sm font-mono text-gray-900">{p.username}</div>
                  {p.id === room.host_id && (
                    <span className="text-[10px] font-mono text-accent/70 tracking-wider border border-accent/20 rounded px-1">HOST</span>
                  )}
                  {p.id === user?.id && p.id !== room.host_id && (
                    <span className="text-[10px] font-mono text-gray-600 border border-gray-400/20 rounded px-1">YOU</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {p.id === room.host_id ? (
                    <span className="text-xs font-mono text-accent/80 tracking-wider">HOST &#10003;</span>
                  ) : ((p.id === user?.id) ? isReady : p.is_ready) ? (
                    <span className="text-xs font-mono text-green-500/80 tracking-wider">READY</span>
                  ) : (
                    <span className="text-xs font-mono text-gray-600">WAITING</span>
                  )}
                </div>
              </div>
            ))}

            {players.length === 0 && (
              <div className="px-4 py-6 text-center text-xs font-mono text-gray-600">
                Waiting for players...
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-8 space-y-3 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          {/* Ready toggle — non-host only */}
          {!isHost && (
            <button
              onClick={handleToggleReady}
              className={`w-full py-3 border rounded text-sm font-mono tracking-wider transition-all
                ${isReady
                  ? 'border-green-500/50 bg-green-500/10 text-green-500 hover:bg-green-500/20 glow-green'
                  : 'border-gray-400/30 bg-gray-100 text-gray-600 hover:border-gray-400 hover:text-gray-900'}`}
            >
              {isReady ? '✓ READY' : 'CLICK WHEN READY'}
            </button>
          )}

          {/* Start game — host only */}
          {isHost && (
            <button
              onClick={handleStartGame}
              disabled={playerCount < 3 || !allNonHostReady || starting}
              className="w-full py-3 border border-accent/50 rounded text-sm font-mono tracking-wider text-gray-900 bg-accent/10 hover:bg-accent/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all glow-red"
            >
              {starting ? 'STARTING...' : 'START GAME'}
            </button>
          )}

          {startError && (
            <div className="p-3 bg-red-900/20 border border-red-500/30 rounded animate-slide-down">
              <p className="text-xs font-mono text-red-400 text-center">{startError}</p>
            </div>
          )}

          {/* Leave error */}
          {leaveError && (
            <div className="p-3 bg-red-900/20 border border-red-500/30 rounded animate-slide-down">
              <p className="text-xs font-mono text-red-400 text-center">{leaveError}</p>
            </div>
          )}

          {/* Host cannot leave */}
          {isHost && (
            <div className="p-3 bg-yellow-900/20 border border-yellow-500/30 rounded">
              <p className="text-xs font-mono text-yellow-400 text-center">
                You are the host. You cannot leave without transferring host or closing the room.
              </p>
            </div>
          )}

          {/* Leave */}
          <button
            onClick={handleLeave}
            disabled={isHost}
            className="w-full py-2 border border-gray-400/30 rounded text-xs font-mono text-gray-600 hover:text-red-600 hover:border-red-600/30 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            LEAVE ROOM
          </button>
        </div>
      </div>
    </div>
  )
}
