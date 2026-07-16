import { useEffect, useRef, useCallback } from 'react'

interface ReplayControlsProps {
  isPlaying: boolean
  currentIndex: number
  totalEvents: number
  speed: number
  onTogglePlay: () => void
  onStepForward: () => void
  onStepBackward: () => void
  onJumpToStart: () => void
  onJumpToEnd: () => void
  onSpeedChange: (speed: number) => void
  onSeek: (index: number) => void
}

const SPEEDS = [0.5, 1, 2, 4, 8]

export function ReplayControls({
  isPlaying,
  currentIndex,
  totalEvents,
  speed,
  onTogglePlay,
  onStepForward,
  onStepBackward,
  onJumpToStart,
  onJumpToEnd,
  onSpeedChange,
  onSeek,
}: ReplayControlsProps) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const tick = useCallback(() => {
    onStepForward()
  }, [onStepForward])

  useEffect(() => {
    if (isPlaying) {
      const ms = Math.max(50, 500 / speed)
      intervalRef.current = setInterval(tick, ms)
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [isPlaying, speed, tick])

  const progress = totalEvents > 0 ? ((currentIndex + 1) / totalEvents) * 100 : 0

  return (
    <div className="border border-gray-300/50 rounded bg-gray-100 p-4">
      {/* Progress bar */}
      <div className="mb-3">
        <div className="h-2 bg-gray-200 border border-gray-300/30 rounded overflow-hidden">
          <div
            className="h-full bg-accent transition-all duration-100"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between mt-1 text-[10px] font-mono text-gray-500">
          <span>Event {currentIndex + 1} of {totalEvents}</span>
          <span>{Math.round(progress)}%</span>
        </div>
      </div>

      {/* Seek slider */}
      <input
        type="range"
        min={0}
        max={totalEvents - 1}
        value={currentIndex}
        onChange={(e) => onSeek(Number(e.target.value))}
        className="w-full mb-3 accent-accent"
      />

      {/* Transport controls */}
      <div className="flex items-center justify-center gap-2">
        <button
          onClick={onJumpToStart}
          className="px-3 py-1.5 border border-gray-400/30 rounded text-xs font-mono text-gray-600 hover:text-gray-900 hover:border-gray-400 transition-all"
          title="Jump to start"
        >
          {'|<'}
        </button>
        <button
          onClick={onStepBackward}
          className="px-3 py-1.5 border border-gray-400/30 rounded text-xs font-mono text-gray-600 hover:text-gray-900 hover:border-gray-400 transition-all"
          title="Step backward"
        >
          {'<'}
        </button>
        <button
          onClick={onTogglePlay}
          className={`px-5 py-1.5 border rounded text-xs font-mono font-bold tracking-wider transition-all ${
            isPlaying
              ? 'border-accent/50 text-white bg-accent'
              : 'border-gray-400/30 text-gray-600 hover:text-gray-900 hover:border-gray-400'
          }`}
        >
          {isPlaying ? 'PAUSE' : 'PLAY'}
        </button>
        <button
          onClick={onStepForward}
          className="px-3 py-1.5 border border-gray-400/30 rounded text-xs font-mono text-gray-600 hover:text-gray-900 hover:border-gray-400 transition-all"
          title="Step forward"
        >
          {'>'}
        </button>
        <button
          onClick={onJumpToEnd}
          className="px-3 py-1.5 border border-gray-400/30 rounded text-xs font-mono text-gray-600 hover:text-gray-900 hover:border-gray-400 transition-all"
          title="Jump to end"
        >
          {'>|'}
        </button>
      </div>

      {/* Speed selector */}
      <div className="flex items-center justify-center gap-1 mt-3">
        <span className="text-[10px] font-mono text-gray-500 mr-2">SPEED</span>
        {SPEEDS.map((s) => (
          <button
            key={s}
            onClick={() => onSpeedChange(s)}
            className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all ${
              speed === s
                ? 'bg-accent text-white'
                : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
            }`}
          >
            {s}x
          </button>
        ))}
      </div>
    </div>
  )
}
