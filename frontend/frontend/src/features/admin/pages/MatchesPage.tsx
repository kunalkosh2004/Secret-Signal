import { useState, useEffect } from 'react'
import { AdminTopBar } from '../components/TopBar'
import { MatchTable } from '../components/MatchTable'
import { SectionHeader } from '../components/SectionHeader'
import { MetricCard } from '../components/MetricCard'
import { MetricGrid } from '../components/MetricGrid'
import { fetchActiveMatches } from '../services/adminApi'

import type { ActiveMatch } from '../types/admin.types'

export function MatchesPage() {
  const [matches, setMatches] = useState<ActiveMatch[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchActiveMatches().then((m) => {
      setMatches(m)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xs font-mono text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> Loading matches...
        </div>
      </div>
    )
  }

  const totalPlayers = matches.reduce((sum, m) => sum + m.players.length, 0)

  return (
    <div className="space-y-6">
      <AdminTopBar
        title="Active Matches"
        subtitle="Real-time game monitoring"
      />

      <MetricGrid columns={4}>
        <MetricCard label="Active Matches" value={matches.length} />
        <MetricCard label="Total Players" value={totalPlayers} />
        <MetricCard
          label="Avg Latency"
          value={`${Math.round(matches.reduce((s, m) => s + m.avg_latency_ms, 0) / (matches.length || 1))}ms`}
        />
        <MetricCard
          label="AI Scans"
          value={matches.reduce((s, m) => s + m.signal_ai_usage, 0)}
        />
      </MetricGrid>

      <SectionHeader
        title="All Active Matches"
        subtitle="Click a row for match details"
      />
      <MatchTable matches={matches} />
    </div>
  )
}
