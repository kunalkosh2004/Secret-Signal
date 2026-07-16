import { useState, useEffect, useCallback } from 'react'
import type { SignalAIResultEvent, PlayerSuspicion, BehaviorMetric } from '../../room/types/game.types'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type PanelState = 'idle' | 'scanning' | 'ready' | 'error' | 'cooldown'

interface SignalAIAnalysisPanelProps {
  signalAIResult: SignalAIResultEvent | null
  onScan: () => void
  scansUsed: number
  scansRemaining: number
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ConfidenceBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    low: 'text-yellow-600 border-yellow-400/40 bg-yellow-50',
    medium: 'text-orange-600 border-orange-400/40 bg-orange-50',
    high: 'text-red-600 border-red-400/40 bg-red-50',
  }
  return (
    <span className={`px-2 py-0.5 text-[10px] font-mono border rounded ${colors[level] ?? colors.low}`}>
      {level.toUpperCase()}
    </span>
  )
}

function SuspicionBar({ score }: { score: number }) {
  const color =
    score > 65 ? 'bg-red-500' :
    score > 40 ? 'bg-orange-500' :
    score > 20 ? 'bg-yellow-500' :
    'bg-green-500'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-200 border border-gray-300/50 rounded overflow-hidden">
        <div
          className={`h-full ${color} transition-all duration-700`}
          style={{ width: `${Math.min(100, score)}%` }}
        />
      </div>
      <span className="w-10 text-right text-[10px] font-mono text-gray-600">
        {score.toFixed(0)}%
      </span>
    </div>
  )
}

function MetricBar({ metric }: { metric: BehaviorMetric }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-28 text-[10px] font-mono text-gray-600 truncate">{metric.label}</span>
      <div className="flex-1 h-1.5 bg-gray-200 rounded overflow-hidden">
        <div
          className="h-full bg-cyan-500/60 transition-all duration-500"
          style={{ width: `${Math.min(100, metric.normalized * 100)}%` }}
        />
      </div>
      <span className="w-8 text-right text-[10px] font-mono text-gray-500">
        {metric.value.toFixed(1)}
      </span>
    </div>
  )
}

function PlayerSuspicionCard({ player, isTop }: { player: PlayerSuspicion; isTop: boolean }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={`p-3 border rounded transition-all ${
      isTop
        ? 'border-red-400/50 bg-red-50/50'
        : 'border-gray-300/50 bg-gray-50'
    }`}>
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          {isTop && <span className="text-[10px] font-mono text-red-500">{'>'} TOP</span>}
          <span className="text-sm font-mono font-medium text-gray-900">{player.username}</span>
          <ConfidenceBadge level={player.confidence} />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-600">{player.suspicion_score.toFixed(0)}%</span>
          <span className="text-[10px] text-gray-400">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      <div className="mt-2">
        <SuspicionBar score={player.suspicion_score} />
      </div>

      {expanded && (
        <div className="mt-3 space-y-3 animate-fade-in-up">
          {/* Reasons */}
          {player.reasons.length > 0 && (
            <div>
              <div className="text-[10px] font-mono text-gray-500 mb-1 tracking-wider">REASONS</div>
              <div className="space-y-1">
                {player.reasons.map((reason, i) => (
                  <div key={i} className="flex items-start gap-1.5">
                    <span className="text-cyan-500 text-[10px] mt-0.5">{'>'}</span>
                    <span className="text-[11px] font-mono text-gray-700">{reason}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Behavior Metrics */}
          {player.behavior_metrics.length > 0 && (
            <div>
              <div className="text-[10px] font-mono text-gray-500 mb-1 tracking-wider">BEHAVIOR METRICS</div>
              <div className="space-y-1.5">
                {player.behavior_metrics.map((m) => (
                  <MetricBar key={m.name} metric={m} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Scanning animation
// ---------------------------------------------------------------------------

function ScanningAnimation() {
  const [dots, setDots] = useState('')

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '' : prev + '.'))
    }, 400)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="text-center py-8 space-y-4">
      <div className="inline-flex items-center gap-2">
        <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-mono text-gray-700">Analyzing behavior{dots}</span>
      </div>
      <div className="text-[10px] font-mono text-gray-500">
        Processing interaction patterns, social graph, and voting history
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function SignalAIAnalysisPanel({
  signalAIResult,
  onScan,
  scansUsed,
  scansRemaining,
}: SignalAIAnalysisPanelProps) {
  const [state, setState] = useState<PanelState>('idle')
  const [report, setReport] = useState<SignalAIResultEvent['report'] | null>(null)
  const [errorMsg, setErrorMsg] = useState<string>('')
  const [scansUsedState, setScansUsedState] = useState(scansUsed)
  const [scansRemainingState, setScansRemainingState] = useState(scansRemaining)

  // React to WS results
  useEffect(() => {
    if (!signalAIResult) return

    if (signalAIResult.status === 'ready' && signalAIResult.report) {
      setReport(signalAIResult.report)
      setScansUsedState(signalAIResult.report.scans_used)
      setScansRemainingState(signalAIResult.report.scans_remaining)
      // Brief delay so the scanning animation is visible
      setTimeout(() => setState('ready'), 800)
    } else if (signalAIResult.status === 'cooldown') {
      setErrorMsg(signalAIResult.message ?? 'Cooldown active')
      setScansUsedState(signalAIResult.scans_used ?? scansUsedState)
      setScansRemainingState(signalAIResult.scans_remaining ?? scansRemainingState)
      setState('cooldown')
    } else if (signalAIResult.status === 'error') {
      setErrorMsg(signalAIResult.message ?? 'Analysis failed')
      setState('error')
    }
  }, [signalAIResult])

  const handleScan = useCallback(() => {
    setState('scanning')
    setErrorMsg('')
    setReport(null)
    onScan()
  }, [onScan])

  const handleDismiss = useCallback(() => {
    setState('idle')
    setReport(null)
    setErrorMsg('')
  }, [])

  const canScan = state === 'idle' || state === 'error' || state === 'cooldown'

  return (
    <div className="border border-gray-300/50 rounded bg-white animate-fade-in-up">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-cyan-500 rounded-full" />
          <span className="text-xs font-mono font-bold tracking-wider text-gray-900">SIGNAL AI</span>
          <span className="text-[10px] font-mono text-gray-500">v0.1</span>
        </div>
        <div className="text-[10px] font-mono text-gray-500">
          {scansUsedState}/4 scans used
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Idle state */}
        {state === 'idle' && (
          <div className="text-center py-4 space-y-3">
            <p className="text-xs font-mono text-gray-600">
              Behavioral analysis available during Discussion phase.
            </p>
            <button
              onClick={handleScan}
              disabled={!canScan}
              className="px-5 py-2 border border-cyan-500/50 rounded text-xs font-mono font-bold tracking-wider text-cyan-600 bg-cyan-50 hover:bg-cyan-100 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              ANALYZE ROOM
            </button>
            <div className="text-[10px] font-mono text-gray-400">
              {scansRemainingState} scans remaining this match
            </div>
          </div>
        )}

        {/* Scanning state */}
        {state === 'scanning' && <ScanningAnimation />}

        {/* Ready state */}
        {state === 'ready' && report && (
          <div className="space-y-4">
            {/* Summary header */}
            <div className="text-center">
              <div className="text-[10px] font-mono text-gray-500 tracking-wider mb-1">ANALYSIS COMPLETE</div>
              {report.most_suspicious && (
                <div>
                  <div className="text-[10px] font-mono text-gray-500">MOST SUSPICIOUS</div>
                  <div className="text-lg font-mono font-bold text-gray-900">
                    {report.most_suspicious.username}
                  </div>
                  <SuspicionBar score={report.most_suspicious.suspicion_score} />
                  <div className="mt-1">
                    <ConfidenceBadge level={report.most_suspicious.confidence} />
                  </div>
                </div>
              )}
            </div>

            {/* All players */}
            <div className="space-y-2">
              {report.all_players
                .sort((a, b) => b.suspicion_score - a.suspicion_score)
                .map((player, i) => (
                  <PlayerSuspicionCard
                    key={player.user_id}
                    player={player}
                    isTop={i === 0}
                  />
                ))}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-2 border-t border-gray-200">
              <span className="text-[10px] font-mono text-gray-400">
                Round {report.round_number} &middot; {report.model_version}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={handleDismiss}
                  className="px-3 py-1 text-[10px] font-mono text-gray-500 border border-gray-300/50 rounded hover:bg-gray-50 transition-all"
                >
                  DISMISS
                </button>
                {scansRemainingState > 0 && (
                  <button
                    onClick={handleScan}
                    className="px-3 py-1 text-[10px] font-mono text-cyan-600 border border-cyan-400/50 rounded hover:bg-cyan-50 transition-all"
                  >
                    SCAN AGAIN
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error state */}
        {state === 'error' && (
          <div className="text-center py-4 space-y-3">
            <div className="text-xs font-mono text-red-500">{errorMsg}</div>
            <button
              onClick={handleScan}
              className="px-4 py-1.5 text-[10px] font-mono text-gray-600 border border-gray-300/50 rounded hover:bg-gray-50 transition-all"
            >
              RETRY
            </button>
          </div>
        )}

        {/* Cooldown state */}
        {state === 'cooldown' && (
          <div className="text-center py-4 space-y-2">
            <div className="text-xs font-mono text-orange-600">{errorMsg}</div>
            <div className="text-[10px] font-mono text-gray-500">
              {scansRemainingState} scans remaining this match
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
