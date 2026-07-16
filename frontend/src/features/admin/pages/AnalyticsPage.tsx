import { useState, useEffect } from 'react'
import { AdminTopBar } from '../components/TopBar'
import { MetricCard } from '../components/MetricCard'
import { MetricGrid } from '../components/MetricGrid'
import { ChartCard } from '../components/ChartCard'
import { SparkBar } from '../components/SparkBar'
import { SparkLine } from '../components/SparkLine'
import { fetchAnalyticsMetrics } from '../services/adminApi'

import type { AnalyticsMetrics } from '../types/admin.types'

export function AnalyticsPage() {
  const [metrics, setMetrics] = useState<AnalyticsMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalyticsMetrics().then((m) => {
      setMetrics(m)
      setLoading(false)
    })
  }, [])

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xs font-mono text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> Loading analytics...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <AdminTopBar
        title="Analytics"
        subtitle="Game performance, player behavior, and trends"
      />

      {/* Summary Metrics */}
      <MetricGrid columns={4}>
        <MetricCard
          label="Avg Messages/Game"
          value={metrics.avg_messages_per_game.toFixed(1)}
        />
        <MetricCard
          label="Avg Round Duration"
          value={`${metrics.avg_round_duration}s`}
        />
        <MetricCard
          label="Total Games"
          value={metrics.games_per_day.reduce((s, d) => s + d.count, 0)}
        />
        <MetricCard
          label="Top Mission"
          value={metrics.most_common_missions[0]?.type ?? 'N/A'}
        />
      </MetricGrid>

      {/* Charts Grid */}
      <div className="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
        {/* Games Per Day */}
        <ChartCard title="Games Per Day" subtitle="Last 7 days">
          <SparkBar
            data={metrics.games_per_day.map((d) => ({
              label: d.date.slice(5),
              value: d.count,
            }))}
            height={80}
            color="#ef4444"
            showLabels
          />
        </ChartCard>

        {/* Coordinator Win Rate Trend */}
        <ChartCard title="Coordinator Win Rate" subtitle="Daily trend">
          <SparkLine
            values={metrics.coordinator_win_rate_trend.map((d) => d.rate)}
            height={60}
            color="#ef4444"
            showDots
          />
          <div className="flex justify-between mt-1 text-[8px] font-mono text-gray-600">
            {metrics.coordinator_win_rate_trend.map((d) => (
              <span key={d.date}>{d.date.slice(5)}</span>
            ))}
          </div>
        </ChartCard>

        {/* Conversation Volume */}
        <ChartCard title="Conversation Volume" subtitle="Messages per day">
          <SparkLine
            values={metrics.conversation_volume.map((d) => d.messages)}
            height={60}
            color="#22d3ee"
            showDots
          />
          <div className="flex justify-between mt-1 text-[8px] font-mono text-gray-600">
            {metrics.conversation_volume.map((d) => (
              <span key={d.date}>{d.date}</span>
            ))}
          </div>
        </ChartCard>

        {/* Mission Completion Rates */}
        <ChartCard title="Mission Completion" subtitle="By type">
          <div className="space-y-2">
            {metrics.most_common_missions.map((m) => (
              <div key={m.type} className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-gray-500 w-28 truncate">
                  {m.type}
                </span>
                <div className="flex-1 h-2 bg-gray-800 rounded overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded transition-all duration-500"
                    style={{ width: `${m.completion_rate * 100}%` }}
                  />
                </div>
                <span className="text-[10px] font-mono text-gray-500 w-12 text-right">
                  {(m.completion_rate * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      {/* Player Retention */}
      <ChartCard title="Player Retention" subtitle="Funnel: games played">
        <div className="flex items-end gap-3 h-24">
          {metrics.player_retention.map((bucket) => (
            <div key={bucket.label} className="flex-1 flex flex-col items-center gap-1">
              <span className="text-[10px] font-mono text-gray-400">
                {bucket.percentage}%
              </span>
              <div
                className="w-full bg-accent/60 rounded-t transition-all duration-500"
                style={{ height: `${bucket.percentage}%` }}
              />
              <span className="text-[9px] font-mono text-gray-600 text-center">
                {bucket.label}
              </span>
            </div>
          ))}
        </div>
      </ChartCard>
    </div>
  )
}
