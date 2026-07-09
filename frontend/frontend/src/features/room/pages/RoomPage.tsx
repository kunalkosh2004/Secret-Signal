import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../../../stores/authStore'
import { useWebSocket } from '../../../hooks/useWebSocket'
import { getRoom, leaveRoom } from '../services/roomApi'
import type { RoomResponse } from '../types/room.types'

export function RoomPage() {
  const { code } = useParams<{ code: string }>()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const { lastRoomState, isConnected } = useWebSocket(code ?? null)

  const [room, setRoom] = useState<RoomResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Fetch room on mount (fallback for initial render before WS connects)
  useEffect(() => {
    if (!isAuthenticated || !code) return

    getRoom(code)
      .then(setRoom)
      .catch((err) => setError(err.message))
  }, [isAuthenticated, code])

  // Update room state from WebSocket
  useEffect(() => {
    if (lastRoomState) {
      setRoom(lastRoomState.room)
    }
  }, [lastRoomState])

  // Redirect if not authenticated
  if (!isAuthenticated) {
    navigate('/auth', { replace: true })
    return null
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <div className="text-sm font-mono tracking-wider text-gray-600 mb-2">
            <span className="text-accent">{'//'}</span> ERROR
          </div>
          <p className="text-gray-800 font-mono text-sm mb-6">{error}</p>
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
        <div className="text-sm font-mono tracking-wider text-gray-600">
          <span className="text-accent">{'//'}</span> LOADING ROOM...
        </div>
      </div>
    )
  }

  const players = lastRoomState?.players ?? []
  const isHost = user?.id === room.host_id
  const playerCount = players.length

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleLeave = async () => {
    try {
      await leaveRoom(code)
      navigate('/lobby', { replace: true })
    } catch {
      // Navigate anyway
      navigate('/lobby', { replace: true })
    }
  }

  const handleStartGame = () => {
    // TODO: POST /api/v1/games — start the game
  }

  return (
    <div className="min-h-screen bg-gray-50 bg-grid">
      <div className="max-w-2xl mx-auto px-4 py-12">
        {/* Room header */}
        <div className="text-center mb-8">
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
            <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
              {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
            <span>|</span>
            <span>{playerCount}/{room.max_players} PLAYERS</span>
            <span>|</span>
            <span>STATUS: {room.status.toUpperCase()}</span>
            <span>|</span>
            <span>{isHost ? 'YOU ARE HOST' : 'HOST: Player ' + room.host_id}</span>
          </div>
        </div>

        {/* Player list */}
        <div className="border border-gray-400/30 rounded overflow-hidden">
          <div className="bg-gray-100 px-4 py-2 border-b border-gray-400/20">
            <span className="text-xs font-mono tracking-wider text-gray-600">PLAYERS</span>
          </div>
          <div className="divide-y divide-gray-400/10">
            {players.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-mono font-bold
                    ${p.id === room.host_id ? 'bg-accent/20 text-accent border border-accent/40' : 'bg-gray-200 text-gray-700'}`}
                  >
                    {p.username.charAt(0).toUpperCase()}
                  </div>
                  <div className="text-sm font-mono text-gray-900">{p.username}</div>
                  {p.id === room.host_id && (
                    <span className="text-xs font-mono text-accent tracking-wider">[HOST]</span>
                  )}
                </div>
                {p.id === user?.id && (
                  <span className="text-xs font-mono text-gray-500">YOU</span>
                )}
              </div>
            ))}

            {players.length === 0 && (
              <div className="px-4 py-6 text-center text-xs font-mono text-gray-500">
                Waiting for players...
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-8 space-y-3">
          {isHost && (
            <button
              onClick={handleStartGame}
              disabled={playerCount < 2}
              className="w-full py-3 border border-accent/50 rounded text-sm font-mono tracking-wider text-gray-900 bg-accent/10 hover:bg-accent/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all glow-red"
            >
              START GAME
            </button>
          )}
          {!isHost && (
            <div className="text-center text-xs font-mono text-gray-500 py-2">
              Waiting for host to start the game...
            </div>
          )}

          <button
            onClick={handleLeave}
            className="w-full py-2 border border-gray-400/30 rounded text-xs font-mono text-gray-600 hover:text-red-600 hover:border-red-600/30 transition-colors"
          >
            LEAVE ROOM
          </button>
        </div>
      </div>
    </div>
  )
}
