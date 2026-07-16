import { useState, useEffect } from 'react'
import { AdminTopBar } from '../components/TopBar'
import { MetricCard } from '../components/MetricCard'
import { MetricGrid } from '../components/MetricGrid'
import { SparkLine } from '../components/SparkLine'
import { ChartCard } from '../components/ChartCard'
import { ActivityFeed } from '../components/ActivityFeed'
import { MatchTable } from '../components/MatchTable'
import { ServiceStatusCard } from '../components/ServiceStatusCard'
import { SectionHeader } from '../components/SectionHeader'
import {
  fetchPlatformMetrics,
  fetchServices,
  fetchActiveMatches,
  fetchActivityFeed,
  fetchHourlyMessageVolume,
  fetchHourlyPlayerCount,
  fetchBackendLatencyHistory,
} from '../services/adminApi'

import type {
  PlatformMetrics,
  ServiceHealth,
  ActiveMatch,
  ActivityEvent,
  TimeSeriesPoint,
} from '../types/admin.types'

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function AdminOverview() {
  const [metrics, setMetrics] = useState<PlatformMetrics | null>(null)
  const [services, setServices] = useState<ServiceHealth[]>([])
  const [matches, setMatches] = useState<ActiveMatch[]>([])
  const [activity, setActivity] = useState<ActivityEvent[]>([])
  const [msgVolume, setMsgVolume] = useState<TimeSeriesPoint[]>([])
  const [playerCount, setPlayerCount] = useState<TimeSeriesPoint[]>([])
  const [latency, setLatency] = useState<TimeSeriesPoint[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetchPlatformMetrics(),
      fetchServices(),
      fetchActiveMatches(),
      fetchActivityFeed(),
      fetchHourlyMessageVolume(),
      fetchHourlyPlayerCount(),
      fetchBackendLatencyHistory(),
    ]).then(([m, s, ma, a, mv, pc, l]) => {
      setMetrics(m)
      setServices(s)
      setMatches(ma)
      setActivity(a)
      setMsgVolume(mv)
      setPlayerCount(pc)
      setLatency(l)
      setLoading(false)
    })
  }, [])

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xs font-mono text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> Loading dashboard...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <AdminTopBar
        title="Overview"
        subtitle="Platform metrics and real-time activity"
      />

      {/* Primary Metrics */}
      <SectionHeader
        title="Platform Metrics"
        subtitle="Current system state"
      />
      <MetricGrid columns={4}>
        <MetricCard label="Players Online" value={metrics.players_online} />
        <MetricCard label="Active Rooms" value={metrics.active_rooms} />
        <MetricCard label="Games Running" value={metrics.games_running} />
        <MetricCard label="WebSockets" value={metrics.connected_websockets} />
      </MetricGrid>

      {/* Secondary Metrics */}
      <MetricGrid columns={4}>
        <MetricCard
          label="Avg Game Duration"
          value={formatDuration(metrics.avg_game_duration_seconds)}
        />
        <MetricCard
          label="Avg Round Duration"
          value={formatDuration(metrics.avg_round_duration_seconds)}
        />
        <MetricCard
          label="Messages/sec"
          value={metrics.messages_per_second.toFixed(1)}
        />
        <MetricCard label="Error Rate" value={`${metrics.error_rate}%`} />
      </MetricGrid>

      {/* Game Performance */}
      <MetricGrid columns={4}>
        <MetricCard
          label="Coordinator Win Rate"
          value={`${metrics.coordinator_win_rate}%`}
          change={2.1}
          changeLabel="vs last week"
        />
        <MetricCard
          label="Mission Success Rate"
          value={`${metrics.mission_success_rate}%`}
          change={-1.3}
          changeLabel="vs last week"
        />
        <MetricCard
          label="AI Accuracy"
          value={`${metrics.ai_accuracy}%`}
          change={0.5}
          changeLabel="vs last week"
        />
        <MetricCard
          label="Backend Response"
          value={metrics.backend_response_time_ms}
          unit="ms"
        />
      </MetricGrid>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-3 max-lg:grid-cols-1">
        <ChartCard title="Messages / Hour" subtitle="Last 24h">
          <SparkLine
            values={msgVolume.map((p) => p.value)}
            height={50}
            color="#ef4444"
          />
        </ChartCard>
        <ChartCard title="Players Online" subtitle="Last 24h">
          <SparkLine
            values={playerCount.map((p) => p.value)}
            height={50}
            color="#22d3ee"
          />
        </ChartCard>
        <ChartCard title="Backend Latency" subtitle="Last 24h">
          <SparkLine
            values={latency.map((p) => p.value)}
            height={50}
            color="#a78bfa"
          />
        </ChartCard>
      </div>

      {/* Active Matches */}
      <SectionHeader title="Active Matches" subtitle={`${matches.length} in progress`} />
      <MatchTable matches={matches} />

      {/* Bottom Row: Services + Activity */}
      <div className="grid grid-cols-3 gap-3 max-lg:grid-cols-1">
        {/* Service Status */}
        <div className="col-span-1">
          <SectionHeader title="Services" subtitle="Health status" />
          <div className="space-y-2">
            {services.map((service) => (
              <ServiceStatusCard key={service.id} {...service} />
            ))}
          </div>
        </div>

        {/* Activity Feed */}
        <div className="col-span-2">
          <SectionHeader title="Activity" subtitle="Recent platform events" />
          <ActivityFeed events={activity} />
        </div>
      </div>
    </div>
  )
}
