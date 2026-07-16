import { useState, useEffect } from 'react'
import { AdminTopBar } from '../components/TopBar'
import { MetricCard } from '../components/MetricCard'
import { MetricGrid } from '../components/MetricGrid'
import { ChartCard } from '../components/ChartCard'
import { SparkBar } from '../components/SparkBar'
import { fetchReplayMetrics } from '../services/adminApi'

import type { ReplayMetrics } from '../types/admin.types'

export function ReplayEnginePage() {
  const [metrics, setMetrics] = useState<ReplayMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchReplayMetrics().then((m) => {
      setMetrics(m)
      setLoading(false)
    })
  }, [])

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xs font-mono text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> Loading replay metrics...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <AdminTopBar
        title="Replay Engine"
        subtitle="Event sourcing and replay generation metrics"
      />

      <MetricGrid columns={4}>
        <MetricCard label="Games Recorded" value={metrics.games_recorded} />
        <MetricCard label="Events Stored" value={metrics.events_stored} />
        <MetricCard
          label="Avg Generation Time"
          value={`${metrics.avg_generation_time_ms}ms`}
        />
        <MetricCard
          label="Avg Replay Size"
          value={`${metrics.avg_replay_size_kb}KB`}
        />
      </MetricGrid>

      <MetricGrid columns={4}>
        <MetricCard
          label="Largest Replay"
          value={`${metrics.largest_replay_kb}KB`}
        />
        <MetricCard label="Replay Queue" value={metrics.replay_queue} />
        <MetricCard
          label="Total Gen Time"
          value={`${(metrics.total_replay_time_ms / 1000).toFixed(1)}s`}
        />
        <MetricCard
          label="Events/Game Avg"
          value={metrics.events_per_game_avg.toFixed(1)}
        />
      </MetricGrid>

      <div className="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
        <ChartCard title="Events Per Game" subtitle="Distribution">
          <SparkBar
            data={Array.from({ length: 10 }, (_, i) => ({
              label: `G${i + 1}`,
              value: Math.floor(Math.random() * 60 + 20),
            }))}
            height={80}
            color="#a78bfa"
            showLabels
          />
        </ChartCard>
        <ChartCard title="Generation Time" subtitle="Last 10 games (ms)">
          <SparkBar
            data={Array.from({ length: 10 }, (_, i) => ({
              label: `G${i + 1}`,
              value: Math.floor(Math.random() * 300 + 150),
            }))}
            height={80}
            color="#22d3ee"
            showLabels
          />
        </ChartCard>
      </div>
    </div>
  )
}
