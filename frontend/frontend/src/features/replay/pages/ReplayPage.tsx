import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuthStore } from '../../../stores/authStore'
import { getReplayTimeline } from '../services/replayApi'
import type { ReplayTimeline, ReplayEvent } from '../types/replay.types'
import { EVENT_CATEGORY_COLORS } from '../types/replay.types'
import { ReplayTimeline as ReplayTimelineComponent } from '../components/ReplayTimeline'
import { ReplayControls } from '../components/ReplayControls'
import { ReplayInspector } from '../components/ReplayInspector'

export function ReplayPage() {
  const { gameId } = useParams<{ gameId: string }>()
  const { isAuthenticated } = useAuthStore()

  const [timeline, setTimeline] = useState<ReplayTimeline | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated || !gameId) return
    setLoading(true)
    setError(null)
    getReplayTimeline(Number(gameId))
      .then(setTimeline)
      .catch((err) => setError(err.message ?? 'Failed to load replay'))
      .finally(() => setLoading(false))
  }, [gameId, isAuthenticated])

  const events = timeline?.events ?? []
  const currentEvent: ReplayEvent | null = events[currentIndex] ?? null

  const stepForward = useCallback(() => {
    setCurrentIndex((prev) => {
      if (prev >= events.length - 1) {
        setIsPlaying(false)
        return prev
      }
      return prev + 1
    })
  }, [events.length])

  const stepBackward = useCallback(() => {
    setCurrentIndex((prev) => Math.max(0, prev - 1))
  }, [])

  const jumpToStart = useCallback(() => {
    setCurrentIndex(0)
    setIsPlaying(false)
  }, [])

  const jumpToEnd = useCallback(() => {
    setCurrentIndex(events.length - 1)
    setIsPlaying(false)
  }, [events.length])

  // Auto-stop at end
  useEffect(() => {
    if (isPlaying && currentIndex >= events.length - 1) {
      setIsPlaying(false)
    }
  }, [isPlaying, currentIndex, events.length])

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-sm font-mono text-gray-600">Please log in to view replay.</div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-sm font-mono tracking-wider text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> LOADING REPLAY DATA...
        </div>
      </div>
    )
  }

  if (error || !timeline) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="text-sm font-mono text-red-500">{error ?? 'Replay not available'}</div>
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
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 animate-fade-in-up">
          <div>
            <Link
              to={`/game/${gameId}/analysis`}
              className="text-xs font-mono text-gray-600 hover:text-gray-900 transition-colors"
            >
              {'<'} ANALYSIS
            </Link>
            <h1 className="mt-2 text-xl font-mono font-bold tracking-wider text-gray-900">
              <span className="text-accent">&gt;</span> GAME REPLAY
            </h1>
            <p className="mt-1 text-xs font-mono text-gray-500">
              Game #{timeline.game.game_id} &middot; {timeline.game.room_code} &middot;{' '}
              {timeline.total_events} events &middot; {timeline.total_rounds} rounds
            </p>
          </div>
          <div className={`px-4 py-2 border rounded text-sm font-mono font-bold tracking-wider ${
            timeline.game.winner === 'coordinator'
              ? 'border-accent/50 text-accent bg-accent/10'
              : 'border-cyan-500/50 text-cyan-600 bg-cyan-500/10'
          }`}>
            {timeline.game.winner === 'coordinator' ? 'COORDINATOR WINS' : 'INVESTIGATION TEAM WINS'}
          </div>
        </div>

        {/* Players */}
        <div className="mb-4 flex flex-wrap gap-2 animate-fade-in-up" style={{ animationDelay: '0.05s' }}>
          {timeline.game.players.map((p) => (
            <div
              key={p.user_id}
              className="px-3 py-1.5 border border-gray-300/50 rounded bg-gray-100 text-xs font-mono"
            >
              <span className="text-gray-900 font-medium">{p.username}</span>
              <span className="text-gray-500 ml-1.5">({p.role})</span>
              <span className="text-accent ml-1.5">{p.score}pts</span>
            </div>
          ))}
        </div>

        {/* Main layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Left: Timeline + Controls */}
          <div className="lg:col-span-2 space-y-4 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            <ReplayTimelineComponent
              events={events}
              currentIndex={currentIndex}
              onSelectEvent={setCurrentIndex}
              totalRounds={timeline.total_rounds}
            />

            <ReplayControls
              isPlaying={isPlaying}
              currentIndex={currentIndex}
              totalEvents={events.length}
              speed={speed}
              onTogglePlay={() => setIsPlaying(!isPlaying)}
              onStepForward={stepForward}
              onStepBackward={stepBackward}
              onJumpToStart={jumpToStart}
              onJumpToEnd={jumpToEnd}
              onSpeedChange={setSpeed}
              onSeek={setCurrentIndex}
            />

            {/* Event list */}
            <div className="border border-gray-300/50 rounded bg-gray-100 p-4">
              <div className="text-[10px] font-mono text-gray-500 mb-3 tracking-wider">EVENT LOG</div>
              <div className="max-h-96 overflow-y-auto space-y-1">
                {events.map((event, idx) => {
                  const colorClass = EVENT_CATEGORY_COLORS[event.category] ?? 'bg-gray-300'
                  const isActive = idx === currentIndex
                  return (
                    <button
                      key={event.sequence_number}
                      onClick={() => setCurrentIndex(idx)}
                      className={`w-full text-left px-3 py-2 rounded text-xs font-mono flex items-center gap-2 transition-all ${
                        isActive
                          ? 'bg-accent/10 border border-accent/30'
                          : 'hover:bg-gray-200 border border-transparent'
                      }`}
                    >
                      <span className={`w-2 h-2 rounded-full ${colorClass} shrink-0`} />
                      <span className="text-gray-500 w-8 shrink-0">#{event.sequence_number}</span>
                      <span className="text-gray-900 shrink-0">{event.label}</span>
                      {event.actor_name && (
                        <span className="text-gray-500 truncate">{event.actor_name}</span>
                      )}
                      <span className="text-gray-400 ml-auto shrink-0">
                        {Math.floor(event.relative_time_seconds)}s
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Right: Inspector */}
          <div className="animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
            <ReplayInspector event={currentEvent} />
          </div>
        </div>

        {/* Back link */}
        <div className="mt-8 text-center animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <Link
            to="/lobby"
            className="inline-block px-6 py-2 border border-gray-400/30 rounded text-sm font-mono text-gray-600 hover:text-gray-900 hover:border-gray-400 transition-all"
          >
            BACK TO LOBBY
          </Link>
        </div>
      </div>
    </div>
  )
}
