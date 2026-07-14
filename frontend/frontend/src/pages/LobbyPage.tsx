import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { createRoom, joinRoom } from '../features/room/services/roomApi'

const PHASE_LABELS: Record<string, { label: string; min: number; max: number; default: number }> = {
  role_assignment: { label: 'Role Reveal', min: 3, max: 15, default: 6 },
  round_start: { label: 'Round Start', min: 3, max: 15, default: 5 },
  interaction: { label: 'Chat', min: 30, max: 300, default: 120 },
  discussion: { label: 'Discussion', min: 30, max: 300, default: 90 },
  result: { label: 'Results', min: 5, max: 30, default: 10 },
}

export function LobbyPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuthStore()
  const [roomCode, setRoomCode] = useState('')
  const [showJoin, setShowJoin] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const [maxRounds, setMaxRounds] = useState(1)
  const [phaseDurations, setPhaseDurations] = useState<Record<string, number>>(() => {
    const init: Record<string, number> = {}
    for (const [key, val] of Object.entries(PHASE_LABELS)) {
      init[key] = val.default
    }
    return init
  })

  if (!isAuthenticated || !user) {
    navigate('/auth', { replace: true })
    return null
  }

  const handleCreateRoom = async () => {
    setError(null)
    setLoading(true)
    try {
      const room = await createRoom({
        max_players: 8,
        settings: {
          max_rounds: maxRounds,
          phase_durations: phaseDurations,
        },
      })
      navigate(`/room/${room.code}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create room')
    } finally {
      setLoading(false)
    }
  }

  const handleJoinRoom = async () => {
    const code = roomCode.trim()
    if (!code) return
    setError(null)
    setLoading(true)
    try {
      const room = await joinRoom({ code })
      navigate(`/room/${room.code}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join room')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (seconds: number) => {
    if (seconds >= 60) {
      const m = Math.floor(seconds / 60)
      const s = seconds % 60
      return s > 0 ? `${m}m ${s}s` : `${m}m`
    }
    return `${seconds}s`
  }

  return (
    <div className="min-h-screen bg-gray-50 bg-grid">
      <div className="max-w-2xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="text-sm font-mono tracking-wider text-gray-600 mb-2">
            <span className="text-accent">{'//'}</span> SECRET_SIGNAL
          </div>
          <h1 className="text-2xl font-bold text-gray-900 font-mono">
            <span className="text-accent">&gt;</span> Game Hub
          </h1>
          <p className="text-sm text-gray-600 font-mono mt-2">
            Signed in as <span className="text-gray-800">{user.username}</span>
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-400/30 rounded">
            <p className="text-xs font-mono text-red-700">{error}</p>
          </div>
        )}

        {/* Action cards */}
        <div className="space-y-4">
          {/* Create Room + Settings */}
          <div className="bg-gray-100 border border-gray-400/30 rounded">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="w-full p-6 text-left"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-mono tracking-wider text-gray-800">
                    <span className="text-accent">{'>'}</span> CREATE ROOM
                  </div>
                  <p className="text-xs text-gray-600 font-mono mt-1">
                    Start a new game and invite your friends
                  </p>
                </div>
                <div className={`w-6 h-6 flex items-center justify-center transition-transform ${showSettings ? 'rotate-90' : ''}`}>
                  <span className="text-gray-600 text-sm font-mono">{'>'}</span>
                </div>
              </div>
            </button>

            {showSettings && (
              <div className="px-6 pb-6 space-y-5 border-t border-gray-400/20 pt-5">
                {/* Max Rounds */}
                <div>
                  <label className="block text-xs font-mono tracking-wider text-gray-700 mb-2">
                    ROUNDS
                  </label>
                  <div className="flex items-center gap-3">
                    {[1, 2, 3, 5].map((n) => (
                      <button
                        key={n}
                        onClick={() => setMaxRounds(n)}
                        className={`px-3 py-1.5 border rounded text-sm font-mono transition-all
                          ${maxRounds === n
                            ? 'border-accent/60 bg-accent/10 text-gray-900'
                            : 'border-gray-400/30 text-gray-600 hover:border-gray-400'}`}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Phase Durations */}
                <div>
                  <label className="block text-xs font-mono tracking-wider text-gray-700 mb-2">
                    PHASE TIMERS
                  </label>
                  <div className="space-y-2">
                    {Object.entries(PHASE_LABELS).map(([key, meta]) => (
                      <div key={key} className="flex items-center justify-between">
                        <span className="text-xs font-mono text-gray-600 w-28">{meta.label}</span>
                        <div className="flex items-center gap-2">
                          <input
                            type="range"
                            min={meta.min}
                            max={meta.max}
                            step={key === 'interaction' || key === 'discussion' ? 10 : 1}
                            value={phaseDurations[key] ?? meta.default}
                            onChange={(e) =>
                              setPhaseDurations((prev) => ({
                                ...prev,
                                [key]: parseInt(e.target.value),
                              }))
                            }
                            className="w-32 accent-accent"
                          />
                          <span className="text-xs font-mono text-gray-800 w-12 text-right">
                            {formatTime(phaseDurations[key] ?? meta.default)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Create button */}
                <button
                  onClick={handleCreateRoom}
                  disabled={loading}
                  className="w-full py-3 border border-accent/50 rounded text-sm font-mono tracking-wider text-gray-900 bg-accent/10 hover:bg-accent/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all glow-red"
                >
                  {loading ? 'CREATING...' : 'CREATE ROOM'}
                </button>
              </div>
            )}
          </div>

          {/* Join Room */}
          <div className="p-6 bg-gray-100 border border-gray-400/30 rounded">
            <button
              onClick={() => setShowJoin(!showJoin)}
              className="w-full text-left"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-mono tracking-wider text-gray-800">
                    <span className="text-accent">{'>'}</span> JOIN ROOM
                  </div>
                  <p className="text-xs text-gray-600 font-mono mt-1">
                    Enter a room code to join an existing game
                  </p>
                </div>
                <div className={`w-6 h-6 flex items-center justify-center transition-transform ${showJoin ? 'rotate-90' : ''}`}>
                  <span className="text-gray-600 text-sm font-mono">{'>'}</span>
                </div>
              </div>
            </button>

            {showJoin && (
              <div className="mt-4 pt-4 border-t border-gray-400/20">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={roomCode}
                    onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                    placeholder="ROOM CODE"
                    maxLength={6}
                    className="flex-1 bg-gray-200 border border-gray-400/30 rounded px-3 py-2.5 text-sm font-mono text-gray-900 placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50 uppercase tracking-widest"
                    onKeyDown={(e) => e.key === 'Enter' && handleJoinRoom()}
                  />
                  <button
                    onClick={handleJoinRoom}
                    disabled={!roomCode.trim() || loading}
                    className="px-5 py-2.5 border border-accent/50 rounded text-sm font-mono tracking-wider text-gray-900 bg-accent/10 hover:bg-accent/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all glow-red"
                  >
                    JOIN
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Back + logout */}
        <div className="mt-12 flex items-center justify-between">
          <Link
            to="/"
            className="text-xs font-mono text-gray-600 hover:text-gray-800 transition-colors"
          >
            {'<'} BACK TO HOME
          </Link>
          <button
            onClick={() => { logout(); navigate('/') }}
            className="text-xs font-mono text-gray-600 hover:text-accent transition-colors"
          >
            LOG OUT
          </button>
        </div>
      </div>
    </div>
  )
}
